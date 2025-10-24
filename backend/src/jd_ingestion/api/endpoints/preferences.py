"""
Session-based User Preferences API.

Provides endpoints for managing user preferences without authentication,
using session IDs for preference storage and retrieval.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ...database.connection import get_db
from ...database.models import UserPreference
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferenceUpdate(BaseModel):
    """Request model for updating a preference."""

    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value (any JSON-serializable type)")


class PreferenceResponse(BaseModel):
    """Response model for a single preference."""

    key: str
    value: Any
    updated_at: Optional[str] = None


class PreferencesResponse(BaseModel):
    """Response model for all preferences."""

    preferences: Dict[str, Any]
    session_id: str


def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """
    Extract session ID from header.

    In production, this would validate and create sessions properly.
    For now, we accept any session ID or generate a default.
    """
    return x_session_id or "default-session"


@router.get("", response_model=PreferencesResponse)
async def get_all_preferences(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all preferences for the current session.

    Returns a dictionary of all preference key-value pairs.
    """
    try:
        # Query all preferences for this session
        result = await db.execute(
            select(UserPreference).where(UserPreference.session_id == session_id)
        )
        preferences_list = result.scalars().all()

        # Convert to dictionary
        preferences_dict = {
            str(pref.preference_key): pref.preference_value for pref in preferences_list
        }

        logger.info(
            f"Retrieved {len(preferences_dict)} preferences for session {session_id}"
        )

        return PreferencesResponse(preferences=preferences_dict, session_id=session_id)

    except Exception as e:
        logger.error(f"Error retrieving preferences: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve preferences: {str(e)}"
        )


@router.post("", status_code=200)
async def update_preference(
    preference: PreferenceUpdate,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update or create a single preference.

    If the preference exists, it will be updated. Otherwise, a new one is created.
    """
    try:
        # Check if preference exists
        result = await db.execute(
            select(UserPreference).where(
                and_(
                    UserPreference.session_id == session_id,
                    UserPreference.preference_key == preference.key,
                )
            )
        )
        existing_pref = result.scalar_one_or_none()

        if existing_pref:
            # Update existing preference
            existing_pref.preference_value = preference.value
            logger.info(
                f"Updated preference '{preference.key}' for session {session_id}"
            )
        else:
            # Create new preference
            new_pref = UserPreference(
                session_id=session_id,
                preference_type="user_settings",
                preference_key=preference.key,
                preference_value=preference.value,
            )
            db.add(new_pref)
            logger.info(
                f"Created preference '{preference.key}' for session {session_id}"
            )

        await db.commit()

        return {
            "message": "Preference updated successfully",
            "key": preference.key,
            "value": preference.value,
        }

    except Exception as e:
        logger.error(f"Error updating preference: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update preference: {str(e)}"
        )


@router.post("/bulk", status_code=200)
async def update_preferences_bulk(
    preferences: Dict[str, Any],
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Update multiple preferences at once.

    Accepts a dictionary of key-value pairs and updates/creates all preferences.
    This is more efficient than making individual calls for each preference.
    """
    try:
        updated_count = 0
        created_count = 0

        for key, value in preferences.items():
            # Check if preference exists
            result = await db.execute(
                select(UserPreference).where(
                    and_(
                        UserPreference.session_id == session_id,
                        UserPreference.preference_key == key,
                    )
                )
            )
            existing_pref = result.scalar_one_or_none()

            if existing_pref:
                existing_pref.preference_value = value
                updated_count += 1
            else:
                new_pref = UserPreference(
                    session_id=session_id,
                    preference_type="user_settings",
                    preference_key=key,
                    preference_value=value,
                )
                db.add(new_pref)
                created_count += 1

        await db.commit()

        logger.info(
            f"Bulk update: {updated_count} updated, {created_count} created for session {session_id}"
        )

        return {
            "message": "Preferences updated successfully",
            "updated": updated_count,
            "created": created_count,
            "total": updated_count + created_count,
        }

    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update preferences: {str(e)}"
        )


@router.get("/{key}", response_model=PreferenceResponse)
async def get_preference(
    key: str,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific preference by key.

    Returns 404 if the preference doesn't exist.
    """
    try:
        result = await db.execute(
            select(UserPreference).where(
                and_(
                    UserPreference.session_id == session_id,
                    UserPreference.preference_key == key,
                )
            )
        )
        preference = result.scalar_one_or_none()

        if not preference:
            raise HTTPException(status_code=404, detail=f"Preference '{key}' not found")

        return PreferenceResponse(
            key=str(preference.preference_key),
            value=preference.preference_value,
            updated_at=preference.updated_at.isoformat()
            if preference.updated_at
            else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving preference: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve preference: {str(e)}"
        )


@router.delete("/{key}", status_code=200)
async def delete_preference(
    key: str,
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific preference.

    Returns 404 if the preference doesn't exist.
    """
    try:
        result = await db.execute(
            delete(UserPreference).where(
                and_(
                    UserPreference.session_id == session_id,
                    UserPreference.preference_key == key,
                )
            )
        )

        await db.commit()

        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise HTTPException(status_code=404, detail=f"Preference '{key}' not found")

        logger.info(f"Deleted preference '{key}' for session {session_id}")

        return {"message": f"Preference '{key}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preference: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete preference: {str(e)}"
        )


@router.delete("", status_code=200)
async def reset_all_preferences(
    session_id: str = Depends(get_session_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete all preferences for the current session.

    This is useful for resetting to defaults.
    """
    try:
        result = await db.execute(
            delete(UserPreference).where(UserPreference.session_id == session_id)
        )

        await db.commit()

        deleted_count = result.rowcount  # type: ignore[attr-defined]
        logger.info(f"Reset {deleted_count} preferences for session {session_id}")

        return {
            "message": "All preferences reset successfully",
            "deleted": deleted_count,
        }

    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to reset preferences: {str(e)}"
        )
