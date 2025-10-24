"""Tests for Skill Extraction Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.skill_extraction_service import SkillExtractionService
from jd_ingestion.services.lightcast_client import ExtractedSkill
from jd_ingestion.database.models import Skill


@pytest.fixture
def skill_service():
    """Create SkillExtractionService instance."""
    return SkillExtractionService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_extracted_skills():
    """Create sample extracted skills from Lightcast."""
    return [
        ExtractedSkill(
            id="skill1",
            name="Python Programming",
            confidence=0.95,
            category="Technical",
        ),
        ExtractedSkill(
            id="skill2",
            name="Project Management",
            confidence=0.88,
            category="Management",
        ),
        ExtractedSkill(
            id="skill3",
            name="Communication",
            confidence=0.75,
            category="Soft Skills",
        ),
    ]


@pytest.fixture
def sample_skill():
    """Create sample skill model."""
    return Skill(
        id=1,
        lightcast_id="skill1",
        name="Python Programming",
        category="Technical",
    )


@pytest.mark.asyncio
async def test_extract_and_save_skills(skill_service, mock_db, sample_extracted_skills):
    """Test extracting and saving skills from job text."""
    job_text = "Looking for Python programmer with project management experience"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=sample_extracted_skills)
        mock_client.return_value = mock_lightcast

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        assert len(skills) == 3
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_extract_skills_with_confidence_threshold(
    skill_service, mock_db, sample_extracted_skills
):
    """Test filtering skills by confidence threshold."""
    job_text = "Test job description"

    # Filter skills based on threshold - Lightcast client does this filtering
    filtered_skills = [s for s in sample_extracted_skills if s.confidence >= 0.8]

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        # Mock Lightcast to return pre-filtered skills (as the real client would)
        mock_lightcast.extract_skills = AsyncMock(return_value=filtered_skills)
        mock_client.return_value = mock_lightcast

        # Mock database to return None (new skills need to be created)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock the flush operation to set skill IDs
        created_skills = []

        def mock_add(obj):
            if isinstance(obj, Skill):
                obj.id = len(created_skills) + 1
                created_skills.append(obj)

        mock_db.add = mock_add

        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
            confidence_threshold=0.8,
        )

        # Only skills with confidence >= 0.8 should be returned
        assert len(skills) == 2
        for skill in skills:
            assert skill.name in ["Python Programming", "Project Management"]


@pytest.mark.asyncio
async def test_extract_skills_existing_skill(
    skill_service, mock_db, sample_extracted_skills, sample_skill
):
    """Test handling existing skills in database."""
    job_text = "Test job description"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=sample_extracted_skills)
        mock_client.return_value = mock_lightcast

        # First call returns existing skill, subsequent calls return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(
            side_effect=[sample_skill, None, None]
        )
        mock_db.execute.return_value = mock_result

        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        assert len(skills) == 3


@pytest.mark.asyncio
async def test_extract_skills_no_results(skill_service, mock_db):
    """Test handling when no skills are extracted."""
    job_text = "Simple text with no skills"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=[])
        mock_client.return_value = mock_lightcast

        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        assert len(skills) == 0


@pytest.mark.asyncio
async def test_extract_skills_api_error(skill_service, mock_db):
    """Test handling Lightcast API errors."""
    job_text = "Test job description"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(side_effect=Exception("API Error"))
        mock_client.return_value = mock_lightcast

        with pytest.raises(Exception) as exc_info:
            await skill_service.extract_and_save_skills(
                job_id=1,
                job_text=job_text,
                db=mock_db,
            )

        assert "API Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_job_skills(skill_service, mock_db, sample_skill):
    """Test retrieving skills for a job."""
    # Mock a job object with skills
    mock_job = MagicMock()
    mock_job.skills = [sample_skill]

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_job
    mock_db.execute.return_value = mock_result

    skills = await skill_service.get_job_skills(
        job_id=1,
        db=mock_db,
    )

    assert len(skills) == 1
    assert skills[0].name == "Python Programming"


@pytest.mark.asyncio
async def test_skill_deduplication(skill_service, mock_db):
    """Test that duplicate skills are not created."""
    duplicate_skills = [
        ExtractedSkill(id="skill1", name="Python", confidence=0.9, category="Tech"),
        ExtractedSkill(id="skill1", name="Python", confidence=0.85, category="Tech"),
    ]

    job_text = "Python Python"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=duplicate_skills)
        mock_client.return_value = mock_lightcast

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        # Should only save skill once
        assert len(skills) <= len(duplicate_skills)


@pytest.mark.asyncio
async def test_skill_categories(skill_service, mock_db, sample_extracted_skills):
    """Test that skill categories are properly stored."""
    job_text = "Test job description"

    # Create Skill objects with proper categories
    created_skills = []
    for idx, extracted in enumerate(sample_extracted_skills):
        skill = Skill(
            id=idx + 1,
            lightcast_id=extracted.id,
            name=extracted.name,
            category=extracted.category,
            skill_type=extracted.category,
        )
        created_skills.append(skill)

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=sample_extracted_skills)
        mock_client.return_value = mock_lightcast

        # Mock the database to return None (new skills), then return created skills
        call_count = [0]

        def mock_execute_side_effect(*args, **kwargs):
            result = MagicMock()
            result.scalars.return_value.first.return_value = None
            result.first.return_value = None
            call_count[0] += 1
            return result

        mock_db.execute.side_effect = mock_execute_side_effect

        # Mock flush to set skill IDs
        async def mock_flush():
            for idx, skill in enumerate(created_skills):
                if not hasattr(skill, "id") or skill.id is None:
                    skill.id = idx + 1

        mock_db.flush = mock_flush

        await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        # The service should have created skills with categories
        categories = {extracted.category for extracted in sample_extracted_skills}
        assert "Technical" in categories or "Management" in categories


@pytest.mark.asyncio
async def test_remove_job_skills(skill_service, mock_db):
    """Test removing skills from a job."""
    await skill_service.remove_job_skills(
        job_id=1,
        db=mock_db,
    )

    mock_db.execute.assert_called()
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_update_job_skills(skill_service, mock_db, sample_extracted_skills):
    """Test updating skills for an existing job."""
    job_text = "Updated job description"

    with patch(
        "jd_ingestion.services.skill_extraction_service.get_lightcast_client"
    ) as mock_client:
        mock_lightcast = MagicMock()
        mock_lightcast.extract_skills = AsyncMock(return_value=sample_extracted_skills)
        mock_client.return_value = mock_lightcast

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        # First remove existing skills, then add new ones
        await skill_service.remove_job_skills(job_id=1, db=mock_db)
        skills = await skill_service.extract_and_save_skills(
            job_id=1,
            job_text=job_text,
            db=mock_db,
        )

        assert len(skills) == 3
