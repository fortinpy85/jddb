"""
API endpoints for saved searches and user preferences.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from pydantic import BaseModel

from ...database.connection import get_async_session
from ...database.models import SavedSearch, UserPreference
from ...services.analytics_service import analytics_service
from ...utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["saved-searches"])


class SavedSearchRequest(BaseModel):
    """Request model for creating/updating saved searches."""

    name: str
    description: Optional[str] = None
    search_query: Optional[str] = None
    search_type: str = "text"
    search_filters: Optional[Dict] = None
    is_public: bool = False
    is_favorite: bool = False
    search_metadata: Optional[Dict] = None


class SavedSearchUpdate(BaseModel):
    """Request model for updating saved searches."""

    name: Optional[str] = None
    description: Optional[str] = None
    search_query: Optional[str] = None
    search_type: Optional[str] = None
    search_filters: Optional[Dict] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    search_metadata: Optional[Dict] = None


class UserPreferenceRequest(BaseModel):
    """Request model for setting user preferences."""

    preference_type: str
    preference_key: str
    preference_value: Any


def get_user_session(request: Request) -> Dict[str, Optional[str]]:
    """Extract user and session information from request."""
    user_id = request.headers.get("x-user-id")
    session_id = request.headers.get("x-session-id")
    return {"user_id": user_id, "session_id": session_id}


@router.post("/")
async def create_saved_search(
    search_request: SavedSearchRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Create a new saved search.

    Args:
        search_request: Search creation parameters
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Created saved search details
    """
    try:
        user_info = get_user_session(request)

        # Validate that we have some form of user identification
        if not user_info["user_id"] and not user_info["session_id"]:
            raise HTTPException(
                status_code=400,
                detail="Either x-user-id or x-session-id header is required",
            )

        # Create saved search
        saved_search = SavedSearch(
            name=search_request.name,
            description=search_request.description,
            user_id=user_info["user_id"],
            session_id=user_info["session_id"],
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

        # Track the creation activity
        await analytics_service.track_activity(
            db=db,
            action_type="create_saved_search",
            endpoint="/api/saved-searches/",
            http_method="POST",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            resource_id=str(saved_search.id),
            metadata={"search_name": search_request.name},
        )

        logger.info(
            "Saved search created",
            search_id=saved_search.id,
            name=search_request.name,
            user_id=user_info["user_id"],
            session_id=user_info["session_id"],
        )

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
                "created_at": saved_search.created_at.isoformat(),
                "search_metadata": saved_search.search_metadata,
            },
        }

    except Exception as e:
        logger.error("Failed to create saved search", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create saved search: {str(e)}"
        )


@router.get("/")
async def list_saved_searches(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search_type: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    List saved searches for the current user/session.

    Args:
        request: FastAPI request object for user identification
        skip: Number of searches to skip
        limit: Maximum number of searches to return
        search_type: Filter by search type
        is_favorite: Filter by favorite status
        db: Database session

    Returns:
        List of saved searches
    """
    try:
        user_info = get_user_session(request)

        if not user_info["user_id"] and not user_info["session_id"]:
            raise HTTPException(
                status_code=400,
                detail="Either x-user-id or x-session-id header is required",
            )

        # Build query
        query = select(SavedSearch)

        # Filter by user or session
        if user_info["user_id"]:
            query = query.where(
                or_(
                    SavedSearch.user_id == user_info["user_id"],
                    and_(
                        SavedSearch.user_id.is_(None),
                        SavedSearch.session_id == user_info["session_id"],
                    ),
                    SavedSearch.is_public == "true",
                )
            )
        else:
            query = query.where(
                or_(
                    SavedSearch.session_id == user_info["session_id"],
                    SavedSearch.is_public == "true",
                )
            )

        # Apply filters
        if search_type:
            query = query.where(SavedSearch.search_type == search_type)
        if is_favorite is not None:
            query = query.where(
                SavedSearch.is_favorite == ("true" if is_favorite else "false")
            )

        # Order by last used, then by favorites, then by name
        query = query.order_by(
            desc(SavedSearch.is_favorite), desc(SavedSearch.last_used), SavedSearch.name
        )

        # Get count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar_one()

        # Apply pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        searches = result.scalars().all()

        # Track the list activity
        await analytics_service.track_activity(
            db=db,
            action_type="list_saved_searches",
            endpoint="/api/saved-searches/",
            http_method="GET",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            results_count=len(searches),
        )

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
                    "created_at": search.created_at.isoformat(),
                    "updated_at": search.updated_at.isoformat(),
                    "last_used": (
                        search.last_used.isoformat() if search.last_used else None
                    ),
                    "use_count": search.use_count,
                    "last_result_count": search.last_result_count,
                    "search_metadata": search.search_metadata,
                }
                for search in searches
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_count,
                "has_more": skip + limit < total_count,
            },
        }

    except Exception as e:
        logger.error("Failed to list saved searches", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to list saved searches: {str(e)}"
        )


@router.get("/{search_id}")
async def get_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get a specific saved search.

    Args:
        search_id: ID of the saved search
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Saved search details
    """
    try:
        user_info = get_user_session(request)

        # Get the search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions
        can_access = (
            search.is_public == "true"
            or (user_info["user_id"] and search.user_id == user_info["user_id"])
            or (
                user_info["session_id"] and search.session_id == user_info["session_id"]
            )
        )

        if not can_access:
            raise HTTPException(
                status_code=403, detail="Access denied to this saved search"
            )

        # Track the access
        await analytics_service.track_activity(
            db=db,
            action_type="view_saved_search",
            endpoint=f"/api/saved-searches/{search_id}",
            http_method="GET",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            resource_id=str(search_id),
        )

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
                "created_at": search.created_at.isoformat(),
                "updated_at": search.updated_at.isoformat(),
                "last_used": search.last_used.isoformat() if search.last_used else None,
                "use_count": search.use_count,
                "last_result_count": search.last_result_count,
                "last_execution_time_ms": search.last_execution_time_ms,
                "search_metadata": search.search_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get saved search", search_id=search_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get saved search: {str(e)}"
        )


@router.put("/{search_id}")
async def update_saved_search(
    search_id: int,
    search_update: SavedSearchUpdate,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Update a saved search.

    Args:
        search_id: ID of the saved search
        search_update: Updated search parameters
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Updated saved search details
    """
    try:
        user_info = get_user_session(request)

        # Get the search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions (only owner can update)
        can_update = (
            user_info["user_id"] and search.user_id == user_info["user_id"]
        ) or (
            not search.user_id
            and user_info["session_id"]
            and search.session_id == user_info["session_id"]
        )

        if not can_update:
            raise HTTPException(
                status_code=403, detail="Permission denied to update this saved search"
            )

        # Update fields
        if search_update.name is not None:
            search.name = search_update.name
        if search_update.description is not None:
            search.description = search_update.description
        if search_update.search_query is not None:
            search.search_query = search_update.search_query
        if search_update.search_type is not None:
            search.search_type = search_update.search_type
        if search_update.search_filters is not None:
            search.search_filters = search_update.search_filters
        if search_update.is_public is not None:
            search.is_public = "true" if search_update.is_public else "false"
        if search_update.is_favorite is not None:
            search.is_favorite = "true" if search_update.is_favorite else "false"
        if search_update.search_metadata is not None:
            search.search_metadata = search_update.search_metadata

        search.updated_at = func.now()

        await db.commit()
        await db.refresh(search)

        # Track the update
        await analytics_service.track_activity(
            db=db,
            action_type="update_saved_search",
            endpoint=f"/api/saved-searches/{search_id}",
            http_method="PUT",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            resource_id=str(search_id),
        )

        logger.info("Saved search updated", search_id=search_id, name=search.name)

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
                "created_at": search.created_at.isoformat(),
                "updated_at": search.updated_at.isoformat(),
                "last_used": search.last_used.isoformat() if search.last_used else None,
                "use_count": search.use_count,
                "search_metadata": search.search_metadata,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update saved search", search_id=search_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update saved search: {str(e)}"
        )


@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Delete a saved search.

    Args:
        search_id: ID of the saved search
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Deletion confirmation
    """
    try:
        user_info = get_user_session(request)

        # Get the search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions (only owner can delete)
        can_delete = (
            user_info["user_id"] and search.user_id == user_info["user_id"]
        ) or (
            not search.user_id
            and user_info["session_id"]
            and search.session_id == user_info["session_id"]
        )

        if not can_delete:
            raise HTTPException(
                status_code=403, detail="Permission denied to delete this saved search"
            )

        # Delete the search
        await db.delete(search)
        await db.commit()

        # Track the deletion
        await analytics_service.track_activity(
            db=db,
            action_type="delete_saved_search",
            endpoint=f"/api/saved-searches/{search_id}",
            http_method="DELETE",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            resource_id=str(search_id),
            metadata={"deleted_search_name": search.name},
        )

        logger.info("Saved search deleted", search_id=search_id, name=search.name)

        return {
            "status": "success",
            "message": f"Saved search '{search.name}' deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete saved search", search_id=search_id, error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete saved search: {str(e)}"
        )


@router.post("/{search_id}/execute")
async def execute_saved_search(
    search_id: int, request: Request, db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Execute a saved search and update its usage statistics.

    Args:
        search_id: ID of the saved search
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Execution details and redirect information
    """
    try:
        user_info = get_user_session(request)

        # Get the search
        query = select(SavedSearch).where(SavedSearch.id == search_id)
        result = await db.execute(query)
        search = result.scalar_one_or_none()

        if not search:
            raise HTTPException(status_code=404, detail="Saved search not found")

        # Check permissions
        can_access = (
            search.is_public == "true"
            or (user_info["user_id"] and search.user_id == user_info["user_id"])
            or (
                user_info["session_id"] and search.session_id == user_info["session_id"]
            )
        )

        if not can_access:
            raise HTTPException(
                status_code=403, detail="Access denied to this saved search"
            )

        # Update usage statistics
        search.last_used = func.now()
        search.use_count = (search.use_count or 0) + 1

        await db.commit()

        # Track the execution
        await analytics_service.track_activity(
            db=db,
            action_type="execute_saved_search",
            endpoint=f"/api/saved-searches/{search_id}/execute",
            http_method="POST",
            session_id=user_info["session_id"],
            user_id=user_info["user_id"],
            resource_id=str(search_id),
            search_query=search.search_query,
            search_filters=search.search_filters,
        )

        logger.info("Saved search executed", search_id=search_id, name=search.name)

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
                "message": "Search parameters retrieved successfully",
                "use_count": search.use_count,
                "redirect_url": f"/api/search/jobs?query={search.search_query or ''}",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to execute saved search", search_id=search_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to execute saved search: {str(e)}"
        )


@router.get("/public/popular")
async def get_popular_public_searches(
    limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Get popular public saved searches.

    Args:
        limit: Maximum number of searches to return
        db: Database session

    Returns:
        List of popular public searches
    """
    try:
        query = (
            select(SavedSearch)
            .where(SavedSearch.is_public == "true")
            .order_by(desc(SavedSearch.use_count), desc(SavedSearch.last_used))
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
                    "search_type": search.search_type,
                    "use_count": search.use_count,
                    "last_used": (
                        search.last_used.isoformat() if search.last_used else None
                    ),
                    "created_at": search.created_at.isoformat(),
                }
                for search in searches
            ],
        }

    except Exception as e:
        logger.error("Failed to get popular public searches", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get popular searches: {str(e)}"
        )


@router.post("/preferences")
async def set_user_preference(
    preference_request: UserPreferenceRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Set a user preference.

    Args:
        preference_request: Preference data
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        Preference setting confirmation
    """
    try:
        user_info = get_user_session(request)

        if not user_info["user_id"] and not user_info["session_id"]:
            raise HTTPException(
                status_code=400,
                detail="Either x-user-id or x-session-id header is required",
            )

        # Check if preference exists
        query = select(UserPreference).where(
            and_(
                (
                    UserPreference.user_id == user_info["user_id"]
                    if user_info["user_id"]
                    else True
                ),
                (
                    UserPreference.session_id == user_info["session_id"]
                    if user_info["session_id"]
                    else True
                ),
                UserPreference.preference_type == preference_request.preference_type,
                UserPreference.preference_key == preference_request.preference_key,
            )
        )
        result = await db.execute(query)
        existing_pref = result.scalar_one_or_none()

        if existing_pref:
            # Update existing preference
            existing_pref.preference_value = preference_request.preference_value
            existing_pref.updated_at = func.now()
            await db.commit()
            pref_id = existing_pref.id
        else:
            # Create new preference
            new_pref = UserPreference(
                user_id=user_info["user_id"],
                session_id=user_info["session_id"],
                preference_type=preference_request.preference_type,
                preference_key=preference_request.preference_key,
                preference_value=preference_request.preference_value,
            )
            db.add(new_pref)
            await db.commit()
            await db.refresh(new_pref)
            pref_id = new_pref.id

        return {
            "status": "success",
            "preference": {
                "id": pref_id,
                "preference_type": preference_request.preference_type,
                "preference_key": preference_request.preference_key,
                "preference_value": preference_request.preference_value,
            },
        }

    except Exception as e:
        logger.error("Failed to set user preference", error=str(e))
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to set preference: {str(e)}"
        )


@router.get("/preferences/{preference_type}")
async def get_user_preferences(
    preference_type: str,
    request: Request,
    db: AsyncSession = Depends(get_async_session),
) -> Dict[str, Any]:
    """
    Get user preferences by type.

    Args:
        preference_type: Type of preferences to retrieve
        request: FastAPI request object for user identification
        db: Database session

    Returns:
        User preferences
    """
    try:
        user_info = get_user_session(request)

        if not user_info["user_id"] and not user_info["session_id"]:
            raise HTTPException(
                status_code=400,
                detail="Either x-user-id or x-session-id header is required",
            )

        query = select(UserPreference).where(
            and_(
                UserPreference.preference_type == preference_type,
                or_(
                    (
                        UserPreference.user_id == user_info["user_id"]
                        if user_info["user_id"]
                        else False
                    ),
                    (
                        UserPreference.session_id == user_info["session_id"]
                        if user_info["session_id"]
                        else False
                    ),
                ),
            )
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
                    "created_at": pref.created_at.isoformat(),
                    "updated_at": pref.updated_at.isoformat(),
                }
                for pref in preferences
            ],
        }

    except Exception as e:
        logger.error(
            "Failed to get user preferences",
            preference_type=preference_type,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get preferences: {str(e)}"
        )
