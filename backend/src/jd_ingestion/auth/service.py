"""
Authentication Service for Phase 2 User Management.

This module provides authentication, authorization, and user management services.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import secrets
from passlib.context import CryptContext

try:
    import jwt
except ImportError:
    jwt = None  # Will handle this gracefully in production

from .models import User, UserSession, UserPreference, UserPermission, hash_password, verify_password
from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings (in production, use proper secret management)
SECRET_KEY = getattr(settings, 'jwt_secret_key', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when authorization fails."""
    pass


class UserService:
    """Service for user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, username: str, email: str, password: str,
                         first_name: Optional[str] = None, last_name: Optional[str] = None,
                         role: str = "user", department: Optional[str] = None,
                         security_clearance: Optional[str] = None,
                         preferred_language: str = "en") -> User:
        """Create a new user."""

        # Check if username or email already exists
        result = await self.db.execute(
            select(User).where(or_(User.username == username, User.email == email))
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == username:
                raise ValueError("Username already exists")
            if existing_user.email == email:
                raise ValueError("Email already exists")

        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department=department,
            security_clearance=security_clearance,
            preferred_language=preferred_language
        )
        user.set_password(password)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Created user: {username} (ID: {user.id})")
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/password."""
        user = await self.get_user_by_username(username)

        if not user or not user.is_active:
            return None

        if not user.verify_password(password):
            return None

        # Update last login
        user.update_last_login()
        await self.db.commit()

        logger.info(f"User authenticated: {username}")
        return user

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'email', 'role', 'department',
                         'security_clearance', 'preferred_language', 'is_active']

        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(user, field):
                setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Updated user: {user.username} (ID: {user.id})")
        return user

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        if not user.verify_password(current_password):
            return False

        user.set_password(new_password)
        await self.db.commit()

        logger.info(f"Password changed for user: {user.username}")
        return True

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False

        user.is_active = False
        await self.db.commit()

        logger.info(f"Deactivated user: {user.username}")
        return True


class SessionService:
    """Service for session management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: int, ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> UserSession:
        """Create a new user session."""
        session = UserSession.create_session(user_id, ip_address, user_agent)

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Created session for user {user_id}: {session.session_token[:8]}...")
        return session

    async def get_session(self, session_token: str) -> Optional[UserSession]:
        """Get session by token."""
        result = await self.db.execute(
            select(UserSession).options(selectinload(UserSession.user))
            .where(UserSession.session_token == session_token)
        )
        return result.scalar_one_or_none()

    async def validate_session(self, session_token: str) -> Optional[User]:
        """Validate session and return user if valid."""
        session = await self.get_session(session_token)

        if not session or not session.is_valid:
            return None

        # Update last activity
        session.last_activity = datetime.utcnow()
        await self.db.commit()

        return session.user

    async def invalidate_session(self, session_token: str) -> bool:
        """Invalidate a session."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.session_token == session_token)
        )
        session = result.scalar_one_or_none()

        if session:
            await self.db.delete(session)
            await self.db.commit()
            logger.info(f"Invalidated session: {session_token[:8]}...")
            return True

        return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        result = await self.db.execute(
            select(UserSession).where(UserSession.expires_at < datetime.utcnow())
        )
        expired_sessions = result.scalars().all()

        for session in expired_sessions:
            await self.db.delete(session)

        await self.db.commit()

        count = len(expired_sessions)
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

        return count


class PermissionService:
    """Service for permission and authorization management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def grant_permission(self, user_id: int, resource_type: str,
                             permission_type: str, resource_id: Optional[int] = None,
                             granted_by_id: Optional[int] = None,
                             expires_at: Optional[datetime] = None) -> UserPermission:
        """Grant a permission to a user."""

        permission = UserPermission(
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            permission_type=permission_type,
            granted_by=granted_by_id,
            expires_at=expires_at
        )

        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)

        logger.info(f"Granted permission {permission_type} on {resource_type} to user {user_id}")
        return permission

    async def check_permission(self, user_id: int, resource_type: str,
                             permission_type: str, resource_id: Optional[int] = None) -> bool:
        """Check if user has specific permission."""

        # Check for specific resource permission
        conditions = [
            UserPermission.user_id == user_id,
            UserPermission.resource_type == resource_type,
            UserPermission.permission_type == permission_type,
        ]

        if resource_id is not None:
            conditions.append(
                or_(UserPermission.resource_id == resource_id,
                    UserPermission.resource_id.is_(None))  # Global permission
            )

        result = await self.db.execute(
            select(UserPermission).where(and_(*conditions))
        )
        permissions = result.scalars().all()

        # Check if any valid permission exists
        for permission in permissions:
            if permission.is_valid:
                return True

        return False

    async def get_user_permissions(self, user_id: int) -> List[UserPermission]:
        """Get all permissions for a user."""
        result = await self.db.execute(
            select(UserPermission).where(UserPermission.user_id == user_id)
        )
        return result.scalars().all()

    async def revoke_permission(self, permission_id: int) -> bool:
        """Revoke a specific permission."""
        result = await self.db.execute(
            select(UserPermission).where(UserPermission.id == permission_id)
        )
        permission = result.scalar_one_or_none()

        if permission:
            await self.db.delete(permission)
            await self.db.commit()
            logger.info(f"Revoked permission {permission_id}")
            return True

        return False


class PreferenceService:
    """Service for user preference management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def set_preference(self, user_id: int, key: str, value: Any) -> UserPreference:
        """Set a user preference."""

        # Check if preference already exists
        result = await self.db.execute(
            select(UserPreference).where(
                and_(UserPreference.user_id == user_id,
                     UserPreference.preference_key == key)
            )
        )
        preference = result.scalar_one_or_none()

        if preference:
            preference.preference_value = value
        else:
            preference = UserPreference(
                user_id=user_id,
                preference_key=key,
                preference_value=value
            )
            self.db.add(preference)

        await self.db.commit()
        await self.db.refresh(preference)

        return preference

    async def get_preference(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        result = await self.db.execute(
            select(UserPreference).where(
                and_(UserPreference.user_id == user_id,
                     UserPreference.preference_key == key)
            )
        )
        preference = result.scalar_one_or_none()

        if preference:
            return preference.preference_value

        return default

    async def get_all_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get all preferences for a user."""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        preferences = result.scalars().all()

        return {pref.preference_key: pref.preference_value for pref in preferences}

    async def delete_preference(self, user_id: int, key: str) -> bool:
        """Delete a user preference."""
        result = await self.db.execute(
            select(UserPreference).where(
                and_(UserPreference.user_id == user_id,
                     UserPreference.preference_key == key)
            )
        )
        preference = result.scalar_one_or_none()

        if preference:
            await self.db.delete(preference)
            await self.db.commit()
            return True

        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if jwt is None:
        # Fallback to simple token for development
        return f"dev_token_{data.get('sub', 'unknown')}_{secrets.token_urlsafe(16)}"

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT access token."""
    if jwt is None:
        # Simple token verification for development
        if token.startswith("dev_token_"):
            parts = token.split("_")
            if len(parts) >= 3:
                return {"sub": parts[2]}
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None