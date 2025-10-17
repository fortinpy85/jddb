"""
Tests for authentication API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi import status

from jd_ingestion.api.main import app
from jd_ingestion.auth.models import User, UserSession
from jd_ingestion.auth.service import UserService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_user() -> User:
    """Mock user instance."""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        # Use pre-hashed password to avoid bcrypt backend issues in tests
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqK7M8kS3i",  # hash of "testpass"
        first_name="Test",
        last_name="User",
        role="user",
        department="IT",
        security_clearance="basic",
        preferred_language="en",
        is_active=True,
        last_login=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    return user


@pytest.fixture
def mock_session(mock_user: User) -> UserSession:
    """Mock session instance."""
    token, expires_at = UserSession.create_token(user_id=mock_user.id)
    return UserSession(
        id=1,
        user_id=mock_user.id,
        session_token=token,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def auth_headers(mock_session: UserSession) -> dict:
    """Create authentication headers."""
    return {"Authorization": f"Bearer {mock_session.session_token}"}


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
