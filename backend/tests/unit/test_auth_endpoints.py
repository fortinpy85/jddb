"""
Tests for authentication API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status

from jd_ingestion.api.main import app
from jd_ingestion.auth.models import User, UserSession
from jd_ingestion.auth.service import UserService, SessionService, PreferenceService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock user instance."""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.role = "user"
    user.department = "IT"
    user.security_clearance = "basic"
    user.preferred_language = "en"
    user.is_active = True
    user.last_login = datetime.utcnow()
    user.created_at = datetime.utcnow()
    return user


@pytest.fixture
def mock_session():
    """Mock session instance."""
    session = Mock(spec=UserSession)
    session.id = 1
    session.user_id = 1
    session.session_token = "test_session_token"
    session.expires_at = datetime.utcnow() + timedelta(hours=24)
    session.is_valid = True
    return session


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    def test_register_user_success(self, mock_get_service, client, mock_user):
        """Test successful user registration."""
        mock_service = AsyncMock(spec=UserService)
        mock_service.create_user = AsyncMock(return_value=mock_user)
        mock_get_service.return_value = mock_service

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "user",
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    def test_register_user_failure(self, mock_get_service, client):
        """Test user registration failure."""
        mock_service = AsyncMock(spec=UserService)
        mock_service.create_user.side_effect = ValueError("Username already exists")
        mock_get_service.return_value = mock_service

        user_data = {
            "username": "existinguser",
            "email": "test@example.com",
            "password": "password123",
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already exists" in response.json()["detail"]

    def test_register_user_invalid_data(self, client):
        """Test user registration with invalid data."""
        user_data = {
            "username": "te",  # Too short
            "email": "invalid-email",
            "password": "123",  # Too short
        }

        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("jd_ingestion.api.endpoints.auth.get_session_service")
    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    @patch("jd_ingestion.api.endpoints.auth.create_access_token")
    def test_login_success(
        self,
        mock_create_token,
        mock_get_user_service,
        mock_get_session_service,
        client,
        mock_user,
        mock_session,
    ):
        """Test successful login."""
        mock_user_service = AsyncMock(spec=UserService)
        mock_session_service = AsyncMock(spec=SessionService)

        mock_user_service.authenticate_user = AsyncMock(return_value=mock_user)
        mock_session_service.create_session = AsyncMock(return_value=mock_session)
        mock_create_token.return_value = "test_access_token"

        mock_get_user_service.return_value = mock_user_service
        mock_get_session_service.return_value = mock_session_service

        form_data = {"username": "testuser", "password": "password123"}

        response = client.post("/api/auth/login", data=form_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["access_token"] == "test_access_token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
        assert data["user"]["username"] == "testuser"

    @patch("jd_ingestion.api.endpoints.auth.get_session_service")
    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    def test_login_email_fallback(
        self,
        mock_get_user_service,
        mock_get_session_service,
        client,
        mock_user,
        mock_session,
    ):
        """Test login with email fallback."""
        mock_user_service = AsyncMock(spec=UserService)
        mock_session_service = AsyncMock(spec=SessionService)

        # First auth attempt fails, second succeeds
        mock_user_service.authenticate_user.side_effect = [None, mock_user]
        mock_user_service.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_session_service.create_session = AsyncMock(return_value=mock_session)

        mock_get_user_service.return_value = mock_user_service
        mock_get_session_service.return_value = mock_session_service

        with patch(
            "jd_ingestion.api.endpoints.auth.create_access_token",
            return_value="test_token",
        ):
            form_data = {"username": "test@example.com", "password": "password123"}

            response = client.post("/api/auth/login", data=form_data)
            assert response.status_code == status.HTTP_200_OK

    @patch("jd_ingestion.api.endpoints.auth.get_session_service")
    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    def test_login_failure(
        self, mock_get_user_service, mock_get_session_service, client
    ):
        """Test login failure."""
        mock_user_service = AsyncMock(spec=UserService)
        mock_session_service = AsyncMock(spec=SessionService)

        mock_user_service.authenticate_user = AsyncMock(return_value=None)
        mock_user_service.get_user_by_email = AsyncMock(return_value=None)

        mock_get_user_service.return_value = mock_user_service
        mock_get_session_service.return_value = mock_session_service

        form_data = {"username": "wronguser", "password": "wrongpassword"}

        response = client.post("/api/auth/login", data=form_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.auth.get_session_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_logout_success(
        self, mock_get_current_user, mock_get_session_service, client, mock_user
    ):
        """Test successful logout."""
        mock_get_current_user.return_value = mock_user
        mock_session_service = AsyncMock(spec=SessionService)
        mock_get_session_service.return_value = mock_session_service

        response = client.post(
            "/api/auth/logout", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Successfully logged out" in response.json()["message"]

    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_get_current_user_info(self, mock_get_current_user, client, mock_user):
        """Test getting current user info."""
        mock_get_current_user.return_value = mock_user

        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_update_current_user(
        self, mock_get_current_user, mock_get_user_service, client, mock_user
    ):
        """Test updating current user profile."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=UserService)

        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.username = "testuser"
        updated_user.email = "newemail@example.com"
        updated_user.first_name = "Updated"
        updated_user.last_name = "User"
        updated_user.role = "user"
        updated_user.department = "IT"
        updated_user.security_clearance = "basic"
        updated_user.preferred_language = "en"
        updated_user.is_active = True
        updated_user.last_login = datetime.utcnow()
        updated_user.created_at = datetime.utcnow()

        mock_service.update_user = AsyncMock(return_value=updated_user)
        mock_get_user_service.return_value = mock_service

        update_data = {"email": "newemail@example.com", "first_name": "Updated"}

        response = client.put(
            "/api/auth/me",
            json=update_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["email"] == "newemail@example.com"
        assert data["first_name"] == "Updated"

    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_change_password_success(
        self, mock_get_current_user, mock_get_user_service, client, mock_user
    ):
        """Test successful password change."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=UserService)
        mock_service.change_password = AsyncMock(return_value=True)
        mock_get_user_service.return_value = mock_service

        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123",
        }

        response = client.post(
            "/api/auth/change-password",
            json=password_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Password successfully changed" in response.json()["message"]

    @patch("jd_ingestion.api.endpoints.auth.get_user_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_change_password_failure(
        self, mock_get_current_user, mock_get_user_service, client, mock_user
    ):
        """Test password change failure."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=UserService)
        mock_service.change_password = AsyncMock(return_value=False)
        mock_get_user_service.return_value = mock_service

        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        }

        response = client.post(
            "/api/auth/change-password",
            json=password_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Current password is incorrect" in response.json()["detail"]

    @patch("jd_ingestion.api.endpoints.auth.get_preference_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_get_user_preferences(
        self, mock_get_current_user, mock_get_preference_service, client, mock_user
    ):
        """Test getting user preferences."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=PreferenceService)
        mock_service.get_all_preferences = AsyncMock(
            return_value={"theme": "dark", "language": "en"}
        )
        mock_get_preference_service.return_value = mock_service

        response = client.get(
            "/api/auth/preferences", headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["preferences"]["theme"] == "dark"
        assert data["preferences"]["language"] == "en"

    @patch("jd_ingestion.api.endpoints.auth.get_preference_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_set_user_preference(
        self, mock_get_current_user, mock_get_preference_service, client, mock_user
    ):
        """Test setting user preference."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=PreferenceService)

        mock_preference = Mock()
        mock_preference.preference_key = "theme"
        mock_preference.preference_value = "dark"
        mock_service.set_preference = AsyncMock(return_value=mock_preference)
        mock_get_preference_service.return_value = mock_service

        preference_data = {"key": "theme", "value": "dark"}

        response = client.post(
            "/api/auth/preferences",
            json=preference_data,
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["key"] == "theme"
        assert data["value"] == "dark"

    @patch("jd_ingestion.api.endpoints.auth.get_preference_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_get_user_preference(
        self, mock_get_current_user, mock_get_preference_service, client, mock_user
    ):
        """Test getting specific user preference."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=PreferenceService)
        mock_service.get_preference = AsyncMock(return_value="dark")
        mock_get_preference_service.return_value = mock_service

        response = client.get(
            "/api/auth/preferences/theme",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["key"] == "theme"
        assert data["value"] == "dark"

    @patch("jd_ingestion.api.endpoints.auth.get_preference_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_get_user_preference_not_found(
        self, mock_get_current_user, mock_get_preference_service, client, mock_user
    ):
        """Test getting non-existent preference."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=PreferenceService)
        mock_service.get_preference = AsyncMock(return_value=None)
        mock_get_preference_service.return_value = mock_service

        response = client.get(
            "/api/auth/preferences/nonexistent",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch("jd_ingestion.api.endpoints.auth.get_preference_service")
    @patch("jd_ingestion.auth.dependencies.get_current_user")
    def test_delete_user_preference(
        self, mock_get_current_user, mock_get_preference_service, client, mock_user
    ):
        """Test deleting user preference."""
        mock_get_current_user.return_value = mock_user
        mock_service = AsyncMock(spec=PreferenceService)
        mock_service.delete_preference = AsyncMock(return_value=True)
        mock_get_preference_service.return_value = mock_service

        response = client.delete(
            "/api/auth/preferences/theme",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "Preference deleted successfully" in response.json()["message"]

    @patch("jd_ingestion.auth.dependencies.get_optional_current_user")
    def test_auth_status_authenticated(self, mock_get_optional_user, client, mock_user):
        """Test auth status when authenticated."""
        mock_get_optional_user.return_value = mock_user

        response = client.get("/api/auth/status")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["username"] == "testuser"

    @patch("jd_ingestion.auth.dependencies.get_optional_current_user")
    def test_auth_status_not_authenticated(self, mock_get_optional_user, client):
        """Test auth status when not authenticated."""
        mock_get_optional_user.return_value = None

        response = client.get("/api/auth/status")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["authenticated"] is False

    @patch("jd_ingestion.api.endpoints.auth.get_session_service")
    def test_cleanup_expired_sessions(self, mock_get_session_service, client):
        """Test cleanup of expired sessions."""
        mock_service = AsyncMock(spec=SessionService)
        mock_service.cleanup_expired_sessions = AsyncMock(return_value=5)
        mock_get_session_service.return_value = mock_service

        response = client.post("/api/auth/cleanup-sessions")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "Cleaned up 5 expired sessions" in data["message"]
