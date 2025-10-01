"""
Bilingual Document API Endpoints

FastAPI endpoints for concurrent bilingual document editing and management.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import get_async_session
from ...services.bilingual_document_service import BilingualDocumentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bilingual-documents", tags=["bilingual-documents"])

# Initialize service
bilingual_service = BilingualDocumentService()


# Pydantic Models
class SegmentUpdate(BaseModel):
    id: str = Field(..., description="Segment identifier")
    english: Optional[str] = Field(None, description="English content")
    french: Optional[str] = Field(None, description="French content")
    status: Optional[str] = Field(None, description="Translation status")


class SegmentStatusUpdate(BaseModel):
    segment_id: str = Field(..., description="Segment identifier")
    status: str = Field(..., description="New status (draft, review, approved)")


class BatchStatusUpdate(BaseModel):
    segment_ids: List[str] = Field(..., description="List of segment IDs")
    status: str = Field(..., description="New status to apply")


class DocumentSaveRequest(BaseModel):
    segments: List[SegmentUpdate] = Field(..., description="Segments to save")


@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_bilingual_document(
    job_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get bilingual document with all segments and translation status.

    Args:
        job_id: Job description ID
        db: Database session

    Returns:
        Bilingual document with segments and metadata
    """
    try:
        document = await bilingual_service.get_bilingual_document(db, job_id)
        return {
            "success": True,
            "document": document,
        }
    except Exception as e:
        logger.error(f"Error fetching bilingual document {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch bilingual document: {str(e)}",
        )


@router.put("/{job_id}/segments/{segment_id}", response_model=Dict[str, Any])
async def update_segment(
    job_id: int,
    segment_id: str,
    language: str = Query(..., description="Language code (en or fr)"),
    content: str = Query(..., description="New content"),
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update a specific segment's content.

    Args:
        job_id: Job description ID
        segment_id: Segment identifier
        language: Language code
        content: New content
        user_id: User making the change
        db: Database session

    Returns:
        Updated segment data
    """
    try:
        if language not in ["en", "fr"]:
            raise HTTPException(
                status_code=400,
                detail="Language must be 'en' or 'fr'",
            )

        updated = await bilingual_service.update_segment(
            db, job_id, segment_id, language, content, user_id
        )

        return {
            "success": True,
            "segment": updated,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating segment {segment_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update segment: {str(e)}",
        )


@router.put("/{job_id}/segments/{segment_id}/status", response_model=Dict[str, Any])
async def update_segment_status(
    job_id: int,
    segment_id: str,
    request: SegmentStatusUpdate,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update a segment's translation status.

    Args:
        job_id: Job description ID
        segment_id: Segment identifier
        request: Status update request
        user_id: User making the change
        db: Database session

    Returns:
        Updated segment with new status
    """
    try:
        if request.status not in ["draft", "review", "approved"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be 'draft', 'review', or 'approved'",
            )

        updated = await bilingual_service.update_segment_status(
            db, job_id, segment_id, request.status, user_id
        )

        return {
            "success": True,
            "segment": updated,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating segment status {segment_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update segment status: {str(e)}",
        )


@router.post("/{job_id}/batch-status", response_model=Dict[str, Any])
async def batch_update_status(
    job_id: int,
    request: BatchStatusUpdate,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update status for multiple segments at once.

    Args:
        job_id: Job description ID
        request: Batch status update request
        user_id: User making the changes
        db: Database session

    Returns:
        Summary of updated segments
    """
    try:
        if request.status not in ["draft", "review", "approved"]:
            raise HTTPException(
                status_code=400,
                detail="Status must be 'draft', 'review', or 'approved'",
            )

        result = await bilingual_service.batch_update_status(
            db, job_id, request.segment_ids, request.status, user_id
        )

        return {
            "success": True,
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch updating status for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to batch update status: {str(e)}",
        )


@router.post("/{job_id}/save", response_model=Dict[str, Any])
async def save_bilingual_document(
    job_id: int,
    request: DocumentSaveRequest,
    user_id: Optional[str] = Query(None, description="User ID"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Save all segments of a bilingual document.

    Args:
        job_id: Job description ID
        request: Document save request with segments
        user_id: User saving the document
        db: Database session

    Returns:
        Save operation result
    """
    try:
        segments_data = [segment.dict() for segment in request.segments]

        result = await bilingual_service.save_bilingual_document(
            db, job_id, segments_data, user_id
        )

        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Error saving bilingual document {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save bilingual document: {str(e)}",
        )


@router.get("/{job_id}/history", response_model=Dict[str, Any])
async def get_translation_history(
    job_id: int,
    limit: int = Query(50, ge=1, le=200, description="Max number of history entries"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get translation status change history.

    Args:
        job_id: Job description ID
        limit: Maximum number of history entries
        db: Database session

    Returns:
        List of status change records
    """
    try:
        history = await bilingual_service.get_translation_history(db, job_id, limit)

        return {
            "success": True,
            "history": history,
            "count": len(history),
        }
    except Exception as e:
        logger.error(f"Error fetching translation history for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch translation history: {str(e)}",
        )


@router.get("/{job_id}/completeness", response_model=Dict[str, Any])
async def get_document_completeness(
    job_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Calculate translation completeness metrics.

    Args:
        job_id: Job description ID
        db: Database session

    Returns:
        Completeness metrics for both languages
    """
    try:
        completeness = await bilingual_service.calculate_document_completeness(
            db, job_id
        )

        return {
            "success": True,
            "completeness": completeness,
        }
    except Exception as e:
        logger.error(f"Error calculating completeness for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate completeness: {str(e)}",
        )
