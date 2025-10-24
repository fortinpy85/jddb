"""Tests for Translation Quality Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.translation_quality_service import TranslationQualityService


@pytest.fixture
def quality_service():
    """Create TranslationQualityService instance."""
    return TranslationQualityService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_assess_translation_quality(quality_service, mock_db):
    """Test assessing translation quality."""
    source_text = "Strategic planning and policy development"
    target_text = "Planification stratégique et élaboration de politiques"

    result = await quality_service.assess_quality(
        source_text=source_text,
        target_text=target_text,
        source_language="en",
        target_language="fr",
        db=mock_db,
    )

    assert "overall_score" in result
    assert "fluency_score" in result
    assert "accuracy_score" in result
    assert "terminology_score" in result
    assert 0 <= result["overall_score"] <= 1


@pytest.mark.asyncio
async def test_quality_score_range(quality_service, mock_db):
    """Test that quality scores are within valid range."""
    result = await quality_service.assess_quality(
        source_text="Test",
        target_text="Test",
        source_language="en",
        target_language="fr",
        db=mock_db,
    )

    for key in [
        "overall_score",
        "fluency_score",
        "accuracy_score",
        "terminology_score",
    ]:
        assert 0 <= result[key] <= 1


@pytest.mark.asyncio
async def test_detect_terminology_issues(quality_service, mock_db):
    """Test detecting terminology inconsistencies."""
    source_text = "Project Manager"
    target_text = "Gestionnaire de Projet"  # Should be "Gestionnaire de projet"

    result = await quality_service.detect_terminology_issues(
        source_text=source_text,
        target_text=target_text,
        domain="job_titles",
        db=mock_db,
    )

    assert "issues" in result
    assert isinstance(result["issues"], list)


@pytest.mark.asyncio
async def test_check_consistency(quality_service, mock_db):
    """Test checking translation consistency."""
    translations = [
        {"source": "Manager", "target": "Gestionnaire"},
        {"source": "Manager", "target": "Directeur"},  # Inconsistent
    ]

    result = await quality_service.check_consistency(
        translations=translations,
        db=mock_db,
    )

    assert "consistency_score" in result
    assert "inconsistencies" in result


@pytest.mark.asyncio
async def test_validate_formatting(quality_service, mock_db):
    """Test validating formatting preservation."""
    source_text = "**Bold** and *italic* text"
    target_text = "Texte **gras** et *italique*"

    result = await quality_service.validate_formatting(
        source_text=source_text,
        target_text=target_text,
    )

    assert "formatting_preserved" in result
    assert isinstance(result["formatting_preserved"], bool)


@pytest.mark.asyncio
async def test_calculate_edit_distance(quality_service, mock_db):
    """Test calculating edit distance between translations."""
    text1 = "Strategic planning"
    text2 = "Strategic planing"  # Typo

    distance = await quality_service.calculate_edit_distance(
        text1=text1,
        text2=text2,
    )

    assert distance > 0
    assert isinstance(distance, (int, float))


@pytest.mark.asyncio
async def test_empty_text_handling(quality_service, mock_db):
    """Test handling empty text inputs."""
    result = await quality_service.assess_quality(
        source_text="",
        target_text="",
        source_language="en",
        target_language="fr",
        db=mock_db,
    )

    assert "overall_score" in result
    # Empty texts should have low quality score
    assert result["overall_score"] < 0.5


@pytest.mark.asyncio
async def test_language_pair_validation(quality_service, mock_db):
    """Test validating language pairs."""
    is_valid = await quality_service.validate_language_pair(
        source_language="en",
        target_language="fr",
    )

    assert isinstance(is_valid, bool)
    assert is_valid is True


@pytest.mark.asyncio
async def test_generate_quality_report(quality_service, mock_db):
    """Test generating comprehensive quality report."""
    report = await quality_service.generate_quality_report(
        translation_id=1,
        db=mock_db,
    )

    assert "translation_id" in report
    assert "quality_metrics" in report
    assert "recommendations" in report


@pytest.mark.asyncio
async def test_batch_quality_assessment(quality_service, mock_db):
    """Test assessing quality of multiple translations."""
    translations = [
        {"source": "Test 1", "target": "Test 1 FR"},
        {"source": "Test 2", "target": "Test 2 FR"},
    ]

    results = await quality_service.assess_batch_quality(
        translations=translations,
        source_language="en",
        target_language="fr",
        db=mock_db,
    )

    assert len(results) == 2
    for result in results:
        assert "overall_score" in result


@pytest.mark.asyncio
async def test_identify_improvement_areas(quality_service, mock_db):
    """Test identifying areas for translation improvement."""
    source_text = "Strategic planning"
    target_text = "Plan strategique"

    suggestions = await quality_service.suggest_improvements(
        source_text=source_text,
        target_text=target_text,
        source_language="en",
        target_language="fr",
        db=mock_db,
    )

    assert "suggestions" in suggestions
    assert isinstance(suggestions["suggestions"], list)


@pytest.mark.asyncio
async def test_track_quality_metrics(quality_service, mock_db):
    """Test tracking quality metrics over time."""
    metrics = await quality_service.get_quality_trends(
        project_id=1,
        time_period="week",
        db=mock_db,
    )

    assert "average_score" in metrics
    assert "trend" in metrics
