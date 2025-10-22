"""
Tests for RLHF Service

Tests the Reinforcement Learning from Human Feedback service functionality
including feedback creation, retrieval, and analytics.
"""

from decimal import Decimal
from sqlalchemy.orm import Session

from jd_ingestion.services.rlhf_service import RLHFService


class TestCreateFeedback:
    """Test creating RLHF feedback entries."""

    def test_create_feedback_success(self, sync_session: Session):
        """Test successful creation of feedback entry."""
        feedback = RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=10,
            event_type="accept",
            original_text="Original text here",
            suggested_text="Suggested improvement",
            final_text="Final accepted text",
            suggestion_type="grammar",
            user_action="accepted",
            confidence=0.95,
            metadata={"source": "AI model v1"},
        )

        assert feedback.id is not None
        assert feedback.user_id == 1
        assert feedback.job_id == 10
        assert feedback.event_type == "accept"
        assert feedback.original_text == "Original text here"
        assert feedback.suggested_text == "Suggested improvement"
        assert feedback.final_text == "Final accepted text"
        assert feedback.suggestion_type == "grammar"
        assert feedback.user_action == "accepted"
        assert feedback.confidence == Decimal("0.950")
        assert feedback.metadata == {"source": "AI model v1"}
        assert feedback.created_at is not None

    def test_create_feedback_without_optional_fields(self, sync_session: Session):
        """Test creating feedback with minimal required fields."""
        feedback = RLHFService.create_feedback(
            db=sync_session,
            user_id=2,
            job_id=None,
            event_type="generate",
            original_text="Original",
            suggested_text=None,
            final_text=None,
            suggestion_type=None,
            user_action="generated",
        )

        assert feedback.id is not None
        assert feedback.user_id == 2
        assert feedback.job_id is None
        assert feedback.suggested_text is None
        assert feedback.confidence is None
        assert feedback.metadata is None


class TestCreateBulkFeedback:
    """Test bulk feedback creation."""

    def test_create_bulk_feedback_success(self, sync_session: Session):
        """Test creating multiple feedback entries in bulk."""
        feedback_items = [
            {
                "user_id": 1,
                "job_id": 10,
                "event_type": "accept",
                "original_text": "Text 1",
                "suggested_text": "Suggestion 1",
                "final_text": "Final 1",
                "suggestion_type": "grammar",
                "user_action": "accepted",
                "confidence": 0.9,
            },
            {
                "user_id": 1,
                "job_id": 11,
                "event_type": "reject",
                "original_text": "Text 2",
                "suggested_text": "Suggestion 2",
                "final_text": "Original kept",
                "suggestion_type": "style",
                "user_action": "rejected",
                "confidence": 0.7,
            },
            {
                "user_id": 2,
                "job_id": 12,
                "event_type": "modify",
                "original_text": "Text 3",
                "suggested_text": "Suggestion 3",
                "final_text": "Modified version",
                "suggestion_type": "grammar",
                "user_action": "modified",
                "confidence": 0.85,
            },
        ]

        results = RLHFService.create_bulk_feedback(
            db=sync_session, feedback_items=feedback_items
        )

        assert len(results) == 3
        assert all(f.id is not None for f in results)
        assert results[0].user_action == "accepted"
        assert results[1].user_action == "rejected"
        assert results[2].user_action == "modified"

    def test_create_bulk_feedback_empty_list(self, sync_session: Session):
        """Test bulk creation with empty list."""
        results = RLHFService.create_bulk_feedback(db=sync_session, feedback_items=[])

        assert results == []


class TestGetFeedbackById:
    """Test retrieving feedback by ID."""

    def test_get_feedback_by_id_success(self, sync_session: Session):
        """Test retrieving existing feedback by ID."""
        # Create feedback first
        created = RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=10,
            event_type="accept",
            original_text="Test",
            suggested_text="Suggestion",
            final_text="Final",
            suggestion_type="grammar",
            user_action="accepted",
        )

        # Retrieve it
        feedback = RLHFService.get_feedback_by_id(
            db=sync_session, feedback_id=created.id
        )

        assert feedback is not None
        assert feedback.id == created.id
        assert feedback.original_text == "Test"

    def test_get_feedback_by_id_not_found(self, sync_session: Session):
        """Test retrieving non-existent feedback returns None."""
        feedback = RLHFService.get_feedback_by_id(db=sync_session, feedback_id=99999)

        assert feedback is None


class TestGetFeedbackByUser:
    """Test retrieving feedback by user ID."""

    def test_get_feedback_by_user_success(self, sync_session: Session):
        """Test retrieving all feedback for a user."""
        # Create feedback for two users
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=10,
            event_type="accept",
            original_text="User 1 feedback 1",
            suggested_text="S1",
            final_text="F1",
            suggestion_type="grammar",
            user_action="accepted",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=11,
            event_type="reject",
            original_text="User 1 feedback 2",
            suggested_text="S2",
            final_text="F2",
            suggestion_type="style",
            user_action="rejected",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=2,
            job_id=12,
            event_type="accept",
            original_text="User 2 feedback",
            suggested_text="S3",
            final_text="F3",
            suggestion_type="grammar",
            user_action="accepted",
        )

        # Get user 1's feedback
        user1_feedback = RLHFService.get_feedback_by_user(db=sync_session, user_id=1)

        assert len(user1_feedback) == 2
        assert all(f.user_id == 1 for f in user1_feedback)
        # Should be ordered by created_at desc (most recent first)
        assert user1_feedback[0].original_text == "User 1 feedback 2"

    def test_get_feedback_by_user_with_pagination(self, sync_session: Session):
        """Test pagination for user feedback."""
        # Create 5 feedback entries
        for i in range(5):
            RLHFService.create_feedback(
                db=sync_session,
                user_id=1,
                job_id=i,
                event_type="accept",
                original_text=f"Text {i}",
                suggested_text=f"Suggestion {i}",
                final_text=f"Final {i}",
                suggestion_type="grammar",
                user_action="accepted",
            )

        # Get first 2
        page1 = RLHFService.get_feedback_by_user(
            db=sync_session, user_id=1, limit=2, offset=0
        )
        assert len(page1) == 2

        # Get next 2
        page2 = RLHFService.get_feedback_by_user(
            db=sync_session, user_id=1, limit=2, offset=2
        )
        assert len(page2) == 2

        # Different pages should have different entries
        assert page1[0].id != page2[0].id


class TestGetFeedbackByJob:
    """Test retrieving feedback by job ID."""

    def test_get_feedback_by_job_success(self, sync_session: Session):
        """Test retrieving all feedback for a job."""
        # Create feedback for two jobs
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=10,
            event_type="accept",
            original_text="Job 10 feedback 1",
            suggested_text="S1",
            final_text="F1",
            suggestion_type="grammar",
            user_action="accepted",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=2,
            job_id=10,
            event_type="modify",
            original_text="Job 10 feedback 2",
            suggested_text="S2",
            final_text="F2",
            suggestion_type="style",
            user_action="modified",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=11,
            event_type="reject",
            original_text="Job 11 feedback",
            suggested_text="S3",
            final_text="F3",
            suggestion_type="grammar",
            user_action="rejected",
        )

        # Get job 10's feedback
        job10_feedback = RLHFService.get_feedback_by_job(db=sync_session, job_id=10)

        assert len(job10_feedback) == 2
        assert all(f.job_id == 10 for f in job10_feedback)


class TestGetFeedbackByType:
    """Test retrieving feedback by suggestion type."""

    def test_get_feedback_by_type_success(self, sync_session: Session):
        """Test filtering feedback by suggestion type."""
        # Create feedback of different types
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=10,
            event_type="accept",
            original_text="Grammar 1",
            suggested_text="S1",
            final_text="F1",
            suggestion_type="grammar",
            user_action="accepted",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=1,
            job_id=11,
            event_type="accept",
            original_text="Style 1",
            suggested_text="S2",
            final_text="F2",
            suggestion_type="style",
            user_action="accepted",
        )
        RLHFService.create_feedback(
            db=sync_session,
            user_id=2,
            job_id=12,
            event_type="accept",
            original_text="Grammar 2",
            suggested_text="S3",
            final_text="F3",
            suggestion_type="grammar",
            user_action="accepted",
        )

        # Get grammar feedback
        grammar_feedback = RLHFService.get_feedback_by_type(
            db=sync_session, suggestion_type="grammar"
        )

        assert len(grammar_feedback) == 2
        assert all(f.suggestion_type == "grammar" for f in grammar_feedback)


class TestGetAcceptanceRate:
    """Test calculating acceptance rate statistics."""

    def test_get_acceptance_rate_all_types(self, sync_session: Session):
        """Test acceptance rate calculation across all suggestion types."""
        # Create varied feedback: 3 accepted, 1 rejected, 1 modified
        RLHFService.create_bulk_feedback(
            db=sync_session,
            feedback_items=[
                {
                    "user_id": 1,
                    "job_id": i,
                    "event_type": "action",
                    "original_text": f"Text {i}",
                    "suggested_text": f"Suggestion {i}",
                    "final_text": f"Final {i}",
                    "suggestion_type": "grammar",
                    "user_action": action,
                }
                for i, action in enumerate(
                    ["accepted", "accepted", "accepted", "rejected", "modified"]
                )
            ],
        )

        stats = RLHFService.get_acceptance_rate(db=sync_session, days=30)

        assert stats["total"] == 5
        assert stats["accepted"] == 3
        assert stats["rejected"] == 1
        assert stats["modified"] == 1
        assert stats["acceptance_rate"] == 60.0  # 3/5 * 100
        assert stats["suggestion_type"] == "all"
        assert stats["days"] == 30

    def test_get_acceptance_rate_by_type(self, sync_session: Session):
        """Test acceptance rate for specific suggestion type."""
        # Create feedback of different types
        RLHFService.create_bulk_feedback(
            db=sync_session,
            feedback_items=[
                {
                    "user_id": 1,
                    "job_id": 1,
                    "event_type": "action",
                    "original_text": "Grammar 1",
                    "suggested_text": "S1",
                    "final_text": "F1",
                    "suggestion_type": "grammar",
                    "user_action": "accepted",
                },
                {
                    "user_id": 1,
                    "job_id": 2,
                    "event_type": "action",
                    "original_text": "Grammar 2",
                    "suggested_text": "S2",
                    "final_text": "F2",
                    "suggestion_type": "grammar",
                    "user_action": "rejected",
                },
                {
                    "user_id": 1,
                    "job_id": 3,
                    "event_type": "action",
                    "original_text": "Style 1",
                    "suggested_text": "S3",
                    "final_text": "F3",
                    "suggestion_type": "style",
                    "user_action": "accepted",
                },
            ],
        )

        stats = RLHFService.get_acceptance_rate(
            db=sync_session, suggestion_type="grammar", days=30
        )

        assert stats["total"] == 2
        assert stats["accepted"] == 1
        assert stats["rejected"] == 1
        assert stats["acceptance_rate"] == 50.0
        assert stats["suggestion_type"] == "grammar"

    def test_get_acceptance_rate_empty(self, sync_session: Session):
        """Test acceptance rate with no data returns 0%."""
        stats = RLHFService.get_acceptance_rate(db=sync_session, days=30)

        assert stats["total"] == 0
        assert stats["accepted"] == 0
        assert stats["acceptance_rate"] == 0


class TestGetTypeStatistics:
    """Test getting statistics grouped by suggestion type."""

    def test_get_type_statistics_success(self, sync_session: Session):
        """Test statistics grouped by suggestion type."""
        # Create feedback of multiple types
        RLHFService.create_bulk_feedback(
            db=sync_session,
            feedback_items=[
                {
                    "user_id": 1,
                    "job_id": 1,
                    "event_type": "action",
                    "original_text": "Grammar 1",
                    "suggested_text": "S1",
                    "final_text": "F1",
                    "suggestion_type": "grammar",
                    "user_action": "accepted",
                    "confidence": 0.9,
                },
                {
                    "user_id": 1,
                    "job_id": 2,
                    "event_type": "action",
                    "original_text": "Grammar 2",
                    "suggested_text": "S2",
                    "final_text": "F2",
                    "suggestion_type": "grammar",
                    "user_action": "rejected",
                    "confidence": 0.8,
                },
                {
                    "user_id": 1,
                    "job_id": 3,
                    "event_type": "action",
                    "original_text": "Style 1",
                    "suggested_text": "S3",
                    "final_text": "F3",
                    "suggestion_type": "style",
                    "user_action": "accepted",
                    "confidence": 0.95,
                },
            ],
        )

        stats = RLHFService.get_type_statistics(db=sync_session, days=30)

        assert len(stats) == 2  # grammar and style

        # Find grammar stats
        grammar_stats = next(
            (s for s in stats if s["suggestion_type"] == "grammar"), None
        )
        assert grammar_stats is not None
        assert grammar_stats["total"] == 2
        assert grammar_stats["accepted"] == 1
        assert grammar_stats["rejected"] == 1
        assert grammar_stats["acceptance_rate"] == 50.0
        assert grammar_stats["avg_confidence"] == 0.85  # (0.9 + 0.8) / 2

        # Find style stats
        style_stats = next((s for s in stats if s["suggestion_type"] == "style"), None)
        assert style_stats is not None
        assert style_stats["total"] == 1
        assert style_stats["accepted"] == 1
        assert style_stats["acceptance_rate"] == 100.0

    def test_get_type_statistics_empty(self, sync_session: Session):
        """Test statistics with no data returns empty list."""
        stats = RLHFService.get_type_statistics(db=sync_session, days=30)

        assert stats == []


class TestExportTrainingData:
    """Test exporting RLHF data for model training."""

    def test_export_training_data_success(self, sync_session: Session):
        """Test exporting training data with confidence filter."""
        # Create feedback with varying confidence
        RLHFService.create_bulk_feedback(
            db=sync_session,
            feedback_items=[
                {
                    "user_id": 1,
                    "job_id": 1,
                    "event_type": "action",
                    "original_text": "High confidence accepted",
                    "suggested_text": "Suggestion 1",
                    "final_text": "Final 1",
                    "suggestion_type": "grammar",
                    "user_action": "accepted",
                    "confidence": 0.95,
                },
                {
                    "user_id": 1,
                    "job_id": 2,
                    "event_type": "action",
                    "original_text": "Low confidence accepted",
                    "suggested_text": "Suggestion 2",
                    "final_text": "Final 2",
                    "suggestion_type": "style",
                    "user_action": "accepted",
                    "confidence": 0.6,  # Below 0.7 threshold
                },
                {
                    "user_id": 1,
                    "job_id": 3,
                    "event_type": "action",
                    "original_text": "High confidence rejected",
                    "suggested_text": "Suggestion 3",
                    "final_text": "Final 3",
                    "suggestion_type": "grammar",
                    "user_action": "rejected",
                    "confidence": 0.85,
                },
                {
                    "user_id": 1,
                    "job_id": 4,
                    "event_type": "action",
                    "original_text": "Modified (excluded)",
                    "suggested_text": "Suggestion 4",
                    "final_text": "Final 4",
                    "suggestion_type": "grammar",
                    "user_action": "modified",  # Not accepted or rejected
                    "confidence": 0.9,
                },
            ],
        )

        training_data = RLHFService.export_training_data(
            db=sync_session, min_confidence=0.7, limit=1000
        )

        # Should only include items with confidence >= 0.7 and action in [accepted, rejected]
        assert len(training_data) == 2

        # Check data structure
        assert "id" in training_data[0]
        assert "original_text" in training_data[0]
        assert "suggested_text" in training_data[0]
        assert "final_text" in training_data[0]
        assert "suggestion_type" in training_data[0]
        assert "user_action" in training_data[0]
        assert "confidence" in training_data[0]
        assert "was_accepted" in training_data[0]
        assert "timestamp" in training_data[0]

        # Verify boolean flag
        accepted_item = next((d for d in training_data if d["was_accepted"]), None)
        rejected_item = next((d for d in training_data if not d["was_accepted"]), None)

        assert accepted_item is not None
        assert rejected_item is not None

    def test_export_training_data_with_limit(self, sync_session: Session):
        """Test training data export respects limit parameter."""
        # Create 5 high-confidence accepted items
        RLHFService.create_bulk_feedback(
            db=sync_session,
            feedback_items=[
                {
                    "user_id": 1,
                    "job_id": i,
                    "event_type": "action",
                    "original_text": f"Text {i}",
                    "suggested_text": f"Suggestion {i}",
                    "final_text": f"Final {i}",
                    "suggestion_type": "grammar",
                    "user_action": "accepted",
                    "confidence": 0.9,
                }
                for i in range(5)
            ],
        )

        training_data = RLHFService.export_training_data(
            db=sync_session, min_confidence=0.7, limit=3
        )

        assert len(training_data) == 3

    def test_export_training_data_empty(self, sync_session: Session):
        """Test export with no qualifying data returns empty list."""
        training_data = RLHFService.export_training_data(
            db=sync_session, min_confidence=0.7, limit=1000
        )

        assert training_data == []
