"""
Unit tests for the LightcastClient.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import httpx

from jd_ingestion.services.lightcast_client import (
    LightcastClient,
    LightcastAuthToken,
    ExtractedSkill,
)


@pytest.mark.unit
class TestLightcastAuthToken:
    """Test LightcastAuthToken model."""

    def test_token_initialization(self):
        """Test token initialization calculates expiration correctly."""
        token = LightcastAuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        assert token.access_token == "test_token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert token.expires_at is not None
        # Should expire in about 55 minutes (3600 - 300 second buffer)
        expected_expiry = datetime.utcnow() + timedelta(seconds=3300)
        assert abs((token.expires_at - expected_expiry).total_seconds()) < 5

    def test_token_is_expired(self):
        """Test token expiration check."""
        # Create an expired token
        token = LightcastAuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )
        # Manually set expiration to the past
        token.expires_at = datetime.utcnow() - timedelta(minutes=5)

        assert token.is_expired() is True

    def test_token_not_expired(self):
        """Test token not expired check."""
        token = LightcastAuthToken(
            access_token="test_token",
            token_type="Bearer",
            expires_in=3600,
        )

        assert token.is_expired() is False


@pytest.mark.unit
class TestLightcastClient:
    """Test LightcastClient functionality."""

    @pytest.fixture
    def client(self):
        """Create LightcastClient instance."""
        with patch("jd_ingestion.services.lightcast_client.settings") as mock_settings:
            mock_settings.lightcast_client_id = "test_client_id"
            mock_settings.lightcast_client_secret = "test_secret"
            mock_settings.lightcast_scope = "emsi_open"
            mock_settings.lightcast_api_base_url = "https://auth.emsicloud.com"
            mock_settings.lightcast_request_timeout = 30
            mock_settings.lightcast_max_retries = 3
            return LightcastClient()

    @pytest.fixture
    def mock_token_response(self):
        """Mock token response from Lightcast API."""
        return {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

    @pytest.fixture
    def mock_skills_response(self):
        """Mock skills extraction response from Lightcast API."""
        return {
            "data": [
                {
                    "skill": {
                        "id": "KS123456",
                        "name": "Python",
                        "type": "Hard Skill",
                    },
                    "confidence": 0.95,
                },
                {
                    "skill": {
                        "id": "KS789012",
                        "name": "Project Management",
                        "type": "Soft Skill",
                    },
                    "confidence": 0.87,
                },
            ]
        }

    @pytest.mark.asyncio
    async def test_authenticate_success(self, client, mock_token_response):
        """Test successful authentication."""
        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        token = await client._authenticate()

        assert isinstance(token, LightcastAuthToken)
        assert token.access_token == "mock_access_token"
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
        assert client._token == token

        # Verify the request was made correctly
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == client.auth_url
        assert call_args[1]["data"]["client_id"] == "test_client_id"
        assert call_args[1]["data"]["grant_type"] == "client_credentials"

    @pytest.mark.asyncio
    async def test_authenticate_http_error(self, client):
        """Test authentication with HTTP error."""
        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(side_effect=httpx.HTTPError("Auth failed"))

        client._http_client = mock_http_client

        with pytest.raises(httpx.HTTPError):
            await client._authenticate()

    @pytest.mark.asyncio
    async def test_get_valid_token_no_token(self, client, mock_token_response):
        """Test getting valid token when no token exists."""
        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client
        client._token = None

        token = await client._get_valid_token()

        assert token == "mock_access_token"
        assert client._token is not None
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_expired_token(self, client, mock_token_response):
        """Test getting valid token when existing token is expired."""
        # Set up expired token
        expired_token = LightcastAuthToken(**mock_token_response)
        expired_token.expires_at = datetime.utcnow() - timedelta(minutes=5)
        client._token = expired_token

        mock_response = Mock()
        mock_response.json.return_value = mock_token_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.post = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        token = await client._get_valid_token()

        assert token == "mock_access_token"
        # Should have called authenticate to refresh
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_valid_token(self, client, mock_token_response):
        """Test getting valid token when token is still valid."""
        # Set up valid token
        valid_token = LightcastAuthToken(**mock_token_response)
        client._token = valid_token

        mock_http_client = AsyncMock()
        client._http_client = mock_http_client

        token = await client._get_valid_token()

        assert token == "mock_access_token"
        # Should NOT have called authenticate
        mock_http_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_make_request_success(self, client, mock_token_response):
        """Test successful API request."""
        # Set up valid token
        client._token = LightcastAuthToken(**mock_token_response)

        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        result = await client._make_request("GET", "https://api.test.com/endpoint")

        assert result == {"result": "success"}
        mock_http_client.request.assert_called_once()
        # Check Authorization header was set
        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer mock_access_token"

    @pytest.mark.asyncio
    async def test_make_request_401_retry(self, client, mock_token_response):
        """Test request retry on 401 Unauthorized."""
        # Set up valid token
        client._token = LightcastAuthToken(**mock_token_response)

        # First request returns 401, second succeeds
        mock_401_response = Mock()
        mock_401_response.status_code = 401
        mock_401_error = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_401_response
        )

        mock_success_response = Mock()
        mock_success_response.json.return_value = {"result": "success"}
        mock_success_response.raise_for_status = Mock()

        # Mock authentication response
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_auth_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        # First call raises 401, second succeeds
        mock_http_client.request = AsyncMock(
            side_effect=[mock_401_error, mock_success_response]
        )
        # Post for re-authentication
        mock_http_client.post = AsyncMock(return_value=mock_auth_response)

        client._http_client = mock_http_client

        result = await client._make_request("GET", "https://api.test.com/endpoint")

        assert result == {"result": "success"}
        # Should have retried
        assert mock_http_client.request.call_count == 2
        # Should have re-authenticated
        mock_http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_max_retries(self, client, mock_token_response):
        """Test request fails after max retries."""
        client._token = LightcastAuthToken(**mock_token_response)

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )

        client._http_client = mock_http_client

        with pytest.raises(httpx.HTTPError):
            await client._make_request("GET", "https://api.test.com/endpoint")

        # Should have retried max_retries + 1 times
        assert mock_http_client.request.call_count == client.max_retries + 1

    @pytest.mark.asyncio
    async def test_extract_skills_success(
        self, client, mock_token_response, mock_skills_response
    ):
        """Test successful skills extraction."""
        client._token = LightcastAuthToken(**mock_token_response)

        mock_response = Mock()
        mock_response.json.return_value = mock_skills_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        skills = await client.extract_skills(
            "Looking for a Python developer with project management skills"
        )

        assert len(skills) == 2
        assert all(isinstance(skill, ExtractedSkill) for skill in skills)

        # Check first skill
        assert skills[0].id == "KS123456"
        assert skills[0].name == "Python"
        assert skills[0].confidence == 0.95
        assert skills[0].type == "Hard Skill"

        # Check second skill
        assert skills[1].id == "KS789012"
        assert skills[1].name == "Project Management"
        assert skills[1].confidence == 0.87
        assert skills[1].type == "Soft Skill"

        # Verify request was made correctly
        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "extract" in call_args[0][1]
        assert call_args[1]["json"]["confidenceThreshold"] == 0.5

    @pytest.mark.asyncio
    async def test_extract_skills_with_custom_threshold(
        self, client, mock_token_response, mock_skills_response
    ):
        """Test skills extraction with custom confidence threshold."""
        client._token = LightcastAuthToken(**mock_token_response)

        mock_response = Mock()
        mock_response.json.return_value = mock_skills_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        await client.extract_skills("test text", confidence_threshold=0.8)

        # Verify threshold was passed correctly
        call_args = mock_http_client.request.call_args
        assert call_args[1]["json"]["confidenceThreshold"] == 0.8

    @pytest.mark.asyncio
    async def test_extract_skills_empty_response(self, client, mock_token_response):
        """Test skills extraction with empty response."""
        client._token = LightcastAuthToken(**mock_token_response)

        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        skills = await client.extract_skills("test text")

        assert len(skills) == 0
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_extract_skills_http_error(self, client, mock_token_response):
        """Test skills extraction with HTTP error."""
        client._token = LightcastAuthToken(**mock_token_response)

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(side_effect=httpx.HTTPError("API Error"))

        client._http_client = mock_http_client

        with pytest.raises(httpx.HTTPError):
            await client.extract_skills("test text")

    @pytest.mark.asyncio
    async def test_extract_skills_with_trace(self, client, mock_token_response):
        """Test skills extraction with trace information."""
        client._token = LightcastAuthToken(**mock_token_response)

        trace_response = {
            "data": [
                {
                    "skill": {"id": "KS123", "name": "Python"},
                    "confidence": 0.9,
                    "trace": [{"startIndex": 10, "endIndex": 16}],
                }
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = trace_response
        mock_response.raise_for_status = Mock()

        mock_http_client = AsyncMock()
        mock_http_client.request = AsyncMock(return_value=mock_response)

        client._http_client = mock_http_client

        result = await client.extract_skills_with_trace("test text")

        assert result == trace_response
        # Verify correct endpoint was called
        call_args = mock_http_client.request.call_args
        assert "extract/trace" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_http_client_lifecycle(self, client):
        """Test HTTP client creation and cleanup."""
        # Initially no client
        assert client._http_client is None

        # Get client creates it
        http_client = await client._get_http_client()
        assert http_client is not None
        assert isinstance(http_client, httpx.AsyncClient)

        # Getting again returns same client
        http_client2 = await client._get_http_client()
        assert http_client2 is http_client

        # Close cleans up
        await client.close()
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self, client):
        """Test closing client when no HTTP client exists."""
        # Should not raise an error
        await client.close()
        assert client._http_client is None
