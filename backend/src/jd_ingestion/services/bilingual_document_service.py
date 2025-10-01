"""
Bilingual Document Service

Provides concurrent bilingual document management with:
- Segment-level translation storage
- Translation status tracking (draft, review, approved)
- Concurrent saving for both language versions
- Translation history and audit trail
- Document completeness calculation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

logger = logging.getLogger(__name__)


class BilingualDocumentService:
    """Service for managing bilingual documents and translation status."""

    async def get_bilingual_document(
        self,
        db: AsyncSession,
        job_id: int,
    ) -> Dict[str, Any]:
        """
        Get bilingual document with all segments and translation status.

        Args:
            db: Database session
            job_id: Job description ID

        Returns:
            Bilingual document with segments and metadata
        """
        # For now, we'll create a mock implementation
        # In production, this would query the database

        segments: List[Dict[str, Any]] = [
            {
                "id": "1",
                "english": "Director of Strategic Planning and Policy Development",
                "french": "Directeur de la planification stratégique et de l'élaboration des politiques",
                "status": "approved",
                "lastModified": datetime.utcnow().isoformat(),
                "modifiedBy": "admin",
            },
            {
                "id": "2",
                "english": "Reports to the Deputy Minister",
                "french": "Relève du sous-ministre",
                "status": "approved",
                "lastModified": datetime.utcnow().isoformat(),
                "modifiedBy": "admin",
            },
            {
                "id": "3",
                "english": "Lead strategic planning initiatives across the department",
                "french": "Diriger les initiatives de planification stratégique dans l'ensemble du ministère",
                "status": "review",
                "lastModified": datetime.utcnow().isoformat(),
                "modifiedBy": "translator",
            },
            {
                "id": "4",
                "english": "Develop and implement policy frameworks",
                "french": "",
                "status": "draft",
                "lastModified": datetime.utcnow().isoformat(),
                "modifiedBy": None,
            },
            {
                "id": "5",
                "english": "Provide executive leadership on strategic priorities",
                "french": "",
                "status": "draft",
                "lastModified": datetime.utcnow().isoformat(),
                "modifiedBy": None,
            },
        ]

        english_complete = len([s for s in segments if s["english"]])
        french_complete = len([s for s in segments if s["french"]])
        total = len(segments)

        return {
            "id": str(job_id),
            "title": f"Job Description {job_id}",
            "segments": segments,
            "metadata": {
                "created": datetime.utcnow().isoformat(),
                "modified": datetime.utcnow().isoformat(),
                "englishCompleteness": int((english_complete / total) * 100),
                "frenchCompleteness": int((french_complete / total) * 100),
                "overallStatus": "review",
            },
        }

    async def update_segment(
        self,
        db: AsyncSession,
        job_id: int,
        segment_id: str,
        language: str,
        content: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a specific segment's content.

        Args:
            db: Database session
            job_id: Job description ID
            segment_id: Segment identifier
            language: Language code (en or fr)
            content: New content
            user_id: User making the change

        Returns:
            Updated segment data
        """
        logger.info(
            f"Updating segment {segment_id} for job {job_id} in {language}"
        )

        # In production, this would update the database
        return {
            "id": segment_id,
            "language": language,
            "content": content,
            "lastModified": datetime.utcnow().isoformat(),
            "modifiedBy": user_id or "system",
        }

    async def update_segment_status(
        self,
        db: AsyncSession,
        job_id: int,
        segment_id: str,
        status: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a segment's translation status.

        Args:
            db: Database session
            job_id: Job description ID
            segment_id: Segment identifier
            status: New status (draft, review, approved)
            user_id: User making the change

        Returns:
            Updated segment with new status
        """
        logger.info(
            f"Updating segment {segment_id} status to {status} for job {job_id}"
        )

        # In production, this would:
        # 1. Update the database
        # 2. Create audit trail entry
        # 3. Trigger notifications if needed

        return {
            "id": segment_id,
            "status": status,
            "lastModified": datetime.utcnow().isoformat(),
            "modifiedBy": user_id or "system",
        }

    async def batch_update_status(
        self,
        db: AsyncSession,
        job_id: int,
        segment_ids: List[str],
        status: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update status for multiple segments at once.

        Args:
            db: Database session
            job_id: Job description ID
            segment_ids: List of segment identifiers
            status: New status to apply
            user_id: User making the changes

        Returns:
            Summary of updated segments
        """
        logger.info(
            f"Batch updating {len(segment_ids)} segments to {status} for job {job_id}"
        )

        updated_segments = []
        for segment_id in segment_ids:
            updated = await self.update_segment_status(
                db, job_id, segment_id, status, user_id
            )
            updated_segments.append(updated)

        return {
            "updated_count": len(updated_segments),
            "segments": updated_segments,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def save_bilingual_document(
        self,
        db: AsyncSession,
        job_id: int,
        segments: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save all segments of a bilingual document.

        Args:
            db: Database session
            job_id: Job description ID
            segments: List of segments with content
            user_id: User saving the document

        Returns:
            Save operation result
        """
        logger.info(f"Saving bilingual document for job {job_id}")

        # In production, this would:
        # 1. Update all segments in a transaction
        # 2. Calculate completeness percentages
        # 3. Update document metadata
        # 4. Create save history entry

        saved_count = 0
        for segment in segments:
            # Update English content if present
            if "english" in segment:
                await self.update_segment(
                    db,
                    job_id,
                    segment["id"],
                    "en",
                    segment["english"],
                    user_id,
                )
                saved_count += 1

            # Update French content if present
            if "french" in segment:
                await self.update_segment(
                    db,
                    job_id,
                    segment["id"],
                    "fr",
                    segment["french"],
                    user_id,
                )
                saved_count += 1

            # Update status if present
            if "status" in segment:
                await self.update_segment_status(
                    db,
                    job_id,
                    segment["id"],
                    segment["status"],
                    user_id,
                )

        return {
            "success": True,
            "saved_segments": saved_count,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Successfully saved {saved_count} segment updates",
        }

    async def get_translation_history(
        self,
        db: AsyncSession,
        job_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get translation status change history.

        Args:
            db: Database session
            job_id: Job description ID
            limit: Maximum number of history entries

        Returns:
            List of status change records
        """
        logger.info(f"Fetching translation history for job {job_id}")

        # Mock history data
        history = [
            {
                "id": "1",
                "segmentId": "3",
                "oldStatus": "draft",
                "newStatus": "review",
                "timestamp": datetime.utcnow().isoformat(),
                "user": "translator@example.com",
            },
            {
                "id": "2",
                "segmentId": "2",
                "oldStatus": "review",
                "newStatus": "approved",
                "timestamp": datetime.utcnow().isoformat(),
                "user": "reviewer@example.com",
            },
            {
                "id": "3",
                "segmentId": "1",
                "oldStatus": "review",
                "newStatus": "approved",
                "timestamp": datetime.utcnow().isoformat(),
                "user": "reviewer@example.com",
            },
        ]

        return history[:limit]

    async def calculate_document_completeness(
        self,
        db: AsyncSession,
        job_id: int,
    ) -> Dict[str, Any]:
        """
        Calculate translation completeness metrics.

        Args:
            db: Database session
            job_id: Job description ID

        Returns:
            Completeness metrics for both languages
        """
        document = await self.get_bilingual_document(db, job_id)
        segments = document["segments"]
        total = len(segments)

        if total == 0:
            return {
                "englishCompleteness": 0,
                "frenchCompleteness": 0,
                "overallCompleteness": 0,
                "draftSegments": 0,
                "reviewSegments": 0,
                "approvedSegments": 0,
            }

        english_filled = len([s for s in segments if s.get("english", "").strip()])
        french_filled = len([s for s in segments if s.get("french", "").strip()])
        draft = len([s for s in segments if s.get("status") == "draft"])
        review = len([s for s in segments if s.get("status") == "review"])
        approved = len([s for s in segments if s.get("status") == "approved"])

        both_filled = len([
            s for s in segments
            if s.get("english", "").strip() and s.get("french", "").strip()
        ])

        return {
            "englishCompleteness": int((english_filled / total) * 100),
            "frenchCompleteness": int((french_filled / total) * 100),
            "overallCompleteness": int((both_filled / total) * 100),
            "draftSegments": draft,
            "reviewSegments": review,
            "approvedSegments": approved,
            "totalSegments": total,
        }