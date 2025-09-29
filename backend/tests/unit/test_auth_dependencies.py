"""
Tests for authentication dependencies module.
"""

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import Mock, AsyncMock, patch

from jd_ingestion.auth.dependencies import (
    get_user_service,
    get_session_service,
    get_permission_service,
    get_preference_service,
    get_current_user_optional,
    get_current_user,
    get_active_user,
    require_role,
    require_roles,
    require_permission,
    get_user_context,
    UserContext,
    security,
    require_admin,
    require_editor,
    require_translator,
    require_reviewer,
)
from jd_ingestion.auth.models import User


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_active_user():
    """Mock active user."""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = "user"
    user.is_active = True
    user.is_admin = False
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    user = Mock(spec=User)
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = "admin"
    user.is_active = True
    user.is_admin = True
    return user


@pytest.fixture
def mock_inactive_user():
    """Mock inactive user."""
    user = Mock(spec=User)
    user.id = 3
    user.username = "inactive"
    user.email = "inactive@example.com"
    user.role = "user"
    user.is_active = False
    user.is_admin = False
    return user


class TestServiceDependencies:
    """Test service dependency providers."""

    @pytest.mark.asyncio
    async def test_get_user_service(self, mock_db):
        """Test getting UserService instance."""
        service = await get_user_service(mock_db)

        from jd_ingestion.auth.service import UserService

        assert isinstance(service, UserService)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_get_session_service(self, mock_db):
        """Test getting SessionService instance."""
        service = await get_session_service(mock_db)

        from jd_ingestion.auth.service import SessionService

        assert isinstance(service, SessionService)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_get_permission_service(self, mock_db):
        """Test getting PermissionService instance."""
        service = await get_permission_service(mock_db)

        from jd_ingestion.auth.service import PermissionService

        assert isinstance(service, PermissionService)
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_get_preference_service(self, mock_db):
        """Test getting PreferenceService instance."""
        service = await get_preference_service(mock_db)

        from jd_ingestion.auth.service import PreferenceService

        assert isinstance(service, PreferenceService)
        assert service.db == mock_db


class TestCurrentUserOptional:
    """Test optional current user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_optional_no_credentials(self):
        """Test getting current user with no credentials."""
        mock_session_service = Mock()

        result = await get_current_user_optional(None, mock_session_service)

        assert result is None

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    @patch("jd_ingestion.auth.dependencies.UserService")
    async def test_get_current_user_optional_valid_jwt(
        self, mock_user_service_class, mock_verify_token, mock_active_user
    ):
        """Test getting current user with valid JWT token."""
        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_jwt_token"
        )

        # Mock JWT verification
        mock_verify_token.return_value = {"sub": "1"}

        # Mock user service
        mock_user_service = Mock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_active_user)
        mock_user_service_class.return_value = mock_user_service

        mock_session_service = Mock()
        mock_session_service.db = Mock()

        result = await get_current_user_optional(credentials, mock_session_service)

        assert result == mock_active_user
        mock_verify_token.assert_called_once_with("valid_jwt_token")
        mock_user_service.get_user_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    async def test_get_current_user_optional_invalid_jwt_valid_session(
        self, mock_verify_token, mock_active_user
    ):
        """Test getting current user with invalid JWT but valid session token."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="session_token"
        )

        # Mock JWT verification failure
        mock_verify_token.return_value = None

        # Mock session validation success
        mock_session_service = Mock()
        mock_session_service.validate_session = AsyncMock(return_value=mock_active_user)

        result = await get_current_user_optional(credentials, mock_session_service)

        assert result == mock_active_user
        mock_session_service.validate_session.assert_called_once_with("session_token")

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    async def test_get_current_user_optional_invalid_tokens(self, mock_verify_token):
        """Test getting current user with invalid JWT and session tokens."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid_token"
        )

        # Mock JWT verification failure
        mock_verify_token.return_value = None

        # Mock session validation failure
        mock_session_service = Mock()
        mock_session_service.validate_session = AsyncMock(return_value=None)

        result = await get_current_user_optional(credentials, mock_session_service)

        assert result is None

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    @patch("jd_ingestion.auth.dependencies.UserService")
    async def test_get_current_user_optional_inactive_user(
        self, mock_user_service_class, mock_verify_token, mock_inactive_user
    ):
        """Test getting current user with valid JWT but inactive user."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="valid_jwt_token"
        )

        # Mock JWT verification
        mock_verify_token.return_value = {"sub": "3"}

        # Mock user service returning inactive user
        mock_user_service = Mock()
        mock_user_service.get_user_by_id = AsyncMock(return_value=mock_inactive_user)
        mock_user_service_class.return_value = mock_user_service

        mock_session_service = Mock()
        mock_session_service.db = Mock()

        result = await get_current_user_optional(credentials, mock_session_service)

        # Should return None for inactive user
        assert result is None

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    async def test_get_current_user_optional_service_error(self, mock_verify_token):
        """Test handling service errors in get_current_user_optional."""
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

        # Mock JWT verification failure
        mock_verify_token.return_value = None

        # Mock session service error
        mock_session_service = Mock()
        mock_session_service.validate_session = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await get_current_user_optional(credentials, mock_session_service)

        assert result is None


class TestCurrentUserRequired:
    """Test required current user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_with_user(self, mock_active_user):
        """Test getting current user when user exists."""
        result = await get_current_user(mock_active_user)

        assert result == mock_active_user

    @pytest.mark.asyncio
    async def test_get_current_user_no_user(self):
        """Test getting current user when no user provided."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Could not validate credentials"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestActiveUser:
    """Test active user dependency."""

    @pytest.mark.asyncio
    async def test_get_active_user_active(self, mock_active_user):
        """Test getting active user when user is active."""
        result = await get_active_user(mock_active_user)

        assert result == mock_active_user

    @pytest.mark.asyncio
    async def test_get_active_user_inactive(self, mock_inactive_user):
        """Test getting active user when user is inactive."""
        with pytest.raises(HTTPException) as exc_info:
            await get_active_user(mock_inactive_user)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Inactive user"


class TestRoleRequirements:
    """Test role requirement dependencies."""

    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_admin_user):
        """Test require_role when user has correct role."""
        mock_admin_user.role = "admin"
        role_checker = require_role("admin")

        result = await role_checker(mock_admin_user)

        assert result == mock_admin_user

    @pytest.mark.asyncio
    async def test_require_role_failure(self, mock_active_user):
        """Test require_role when user has wrong role."""
        mock_active_user.role = "user"
        role_checker = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(mock_active_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Operation requires admin role" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_roles_success(self, mock_active_user):
        """Test require_roles when user has one of the required roles."""
        mock_active_user.role = "editor"
        roles_checker = require_roles(["admin", "editor", "reviewer"])

        result = await roles_checker(mock_active_user)

        assert result == mock_active_user

    @pytest.mark.asyncio
    async def test_require_roles_failure(self, mock_active_user):
        """Test require_roles when user doesn't have any required role."""
        mock_active_user.role = "user"
        roles_checker = require_roles(["admin", "editor"])

        with pytest.raises(HTTPException) as exc_info:
            await roles_checker(mock_active_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Operation requires one of these roles" in exc_info.value.detail


class TestPermissionRequirements:
    """Test permission requirement dependencies."""

    @pytest.mark.asyncio
    async def test_require_permission_admin_user(self, mock_admin_user):
        """Test require_permission with admin user (should always pass)."""
        mock_admin_user.is_admin = True
        mock_permission_service = Mock()

        permission_checker = require_permission("job_description", "read")
        result = await permission_checker(mock_admin_user, mock_permission_service)

        assert result == mock_admin_user
        # Admin users should bypass permission check
        mock_permission_service.check_permission.assert_not_called()

    @pytest.mark.asyncio
    async def test_require_permission_success(self, mock_active_user):
        """Test require_permission when user has permission."""
        mock_active_user.is_admin = False
        mock_permission_service = Mock()
        mock_permission_service.check_permission = AsyncMock(return_value=True)

        permission_checker = require_permission("job_description", "read", 123)
        result = await permission_checker(mock_active_user, mock_permission_service)

        assert result == mock_active_user
        mock_permission_service.check_permission.assert_called_once_with(
            1, "job_description", "read", 123
        )

    @pytest.mark.asyncio
    async def test_require_permission_failure(self, mock_active_user):
        """Test require_permission when user lacks permission."""
        mock_active_user.is_admin = False
        mock_permission_service = Mock()
        mock_permission_service.check_permission = AsyncMock(return_value=False)

        permission_checker = require_permission("job_description", "write")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(mock_active_user, mock_permission_service)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Permission denied: write on job_description" in exc_info.value.detail


class TestUserContext:
    """Test UserContext class."""

    def test_user_context_with_user(self, mock_active_user):
        """Test UserContext with authenticated user."""
        context = UserContext(mock_active_user)

        assert context.is_authenticated is True
        assert context.user_id == 1
        assert context.username == "testuser"
        assert context.role == "user"

    def test_user_context_without_user(self):
        """Test UserContext without authenticated user."""
        context = UserContext(None)

        assert context.is_authenticated is False
        assert context.user_id is None
        assert context.username is None
        assert context.role is None

    def test_user_context_has_role(self, mock_admin_user):
        """Test UserContext has_role method."""
        mock_admin_user.role = "admin"
        context = UserContext(mock_admin_user)

        assert context.has_role("admin") is True
        assert context.has_role("user") is False

    def test_user_context_has_role_no_user(self):
        """Test UserContext has_role method with no user."""
        context = UserContext(None)

        assert context.has_role("admin") is False
        assert context.has_role("user") is False

    def test_user_context_has_any_role(self, mock_active_user):
        """Test UserContext has_any_role method."""
        mock_active_user.role = "editor"
        context = UserContext(mock_active_user)

        assert context.has_any_role(["admin", "editor"]) is True
        assert context.has_any_role(["admin", "reviewer"]) is False

    def test_user_context_has_any_role_no_user(self):
        """Test UserContext has_any_role method with no user."""
        context = UserContext(None)

        assert context.has_any_role(["admin", "user"]) is False

    @pytest.mark.asyncio
    async def test_get_user_context(self, mock_active_user):
        """Test get_user_context dependency."""
        context = await get_user_context(mock_active_user)

        assert isinstance(context, UserContext)
        assert context.user == mock_active_user


class TestSecurityConfiguration:
    """Test security configuration."""

    def test_security_scheme_configuration(self):
        """Test that HTTPBearer security scheme is configured correctly."""
        from fastapi.security import HTTPBearer

        assert isinstance(security, HTTPBearer)
        assert security.auto_error is False


class TestPrebuiltDependencies:
    """Test prebuilt role dependencies."""

    def test_prebuilt_dependencies_exist(self):
        """Test that all prebuilt dependencies exist."""
        assert callable(require_admin)
        assert callable(require_editor)
        assert callable(require_translator)
        assert callable(require_reviewer)

    @pytest.mark.asyncio
    async def test_require_admin_success(self, mock_admin_user):
        """Test prebuilt require_admin dependency."""
        mock_admin_user.role = "admin"

        result = await require_admin(mock_admin_user)
        assert result == mock_admin_user

    @pytest.mark.asyncio
    async def test_require_admin_failure(self, mock_active_user):
        """Test prebuilt require_admin dependency failure."""
        mock_active_user.role = "user"

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_active_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_require_editor_success(self, mock_active_user):
        """Test prebuilt require_editor dependency."""
        mock_active_user.role = "editor"

        result = await require_editor(mock_active_user)
        assert result == mock_active_user

    @pytest.mark.asyncio
    async def test_require_translator_success(self, mock_active_user):
        """Test prebuilt require_translator dependency."""
        mock_active_user.role = "translator"

        result = await require_translator(mock_active_user)
        assert result == mock_active_user

    @pytest.mark.asyncio
    async def test_require_reviewer_success(self, mock_active_user):
        """Test prebuilt require_reviewer dependency."""
        mock_active_user.role = "reviewer"

        result = await require_reviewer(mock_active_user)
        assert result == mock_active_user


class TestTypeAliases:
    """Test type alias definitions."""

    def test_type_aliases_exist(self):
        """Test that all type aliases are defined."""
        from jd_ingestion.auth.dependencies import (
            CurrentUser,
            OptionalCurrentUser,
            ActiveUser,
            AdminUser,
            EditorUser,
            TranslatorUser,
            ReviewerUser,
        )

        # Type aliases should be importable
        assert CurrentUser is not None
        assert OptionalCurrentUser is not None
        assert ActiveUser is not None
        assert AdminUser is not None
        assert EditorUser is not None
        assert TranslatorUser is not None
        assert ReviewerUser is not None


class TestDependencyIntegration:
    """Test dependency integration scenarios."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.auth.dependencies.verify_access_token")
    async def test_jwt_token_parsing(self, mock_verify_token):
        """Test JWT token parsing in get_current_user_optional."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token",
        )

        mock_verify_token.return_value = None
        mock_session_service = Mock()
        mock_session_service.validate_session = AsyncMock(return_value=None)

        result = await get_current_user_optional(credentials, mock_session_service)

        # Should pass the credentials.credentials (the actual token) to verify
        mock_verify_token.assert_called_once_with(
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_dependency_chain_flow(self):
        """Test the flow of dependencies from optional to required to active."""
        # This tests the conceptual flow but with mocked components
        mock_user = Mock(spec=User)
        mock_user.is_active = True

        # get_current_user_optional -> get_current_user -> get_active_user
        optional_result = await get_current_user_optional(None, Mock())
        assert optional_result is None

        with pytest.raises(HTTPException):
            await get_current_user(optional_result)

        # Test with user
        required_result = await get_current_user(mock_user)
        assert required_result == mock_user

        active_result = await get_active_user(required_result)
        assert active_result == mock_user
