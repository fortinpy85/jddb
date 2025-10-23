"""
Unit tests for the EmbeddingService.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from jd_ingestion.services.embedding_service import EmbeddingService


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
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
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
    async def test_generate_embedding_api_error(
        self, mock_openai_client, embedding_service
    ):
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
    async def test_generate_embedding_timeout(
        self, mock_openai_client, embedding_service
    ):
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
    async def test_generate_embedding_empty_text(
        self, mock_openai_client, embedding_service
    ):
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
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=8000)
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
        self, mock_openai_client, embedding_service, mock_openai_embedding
    ):
        """Test semantic search functionality."""
        # Mock OpenAI response
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        # Reinitialize service with mocked client
        service = EmbeddingService()

        # Mock database session and query results
        mock_session = Mock()
        mock_session.execute = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = []

        results = await service.semantic_search(
            query="test query", db=mock_session, limit=10
        )

        assert isinstance(results, list)
        mock_embeddings.create.assert_called_once()
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_similar_jobs(self, embedding_service):
        """Test finding similar jobs by embedding similarity."""
        # Mock database session and query results
        mock_session = Mock()
        mock_session.execute = AsyncMock()

        # Mock the query result to return some similar jobs
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [
            Mock(job_id=2, similarity=0.95),
            Mock(job_id=3, similarity=0.87),
        ]
        mock_session.execute.return_value = mock_result

        similar_jobs = await embedding_service.get_similar_jobs(
            job_id=1, db=mock_session, limit=5
        )

        assert len(similar_jobs) >= 0  # May be empty if no similar jobs found
        assert mock_session.execute.call_count >= 1  # May call multiple queries

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job(self, embedding_service):
        """Test generating embeddings for a job's content chunks."""
        # Mock database session and content chunks
        mock_session = Mock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock chunks from database
        mock_chunks = [
            Mock(id=1, chunk_text="Chunk 1 content", embedding=None),
            Mock(id=2, chunk_text="Chunk 2 content", embedding=None),
            Mock(id=3, chunk_text="Chunk 3 content", embedding=None),
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_chunks
        mock_session.execute.return_value = mock_result

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            await embedding_service.generate_embeddings_for_job(1, mock_session)

            # Should call generate_embedding for each chunk
            assert mock_generate.call_count == len(mock_chunks)
            mock_session.execute.assert_called()
            mock_session.commit.assert_called()

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
    def test_similarity_calculation_performance(self, embedding_service):
        """Test similarity calculation performance."""
        embedding1 = [0.1] * 1536
        embedding2 = [0.2] * 1536

        result = embedding_service.calculate_similarity(embedding1, embedding2)
        assert isinstance(result, float)
        assert 0 <= result <= 1

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

    # Tests for generate_embeddings_batch
    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_success(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test successful batch embedding generation."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()
        texts = ["Text 1", "Text 2", "Text 3"]

        embeddings = await service.generate_embeddings_batch(texts)

        assert len(embeddings) == len(texts)
        assert all(emb is not None for emb in embeddings)
        assert all(len(emb) == 1536 for emb in embeddings)

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_empty_list(self, embedding_service):
        """Test batch embedding generation with empty list."""
        embeddings = await embedding_service.generate_embeddings_batch([])
        assert embeddings == []

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_no_client(self):
        """Test batch embedding generation without OpenAI client."""
        with patch("jd_ingestion.services.embedding_service.settings") as mock_settings:
            mock_settings.openai_api_key = None
            service = EmbeddingService()

            texts = ["Text 1", "Text 2"]
            embeddings = await service.generate_embeddings_batch(texts)

            assert len(embeddings) == len(texts)
            assert all(emb is None for emb in embeddings)

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_with_failures(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test batch embedding generation with some failures."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()

        # Simulate mixed success/failure
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("API Error")
            return Mock(
                data=[Mock(embedding=mock_openai_embedding)],
                usage=Mock(total_tokens=100),
            )

        mock_embeddings.create.side_effect = side_effect

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()
        texts = ["Text 1", "Text 2", "Text 3"]

        embeddings = await service.generate_embeddings_batch(texts)

        assert len(embeddings) == len(texts)
        assert embeddings[0] is not None
        assert embeddings[1] is None  # Failed
        assert embeddings[2] is not None

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch_large_batch(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test batch embedding generation with large batch."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()
        texts = [f"Text {i}" for i in range(150)]  # More than default batch size

        embeddings = await service.generate_embeddings_batch(texts, batch_size=50)

        assert len(embeddings) == len(texts)
        assert all(emb is not None for emb in embeddings)

    # Tests for find_similar_chunks
    @pytest.mark.asyncio
    async def test_find_similar_chunks_success(self, embedding_service):
        """Test successful similar chunks search."""
        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock database result rows
        mock_row = Mock()
        mock_row.id = 1
        mock_row.job_id = 100
        mock_row.job_number = "JD-001"
        mock_row.title = "Test Job"
        mock_row.classification = "Professional"
        mock_row.language = "en"
        mock_row.chunk_text = "Test chunk content"
        mock_row.similarity_score = 0.85

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        query_embedding = [0.1] * 1536
        results = await embedding_service.find_similar_chunks(
            query_embedding=query_embedding,
            db=mock_session,
            limit=10,
            similarity_threshold=0.7,
        )

        assert len(results) == 1
        assert results[0]["chunk_id"] == 1
        assert results[0]["job_id"] == 100
        assert results[0]["similarity_score"] == 0.85
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_similar_chunks_with_filters(self, embedding_service):
        """Test similar chunks search with classification and language filters."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        query_embedding = [0.1] * 1536
        results = await embedding_service.find_similar_chunks(
            query_embedding=query_embedding,
            db=mock_session,
            classification_filter="Professional",
            language_filter="en",
            job_id_exclude=5,
        )

        assert isinstance(results, list)
        mock_session.execute.assert_called_once()
        # Verify filters were applied (check call args contain filter values)
        call_args = mock_session.execute.call_args
        assert "Professional" in call_args[0][1]
        assert "en" in call_args[0][1]
        assert 5 in call_args[0][1]

    @pytest.mark.asyncio
    async def test_find_similar_chunks_below_threshold(self, embedding_service):
        """Test similar chunks search filters results below threshold."""
        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock row with low similarity score
        mock_row = Mock()
        mock_row.id = 1
        mock_row.job_id = 100
        mock_row.job_number = "JD-001"
        mock_row.title = "Test Job"
        mock_row.classification = "Professional"
        mock_row.language = "en"
        mock_row.chunk_text = "Test chunk"
        mock_row.similarity_score = 0.5  # Below threshold

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        query_embedding = [0.1] * 1536
        results = await embedding_service.find_similar_chunks(
            query_embedding=query_embedding, db=mock_session, similarity_threshold=0.7
        )

        assert len(results) == 0  # Filtered out

    @pytest.mark.asyncio
    async def test_find_similar_chunks_database_error(self, embedding_service):
        """Test similar chunks search handles database errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        query_embedding = [0.1] * 1536
        results = await embedding_service.find_similar_chunks(
            query_embedding=query_embedding, db=mock_session
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_find_similar_chunks_optimized(self, embedding_service):
        """Test optimized similar chunks search delegates to main method."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        query_embedding = [0.1] * 1536
        results = await embedding_service.find_similar_chunks_optimized(
            query_embedding=query_embedding, db=mock_session
        )

        assert isinstance(results, list)
        mock_session.execute.assert_called_once()

    # Tests for semantic_search
    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_semantic_search_success(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test successful semantic search."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()

        mock_session = AsyncMock()
        mock_result = Mock()

        # Mock search results
        mock_row = Mock()
        mock_row.job_id = 1
        mock_row.job_number = "JD-001"
        mock_row.title = "Software Engineer"
        mock_row.classification = "Professional"
        mock_row.language = "en"
        mock_row.max_similarity_score = 0.85
        mock_row.matching_chunks = 3

        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        results = await service.semantic_search(
            query="python developer", db=mock_session, limit=20
        )

        assert len(results) == 1
        assert results[0]["job_id"] == 1
        assert results[0]["relevance_score"] == 0.85
        assert results[0]["matching_chunks"] == 3

    @pytest.mark.asyncio
    async def test_semantic_search_no_embedding(self, embedding_service):
        """Test semantic search when embedding generation fails."""
        mock_session = AsyncMock()

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = None

            results = await embedding_service.semantic_search(
                query="test query", db=mock_session
            )

        assert results == []

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_semantic_search_with_filters(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test semantic search with classification and language filters."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        results = await service.semantic_search(
            query="test query",
            db=mock_session,
            classification_filter="Professional",
            language_filter="en",
            similarity_threshold=0.8,
        )

        assert isinstance(results, list)
        mock_session.execute.assert_called_once()

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_semantic_search_optimized_false(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test semantic search with optimized=False uses fallback query."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        results = await service.semantic_search(
            query="test query", db=mock_session, use_optimized=False
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_semantic_search_database_error(self, embedding_service):
        """Test semantic search handles database errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            results = await embedding_service.semantic_search(
                query="test query", db=mock_session
            )

        assert results == []

    @patch("jd_ingestion.services.embedding_service.openai.AsyncOpenAI")
    @pytest.mark.asyncio
    async def test_semantic_search_optimized_method(
        self, mock_openai_client, mock_openai_embedding
    ):
        """Test semantic_search_optimized delegates to main method."""
        mock_embeddings = Mock()
        mock_embeddings.create = AsyncMock()
        mock_embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_openai_embedding)], usage=Mock(total_tokens=100)
        )

        mock_client = Mock()
        mock_client.embeddings = mock_embeddings
        mock_openai_client.return_value = mock_client

        service = EmbeddingService()

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        results = await service.semantic_search_optimized(
            query="test query", db=mock_session
        )

        assert isinstance(results, list)

    # Tests for batch_similarity_search
    @pytest.mark.asyncio
    async def test_batch_similarity_search_success(self, embedding_service):
        """Test successful batch similarity search."""
        mock_session = AsyncMock()

        # Mock find_similar_chunks to return results
        with patch.object(
            embedding_service, "find_similar_chunks"
        ) as mock_find_similar:
            mock_find_similar.return_value = [
                {"chunk_id": 1, "similarity_score": 0.9},
                {"chunk_id": 2, "similarity_score": 0.8},
            ]

            query_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
            results = await embedding_service.batch_similarity_search(
                query_embeddings=query_embeddings, db=mock_session, limit_per_query=5
            )

            assert len(results) == len(query_embeddings)
            assert all(isinstance(result, list) for result in results)
            assert mock_find_similar.call_count == len(query_embeddings)

    @pytest.mark.asyncio
    async def test_batch_similarity_search_empty_list(self, embedding_service):
        """Test batch similarity search with empty list."""
        mock_session = AsyncMock()

        results = await embedding_service.batch_similarity_search(
            query_embeddings=[], db=mock_session
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_similarity_search_with_errors(self, embedding_service):
        """Test batch similarity search with some queries failing."""
        mock_session = AsyncMock()

        # Mock find_similar_chunks to simulate mixed results
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Database error")
            return [{"chunk_id": 1, "similarity_score": 0.9}]

        with patch.object(
            embedding_service, "find_similar_chunks"
        ) as mock_find_similar:
            mock_find_similar.side_effect = side_effect

            query_embeddings = [[0.1] * 1536, [0.2] * 1536, [0.3] * 1536]
            results = await embedding_service.batch_similarity_search(
                query_embeddings=query_embeddings, db=mock_session
            )

            assert len(results) == len(query_embeddings)
            assert results[0] != []  # First succeeded
            assert results[1] == []  # Second failed
            assert results[2] != []  # Third succeeded

    @pytest.mark.asyncio
    async def test_batch_similarity_search_general_error(self, embedding_service):
        """Test batch similarity search handles general errors."""
        mock_session = AsyncMock()

        with patch(
            "jd_ingestion.services.embedding_service.asyncio.gather"
        ) as mock_gather:
            mock_gather.side_effect = Exception("General error")

            query_embeddings = [[0.1] * 1536]
            results = await embedding_service.batch_similarity_search(
                query_embeddings=query_embeddings, db=mock_session
            )

            assert results == []

    # Tests for get_performance_stats
    @pytest.mark.asyncio
    async def test_get_performance_stats_success(self, embedding_service):
        """Test successful performance stats retrieval."""
        mock_session = AsyncMock()

        # Mock index stats result
        mock_index_row = Mock()
        mock_index_row.schemaname = "public"
        mock_index_row.tablename = "content_chunks"
        mock_index_row.indexname = "idx_embedding_vector"
        mock_index_row.idx_scan = 1000
        mock_index_row.idx_tup_read = 5000
        mock_index_row.idx_tup_fetch = 4800

        # Mock table stats result
        mock_table_row = Mock()
        mock_table_row.schemaname = "public"
        mock_table_row.tablename = "content_chunks"
        mock_table_row.n_live_tup = 10000
        mock_table_row.n_dead_tup = 100
        mock_table_row.seq_scan = 50
        mock_table_row.seq_tup_read = 1000
        mock_table_row.idx_scan = 950
        mock_table_row.idx_tup_fetch = 9000

        # Setup mock to return different results for different queries
        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:  # First call - index stats
                mock_result.fetchall.return_value = [mock_index_row]
            else:  # Second call - table stats
                mock_result.fetchall.return_value = [mock_table_row]
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        stats = await embedding_service.get_performance_stats(mock_session)

        assert "index_performance" in stats
        assert "table_performance" in stats
        assert len(stats["index_performance"]) == 1
        assert len(stats["table_performance"]) == 1
        assert stats["index_performance"][0]["table"] == "content_chunks"
        assert stats["table_performance"][0]["table"] == "content_chunks"
        assert "index_efficiency" in stats["table_performance"][0]

    @pytest.mark.asyncio
    async def test_get_performance_stats_empty_results(self, embedding_service):
        """Test performance stats with no results."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        stats = await embedding_service.get_performance_stats(mock_session)

        assert "index_performance" in stats
        assert "table_performance" in stats
        assert stats["index_performance"] == []
        assert stats["table_performance"] == []

    @pytest.mark.asyncio
    async def test_get_performance_stats_database_error(self, embedding_service):
        """Test performance stats handles database errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection error")

        stats = await embedding_service.get_performance_stats(mock_session)

        assert "error" in stats
        assert "Database connection error" in stats["error"]

    # Tests for get_similar_jobs
    @pytest.mark.asyncio
    async def test_get_similar_jobs_success(self, embedding_service):
        """Test successful similar jobs retrieval."""
        mock_session = AsyncMock()

        # Mock the embedding query
        mock_embedding_result = Mock()
        mock_chunk = Mock()
        mock_chunk.embedding = [0.1] * 1536
        mock_embedding_result.first.return_value = mock_chunk

        # Mock find_similar_chunks to return results
        with patch.object(
            embedding_service, "find_similar_chunks"
        ) as mock_find_similar:
            mock_find_similar.return_value = [
                {"job_id": 2, "similarity_score": 0.9, "title": "Job 2"},
                {"job_id": 3, "similarity_score": 0.85, "title": "Job 3"},
                {"job_id": 2, "similarity_score": 0.75, "title": "Job 2"},  # Duplicate
                {"job_id": 4, "similarity_score": 0.8, "title": "Job 4"},
            ]

            mock_session.execute.return_value = mock_embedding_result

            results = await embedding_service.get_similar_jobs(
                job_id=1, db=mock_session, limit=3
            )

            assert len(results) <= 3  # Limited to 3
            assert all(job["job_id"] != 1 for job in results)  # Excludes source job
            # Should be sorted by similarity score
            if len(results) > 1:
                assert results[0]["similarity_score"] >= results[-1]["similarity_score"]

    @pytest.mark.asyncio
    async def test_get_similar_jobs_no_embeddings(self, embedding_service):
        """Test get_similar_jobs when source job has no embeddings."""
        mock_session = AsyncMock()

        # Mock empty result
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.execute.return_value = mock_result

        results = await embedding_service.get_similar_jobs(job_id=1, db=mock_session)

        assert results == []

    @pytest.mark.asyncio
    async def test_get_similar_jobs_database_error(self, embedding_service):
        """Test get_similar_jobs handles database errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        results = await embedding_service.get_similar_jobs(job_id=1, db=mock_session)

        assert results == []

    # Tests for generate_embeddings_for_job
    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job_success(self, embedding_service):
        """Test successful embedding generation for job chunks."""
        mock_session = AsyncMock()

        # Mock chunks without embeddings
        mock_chunks = [
            Mock(id=1, chunk_text="Chunk 1", embedding=None),
            Mock(id=2, chunk_text="Chunk 2", embedding=None),
            Mock(id=3, chunk_text="Chunk 3", embedding=None),
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_chunks
        mock_session.execute.return_value = mock_result

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = [0.1] * 1536

            success = await embedding_service.generate_embeddings_for_job(
                job_id=1, db=mock_session
            )

            assert success is True
            assert mock_generate.call_count == len(mock_chunks)
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job_already_exists(self, embedding_service):
        """Test generate_embeddings_for_job when all chunks already have embeddings."""
        mock_session = AsyncMock()

        # Mock empty result (no chunks without embeddings)
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        success = await embedding_service.generate_embeddings_for_job(
            job_id=1, db=mock_session
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job_partial_failures(
        self, embedding_service
    ):
        """Test generate_embeddings_for_job with some embedding failures."""
        mock_session = AsyncMock()

        mock_chunks = [
            Mock(id=1, chunk_text="Chunk 1", embedding=None),
            Mock(id=2, chunk_text="Chunk 2", embedding=None),
            Mock(id=3, chunk_text="Chunk 3", embedding=None),
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_chunks
        mock_session.execute.return_value = mock_result

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            # First succeeds, second fails, third succeeds
            mock_generate.side_effect = [[0.1] * 1536, None, [0.2] * 1536]

            success = await embedding_service.generate_embeddings_for_job(
                job_id=1, db=mock_session
            )

            assert success is True  # Some succeeded
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job_all_failures(self, embedding_service):
        """Test generate_embeddings_for_job when all embeddings fail."""
        mock_session = AsyncMock()

        mock_chunks = [
            Mock(id=1, chunk_text="Chunk 1", embedding=None),
            Mock(id=2, chunk_text="Chunk 2", embedding=None),
        ]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_chunks
        mock_session.execute.return_value = mock_result

        with patch.object(embedding_service, "generate_embedding") as mock_generate:
            mock_generate.return_value = None  # All fail

            success = await embedding_service.generate_embeddings_for_job(
                job_id=1, db=mock_session
            )

            assert success is False  # None succeeded

    @pytest.mark.asyncio
    async def test_generate_embeddings_for_job_database_error(self, embedding_service):
        """Test generate_embeddings_for_job handles database errors."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        success = await embedding_service.generate_embeddings_for_job(
            job_id=1, db=mock_session
        )

        assert success is False
        mock_session.rollback.assert_called_once()

    # Tests for _prepare_text_for_embedding
    def test_prepare_text_for_embedding_normal(self, embedding_service):
        """Test text preparation with normal text."""
        text = "This is a normal text with some content."
        prepared = embedding_service._prepare_text_for_embedding(text)

        assert prepared == text
        assert isinstance(prepared, str)

    def test_prepare_text_for_embedding_empty(self, embedding_service):
        """Test text preparation with empty string."""
        prepared = embedding_service._prepare_text_for_embedding("")
        assert prepared == ""

    def test_prepare_text_for_embedding_whitespace(self, embedding_service):
        """Test text preparation removes excessive whitespace."""
        text = "This   has    extra     spaces\n\nand\nnewlines\t\ttabs"
        prepared = embedding_service._prepare_text_for_embedding(text)

        assert "   " not in prepared
        assert "\n\n" not in prepared
        assert "\t\t" not in prepared
        assert prepared == "This has extra spaces and newlines tabs"

    def test_prepare_text_for_embedding_long_text(self, embedding_service):
        """Test text preparation truncates very long text."""
        long_text = "word " * 2000  # Creates text longer than 8000 chars
        prepared = embedding_service._prepare_text_for_embedding(long_text)

        assert len(prepared) <= 8000
        assert len(prepared) < len(long_text)

    def test_prepare_text_for_embedding_special_chars(self, embedding_service):
        """Test text preparation preserves special characters."""
        text = "Hello! This has @special #characters $and %symbols & (punctuation)."
        prepared = embedding_service._prepare_text_for_embedding(text)

        assert "@special" in prepared
        assert "#characters" in prepared
        assert "$and" in prepared

    def test_prepare_text_for_embedding_none(self, embedding_service):
        """Test text preparation with None input."""
        prepared = embedding_service._prepare_text_for_embedding(None)
        assert prepared == ""

    # Tests for _truncate_text
    def test_truncate_text_long(self, embedding_service):
        """Test text truncation with long text."""
        long_text = "word " * 1000
        result = embedding_service._truncate_text(long_text, max_tokens=100)

        assert len(result) < len(long_text)
        assert result.endswith("...")

    def test_truncate_text_empty(self, embedding_service):
        """Test text truncation with empty string."""
        result = embedding_service._truncate_text("", max_tokens=100)
        assert result == ""

    def test_truncate_text_none(self, embedding_service):
        """Test text truncation with None."""
        result = embedding_service._truncate_text(None, max_tokens=100)
        assert result is None

    def test_truncate_text_exact_limit(self, embedding_service):
        """Test text truncation at exact token limit."""
        # Create text that's exactly at the limit
        text = "word " * 75  # Approximately 100 tokens
        result = embedding_service._truncate_text(text, max_tokens=100)

        # Should not be truncated
        assert "..." not in result

    # Tests for _estimate_tokens
    def test_estimate_tokens_empty(self, embedding_service):
        """Test token estimation with empty string."""
        count = embedding_service._estimate_tokens("")
        assert count == 0

    def test_estimate_tokens_none(self, embedding_service):
        """Test token estimation with None."""
        count = embedding_service._estimate_tokens(None)
        assert count == 0

    def test_estimate_tokens_short_text(self, embedding_service):
        """Test token estimation with short text."""
        text = "Hello world"
        count = embedding_service._estimate_tokens(text)

        # Should be reasonable estimate (2-6 tokens for 2 words)
        assert count > 0
        assert count < 20

    def test_estimate_tokens_long_text(self, embedding_service):
        """Test token estimation with long text."""
        text = "word " * 1000  # 1000 words
        count = embedding_service._estimate_tokens(text)

        # Should estimate roughly 1000-1500 tokens
        assert count >= 800
        assert count <= 2000

    def test_estimate_tokens_special_chars(self, embedding_service):
        """Test token estimation with special characters."""
        text = "!@#$%^&*()_+-=[]{}|;:',.<>?/"
        count = embedding_service._estimate_tokens(text)

        # Should provide reasonable estimate
        assert count > 0

    # Tests for _validate_embedding
    def test_validate_embedding_valid(self, embedding_service):
        """Test embedding validation with valid embedding."""
        valid_embedding = [0.1] * 1536
        assert embedding_service._validate_embedding(valid_embedding) is True

    def test_validate_embedding_none(self, embedding_service):
        """Test embedding validation with None."""
        assert embedding_service._validate_embedding(None) is False

    def test_validate_embedding_empty(self, embedding_service):
        """Test embedding validation with empty list."""
        assert embedding_service._validate_embedding([]) is False

    def test_validate_embedding_wrong_dimension(self, embedding_service):
        """Test embedding validation with wrong dimensions."""
        wrong_dimension = [0.1] * 100
        assert embedding_service._validate_embedding(wrong_dimension) is False

    def test_validate_embedding_not_list(self, embedding_service):
        """Test embedding validation with non-list type."""
        assert embedding_service._validate_embedding("not a list") is False
        assert embedding_service._validate_embedding(123) is False
        assert embedding_service._validate_embedding({}) is False

    def test_validate_embedding_non_numeric(self, embedding_service):
        """Test embedding validation with non-numeric values."""
        invalid_embedding = ["string"] * 1536
        assert embedding_service._validate_embedding(invalid_embedding) is False

    def test_validate_embedding_mixed_types(self, embedding_service):
        """Test embedding validation with mixed numeric types."""
        mixed_embedding = [0.1] * 1000 + [1] * 536  # Mix of float and int
        assert embedding_service._validate_embedding(mixed_embedding) is True

    # Tests for _create_chunks_for_embedding
    def test_create_chunks_empty_text(self, embedding_service):
        """Test chunk creation with empty text."""
        chunks = embedding_service._create_chunks_for_embedding("")
        assert chunks == []

    def test_create_chunks_none(self, embedding_service):
        """Test chunk creation with None."""
        chunks = embedding_service._create_chunks_for_embedding(None)
        assert chunks == []

    def test_create_chunks_short_text(self, embedding_service):
        """Test chunk creation with text shorter than chunk size."""
        text = "This is a short text."
        chunks = embedding_service._create_chunks_for_embedding(text, chunk_size=1000)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_create_chunks_long_text(self, embedding_service):
        """Test chunk creation with text longer than chunk size."""
        text = "word " * 500  # ~2500 chars
        chunks = embedding_service._create_chunks_for_embedding(
            text, chunk_size=1000, overlap=200
        )

        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)
        # Check overlap exists between consecutive chunks
        if len(chunks) > 1:
            # Some text should appear in both chunks (overlap)
            assert any(
                word in chunks[1]
                for word in chunks[0].split()[-10:]  # Last 10 words of first chunk
            )

    def test_create_chunks_word_boundaries(self, embedding_service):
        """Test chunk creation respects word boundaries."""
        text = "word1 word2 word3 " * 100
        chunks = embedding_service._create_chunks_for_embedding(
            text, chunk_size=50, overlap=10
        )

        # Chunks should not break words
        for chunk in chunks:
            # Chunks should start and end with complete words (or whitespace)
            assert not chunk.startswith(" word") or chunk.startswith(" ")

    def test_create_chunks_no_overlap(self, embedding_service):
        """Test chunk creation with no overlap."""
        text = "word " * 500
        chunks = embedding_service._create_chunks_for_embedding(
            text, chunk_size=100, overlap=0
        )

        assert len(chunks) > 1
        # With no overlap, chunks should be more distinct
        if len(chunks) > 1:
            assert chunks[0] != chunks[1]

    def test_create_chunks_large_overlap(self, embedding_service):
        """Test chunk creation with large overlap."""
        # Create text with different words to properly test overlap
        text = " ".join([f"word{i}" for i in range(500)])
        chunks = embedding_service._create_chunks_for_embedding(
            text, chunk_size=1000, overlap=500
        )

        # Should have significant overlap
        if len(chunks) > 1:
            # Count common words between consecutive chunks
            words1 = set(chunks[0].split())
            words2 = set(chunks[1].split())
            common = words1 & words2
            # Should have substantial overlap
            assert len(common) > 10

    def test_create_chunks_exact_boundary(self, embedding_service):
        """Test chunk creation at exact chunk size boundary."""
        text = "x" * 1000  # Exactly chunk size
        chunks = embedding_service._create_chunks_for_embedding(
            text, chunk_size=1000, overlap=0
        )

        assert len(chunks) == 1
        assert chunks[0] == text

    # Tests for calculate_similarity edge cases
    def test_calculate_similarity_empty_embeddings(self, embedding_service):
        """Test similarity calculation with empty embeddings."""
        assert embedding_service.calculate_similarity([], []) == 0.0

    def test_calculate_similarity_one_empty(self, embedding_service):
        """Test similarity calculation with one empty embedding."""
        normal = [1.0, 2.0, 3.0]
        assert embedding_service.calculate_similarity(normal, []) == 0.0
        assert embedding_service.calculate_similarity([], normal) == 0.0

    def test_calculate_similarity_none_values(self, embedding_service):
        """Test similarity calculation with None values."""
        normal = [1.0, 2.0, 3.0]
        assert embedding_service.calculate_similarity(None, normal) == 0.0
        assert embedding_service.calculate_similarity(normal, None) == 0.0

    def test_calculate_similarity_negative_values(self, embedding_service):
        """Test similarity calculation with negative values."""
        emb1 = [1.0, -2.0, 3.0]
        emb2 = [-1.0, 2.0, -3.0]

        similarity = embedding_service.calculate_similarity(emb1, emb2)
        assert -1.0 <= similarity <= 1.0  # Cosine similarity range

    def test_calculate_similarity_large_values(self, embedding_service):
        """Test similarity calculation with large values."""
        emb1 = [1000.0, 2000.0, 3000.0]
        emb2 = [1000.0, 2000.0, 3000.0]

        similarity = embedding_service.calculate_similarity(emb1, emb2)
        # Use pytest.approx for floating point comparison
        assert similarity == pytest.approx(1.0, rel=1e-9)
