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
