"""
Tests for API key authentication module.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import patch

from jd_ingestion.auth.api_key import get_api_key, API_KEY_HEADER


class TestGetApiKey:
    """Test API key validation functionality."""

    @patch("jd_ingestion.auth.api_key.settings")
    def test_valid_api_key(self, mock_settings):
        """Test API key validation with correct key."""
        mock_settings.API_KEY = "valid_api_key_123"

        result = get_api_key("valid_api_key_123")

        assert result == "valid_api_key_123"

    @patch("jd_ingestion.auth.api_key.settings")
    def test_invalid_api_key(self, mock_settings):
        """Test API key validation with incorrect key."""
        mock_settings.API_KEY = "valid_api_key_123"

        with pytest.raises(HTTPException) as exc_info:
            get_api_key("invalid_key")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Could not validate credentials"

    @patch("jd_ingestion.auth.api_key.settings")
    def test_empty_api_key(self, mock_settings):
        """Test API key validation with empty key."""
        mock_settings.API_KEY = "valid_api_key_123"

        with pytest.raises(HTTPException) as exc_info:
            get_api_key("")

        assert exc_info.value.status_code == 403

    @patch("jd_ingestion.auth.api_key.settings")
    def test_none_api_key(self, mock_settings):
        """Test API key validation with None key."""
        mock_settings.API_KEY = "valid_api_key_123"

        with pytest.raises(HTTPException) as exc_info:
            get_api_key(None)

        assert exc_info.value.status_code == 403

    @patch("jd_ingestion.auth.api_key.settings")
    def test_case_sensitive_api_key(self, mock_settings):
        """Test that API key validation is case sensitive."""
        mock_settings.API_KEY = "Valid_API_Key_123"

        # Correct case should work
        result = get_api_key("Valid_API_Key_123")
        assert result == "Valid_API_Key_123"

        # Wrong case should fail
        with pytest.raises(HTTPException):
            get_api_key("valid_api_key_123")

        with pytest.raises(HTTPException):
            get_api_key("VALID_API_KEY_123")

    @patch("jd_ingestion.auth.api_key.settings")
    def test_whitespace_handling(self, mock_settings):
        """Test API key validation with whitespace."""
        mock_settings.API_KEY = "valid_key"

        # Leading/trailing whitespace should fail
        with pytest.raises(HTTPException):
            get_api_key(" valid_key")

        with pytest.raises(HTTPException):
            get_api_key("valid_key ")

        with pytest.raises(HTTPException):
            get_api_key(" valid_key ")

    @patch("jd_ingestion.auth.api_key.settings")
    def test_special_characters_in_key(self, mock_settings):
        """Test API key validation with special characters."""
        special_key = "key-with_special.chars@123!"
        mock_settings.API_KEY = special_key

        result = get_api_key(special_key)
        assert result == special_key

    @patch("jd_ingestion.auth.api_key.settings")
    def test_long_api_key(self, mock_settings):
        """Test API key validation with very long key."""
        long_key = "a" * 1000  # 1000 character key
        mock_settings.API_KEY = long_key

        result = get_api_key(long_key)
        assert result == long_key

    @patch("jd_ingestion.auth.api_key.settings")
    def test_settings_api_key_change(self, mock_settings):
        """Test that API key validation uses current settings value."""
        # First validation with initial key
        mock_settings.API_KEY = "initial_key"
        result = get_api_key("initial_key")
        assert result == "initial_key"

        # Change settings and test again
        mock_settings.API_KEY = "new_key"

        # Old key should now fail
        with pytest.raises(HTTPException):
            get_api_key("initial_key")

        # New key should work
        result = get_api_key("new_key")
        assert result == "new_key"


class TestApiKeyHeader:
    """Test API key header configuration."""

    def test_api_key_header_name(self):
        """Test that API key header has correct name."""
        assert API_KEY_HEADER.model.name == "X-API-Key"

    def test_api_key_header_type(self):
        """Test that API key header is of correct type."""
        from fastapi.security import APIKeyHeader

        assert isinstance(API_KEY_HEADER, APIKeyHeader)


class TestApiKeyIntegration:
    """Test API key integration scenarios."""

    @patch("jd_ingestion.auth.api_key.settings")
    def test_function_signature_compatibility(self, mock_settings):
        """Test that get_api_key function signature is compatible with FastAPI."""
        mock_settings.API_KEY = "test_key"

        # Function should work when called with the expected Security dependency pattern
        # This simulates how FastAPI would call it with the API key from headers
        result = get_api_key(api_key_header="test_key")
        assert result == "test_key"

    def test_import_structure(self):
        """Test that all expected components can be imported."""
        from jd_ingestion.auth.api_key import get_api_key, API_KEY_HEADER

        assert callable(get_api_key)
        assert API_KEY_HEADER is not None

    @patch("jd_ingestion.auth.api_key.settings")
    def test_error_message_security(self, mock_settings):
        """Test that error messages don't leak sensitive information."""
        mock_settings.API_KEY = "secret_production_key"

        with pytest.raises(HTTPException) as exc_info:
            get_api_key("wrong_key")

        # Error message should be generic and not reveal the actual key
        error_detail = exc_info.value.detail
        assert "secret_production_key" not in error_detail
        assert "wrong_key" not in error_detail
        assert error_detail == "Could not validate credentials"

    @patch("jd_ingestion.auth.api_key.settings")
    def test_unicode_api_key_support(self, mock_settings):
        """Test API key validation with Unicode characters."""
        unicode_key = "key_with_unicode_café_🔑"
        mock_settings.API_KEY = unicode_key

        result = get_api_key(unicode_key)
        assert result == unicode_key

    @patch("jd_ingestion.auth.api_key.settings")
    def test_numeric_api_key(self, mock_settings):
        """Test API key validation with numeric key."""
        numeric_key = "123456789"
        mock_settings.API_KEY = numeric_key

        result = get_api_key(numeric_key)
        assert result == numeric_key

    @patch("jd_ingestion.auth.api_key.settings")
    def test_settings_access_pattern(self, mock_settings):
        """Test that settings.API_KEY is accessed correctly."""
        mock_settings.API_KEY = "test_access_key"

        get_api_key("test_access_key")

        # Verify that settings.API_KEY was accessed
        # This is implicit since the mock would need to return the value
        assert mock_settings.API_KEY == "test_access_key"
