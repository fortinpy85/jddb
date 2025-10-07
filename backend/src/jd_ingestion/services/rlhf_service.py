"""
RLHF (Reinforcement Learning from Human Feedback) Service

Captures user feedback on AI suggestions to improve model performance.
Tracks accept/reject decisions, modifications, and user preferences.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from ..database.models import RLHFFeedback


class RLHFService:
    """Service for managing RLHF feedback data"""

    @staticmethod
    def create_feedback(
        db: Session,
        user_id: int,
        job_id: Optional[int],
        event_type: str,
        original_text: str,
        suggested_text: Optional[str],
        final_text: Optional[str],
        suggestion_type: Optional[str],
        user_action: str,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RLHFFeedback:
        """
        Create a new RLHF feedback entry

        Args:
            db: Database session
            user_id: ID of the user providing feedback
            job_id: Optional ID of the job being edited
            event_type: Type of event (accept, reject, modify, generate)
            original_text: Original text before AI suggestion
            suggested_text: AI-suggested text
            final_text: Final text after user decision
            suggestion_type: Category of suggestion (grammar, style, etc.)
            user_action: User's action (accepted, rejected, modified)
            confidence: AI confidence score (0-1)
            metadata: Additional metadata as JSON

        Returns:
            Created RLHFFeedback instance
        """
        feedback = RLHFFeedback(
            user_id=user_id,
            job_id=job_id,
            event_type=event_type,
            original_text=original_text,
            suggested_text=suggested_text,
            final_text=final_text,
            suggestion_type=suggestion_type,
            user_action=user_action,
            confidence=confidence,
            metadata=metadata,
            created_at=datetime.utcnow(),
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return feedback

    @staticmethod
    def create_bulk_feedback(
        db: Session,
        feedback_items: List[Dict[str, Any]],
    ) -> List[RLHFFeedback]:
        """
        Create multiple RLHF feedback entries in bulk

        Args:
            db: Database session
            feedback_items: List of feedback dictionaries

        Returns:
            List of created RLHFFeedback instances
        """
        feedback_objects = []

        for item in feedback_items:
            feedback = RLHFFeedback(
                user_id=item.get("user_id"),
                job_id=item.get("job_id"),
                event_type=item.get("event_type"),
                original_text=item.get("original_text"),
                suggested_text=item.get("suggested_text"),
                final_text=item.get("final_text"),
                suggestion_type=item.get("suggestion_type"),
                user_action=item.get("user_action"),
                confidence=item.get("confidence"),
                metadata=item.get("metadata"),
                created_at=datetime.utcnow(),
            )
            feedback_objects.append(feedback)

        db.add_all(feedback_objects)
        db.commit()

        for feedback in feedback_objects:
            db.refresh(feedback)

        return feedback_objects

    @staticmethod
    def get_feedback_by_id(db: Session, feedback_id: int) -> Optional[RLHFFeedback]:
        """Get feedback entry by ID"""
        return db.query(RLHFFeedback).filter(RLHFFeedback.id == feedback_id).first()

    @staticmethod
    def get_feedback_by_user(
        db: Session,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RLHFFeedback]:
        """Get all feedback from a specific user"""
        return (
            db.query(RLHFFeedback)
            .filter(RLHFFeedback.user_id == user_id)
            .order_by(desc(RLHFFeedback.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_feedback_by_job(
        db: Session,
        job_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RLHFFeedback]:
        """Get all feedback for a specific job"""
        return (
            db.query(RLHFFeedback)
            .filter(RLHFFeedback.job_id == job_id)
            .order_by(desc(RLHFFeedback.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_feedback_by_type(
        db: Session,
        suggestion_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RLHFFeedback]:
        """Get feedback filtered by suggestion type"""
        return (
            db.query(RLHFFeedback)
            .filter(RLHFFeedback.suggestion_type == suggestion_type)
            .order_by(desc(RLHFFeedback.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_acceptance_rate(
        db: Session,
        suggestion_type: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Calculate acceptance rate for AI suggestions

        Args:
            db: Database session
            suggestion_type: Optional filter by suggestion type
            days: Number of days to look back

        Returns:
            Dictionary with acceptance statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(RLHFFeedback).filter(RLHFFeedback.created_at >= cutoff_date)

        if suggestion_type:
            query = query.filter(RLHFFeedback.suggestion_type == suggestion_type)

        total = query.count()
        accepted = query.filter(RLHFFeedback.user_action == "accepted").count()
        rejected = query.filter(RLHFFeedback.user_action == "rejected").count()
        modified = query.filter(RLHFFeedback.user_action == "modified").count()

        acceptance_rate = (accepted / total * 100) if total > 0 else 0

        return {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "modified": modified,
            "acceptance_rate": round(acceptance_rate, 2),
            "suggestion_type": suggestion_type or "all",
            "days": days,
        }

    @staticmethod
    def get_type_statistics(
        db: Session,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get acceptance statistics grouped by suggestion type

        Returns:
            List of dictionaries with statistics per type
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        results = (
            db.query(
                RLHFFeedback.suggestion_type,
                func.count(RLHFFeedback.id).label("total"),
                func.sum(
                    func.case((RLHFFeedback.user_action == "accepted", 1), else_=0)
                ).label("accepted"),
                func.sum(
                    func.case((RLHFFeedback.user_action == "rejected", 1), else_=0)
                ).label("rejected"),
                func.avg(RLHFFeedback.confidence).label("avg_confidence"),
            )
            .filter(RLHFFeedback.created_at >= cutoff_date)
            .group_by(RLHFFeedback.suggestion_type)
            .all()
        )

        statistics = []
        for row in results:
            total = row.total or 0
            accepted = row.accepted or 0
            acceptance_rate = (accepted / total * 100) if total > 0 else 0

            statistics.append(
                {
                    "suggestion_type": row.suggestion_type,
                    "total": total,
                    "accepted": accepted,
                    "rejected": row.rejected or 0,
                    "acceptance_rate": round(acceptance_rate, 2),
                    "avg_confidence": round(row.avg_confidence or 0, 3),
                }
            )

        return statistics

    @staticmethod
    def export_training_data(
        db: Session,
        min_confidence: float = 0.7,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Export RLHF data for model training

        Args:
            db: Database session
            min_confidence: Minimum confidence threshold
            limit: Maximum number of records to export

        Returns:
            List of training examples
        """
        feedback_items = (
            db.query(RLHFFeedback)
            .filter(
                and_(
                    RLHFFeedback.confidence >= min_confidence,
                    RLHFFeedback.user_action.in_(["accepted", "rejected"]),
                )
            )
            .order_by(desc(RLHFFeedback.created_at))
            .limit(limit)
            .all()
        )

        training_data = []
        for item in feedback_items:
            training_data.append(
                {
                    "id": item.id,
                    "original_text": item.original_text,
                    "suggested_text": item.suggested_text,
                    "final_text": item.final_text,
                    "suggestion_type": item.suggestion_type,
                    "user_action": item.user_action,
                    "confidence": item.confidence,
                    "was_accepted": item.user_action == "accepted",
                    "timestamp": item.created_at.isoformat(),
                }
            )

        return training_data
