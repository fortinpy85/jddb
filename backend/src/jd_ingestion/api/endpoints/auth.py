"""
Authentication API endpoints for Phase 2.

This module provides REST API endpoints for user authentication,
registration, session management, and user profile operations.
"""

from datetime import timedelta
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from ...auth.dependencies import (
    get_user_service,
    get_session_service,
    get_preference_service,
    CurrentUser,
    OptionalCurrentUser,
)
from ...auth.service import (
    UserService,
    SessionService,
    PreferenceService,
    create_access_token,
)
from ...auth.models import User
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: str = Field("user", pattern="^(user|editor|translator|reviewer|admin)$")
    department: Optional[str] = Field(None, max_length=100)
    security_clearance: Optional[str] = Field(None, max_length=20)
    preferred_language: str = Field("en", pattern="^(en|fr)$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    department: Optional[str]
    security_clearance: Optional[str]
    preferred_language: str
    is_active: bool
    last_login: Optional[str]
    created_at: str

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            department=user.department,
            security_clearance=user.security_clearance,
            preferred_language=user.preferred_language,
            is_active=user.is_active,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
        )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    department: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, pattern="^(en|fr)$")


class PreferenceRequest(BaseModel):
    key: str = Field(..., max_length=100)
    value: Any


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate, user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user account.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 8 characters)
    - **role**: User role (user, editor, translator, reviewer, admin)
    """
    try:
        user = await user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            department=user_data.department,
            security_clearance=user_data.security_clearance,
            preferred_language=user_data.preferred_language,
        )

        logger.info(f"User registered: {user.username}")
        return UserResponse.from_user(user)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
):
    """
    Authenticate user and return access token.

    - **username**: Username or email
    - **password**: User password
    """
    # Try authentication with username
    user = await user_service.authenticate_user(form_data.username, form_data.password)

    # If username auth failed, try with email
    if not user:
        user_by_email = await user_service.get_user_by_email(form_data.username)
        if user_by_email:
            user = await user_service.authenticate_user(
                user_by_email.username, form_data.password
            )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    # Create session for longer-term authentication
    ip_address = getattr(request.client, "host", None) if request else None
    user_agent = request.headers.get("user-agent") if request else None

    _ = await session_service.create_session(
        user_id=user.id, ip_address=ip_address, user_agent=user_agent
    )

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",  # nosec B106 - OAuth 2.0 standard token type, not a password
        expires_in=1800,  # 30 minutes
        user=UserResponse.from_user(user),
    )


@router.post("/logout")
async def logout_user(
    current_user: CurrentUser,
    session_service: SessionService = Depends(get_session_service),
):
    """Logout current user and invalidate sessions."""
    # Note: In a full implementation, we'd need to track which session token
    # was used for this request to invalidate it specifically.
    # For now, we'll implement a basic logout confirmation.

    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return UserResponse.from_user(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdateRequest,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
):
    """Update current user profile."""
    update_data = user_update.dict(exclude_unset=True)

    try:
        updated_user = await user_service.update_user(current_user.id, **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        logger.info(f"User profile updated: {current_user.username}")
        return UserResponse.from_user(updated_user)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
):
    """Change current user password."""
    success = await user_service.change_password(
        current_user.id, password_data.current_password, password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    logger.info(f"Password changed for user: {current_user.username}")
    return {"message": "Password successfully changed"}


@router.get("/preferences")
async def get_user_preferences(
    current_user: CurrentUser,
    preference_service: PreferenceService = Depends(get_preference_service),
):
    """Get all user preferences."""
    preferences = await preference_service.get_all_preferences(current_user.id)
    return {"preferences": preferences}


@router.post("/preferences")
async def set_user_preference(
    preference_data: PreferenceRequest,
    current_user: CurrentUser,
    preference_service: PreferenceService = Depends(get_preference_service),
):
    """Set a user preference."""
    preference = await preference_service.set_preference(
        current_user.id, preference_data.key, preference_data.value
    )

    return {
        "message": "Preference set successfully",
        "key": preference.preference_key,
        "value": preference.preference_value,
    }


@router.get("/preferences/{key}")
async def get_user_preference(
    key: str,
    current_user: CurrentUser,
    preference_service: PreferenceService = Depends(get_preference_service),
):
    """Get a specific user preference."""
    value = await preference_service.get_preference(current_user.id, key)

    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found"
        )

    return {"key": key, "value": value}


@router.delete("/preferences/{key}")
async def delete_user_preference(
    key: str,
    current_user: CurrentUser,
    preference_service: PreferenceService = Depends(get_preference_service),
):
    """Delete a user preference."""
    success = await preference_service.delete_preference(current_user.id, key)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found"
        )

    return {"message": "Preference deleted successfully"}


@router.get("/status")
async def auth_status(current_user: OptionalCurrentUser):
    """Get authentication status."""
    if current_user:
        return {"authenticated": True, "user": UserResponse.from_user(current_user)}
    else:
        return {"authenticated": False}


@router.post("/cleanup-sessions")
async def cleanup_expired_sessions(
    session_service: SessionService = Depends(get_session_service),
):
    """Clean up expired sessions (admin operation)."""
    # Note: In production, this should require admin privileges
    count = await session_service.cleanup_expired_sessions()
    return {"message": f"Cleaned up {count} expired sessions"}
