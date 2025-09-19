"""
Authentication and User Management Utilities for Phase 2.

This module provides authentication utilities and user data models.
The actual database tables are created via Alembic migrations.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from pydantic import BaseModel
import secrets

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """User data model (not a SQLAlchemy model)."""

    id: int
    username: str
    email: str
    password_hash: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    department: Optional[str] = None
    security_clearance: Optional[str] = None
    preferred_language: str = "en"
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    def set_password(self, password: str) -> str:
        """Hash and return the password hash."""
        return pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return pwd_context.verify(password, self.password_hash)

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"

    @property
    def can_edit(self) -> bool:
        """Check if user can edit documents."""
        return self.role in ["admin", "editor", "reviewer"]

    @property
    def can_translate(self) -> bool:
        """Check if user can perform translations."""
        return self.role in ["admin", "translator", "editor"]


class UserSession(BaseModel):
    """User session data model."""

    id: int
    user_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: datetime
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def create_token(cls, user_id: int, expires_hours: int = 24) -> tuple[str, datetime]:
        """Create a new session token and expiration."""
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        return session_token, expires_at

    @property
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the session is valid (not expired)."""
        return not self.is_expired


class UserPreference(BaseModel):
    """User preference data model."""

    id: int
    user_id: int
    preference_key: str
    preference_value: Any
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserPermission(BaseModel):
    """User permission data model."""

    id: int
    user_id: int
    resource_type: str
    resource_id: Optional[int] = None
    permission_type: str
    granted_by: Optional[int] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @property
    def is_expired(self) -> bool:
        """Check if the permission is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the permission is valid (not expired)."""
        return not self.is_expired


# Password utility functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(password, password_hash)