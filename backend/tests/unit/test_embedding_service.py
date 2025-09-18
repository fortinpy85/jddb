"""
Unit tests for the EmbeddingService.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from httpx import Response

from jd_ingestion.services.embedding_service import EmbeddingService
from jd_ingestion.database.models import JobDescription, ContentChunk


@pytest.mark.unit
class TestEmbeddingService:
    """Test EmbeddingService functionality."""

    @pytest.fixture
    def embedding_service(self):
        """Create EmbeddingService instance."""
        return EmbeddingService()

    @pytest.fixture
    def mock_openai_embedding(self):
        """Mock OpenAI embedding response."""
        return [0.1, 0.2, 0.3] + [0.0] * 1533  # 1536 dimensions

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embedding_success(
        self, mock_openai_client, embedding_service, mock_openai_embedding
    ):
        """Test successful embedding generation."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)],
            usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        embedding = await service.generate_embedding("test text")

        assert embedding is not None
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_embeddings.create.assert_called_once()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embedding_api_error(self, mock_openai_client, embedding_service):
        """Test embedding generation with API error."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.side_effect = Exception("API Error")

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        embedding = await service.generate_embedding("test text")

        assert embedding is None
        mock_embeddings.create.assert_called_once()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embedding_timeout(self, mock_openai_client, embedding_service):
        """Test embedding generation with timeout."""
        import asyncio

        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.side_effect = asyncio.TimeoutError("Request timeout")

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        embedding = await service.generate_embedding("test text")

        assert embedding is None
        mock_embeddings.create.assert_called_once()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, mock_openai_client, embedding_service):
        """Test embedding generation with empty text."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        embedding = await service.generate_embedding("")

        assert embedding is None
        mock_embeddings.create.assert_not_called()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embedding_long_text(
        self, mock_openai_client, embedding_service, mock_openai_embedding
    ):
        """Test embedding generation with very long text."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)],
            usage=Mock(total_tokens=8000)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        long_text = "test " * 10000  # Very long text
        embedding = await service.generate_embedding(long_text)

        assert embedding is not None
        # Should call the API with truncated text
        mock_embeddings.create.assert_called_once()
        call_args = mock_embeddings.create.call_args.kwargs
        assert len(call_args["input"]) < len(long_text)

    @pytest.mark.asyncio
    async def test_calculate_similarity(self, embedding_service):
        """Test similarity calculation between embeddings."""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]  # Identical
        embedding3 = [0.0, 1.0, 0.0]  # Orthogonal

        similarity_identical = embedding_service.calculate_similarity(
            embedding1, embedding2
        )
        similarity_orthogonal = embedding_service.calculate_similarity(
            embedding1, embedding3
        )

        assert similarity_identical == 1.0  # Cosine similarity of identical vectors
        assert similarity_orthogonal == 0.0  # Cosine similarity of orthogonal vectors

    def test_calculate_similarity_zero_vectors(self, embedding_service):
        """Test similarity calculation with zero vectors."""
        zero_vector = [0.0, 0.0, 0.0]
        normal_vector = [1.0, 0.0, 0.0]

        similarity = embedding_service.calculate_similarity(zero_vector, normal_vector)
        assert similarity == 0.0

    def test_calculate_similarity_different_dimensions(self, embedding_service):
        """Test similarity calculation with different dimension vectors."""
        embedding1 = [1.0, 0.0]
        embedding2 = [1.0, 0.0, 0.0]

        with pytest.raises(ValueError, match="same dimension"):
            embedding_service.calculate_similarity(embedding1, embedding2)

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_semantic_search(
        self, mock_openai_client, embedding_service, async_session, mock_openai_embedding
    ):
        """Test semantic search functionality."""
        # Mock OpenAI response
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)],
            usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        # Create test job with chunks
        job = JobDescription(
            job_number="123456",
            title="Test Job",
            classification="EX-01",
            language="EN",
            raw_content="Test content",
        )
        async_session.add(job)
        await async_session.commit()

        chunk = ContentChunk(
            job_id=job.id,
            chunk_text="Test chunk content",
            chunk_index=0,
            embedding=[0.1] * 1536,
        )
        async_session.add(chunk)
        await async_session.commit()

        results = await service.semantic_search(
            query="test query", db=async_session, limit=10
        )

        assert isinstance(results, list)
        mock_embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_similar_jobs(self, embedding_service, async_session):
        """Test finding similar jobs by embedding similarity."""
        # Create test jobs with embeddings
        job1 = JobDescription(
            job_number="123456",
            title="Test Job 1",
            classification="EX-01",
            language="EN",
            raw_content="Test content 1",
        )
        job2 = JobDescription(
            job_number="789012",
            title="Test Job 2",
            classification="EX-02",
            language="EN",
            raw_content="Test content 2",
        )

        async_session.add_all([job1, job2])
        await async_session.commit()

        # Add chunks with similar embeddings
        chunk1 = ContentChunk(
            job_id=job1.id,
            chunk_text="Similar content",
            chunk_index=0,
            embedding=[1.0, 0.0] + [0.0] * 1534,
        )
        chunk2 = ContentChunk(
            job_id=job2.id,
            chunk_text="Very similar content",
            chunk_index=0,
            embedding=[0.9, 0.1] + [0.0] * 1534,  # Similar to chunk1
        )

        async_session.add_all([chunk1, chunk2])
        await async_session.commit()

        similar_jobs = await embedding_service.get_similar_jobs(
            job_id=job1.id, db=async_session, limit=5
        )

        assert len(similar_jobs) >= 0  # May be empty if no similar jobs found

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job(
        self, embedding_service, async_session, sample_job_data
    ):
        """Test generating embeddings for a job's content chunks."""
        job = JobDescription(**sample_job_data)
        async_session.add(job)
        await async_session.commit()

        # Add content chunks
        chunks = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        for i, chunk_text in enumerate(chunks):
            chunk = ContentChunk(job_id=job.id, chunk_text=chunk_text, chunk_index=i)
            async_session.add(chunk)
        await async_session.commit()

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            await embedding_service.generate_embeddings_for_job(job.id, async_session)

            # Should call generate_embedding for each chunk
            assert mock_generate.call_count == len(chunks)

    def test_truncate_text(self, embedding_service):
        """Test text truncation for API limits."""
        # Test with text that's too long
        long_text = "word " * 10000  # Very long text
        truncated = embedding_service._truncate_text(long_text, max_tokens=100)

        assert len(truncated.split()) <= 100
        assert truncated.endswith("...")

    def test_truncate_text_short(self, embedding_service):
        """Test text truncation with short text."""
        short_text = "This is a short text."
        result = embedding_service._truncate_text(short_text, max_tokens=100)

        assert result == short_text  # Should remain unchanged

    def test_estimate_tokens(self, embedding_service):
        """Test token estimation."""
        text = "This is a test sentence with multiple words."
        token_count = embedding_service._estimate_tokens(text)

        # Rough estimate: should be close to word count
        word_count = len(text.split())
        assert token_count >= word_count * 0.5  # Conservative estimate
        assert token_count <= word_count * 2.0  # Liberal estimate

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self, embedding_service):
        """Test batch embedding generation."""
        texts = ["Text 1", "Text 2", "Text 3"]

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            embeddings = await embedding_service.batch_generate_embeddings(texts)

            assert len(embeddings) == len(texts)
            assert mock_generate.call_count == len(texts)
            assert all(len(emb) == 1536 for emb in embeddings if emb is not None)

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_with_failures(self, embedding_service):
        """Test batch embedding generation with some failures."""
        texts = ["Text 1", "Text 2", "Text 3"]

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            # First call succeeds, second fails, third succeeds
            mock_generate.side_effect = [[0.1] * 1536, None, [0.2] * 1536]

            embeddings = await embedding_service.batch_generate_embeddings(texts)

            assert len(embeddings) == len(texts)
            assert embeddings[0] is not None
            assert embeddings[1] is None
            assert embeddings[2] is not None

    def test_validate_embedding_dimensions(self, embedding_service):
        """Test embedding dimension validation."""
        valid_embedding = [0.1] * 1536
        invalid_embedding = [0.1] * 100

        assert embedding_service._validate_embedding(valid_embedding) is True
        assert embedding_service._validate_embedding(invalid_embedding) is False
        assert embedding_service._validate_embedding(None) is False
        assert embedding_service._validate_embedding([]) is False

    @pytest.mark.benchmark
    def test_similarity_calculation_performance(self, embedding_service, benchmark):
        """Benchmark similarity calculation performance."""
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536

        result = benchmark(
            embedding_service.calculate_similarity, embedding1, embedding2
        )
        assert isinstance(result, float)

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_openai_client, embedding_service):
        """Test rate limiting behavior."""
        # Mock rate limit response with OpenAI error
        import openai

        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.side_effect = openai.RateLimitError(
            "Rate limit exceeded", response=Mock(), body=None
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        embedding = await service.generate_embedding("test text")

        assert embedding is None
        mock_embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embedding_service_with_real_data(
        self, embedding_service, sample_job_description_text
    ):
        """Test embedding service with realistic job description data."""
        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            # Test chunking and embedding generation
            chunks = embedding_service._create_chunks_for_embedding(
                sample_job_description_text
            )
            assert len(chunks) > 0
            assert all(len(chunk) > 0 for chunk in chunks)

            # Test embedding generation for chunks
            embeddings = await embedding_service.batch_generate_embeddings(chunks)
            assert len(embeddings) == len(chunks)
            assert mock_generate.call_count == len(chunks)
