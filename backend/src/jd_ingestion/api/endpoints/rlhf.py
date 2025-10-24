"""
RLHF (Reinforcement Learning from Human Feedback) API Endpoints

Provides endpoints for capturing and analyzing user feedback on AI suggestions.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...services.rlhf_service import RLHFService
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/rlhf", tags=["rlhf"])


# Request/Response Models
class RLHFFeedbackCreate(BaseModel):
    """Model for creating a single RLHF feedback entry"""

    user_id: Optional[int] = Field(None, description="User ID (optional)")
    job_id: Optional[int] = Field(None, description="Job ID being edited (optional)")
    event_type: str = Field(
        ..., description="Event type: accept, reject, modify, generate"
    )
    original_text: str = Field(..., description="Original text")
    suggested_text: Optional[str] = Field(None, description="AI-suggested text")
    final_text: Optional[str] = Field(
        None, description="Final text after user decision"
    )
    suggestion_type: Optional[str] = Field(
        None, description="Type: grammar, style, clarity, bias, compliance"
    )
    user_action: str = Field(
        ..., description="User action: accepted, rejected, modified"
    )
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="AI confidence score"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RLHFFeedbackBulkCreate(BaseModel):
    """Model for creating multiple RLHF feedback entries"""

    feedback_items: List[RLHFFeedbackCreate] = Field(
        ..., description="List of feedback entries"
    )


class RLHFFeedbackResponse(BaseModel):
    """Response model for RLHF feedback"""

    id: int
    user_id: Optional[int]
    job_id: Optional[int]
    event_type: str
    original_text: str
    suggested_text: Optional[str]
    final_text: Optional[str]
    suggestion_type: Optional[str]
    user_action: str
    confidence: Optional[float]
    metadata: Optional[Dict[str, Any]]
    created_at: str

    class Config:
        from_attributes = True


class AcceptanceRateResponse(BaseModel):
    """Response model for acceptance rate statistics"""

    total: int
    accepted: int
    rejected: int
    modified: int
    acceptance_rate: float
    suggestion_type: str
    days: int


class TypeStatisticsResponse(BaseModel):
    """Response model for type-based statistics"""

    suggestion_type: str
    total: int
    accepted: int
    rejected: int
    acceptance_rate: float
    avg_confidence: float


# Endpoints


@router.post("/feedback", response_model=RLHFFeedbackResponse, status_code=201)
def create_feedback(
    feedback: RLHFFeedbackCreate,
    db: Session = Depends(get_db),
):
    """
    Create a single RLHF feedback entry.

    Captures user feedback on an AI suggestion for model improvement.
    """
    try:
        result = RLHFService.create_feedback(
            db=db,
            user_id=feedback.user_id or 1,  # Default user ID for demo
            job_id=feedback.job_id,
            event_type=feedback.event_type,
            original_text=feedback.original_text,
            suggested_text=feedback.suggested_text,
            final_text=feedback.final_text,
            suggestion_type=feedback.suggestion_type,
            user_action=feedback.user_action,
            confidence=feedback.confidence,
            metadata=feedback.metadata,
        )

        return RLHFFeedbackResponse(
            id=int(result.id),
            user_id=int(result.user_id) if result.user_id is not None else None,
            job_id=int(result.job_id) if result.job_id is not None else None,
            event_type=str(result.event_type),
            original_text=str(result.original_text),
            suggested_text=str(result.suggested_text)
            if result.suggested_text is not None
            else None,
            final_text=str(result.final_text)
            if result.final_text is not None
            else None,
            suggestion_type=str(result.suggestion_type)
            if result.suggestion_type is not None
            else None,
            user_action=str(result.user_action),
            confidence=float(result.confidence) if result.confidence else None,
            metadata=dict(result.metadata) if result.metadata else None,  # type: ignore[call-overload]
            created_at=result.created_at.isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to create feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to create feedback. Please try again later."
        )


@router.post(
    "/feedback/bulk", response_model=List[RLHFFeedbackResponse], status_code=201
)
def create_bulk_feedback(
    bulk_feedback: RLHFFeedbackBulkCreate,
    db: Session = Depends(get_db),
):
    """
    Create multiple RLHF feedback entries in bulk.

    Useful for batch uploading feedback data from localStorage.
    """
    try:
        feedback_dicts = [
            {
                "user_id": item.user_id or 1,
                "job_id": item.job_id,
                "event_type": item.event_type,
                "original_text": item.original_text,
                "suggested_text": item.suggested_text,
                "final_text": item.final_text,
                "suggestion_type": item.suggestion_type,
                "user_action": item.user_action,
                "confidence": item.confidence,
                "metadata": item.metadata,
            }
            for item in bulk_feedback.feedback_items
        ]

        results = RLHFService.create_bulk_feedback(db=db, feedback_items=feedback_dicts)

        return [
            RLHFFeedbackResponse(
                id=int(result.id),
                user_id=int(result.user_id) if result.user_id is not None else None,
                job_id=int(result.job_id) if result.job_id is not None else None,
                event_type=str(result.event_type),
                original_text=str(result.original_text),
                suggested_text=str(result.suggested_text)
                if result.suggested_text is not None
                else None,
                final_text=str(result.final_text)
                if result.final_text is not None
                else None,
                suggestion_type=str(result.suggestion_type)
                if result.suggestion_type is not None
                else None,
                user_action=str(result.user_action),
                confidence=float(result.confidence) if result.confidence else None,
                metadata=dict(result.metadata) if result.metadata else None,  # type: ignore[call-overload]
                created_at=result.created_at.isoformat(),
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"Failed to create bulk feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to create bulk feedback. Please try again later."
        )


@router.get("/feedback/user/{user_id}", response_model=List[RLHFFeedbackResponse])
def get_user_feedback(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all feedback from a specific user"""
    try:
        results = RLHFService.get_feedback_by_user(
            db=db,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        return [
            RLHFFeedbackResponse(
                id=int(result.id),
                user_id=int(result.user_id) if result.user_id is not None else None,
                job_id=int(result.job_id) if result.job_id is not None else None,
                event_type=str(result.event_type),
                original_text=str(result.original_text),
                suggested_text=str(result.suggested_text)
                if result.suggested_text is not None
                else None,
                final_text=str(result.final_text)
                if result.final_text is not None
                else None,
                suggestion_type=str(result.suggestion_type)
                if result.suggestion_type is not None
                else None,
                user_action=str(result.user_action),
                confidence=float(result.confidence) if result.confidence else None,
                metadata=dict(result.metadata) if result.metadata else None,  # type: ignore[call-overload]
                created_at=result.created_at.isoformat(),
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"Failed to get user feedback for user_id={user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get user feedback. Please try again later."
        )


@router.get("/statistics/acceptance-rate", response_model=AcceptanceRateResponse)
def get_acceptance_rate(
    suggestion_type: Optional[str] = Query(
        None, description="Filter by suggestion type"
    ),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """Get acceptance rate statistics for AI suggestions"""
    try:
        stats = RLHFService.get_acceptance_rate(
            db=db,
            suggestion_type=suggestion_type,
            days=days,
        )

        return AcceptanceRateResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get acceptance rate: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get acceptance rate. Please try again later."
        )


@router.get("/statistics/by-type", response_model=List[TypeStatisticsResponse])
def get_type_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
):
    """Get acceptance statistics grouped by suggestion type"""
    try:
        stats = RLHFService.get_type_statistics(db=db, days=days)

        return [TypeStatisticsResponse(**item) for item in stats]

    except Exception as e:
        logger.error(f"Failed to get type statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to get type statistics. Please try again later."
        )


@router.get("/export/training-data")
def export_training_data(
    min_confidence: float = Query(
        0.7, ge=0, le=1, description="Minimum confidence threshold"
    ),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to export"),
    db: Session = Depends(get_db),
):
    """
    Export RLHF data for model training.

    Returns high-quality feedback data suitable for fine-tuning AI models.
    """
    try:
        training_data = RLHFService.export_training_data(
            db=db,
            min_confidence=min_confidence,
            limit=limit,
        )

        return {
            "count": len(training_data),
            "min_confidence": min_confidence,
            "training_data": training_data,
        }

    except Exception as e:
        logger.error(f"Failed to export training data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to export training data. Please try again later."
        )
