"""
FastAPI dependencies for authentication and authorization.

This module provides FastAPI dependency injection for authentication,
authorization, and user management in Phase 2.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .service import (
    UserService,
    SessionService,
    PermissionService,
    PreferenceService,
    verify_access_token,
)
from .models import User
from ..database.connection import get_async_session
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_user_service(
    db: AsyncSession = Depends(get_async_session),
) -> UserService:
    """Get UserService instance."""
    return UserService(db)


async def get_session_service(
    db: AsyncSession = Depends(get_async_session),
) -> SessionService:
    """Get SessionService instance."""
    return SessionService(db)


async def get_permission_service(
    db: AsyncSession = Depends(get_async_session),
) -> PermissionService:
    """Get PermissionService instance."""
    return PermissionService(db)


async def get_preference_service(
    db: AsyncSession = Depends(get_async_session),
) -> PreferenceService:
    """Get PreferenceService instance."""
    return PreferenceService(db)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_service: SessionService = Depends(get_session_service),
) -> Optional[User]:
    """
    Get current user from JWT token or session token (optional).
    Returns None if no valid authentication is provided.
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Try JWT token first
    payload = verify_access_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            try:
                user_service = UserService(session_service.db)
                user = await user_service.get_user_by_id(int(user_id))
                if user and user.is_active:
                    return user
            except Exception as e:
                logger.warning(f"Error getting user from JWT: {e}")

    # Try session token
    try:
        user = await session_service.validate_session(token)
        if user:
            return user
    except Exception as e:
        logger.warning(f"Error validating session: {e}")

    return None


async def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """
    Get current user from JWT token or session token (required).
    Raises HTTPException if no valid authentication is provided.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require specific user role.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """

    async def role_checker(current_user: User = Depends(get_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role",
            )
        return current_user

    return role_checker


def require_roles(required_roles: list):
    """
    Dependency factory to require one of multiple roles.

    Usage:
        @router.get("/editor-or-admin")
        async def editor_endpoint(user: User = Depends(require_roles(["admin", "editor"]))):
            ...
    """

    async def roles_checker(current_user: User = Depends(get_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of these roles: {', '.join(required_roles)}",
            )
        return current_user

    return roles_checker


def require_permission(
    resource_type: str, permission_type: str, resource_id: Optional[int] = None
):
    """
    Dependency factory to require specific permission.

    Usage:
        @router.get("/jobs/{job_id}")
        async def get_job(
            job_id: int,
            user: User = Depends(require_permission("job_description", "read"))
        ):
            ...
    """

    async def permission_checker(
        current_user: User = Depends(get_active_user),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> User:
        # Admin users have all permissions
        if current_user.is_admin:
            return current_user

        # Check specific permission
        has_permission = await permission_service.check_permission(
            current_user.id, resource_type, permission_type, resource_id
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission_type} on {resource_type}",
            )

        return current_user

    return permission_checker


class UserContext:
    """User context for request-scoped user information."""

    def __init__(self, user: Optional[User] = None):
        self.user = user

    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.user is not None

    @property
    def user_id(self) -> Optional[int]:
        """Get user ID."""
        return self.user.id if self.user else None

    @property
    def username(self) -> Optional[str]:
        """Get username."""
        return self.user.username if self.user else None

    @property
    def role(self) -> Optional[str]:
        """Get user role."""
        return self.user.role if self.user else None

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return self.user.role == role if self.user else False

    def has_any_role(self, roles: list) -> bool:
        """Check if user has any of the specified roles."""
        return self.user.role in roles if self.user else False


async def get_user_context(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> UserContext:
    """Get user context for the current request."""
    return UserContext(current_user)


# Common role dependencies for convenience
require_admin = require_role("admin")
require_editor = require_roles(["admin", "editor"])
require_translator = require_roles(["admin", "translator", "editor"])
require_reviewer = require_roles(["admin", "reviewer", "editor"])

# Type aliases for cleaner type hints
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[Optional[User], Depends(get_current_user_optional)]
ActiveUser = Annotated[User, Depends(get_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
EditorUser = Annotated[User, Depends(require_editor)]
TranslatorUser = Annotated[User, Depends(require_translator)]
ReviewerUser = Annotated[User, Depends(require_reviewer)]
