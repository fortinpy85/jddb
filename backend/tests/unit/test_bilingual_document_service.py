"""Tests for Bilingual Document Service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.bilingual_document_service import BilingualDocumentService


@pytest.fixture
def bilingual_service():
    """Create BilingualDocumentService instance."""
    return BilingualDocumentService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_bilingual_document(bilingual_service, mock_db):
    """Test getting bilingual document with segments."""
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=1,
    )

    assert "segments" in result
    assert "metadata" in result
    assert "completeness" in result
    assert isinstance(result["segments"], list)
    assert len(result["segments"]) > 0


@pytest.mark.asyncio
async def test_bilingual_document_segments_structure(bilingual_service, mock_db):
    """Test that bilingual segments have required fields."""
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=1,
    )

    segment = result["segments"][0]
    assert "id" in segment
    assert "english" in segment
    assert "french" in segment
    assert "status" in segment
    assert "lastModified" in segment
    assert "modifiedBy" in segment


@pytest.mark.asyncio
async def test_bilingual_document_status_values(bilingual_service, mock_db):
    """Test that segment statuses are valid."""
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=1,
    )

    valid_statuses = {"draft", "review", "approved"}
    for segment in result["segments"]:
        assert segment["status"] in valid_statuses


@pytest.mark.asyncio
async def test_save_bilingual_segment(bilingual_service, mock_db):
    """Test saving a bilingual segment."""
    segment_data = {
        "id": "1",
        "english": "Test English",
        "french": "Test Français",
        "status": "draft",
    }

    result = await bilingual_service.save_segment(
        db=mock_db,
        job_id=1,
        segment=segment_data,
    )

    assert result["success"] is True
    assert result["segment_id"] == "1"


@pytest.mark.asyncio
async def test_update_segment_status(bilingual_service, mock_db):
    """Test updating segment translation status."""
    result = await bilingual_service.update_segment_status(
        db=mock_db,
        job_id=1,
        segment_id="1",
        status="approved",
    )

    assert result["success"] is True
    assert result["status"] == "approved"


@pytest.mark.asyncio
async def test_calculate_completeness(bilingual_service, mock_db):
    """Test document completeness calculation."""
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=1,
    )

    completeness = result["completeness"]
    assert "overall" in completeness
    assert "approved" in completeness
    assert "review" in completeness
    assert "draft" in completeness
    assert 0 <= completeness["overall"] <= 100


@pytest.mark.asyncio
async def test_get_translation_history(bilingual_service, mock_db):
    """Test getting translation history for a segment."""
    history = await bilingual_service.get_segment_history(
        db=mock_db,
        job_id=1,
        segment_id="1",
    )

    assert isinstance(history, list)
    if len(history) > 0:
        entry = history[0]
        assert "timestamp" in entry
        assert "user" in entry
        assert "action" in entry


@pytest.mark.asyncio
async def test_bulk_update_segments(bilingual_service, mock_db):
    """Test bulk updating multiple segments."""
    segments = [
        {"id": "1", "english": "Test 1", "french": "Test 1 FR"},
        {"id": "2", "english": "Test 2", "french": "Test 2 FR"},
    ]

    result = await bilingual_service.bulk_save_segments(
        db=mock_db,
        job_id=1,
        segments=segments,
    )

    assert result["success"] is True
    assert result["updated_count"] == 2


@pytest.mark.asyncio
async def test_concurrent_edit_detection(bilingual_service, mock_db):
    """Test detecting concurrent edits."""
    result = await bilingual_service.check_concurrent_edit(
        db=mock_db,
        job_id=1,
        segment_id="1",
        last_modified=datetime.utcnow().isoformat(),
    )

    assert "has_conflict" in result
    assert isinstance(result["has_conflict"], bool)


@pytest.mark.asyncio
async def test_export_bilingual_document(bilingual_service, mock_db):
    """Test exporting bilingual document."""
    result = await bilingual_service.export_document(
        db=mock_db,
        job_id=1,
        format="json",
    )

    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_metadata_tracking(bilingual_service, mock_db):
    """Test that metadata is properly tracked."""
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=1,
    )

    metadata = result["metadata"]
    assert "total_segments" in metadata
    assert "last_modified" in metadata
    assert "created_by" in metadata


@pytest.mark.asyncio
async def test_empty_document_handling(bilingual_service, mock_db):
    """Test handling of documents with no segments."""
    # Mock empty result
    result = await bilingual_service.get_bilingual_document(
        db=mock_db,
        job_id=999,
    )

    # Should return structure even with no data
    assert "segments" in result
    assert isinstance(result["segments"], list)


@pytest.mark.asyncio
async def test_update_segment_english(bilingual_service, mock_db):
    """Test updating English content in a segment."""
    result = await bilingual_service.update_segment(
        db=mock_db,
        job_id=1,
        segment_id="1",
        language="en",
        content="Updated English content",
        user_id="test_user",
    )

    assert "id" in result
    assert result["language"] == "en"
    assert result["content"] == "Updated English content"
    assert result["modifiedBy"] == "test_user"


@pytest.mark.asyncio
async def test_update_segment_french(bilingual_service, mock_db):
    """Test updating French content in a segment."""
    result = await bilingual_service.update_segment(
        db=mock_db,
        job_id=1,
        segment_id="2",
        language="fr",
        content="Contenu français mis à jour",
        user_id="translator_user",
    )

    assert "id" in result
    assert result["language"] == "fr"
    assert result["content"] == "Contenu français mis à jour"
    assert result["modifiedBy"] == "translator_user"


@pytest.mark.asyncio
async def test_update_segment_no_user(bilingual_service, mock_db):
    """Test updating segment without user ID (defaults to system)."""
    result = await bilingual_service.update_segment(
        db=mock_db,
        job_id=1,
        segment_id="3",
        language="en",
        content="System update",
    )

    assert result["modifiedBy"] == "system"


@pytest.mark.asyncio
async def test_batch_update_status_multiple_segments(bilingual_service, mock_db):
    """Test updating status for multiple segments at once."""
    segment_ids = ["1", "2", "3"]

    result = await bilingual_service.batch_update_status(
        db=mock_db,
        job_id=1,
        segment_ids=segment_ids,
        status="approved",
        user_id="reviewer",
    )

    assert result["updated_count"] == 3
    assert len(result["segments"]) == 3
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_batch_update_status_to_review(bilingual_service, mock_db):
    """Test batch updating to review status."""
    segment_ids = ["4", "5"]

    result = await bilingual_service.batch_update_status(
        db=mock_db,
        job_id=1,
        segment_ids=segment_ids,
        status="review",
    )

    assert result["updated_count"] == 2


@pytest.mark.asyncio
async def test_save_bilingual_document_with_english(bilingual_service, mock_db):
    """Test saving bilingual document with English segments."""
    segments = [
        {"id": "1", "english": "English content 1"},
        {"id": "2", "english": "English content 2"},
    ]

    result = await bilingual_service.save_bilingual_document(
        db=mock_db,
        job_id=1,
        segments=segments,
        user_id="author",
    )

    assert result["success"] is True
    assert result["saved_segments"] == 2
    assert "timestamp" in result
    assert "message" in result


@pytest.mark.asyncio
async def test_save_bilingual_document_with_french(bilingual_service, mock_db):
    """Test saving bilingual document with French segments."""
    segments = [
        {"id": "1", "french": "Contenu français 1"},
        {"id": "2", "french": "Contenu français 2"},
    ]

    result = await bilingual_service.save_bilingual_document(
        db=mock_db,
        job_id=1,
        segments=segments,
        user_id="translator",
    )

    assert result["success"] is True
    assert result["saved_segments"] == 2


@pytest.mark.asyncio
async def test_save_bilingual_document_both_languages(bilingual_service, mock_db):
    """Test saving with both English and French content."""
    segments = [
        {
            "id": "1",
            "english": "English text",
            "french": "Texte français",
            "status": "approved",
        },
    ]

    result = await bilingual_service.save_bilingual_document(
        db=mock_db,
        job_id=1,
        segments=segments,
        user_id="admin",
    )

    # Should save both languages (2 saves)
    assert result["success"] is True
    assert result["saved_segments"] == 2


@pytest.mark.asyncio
async def test_save_bilingual_document_with_status(bilingual_service, mock_db):
    """Test saving document with status updates."""
    segments = [
        {"id": "1", "english": "Test", "status": "review"},
    ]

    result = await bilingual_service.save_bilingual_document(
        db=mock_db,
        job_id=1,
        segments=segments,
    )

    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_translation_history_basic(bilingual_service, mock_db):
    """Test getting translation history."""
    history = await bilingual_service.get_translation_history(
        db=mock_db,
        job_id=1,
    )

    assert isinstance(history, list)
    assert len(history) > 0

    entry = history[0]
    assert "segmentId" in entry
    assert "oldStatus" in entry
    assert "newStatus" in entry
    assert "timestamp" in entry
    assert "user" in entry


@pytest.mark.asyncio
async def test_get_translation_history_with_limit(bilingual_service, mock_db):
    """Test getting translation history with limit."""
    history = await bilingual_service.get_translation_history(
        db=mock_db,
        job_id=1,
        limit=2,
    )

    assert len(history) <= 2


@pytest.mark.asyncio
async def test_calculate_document_completeness_full(bilingual_service, mock_db):
    """Test calculating completeness metrics."""
    result = await bilingual_service.calculate_document_completeness(
        db=mock_db,
        job_id=1,
    )

    assert "englishCompleteness" in result
    assert "frenchCompleteness" in result
    assert "overallCompleteness" in result
    assert "draftSegments" in result
    assert "reviewSegments" in result
    assert "approvedSegments" in result
    assert "totalSegments" in result


@pytest.mark.asyncio
async def test_calculate_completeness_percentages(bilingual_service, mock_db):
    """Test that completeness percentages are correct."""
    result = await bilingual_service.calculate_document_completeness(
        db=mock_db,
        job_id=1,
    )

    # Percentages should be between 0 and 100
    assert 0 <= result["englishCompleteness"] <= 100
    assert 0 <= result["frenchCompleteness"] <= 100
    assert 0 <= result["overallCompleteness"] <= 100


@pytest.mark.asyncio
async def test_calculate_completeness_empty_document(bilingual_service, mock_db):
    """Test completeness calculation for empty document."""

    # Create a service method that returns empty document
    # This tests the edge case in calculate_document_completeness
    async def mock_get_empty(db, job_id):
        return {"segments": []}

    bilingual_service.get_bilingual_document = mock_get_empty

    result = await bilingual_service.calculate_document_completeness(
        db=mock_db,
        job_id=999,
    )

    assert result["englishCompleteness"] == 0
    assert result["frenchCompleteness"] == 0
    assert result["overallCompleteness"] == 0


@pytest.mark.asyncio
async def test_update_segment_content_validation(bilingual_service, mock_db):
    """Test that segment updates track modifications correctly."""
    result = await bilingual_service.update_segment(
        db=mock_db,
        job_id=1,
        segment_id="10",
        language="en",
        content="Validated content",
        user_id="validator",
    )

    assert "lastModified" in result
    assert result["modifiedBy"] == "validator"


@pytest.mark.asyncio
async def test_batch_status_update_with_user(bilingual_service, mock_db):
    """Test batch status update tracks user."""
    result = await bilingual_service.batch_update_status(
        db=mock_db,
        job_id=1,
        segment_ids=["1", "2"],
        status="approved",
        user_id="reviewer_john",
    )

    # Each segment should have the user tracked
    for segment in result["segments"]:
        assert segment["modifiedBy"] == "reviewer_john"


@pytest.mark.asyncio
async def test_save_document_segment_counting(bilingual_service, mock_db):
    """Test that save document counts segments correctly."""
    segments = [
        {"id": "1", "english": "Test 1", "french": "Test 1 FR"},
        {"id": "2", "english": "Test 2"},  # Only English
        {"id": "3", "french": "Test 3 FR"},  # Only French
    ]

    result = await bilingual_service.save_bilingual_document(
        db=mock_db,
        job_id=1,
        segments=segments,
    )

    # First segment: 2 saves (en+fr), second: 1 save (en), third: 1 save (fr) = 4 total
    assert result["saved_segments"] == 4
