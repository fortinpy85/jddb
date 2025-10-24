"""Tests for Translation Memory Service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from jd_ingestion.services.translation_memory_service import TranslationMemoryService
from jd_ingestion.database.models import (
    TranslationProject,
    TranslationMemory,
)


@pytest.fixture
def tm_service():
    """Create TranslationMemoryService instance."""
    return TranslationMemoryService()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.scalar = AsyncMock()
    return db


@pytest.fixture
def sample_project():
    """Create sample translation project."""
    return TranslationProject(
        id=1,
        name="Test Project",
        source_language="en",
        target_language="fr",
        description="Test project description",
        project_type="job_descriptions",
        created_by=1,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_translation():
    """Create sample translation memory entry."""
    return TranslationMemory(
        id=1,
        project_id=1,
        source_text="Strategic planning",
        target_text="Planification stratégique",
        source_language="en",
        target_language="fr",
        domain="job_title",  # Changed from context to domain
        created_by=1,
        created_at=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_create_project(tm_service, mock_db):
    """Test creating a translation project."""
    with patch.object(tm_service, "embedding_service"):
        result = await tm_service.create_project(
            name="Test Project",
            source_language="en",
            target_language="fr",
            description="Test description",
            project_type="job_descriptions",
            created_by=1,
            db=mock_db,
        )

        assert result["name"] == "Test Project"
        assert result["source_language"] == "en"
        assert result["target_language"] == "fr"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_project_minimal(tm_service, mock_db):
    """Test creating project with minimal parameters."""
    with patch.object(tm_service, "embedding_service"):
        result = await tm_service.create_project(
            name="Minimal Project",
            source_language="en",
            target_language="fr",
            db=mock_db,
        )

        assert result["name"] == "Minimal Project"
        assert result["project_type"] == "job_descriptions"
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_translation(tm_service, mock_db):
    """Test adding translation to memory."""
    with patch.object(
        tm_service.embedding_service, "get_embedding", new_callable=AsyncMock
    ) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        result = await tm_service.add_translation(
            project_id=1,
            source_text="Strategic planning",
            target_text="Planification stratégique",
            source_language="en",
            target_language="fr",
            context="job_title",
            created_by=1,
            db=mock_db,
        )

        assert result["source_text"] == "Strategic planning"
        assert result["target_text"] == "Planification stratégique"
        assert mock_db.add.call_count == 2  # TranslationMemory + TranslationEmbedding
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_similar_translations(tm_service, mock_db, sample_translation):
    """Test searching for similar translations."""
    # Create mock embedding
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 1536

    # The query returns tuples of (translation, embedding, similarity)
    mock_result = MagicMock()
    mock_result.all.return_value = [(sample_translation, mock_embedding, 0.85)]
    mock_db.execute.return_value = mock_result

    with patch.object(
        tm_service.embedding_service, "get_embedding", new_callable=AsyncMock
    ) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        results = await tm_service.search_similar_translations(
            query_text="strategic planning",
            source_language="en",
            target_language="fr",
            similarity_threshold=0.7,
            limit=5,
            db=mock_db,
        )

        assert len(results) > 0
        assert results[0]["similarity_score"] == 0.85
        mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_similar_translations_no_results(tm_service, mock_db):
    """Test searching with no matching results."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    with patch.object(
        tm_service.embedding_service, "get_embedding", new_callable=AsyncMock
    ) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        results = await tm_service.search_similar_translations(
            query_text="nonexistent term",
            source_language="en",
            target_language="fr",
            db=mock_db,
        )

        assert len(results) == 0


@pytest.mark.asyncio
async def test_get_project_translations(tm_service, mock_db, sample_translation):
    """Test getting all translations for a project."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [sample_translation]
    mock_db.execute.return_value = mock_result

    translations = await tm_service.get_project_translations(
        project_id=1,
        db=mock_db,
    )

    assert len(translations) > 0
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_translation(tm_service, mock_db, sample_translation):
    """Test updating an existing translation."""
    # Mock the execute query to return translation
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_translation
    mock_db.execute.return_value = mock_result

    with patch.object(
        tm_service.embedding_service, "get_embedding", new_callable=AsyncMock
    ) as mock_embed:
        mock_embed.return_value = [0.1] * 1536

        result = await tm_service.update_translation(
            translation_id=1,
            target_text="Nouvelle planification stratégique",
            db=mock_db,
        )

        assert result["id"] == 1
        assert result["target_text"] == "Nouvelle planification stratégique"
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_translation(tm_service, mock_db, sample_translation):
    """Test deleting a translation."""
    mock_db.scalar.return_value = sample_translation

    await tm_service.delete_translation(
        translation_id=1,
        db=mock_db,
    )

    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_project_stats(tm_service, mock_db, sample_project):
    """Test getting project statistics."""
    # Mock all db.execute calls in get_project_statistics and get_project_stats
    # get_project_statistics makes 5 queries: total, unique, quality, domains, langs

    # 1. Total translations count
    mock_total = MagicMock()
    mock_total.scalar_one.return_value = 10

    # 2. Unique sources count
    mock_unique = MagicMock()
    mock_unique.scalar_one.return_value = 8

    # 3. Average quality score
    mock_quality = MagicMock()
    mock_quality.scalar_one.return_value = 0.85

    # 4. Domains query
    mock_domains = MagicMock()
    mock_domains.all.return_value = [("job_title", 5), ("job_description", 5)]

    # 5. Language pairs query
    mock_langs = MagicMock()
    mock_langs.all.return_value = [("en", "fr", 10)]

    # 6. Project info query
    mock_project_result = MagicMock()
    mock_project_result.scalar_one_or_none.return_value = sample_project

    # Set up side_effect to return different results for each execute call
    mock_db.execute.side_effect = [
        mock_total,
        mock_unique,
        mock_quality,
        mock_domains,
        mock_langs,
        mock_project_result,
    ]

    stats = await tm_service.get_project_stats(
        project_id=1,
        db=mock_db,
    )

    assert stats["project_id"] == 1
    assert "translation_count" in stats


@pytest.mark.asyncio
async def test_embedding_service_integration(tm_service):
    """Test that embedding service is properly initialized."""
    assert tm_service.embedding_service is not None
    assert hasattr(tm_service.embedding_service, "get_embedding")
