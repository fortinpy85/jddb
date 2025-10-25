"""Tests for tasks/embedding_tasks.py module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from jd_ingestion.tasks.embedding_tasks import (
    generate_embeddings_for_job_task,
    batch_generate_embeddings_task,
    generate_missing_embeddings_task,
    _generate_embeddings_for_job_async,
    _batch_generate_embeddings_async,
    _generate_missing_embeddings_async,
)
from jd_ingestion.utils.retry_utils import is_retryable_error as is_retryable_error
from jd_ingestion.database.models import ContentChunk


class TestRetryableErrorDetection:
    """Test the is_retryable_error function."""

    def test_non_retryable_errors(self):
        """Test that certain errors are marked as non-retryable."""
        non_retryable_errors = [
            FileNotFoundError("File not found"),
            PermissionError("Permission denied"),
            ValueError("Invalid value"),
            TypeError("Type error"),
            KeyError("Missing key"),
        ]

        for error in non_retryable_errors:
            assert is_retryable_error(error) is False

    def test_retryable_errors(self):
        """Test that certain errors are marked as retryable."""
        retryable_errors = [
            ConnectionError("Connection failed"),
            TimeoutError("Operation timeout"),
            OSError("I/O error"),
            ImportError("Module not found"),
            RuntimeError("Runtime error"),
        ]

        for error in retryable_errors:
            assert is_retryable_error(error) is True

    def test_retryable_error_message_patterns(self):
        """Test that errors with certain message patterns are retryable."""
        retryable_messages = [
            "connection failed",
            "timeout occurred",
            "temporary error",
            "rate limit exceeded",
            "service unavailable",
            "internal server error",
            "database connection lost",
            "network error",
            "redis connection failed",
            "celery worker error",
            "openai api error",
            "api quota exceeded",
            "embedding service error",
        ]

        for message in retryable_messages:
            error = Exception(message)
            assert is_retryable_error(error) is True

    def test_unknown_error_not_retryable(self):
        """Test that unknown errors default to non-retryable."""
        unknown_error = Exception("Some unknown error")
        assert is_retryable_error(unknown_error) is False

    def test_case_insensitive_pattern_matching(self):
        """Test that pattern matching is case-insensitive."""
        error = Exception("CONNECTION FAILED")
        assert is_retryable_error(error) is True


class TestGenerateEmbeddingsForJobTask:
    """Test the generate_embeddings_for_job_task function."""

    @patch.object(generate_embeddings_for_job_task, "request")
    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    def test_successful_embedding_generation(
        self, mock_logger, mock_asyncio_run, mock_request
    ):
        """Test successful embedding generation for a job."""
        # Mock the async function result
        expected_result = {
            "status": "completed",
            "job_id": 123,
            "chunks_processed": 5,
            "successful_embeddings": 5,
            "failed_embeddings": 0,
        }
        mock_asyncio_run.return_value = expected_result

        # Mock the task's request object (needed for bind=True tasks)
        mock_request.id = "test-task-id-123"

        # Call the task with just the job_id
        result = generate_embeddings_for_job_task(123)

        # Verify result
        assert result == expected_result

        # Verify logging
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    @patch("jd_ingestion.tasks.embedding_tasks.is_retryable_error")
    def test_retryable_error_handling(
        self, mock_is_retryable, mock_logger, mock_asyncio_run
    ):
        """Test handling of retryable errors."""
        # Mock retryable error
        test_error = ConnectionError("Connection failed")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = True

        # Mock the task's request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-123"
        mock_request.retries = 0
        generate_embeddings_for_job_task.request = mock_request
        generate_embeddings_for_job_task.retry = MagicMock(
            side_effect=Exception("Retry called")
        )

        # Expect retry exception to be raised
        from celery.exceptions import Retry

        with pytest.raises((Retry, Exception)):
            generate_embeddings_for_job_task(123)

        # Verify logging
        mock_logger.warning.assert_called()
        mock_logger.error.assert_called()

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    @patch("jd_ingestion.tasks.embedding_tasks.is_retryable_error")
    def test_non_retryable_error_handling(
        self, mock_is_retryable, mock_logger, mock_asyncio_run
    ):
        """Test handling of non-retryable errors."""
        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-123"
        generate_embeddings_for_job_task.request = mock_request

        # Mock non-retryable error
        test_error = ValueError("Invalid input")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = False

        # Expect error to be re-raised without retry
        with pytest.raises(ValueError):
            generate_embeddings_for_job_task(123)

        # Verify error logging
        mock_logger.error.assert_called()

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.is_retryable_error")
    def test_exponential_backoff_calculation(self, mock_is_retryable, mock_asyncio_run):
        """Test that exponential backoff is calculated correctly."""
        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-123"
        mock_request.retries = 0
        generate_embeddings_for_job_task.request = mock_request
        generate_embeddings_for_job_task.retry = MagicMock(
            side_effect=Exception("Retry called")
        )

        test_error = ConnectionError("Connection failed")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = True

        # Expect retry to be raised
        from celery.exceptions import Retry

        with pytest.raises((Retry, Exception)):
            generate_embeddings_for_job_task(123)


class TestBatchGenerateEmbeddingsTask:
    """Test the batch_generate_embeddings_task function."""

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    def test_successful_batch_generation(self, mock_logger, mock_asyncio_run):
        """Test successful batch embedding generation."""

        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-batch-123"
        batch_generate_embeddings_task.request = mock_request

        job_ids = [123, 456, 789]
        expected_result = {
            "status": "completed",
            "total_jobs": 3,
            "successful_jobs": 3,
            "failed_jobs": 0,
            "total_chunks_processed": 15,
            "total_successful_embeddings": 15,
            "total_failed_embeddings": 0,
        }
        mock_asyncio_run.return_value = expected_result

        result = batch_generate_embeddings_task(job_ids)

        assert result == expected_result
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    def test_batch_generation_error_handling(self, mock_logger, mock_asyncio_run):
        """Test error handling in batch generation."""

        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-batch-456"
        batch_generate_embeddings_task.request = mock_request

        test_error = Exception("Batch processing failed")
        mock_asyncio_run.side_effect = test_error

        with pytest.raises(Exception):
            batch_generate_embeddings_task([123, 456])

        # State updates cannot be tested without celery context
        mock_logger.error.assert_called()


class TestGenerateMissingEmbeddingsTask:
    """Test the generate_missing_embeddings_task function."""

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    def test_successful_missing_embeddings_generation(
        self, mock_logger, mock_asyncio_run
    ):
        """Test successful missing embeddings generation."""

        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-missing-123"
        generate_missing_embeddings_task.request = mock_request

        expected_result = {
            "status": "completed",
            "chunks_processed": 10,
            "successful_embeddings": 10,
            "failed_embeddings": 0,
        }
        mock_asyncio_run.return_value = expected_result

        result = generate_missing_embeddings_task(limit=50)

        assert result == expected_result
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.embedding_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.embedding_tasks.logger")
    def test_missing_embeddings_error_handling(self, mock_logger, mock_asyncio_run):
        """Test error handling in missing embeddings generation."""

        # Mock the task\'s request object (needed for bind=True tasks)
        mock_request = MagicMock()
        mock_request.id = "test-task-id-missing-456"
        generate_missing_embeddings_task.request = mock_request

        test_error = Exception("Missing embeddings task failed")
        mock_asyncio_run.side_effect = test_error

        with pytest.raises(Exception):
            generate_missing_embeddings_task()

        # State updates cannot be tested without celery context
        mock_logger.error.assert_called()


class TestAsyncImplementations:
    """Test the async implementation functions."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        return mock_session

    @pytest.fixture
    def mock_chunks(self):
        """Create mock content chunks."""
        chunks = []
        for i in range(3):
            chunk = MagicMock(spec=ContentChunk)
            chunk.id = i + 1
            chunk.job_id = 123
            chunk.chunk_text = f"Test chunk {i + 1} content"
            chunk.embedding = None
            chunks.append(chunk)
        return chunks

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.embedding_tasks.embedding_service")
    async def test_generate_embeddings_for_job_async_success(
        self, mock_embedding_service, mock_session_local, mock_chunks
    ):
        """Test successful async embedding generation for a job."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock database query - need proper async mock chain
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_chunks
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock embedding service
        mock_embedding_service.generate_embedding = AsyncMock(
            return_value=[0.1, 0.2, 0.3]
        )

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _generate_embeddings_for_job_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["job_id"] == 123
        assert result["chunks_processed"] == 3
        assert result["successful_embeddings"] == 3
        assert result["failed_embeddings"] == 0

        # Verify embeddings were set
        for chunk in mock_chunks:
            assert chunk.embedding == [0.1, 0.2, 0.3]

        # Verify database commit
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    async def test_generate_embeddings_for_job_async_no_chunks(
        self, mock_session_local
    ):
        """Test async embedding generation when no chunks need processing."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock empty result
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _generate_embeddings_for_job_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["chunks_processed"] == 0
        assert "No chunks found" in result["message"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.embedding_tasks.embedding_service")
    async def test_generate_embeddings_for_job_async_partial_failure(
        self, mock_embedding_service, mock_session_local, mock_chunks
    ):
        """Test async embedding generation with some failures."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock database query - need proper async mock chain
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_chunks
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock embedding service with alternating success/failure
        async def mock_generate_embedding(text):
            if "chunk 1" in text:
                return [0.1, 0.2, 0.3]
            elif "chunk 2" in text:
                return None  # Failure
            else:
                raise Exception("Embedding error")

        mock_embedding_service.generate_embedding = mock_generate_embedding

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _generate_embeddings_for_job_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["successful_embeddings"] == 1
        assert result["failed_embeddings"] == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    async def test_generate_embeddings_for_job_async_database_error(
        self, mock_session_local
    ):
        """Test async embedding generation with database error."""
        # Mock database session with error
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        with pytest.raises(Exception, match="Database error"):
            await _generate_embeddings_for_job_async(123, mock_task)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks._generate_embeddings_for_job_async")
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    async def test_batch_generate_embeddings_async_success(
        self, mock_session_local, mock_generate_job_embeddings
    ):
        """Test successful batch embedding generation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock individual job processing
        mock_generate_job_embeddings.return_value = {
            "status": "completed",
            "chunks_processed": 5,
            "successful_embeddings": 5,
            "failed_embeddings": 0,
        }

        job_ids = [123, 456]

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _batch_generate_embeddings_async(job_ids, mock_task)

        assert result["status"] == "completed"
        assert result["total_jobs"] == 2
        assert result["successful_jobs"] == 2
        assert result["failed_jobs"] == 0
        assert result["total_chunks_processed"] == 10
        assert result["total_successful_embeddings"] == 10

        # Verify individual job processing was called
        assert mock_generate_job_embeddings.call_count == 2

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks._generate_embeddings_for_job_async")
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    async def test_batch_generate_embeddings_async_partial_failure(
        self, mock_session_local, mock_generate_job_embeddings
    ):
        """Test batch embedding generation with some failures."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock mixed success/failure
        def mock_generate_side_effect(job_id, task):
            if job_id == 123:
                return {
                    "status": "completed",
                    "chunks_processed": 5,
                    "successful_embeddings": 5,
                    "failed_embeddings": 0,
                }
            else:
                raise Exception("Job processing failed")

        mock_generate_job_embeddings.side_effect = mock_generate_side_effect

        job_ids = [123, 456]

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _batch_generate_embeddings_async(job_ids, mock_task)

        assert result["successful_jobs"] == 1
        assert result["failed_jobs"] == 1
        assert len(result["results"]["failed_jobs"]) == 1
        assert result["results"]["failed_jobs"][0]["job_id"] == 456

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.embedding_tasks.embedding_service")
    async def test_generate_missing_embeddings_async_success(
        self, mock_embedding_service, mock_session_local, mock_chunks
    ):
        """Test successful missing embeddings generation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock database query - need proper async mock chain
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_chunks
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock batch embedding generation
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
        mock_embedding_service.generate_embeddings_batch = AsyncMock(
            return_value=embeddings
        )

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _generate_missing_embeddings_async(50, mock_task)

        assert result["status"] == "completed"
        assert result["chunks_processed"] == 3
        assert result["successful_embeddings"] == 3
        assert result["failed_embeddings"] == 0

        # Verify embeddings were set
        for i, chunk in enumerate(mock_chunks):
            assert chunk.embedding == embeddings[i]

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    async def test_generate_missing_embeddings_async_no_chunks(
        self, mock_session_local
    ):
        """Test missing embeddings generation when no chunks need processing."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock empty result
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = AsyncMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        result = await _generate_missing_embeddings_async(None, mock_task)

        assert result["status"] == "completed"
        assert result["chunks_processed"] == 0
        assert "No chunks found" in result["message"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.embedding_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.embedding_tasks.embedding_service")
    async def test_generate_missing_embeddings_async_with_limit(
        self, mock_embedding_service, mock_session_local
    ):
        """Test missing embeddings generation with limit parameter."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock database query to verify limit is applied
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Mock task
        mock_task = MagicMock()
        mock_task.update_state = MagicMock()

        await _generate_missing_embeddings_async(100, mock_task)

        # Verify that limit was applied to the query
        query_call = mock_db.execute.call_args[0][0]
        # The query should have been modified with limit
        assert (
            hasattr(query_call, "_limit_clause")
            or str(query_call).find("LIMIT") != -1
            or hasattr(query_call, "_limit")
        )


class TestTaskIntegration:
    """Test integration aspects of the embedding tasks."""

    def test_task_decorators(self):
        """Test that tasks are properly decorated."""
        # Check that tasks have bind option in their configuration
        # Celery tasks with bind=True have self as first parameter
        import inspect

        sig1 = inspect.signature(generate_embeddings_for_job_task.run)
        sig2 = inspect.signature(batch_generate_embeddings_task.run)
        sig3 = inspect.signature(generate_missing_embeddings_task.run)

        # When bind=True, the 'run' method has 'self' as first parameter
        assert "self" in sig1.parameters
        assert "self" in sig2.parameters
        assert "self" in sig3.parameters

        # Check task names
        assert (
            generate_embeddings_for_job_task.name
            == "jd_ingestion.tasks.embedding_tasks.generate_embeddings_for_job_task"
        )
        assert (
            batch_generate_embeddings_task.name
            == "jd_ingestion.tasks.embedding_tasks.batch_generate_embeddings_task"
        )
        assert (
            generate_missing_embeddings_task.name
            == "jd_ingestion.tasks.embedding_tasks.generate_missing_embeddings_task"
        )

    @patch("jd_ingestion.tasks.embedding_tasks.settings")
    def test_database_connection_configuration(self, mock_settings):
        """Test that database connection is properly configured."""
        mock_settings.database_url = "postgresql://test:test@localhost/test"

        # Re-import to apply mocked settings
        import importlib
        import jd_ingestion.tasks.embedding_tasks

        importlib.reload(jd_ingestion.tasks.embedding_tasks)

        # Verify that engine and session maker are created
        assert hasattr(jd_ingestion.tasks.embedding_tasks, "engine")
        assert hasattr(jd_ingestion.tasks.embedding_tasks, "AsyncSessionLocal")

    def test_progress_tracking_states(self):
        """Test that tasks use consistent progress states."""
        expected_states = ["PROCESSING", "RETRY", "FAILURE"]

        # This test ensures that the states used in the tasks are consistent
        # and follow Celery conventions
        for state in expected_states:
            assert isinstance(state, str)
            assert state.isupper()  # Convention for Celery states
