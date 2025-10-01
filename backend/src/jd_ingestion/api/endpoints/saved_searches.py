"""
API endpoints for saved searches and user preferences.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ...database.connection import get_async_session
from ...database.models import SavedSearch, UserPreference
from ...services.analytics_service import analytics_service
from ...utils.logging import get_logger
from sqlalchemy import select, desc, func

logger = get_logger(__name__)
router = APIRouter(tags=["saved-searches"])


class SavedSearchRequest(BaseModel):
    """Request model for creating/updating saved searches."""

    name: str
    description: Optional[str] = None
    search_query: Optional[str] = None
    search_type: str = "general"
    search_filters: Optional[Dict[str, Any]] = None
    is_public: bool = False
    is_favorite: bool = False
    search_metadata: Optional[Dict[str, Any]] = None


class SavedSearchUpdate(BaseModel):
    """Request model for updating saved searches."""

    name: Optional[str] = None
    description: Optional[str] = None
    search_query: Optional[str] = None
    search_filters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    search_metadata: Optional[Dict[str, Any]] = None


def get_user_session(request: Request) -> Dict[str, Optional[str]]:
    """Extract user ID and session ID from request headers."""
    user_id = request.headers.get("x-user-id") or request.headers.get("X-User-ID")
    session_id = (
        request.headers.get("x-session-id")
        or request.headers.get("X-Session-ID")
        or request.headers.get("Session-ID")
    )
    return {"user_id": user_id, "session_id": session_id}


@router.post("/")
async def create_saved_search(
    search_request: SavedSearchRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Save a search query for later use."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Create new saved search
        saved_search = SavedSearch(
            name=search_request.name,
            description=search_request.description,
            user_id=user_id,
            session_id=session_id,
            search_query=search_request.search_query,
            search_type=search_request.search_type,
            search_filters=search_request.search_filters,
            is_public="true" if search_request.is_public else "false",
            is_favorite="true" if search_request.is_favorite else "false",
            search_metadata=search_request.search_metadata,
        )

        db.add(saved_search)
        await db.commit()
        await db.refresh(saved_search)

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="saved_search_created",
                endpoint="/api/saved-searches",
                http_method="POST",
                user_id=user_id,
                session_id=session_id,
                metadata={"search_type": search_request.search_type},
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        return {
            "status": "success",
            "saved_search": {
                "id": saved_search.id,
                "name": saved_search.name,
                "description": saved_search.description,
                "search_query": saved_search.search_query,
                "search_type": saved_search.search_type,
                "search_filters": saved_search.search_filters,
                "is_public": saved_search.is_public == "true",
                "is_favorite": saved_search.is_favorite == "true",
                "created_at": saved_search.created_at.isoformat()
                if saved_search.created_at
                else None,
                "search_metadata": saved_search.search_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create saved search", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create saved search")


@router.get("/")
async def list_saved_searches(
    request: Request,
    search_type: Optional[str] = Query(None, description="Filter by search type"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    skip: int = Query(0, description="Number of searches to skip"),
    limit: int = Query(50, description="Maximum number of searches to return"),
    db: AsyncSession = Depends(get_async_session),
):
    """Get saved searches for the current user/session."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Build base query
        query = select(SavedSearch).where(
            (SavedSearch.user_id == user_id) | (SavedSearch.session_id == session_id)
        )

        # Apply filters
        if search_type:
            query = query.where(SavedSearch.search_type == search_type)
        if is_favorite is not None:
            query = query.where(
                SavedSearch.is_favorite == ("true" if is_favorite else "false")
            )

        # Get total count
        count_query = (
            select(func.count())
            .select_from(SavedSearch)
            .where(
                (SavedSearch.user_id == user_id)
                | (SavedSearch.session_id == session_id)
            )
        )
        if search_type:
            count_query = count_query.where(SavedSearch.search_type == search_type)
        if is_favorite is not None:
            count_query = count_query.where(
                SavedSearch.is_favorite == ("true" if is_favorite else "false")
            )

        total_count_result = await db.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Apply pagination and ordering
        query = query.order_by(desc(SavedSearch.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        searches = result.scalars().all()

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="list_saved_searches",
                endpoint="/api/saved-searches",
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "count": len(searches),
                    "filters": {"search_type": search_type, "is_favorite": is_favorite},
                },
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        return {
            "status": "success",
            "searches": [
                {
                    "id": search.id,
                    "name": search.name,
                    "description": search.description,
                    "search_query": search.search_query,
                    "search_type": search.search_type,
                    "search_filters": search.search_filters,
                    "is_public": search.is_public == "true",
                    "is_favorite": search.is_favorite == "true",
                    "created_at": search.created_at.isoformat()
                    if search.created_at
                    else None,
                    "updated_at": search.updated_at.isoformat()
                    if search.updated_at
                    else None,
                    "use_count": search.use_count,
                    "last_used": search.last_used.isoformat()
                    if search.last_used
                    else None,
                }
                for search in searches
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list saved searches", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list saved searches")


@router.get("/{search_id}")
async def get_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
):
    """Get a specific saved search."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions
        if search.is_public != "true":
            if search.user_id != user_id and search.session_id != session_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this saved search"
                )

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="view_saved_search",
                endpoint=f"/api/saved-searches/{search_id}",
                resource_id=str(search_id),
                user_id=user_id,
                session_id=session_id,
                metadata={"search_name": search.name},
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        return {
            "status": "success",
            "search": {
                "id": search.id,
                "name": search.name,
                "description": search.description,
                "search_query": search.search_query,
                "search_type": search.search_type,
                "search_filters": search.search_filters,
                "is_public": search.is_public == "true",
                "is_favorite": search.is_favorite == "true",
                "created_at": search.created_at.isoformat()
                if search.created_at
                else None,
                "updated_at": search.updated_at.isoformat()
                if search.updated_at
                else None,
                "use_count": search.use_count,
                "last_used": search.last_used.isoformat() if search.last_used else None,
                "search_metadata": search.search_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get saved search", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get saved search")


@router.put("/{search_id}")
async def update_saved_search(
    search_id: int,
    search_update: SavedSearchUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Update a saved search."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions - only owner can update
        if search.user_id != user_id and search.session_id != session_id:
            raise HTTPException(
                status_code=403, detail="Permission denied to update this saved search"
            )

        # Update fields
        update_data = search_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["is_public", "is_favorite"] and value is not None:
                setattr(search, field, "true" if value else "false")
            else:
                setattr(search, field, value)

        await db.commit()
        await db.refresh(search)

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="update_saved_search",
                endpoint=f"/api/saved-searches/{search_id}",
                http_method="PUT",
                user_id=user_id,
                session_id=session_id,
                metadata={
                    "search_id": search_id,
                    "updated_fields": list(update_data.keys()),
                },
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        return {
            "status": "success",
            "search": {
                "id": search.id,
                "name": search.name,
                "description": search.description,
                "search_query": search.search_query,
                "search_type": search.search_type,
                "search_filters": search.search_filters,
                "is_public": search.is_public == "true",
                "is_favorite": search.is_favorite == "true",
                "created_at": search.created_at.isoformat()
                if search.created_at
                else None,
                "updated_at": search.updated_at.isoformat()
                if search.updated_at
                else None,
                "search_metadata": search.search_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update saved search", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update saved search")


@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
):
    """Delete a saved search."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions - only owner can delete
        if search.user_id != user_id and search.session_id != session_id:
            raise HTTPException(
                status_code=403, detail="Permission denied to delete this saved search"
            )

        await db.delete(search)
        await db.commit()

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="delete_saved_search",
                endpoint=f"/api/saved-searches/{search_id}",
                http_method="DELETE",
                user_id=user_id,
                session_id=session_id,
                metadata={"search_id": search_id, "search_name": search.name},
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        return {
            "status": "success",
            "message": f"Saved search '{search.name}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete saved search", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete saved search")


@router.post("/{search_id}/execute")
async def execute_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
):
    """Execute a saved search and return results."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Get the saved search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions
        if search.is_public != "true":
            if search.user_id != user_id and search.session_id != session_id:
                raise HTTPException(
                    status_code=403, detail="Access denied to this saved search"
                )

        # Update usage statistics
        search.use_count = (search.use_count or 0) + 1  # type: ignore
        from datetime import datetime

        search.last_used = datetime.now()  # type: ignore

        await db.commit()

        # Track analytics
        try:
            await analytics_service.track_activity(
                db=db,
                action_type="execute_saved_search",
                endpoint=f"/api/saved-searches/{search_id}/execute",
                http_method="POST",
                user_id=user_id,
                session_id=session_id,
                metadata={"search_id": search_id, "search_name": search.name},
            )
        except Exception as e:
            logger.error("Failed to track analytics", error=str(e))

        # Build redirect URL
        redirect_url = "/search"
        if search.search_query:
            redirect_url += f"?q={search.search_query}"
        if search.search_type and search.search_type != "general":
            redirect_url += f"&type={search.search_type}"

        return {
            "status": "success",
            "search": {
                "id": search.id,
                "name": search.name,
                "search_query": search.search_query,
                "search_type": search.search_type,
                "search_filters": search.search_filters,
            },
            "execution_info": {
                "use_count": search.use_count,
                "last_used": search.last_used.isoformat() if search.last_used else None,
                "redirect_url": redirect_url,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute saved search", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to execute saved search")


@router.get("/public/popular")
async def get_popular_public_searches(
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    db: AsyncSession = Depends(get_async_session),
):
    """Get popular public saved searches."""
    try:
        # Get public searches ordered by usage
        query = (
            select(SavedSearch)
            .where(SavedSearch.is_public == "true")
            .order_by(desc(SavedSearch.use_count), desc(SavedSearch.created_at))
            .limit(limit)
        )

        result = await db.execute(query)
        searches = result.scalars().all()

        return {
            "status": "success",
            "popular_searches": [
                {
                    "id": search.id,
                    "name": search.name,
                    "description": search.description,
                    "search_query": search.search_query,
                    "search_type": search.search_type,
                    "use_count": search.use_count or 0,
                    "created_at": search.created_at.isoformat()
                    if search.created_at
                    else None,
                    "search_metadata": search.search_metadata,
                }
                for search in searches
            ],
        }

    except Exception as e:
        logger.error("Failed to get popular searches", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get popular searches")


class UserPreferenceRequest(BaseModel):
    """Request model for setting user preferences."""

    preference_type: str
    preference_key: str
    preference_value: str


@router.post("/preferences")
async def set_user_preference(
    preference_request: UserPreferenceRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Set a user preference."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Check if preference already exists
        query = select(UserPreference).where(
            UserPreference.preference_type == preference_request.preference_type,
            UserPreference.preference_key == preference_request.preference_key,
            (UserPreference.user_id == user_id)
            | (UserPreference.session_id == session_id),
        )
        result = await db.execute(query)
        existing_pref = result.scalar_one_or_none()

        if existing_pref:
            # Update existing preference
            existing_pref.preference_value = preference_request.preference_value  # type: ignore
            preference = existing_pref
        else:
            # Create new preference
            preference = UserPreference(
                user_id=user_id,
                session_id=session_id,
                preference_type=preference_request.preference_type,
                preference_key=preference_request.preference_key,
                preference_value=preference_request.preference_value,
            )
            db.add(preference)

        await db.commit()
        await db.refresh(preference)

        return {
            "status": "success",
            "preference": {
                "id": preference.id,
                "preference_type": preference.preference_type,
                "preference_key": preference.preference_key,
                "preference_value": preference.preference_value,
                "created_at": preference.created_at.isoformat()
                if preference.created_at
                else None,
                "updated_at": preference.updated_at.isoformat()
                if preference.updated_at
                else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to set user preference", error=str(e))
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to set user preference")


@router.get("/preferences/{preference_type}")
async def get_user_preferences(
    preference_type: str,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
):
    """Get user preferences by type."""
    try:
        user_session = get_user_session(request)
        user_id = user_session["user_id"]
        session_id = user_session["session_id"]

        if not user_id and not session_id:
            raise HTTPException(
                status_code=400, detail="x-user-id or x-session-id header is required"
            )

        # Get preferences
        query = select(UserPreference).where(
            UserPreference.preference_type == preference_type,
            (UserPreference.user_id == user_id)
            | (UserPreference.session_id == session_id),
        )
        result = await db.execute(query)
        preferences = result.scalars().all()

        return {
            "status": "success",
            "preferences": [
                {
                    "id": pref.id,
                    "preference_key": pref.preference_key,
                    "preference_value": pref.preference_value,
                    "created_at": pref.created_at.isoformat()
                    if pref.created_at
                    else None,
                    "updated_at": pref.updated_at.isoformat()
                    if pref.updated_at
                    else None,
                }
                for pref in preferences
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user preferences", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user preferences")


async def extract_user_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract user information from request headers."""
    return {
        "user_id": request.headers.get("x-user-id"),
        "session_id": request.headers.get("x-session-id"),
    }
