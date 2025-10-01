"""
Tests for authentication services.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.auth.service import (
    UserService,
    SessionService,
    PermissionService,
    PreferenceService,
    create_access_token,
    verify_access_token,
)
from jd_ingestion.auth.models import User, UserSession, UserPermission, UserPreference


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


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
    user.set_password = Mock()
    user.verify_password = Mock(return_value=True)
    user.update_last_login = Mock()
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
    session.last_activity = datetime.utcnow()
    session.user = None  # Will be set when needed
    return session


@pytest.fixture
def mock_permission():
    """Mock permission instance."""
    permission = Mock(spec=UserPermission)
    permission.id = 1
    permission.user_id = 1
    permission.resource_type = "job_description"
    permission.resource_id = None
    permission.permission_type = "read"
    permission.granted_by = 1
    permission.expires_at = None
    permission.is_valid = True
    return permission


@pytest.fixture
def mock_preference():
    """Mock preference instance."""
    preference = Mock(spec=UserPreference)
    preference.id = 1
    preference.user_id = 1
    preference.preference_key = "theme"
    preference.preference_value = "dark"
    return preference


class TestUserService:
    """Test user service."""

    def test_init(self, mock_db):
        """Test service initialization."""
        service = UserService(mock_db)
        assert service.db == mock_db

    async def test_create_user_success(self, mock_db, mock_user):
        """Test successful user creation."""
        service = UserService(mock_db)

        # Mock database queries
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # No existing user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("jd_ingestion.auth.service.User", return_value=mock_user):
            user = await service.create_user(
                username="testuser", email="test@example.com", password="password123"
            )

            assert user == mock_user
            mock_user.set_password.assert_called_once_with("password123")
            mock_db.add.assert_called_once_with(mock_user)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_user)

    async def test_create_user_username_exists(self, mock_db):
        """Test user creation with existing username."""
        service = UserService(mock_db)

        existing_user = Mock()
        existing_user.username = "testuser"
        existing_user.email = "different@example.com"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="Username already exists"):
            await service.create_user(
                username="testuser", email="test@example.com", password="password123"
            )

    async def test_create_user_email_exists(self, mock_db):
        """Test user creation with existing email."""
        service = UserService(mock_db)

        existing_user = Mock()
        existing_user.username = "different"
        existing_user.email = "test@example.com"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(ValueError, match="Email already exists"):
            await service.create_user(
                username="newuser", email="test@example.com", password="password123"
            )

    async def test_get_user_by_id(self, mock_db, mock_user):
        """Test getting user by ID."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await service.get_user_by_id(1)
        assert user == mock_user

    async def test_get_user_by_username(self, mock_db, mock_user):
        """Test getting user by username."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await service.get_user_by_username("testuser")
        assert user == mock_user

    async def test_authenticate_user_success(self, mock_db, mock_user):
        """Test successful user authentication."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        user = await service.authenticate_user("testuser", "password123")
        assert user == mock_user
        mock_user.verify_password.assert_called_once_with("password123")
        mock_user.update_last_login.assert_called_once()

    async def test_authenticate_user_wrong_password(self, mock_db, mock_user):
        """Test authentication with wrong password."""
        service = UserService(mock_db)

        mock_user.verify_password.return_value = False

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await service.authenticate_user("testuser", "wrongpassword")
        assert user is None

    async def test_authenticate_user_inactive(self, mock_db, mock_user):
        """Test authentication with inactive user."""
        service = UserService(mock_db)

        mock_user.is_active = False

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await service.authenticate_user("testuser", "password123")
        assert user is None

    async def test_update_user(self, mock_db, mock_user):
        """Test user update."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        updated_user = await service.update_user(
            1, first_name="Updated", email="new@example.com"
        )
        assert updated_user == mock_user

    async def test_change_password_success(self, mock_db, mock_user):
        """Test successful password change."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        success = await service.change_password(1, "oldpassword", "newpassword")
        assert success is True
        mock_user.verify_password.assert_called_once_with("oldpassword")
        mock_user.set_password.assert_called_once_with("newpassword")

    async def test_change_password_wrong_current(self, mock_db, mock_user):
        """Test password change with wrong current password."""
        service = UserService(mock_db)

        mock_user.verify_password.return_value = False

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        success = await service.change_password(1, "wrongpassword", "newpassword")
        assert success is False

    async def test_deactivate_user(self, mock_db, mock_user):
        """Test user deactivation."""
        service = UserService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        success = await service.deactivate_user(1)
        assert success is True
        assert mock_user.is_active is False


class TestSessionService:
    """Test session service."""

    def test_init(self, mock_db):
        """Test service initialization."""
        service = SessionService(mock_db)
        assert service.db == mock_db

    async def test_create_session(self, mock_db, mock_session):
        """Test session creation."""
        service = SessionService(mock_db)

        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("jd_ingestion.auth.service.UserSession") as mock_session_class:
            mock_session_class.create_session.return_value = mock_session

            session = await service.create_session(1, "127.0.0.1", "Test Agent")
            assert session == mock_session
            mock_session_class.create_session.assert_called_once_with(
                1, "127.0.0.1", "Test Agent"
            )

    async def test_get_session(self, mock_db, mock_session):
        """Test getting session by token."""
        service = SessionService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        session = await service.get_session("test_token")
        assert session == mock_session

    async def test_validate_session_success(self, mock_db, mock_session, mock_user):
        """Test successful session validation."""
        service = SessionService(mock_db)

        mock_session.user = mock_user

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        user = await service.validate_session("test_token")
        assert user == mock_user

    async def test_validate_session_invalid(self, mock_db, mock_session):
        """Test validation of invalid session."""
        service = SessionService(mock_db)

        mock_session.is_valid = False

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        user = await service.validate_session("test_token")
        assert user is None

    async def test_invalidate_session(self, mock_db, mock_session):
        """Test session invalidation."""
        service = SessionService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        success = await service.invalidate_session("test_token")
        assert success is True
        mock_db.delete.assert_called_once_with(mock_session)

    async def test_cleanup_expired_sessions(self, mock_db):
        """Test cleanup of expired sessions."""
        service = SessionService(mock_db)

        expired_session1 = Mock()
        expired_session2 = Mock()
        expired_sessions = [expired_session1, expired_session2]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = expired_sessions
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        count = await service.cleanup_expired_sessions()
        assert count == 2
        assert mock_db.delete.call_count == 2


class TestPermissionService:
    """Test permission service."""

    def test_init(self, mock_db):
        """Test service initialization."""
        service = PermissionService(mock_db)
        assert service.db == mock_db

    async def test_grant_permission(self, mock_db, mock_permission):
        """Test granting permission."""
        service = PermissionService(mock_db)

        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "jd_ingestion.auth.service.UserPermission", return_value=mock_permission
        ):
            permission = await service.grant_permission(
                1, "job_description", "read", None, 1
            )
            assert permission == mock_permission

    async def test_check_permission_success(self, mock_db, mock_permission):
        """Test successful permission check."""
        service = PermissionService(mock_db)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_permission]
        mock_db.execute = AsyncMock(return_value=mock_result)

        has_permission = await service.check_permission(1, "job_description", "read")
        assert has_permission is True

    async def test_check_permission_failure(self, mock_db, mock_permission):
        """Test failed permission check."""
        service = PermissionService(mock_db)

        mock_permission.is_valid = False

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_permission]
        mock_db.execute = AsyncMock(return_value=mock_result)

        has_permission = await service.check_permission(1, "job_description", "write")
        assert has_permission is False

    async def test_get_user_permissions(self, mock_db, mock_permission):
        """Test getting user permissions."""
        service = PermissionService(mock_db)

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_permission]
        mock_db.execute = AsyncMock(return_value=mock_result)

        permissions = await service.get_user_permissions(1)
        assert permissions == [mock_permission]

    async def test_revoke_permission(self, mock_db, mock_permission):
        """Test revoking permission."""
        service = PermissionService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_permission
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        success = await service.revoke_permission(1)
        assert success is True
        mock_db.delete.assert_called_once_with(mock_permission)


class TestPreferenceService:
    """Test preference service."""

    def test_init(self, mock_db):
        """Test service initialization."""
        service = PreferenceService(mock_db)
        assert service.db == mock_db

    async def test_set_preference_new(self, mock_db, mock_preference):
        """Test setting new preference."""
        service = PreferenceService(mock_db)

        # No existing preference
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "jd_ingestion.auth.service.UserPreference", return_value=mock_preference
        ):
            preference = await service.set_preference(1, "theme", "dark")
            assert preference == mock_preference

    async def test_set_preference_existing(self, mock_db, mock_preference):
        """Test updating existing preference."""
        service = PreferenceService(mock_db)

        # Existing preference
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_preference
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        preference = await service.set_preference(1, "theme", "light")
        assert preference == mock_preference
        assert mock_preference.preference_value == "light"

    async def test_get_preference(self, mock_db, mock_preference):
        """Test getting preference."""
        service = PreferenceService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_preference
        mock_db.execute = AsyncMock(return_value=mock_result)

        value = await service.get_preference(1, "theme")
        assert value == mock_preference.preference_value

    async def test_get_preference_default(self, mock_db):
        """Test getting preference with default."""
        service = PreferenceService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        value = await service.get_preference(1, "theme", "light")
        assert value == "light"

    async def test_get_all_preferences(self, mock_db, mock_preference):
        """Test getting all preferences."""
        service = PreferenceService(mock_db)

        mock_preference.preference_key = "theme"
        mock_preference.preference_value = "dark"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_preference]
        mock_db.execute = AsyncMock(return_value=mock_result)

        preferences = await service.get_all_preferences(1)
        assert preferences == {"theme": "dark"}

    async def test_delete_preference(self, mock_db, mock_preference):
        """Test deleting preference."""
        service = PreferenceService(mock_db)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_preference
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        success = await service.delete_preference(1, "theme")
        assert success is True
        mock_db.delete.assert_called_once_with(mock_preference)


class TestTokenFunctions:
    """Test token creation and verification functions."""

    def test_create_access_token_no_jwt(self):
        """Test token creation without JWT library."""
        with patch("jd_ingestion.auth.service.jwt", None):
            token = create_access_token({"sub": "123", "username": "test"})
            assert token.startswith("dev_token_123_")

    @patch("jd_ingestion.auth.service.jwt")
    def test_create_access_token_with_jwt(self, mock_jwt):
        """Test token creation with JWT library."""
        mock_jwt.encode.return_value = "encoded_jwt_token"

        token = create_access_token({"sub": "123", "username": "test"})
        assert token == "encoded_jwt_token"
        mock_jwt.encode.assert_called_once()

    def test_verify_access_token_no_jwt(self):
        """Test token verification without JWT library."""
        with patch("jd_ingestion.auth.service.jwt", None):
            # Valid dev token
            payload = verify_access_token("dev_token_123_abcd")
            assert payload == {"sub": "123"}

            # Invalid token
            payload = verify_access_token("invalid_token")
            assert payload is None

    @patch("jd_ingestion.auth.service.jwt")
    def test_verify_access_token_with_jwt(self, mock_jwt):
        """Test token verification with JWT library."""
        mock_jwt.decode.return_value = {"sub": "123", "username": "test"}

        payload = verify_access_token("valid_jwt_token")
        assert payload == {"sub": "123", "username": "test"}

    @patch("jd_ingestion.auth.service.jwt")
    def test_verify_access_token_invalid_jwt(self, mock_jwt):
        """Test invalid JWT token verification."""
        from jwt import PyJWTError

        mock_jwt.PyJWTError = PyJWTError
        mock_jwt.decode.side_effect = PyJWTError("Invalid token")

        payload = verify_access_token("invalid_jwt_token")
        assert payload is None
