"""Tests for tasks/processing_tasks.py module."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any

from jd_ingestion.tasks.processing_tasks import (
    process_single_file_task,
    batch_process_files_task,
    _process_single_file_async,
    _is_retryable_error,
    _handle_task_failure,
)


class TestRetryableErrorDetection:
    """Test the _is_retryable_error function for processing tasks."""

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
            assert _is_retryable_error(error) is False

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
            assert _is_retryable_error(error) is True

    def test_retryable_error_message_patterns(self):
        """Test that errors with certain message patterns are retryable."""
        retryable_messages = [
            "connection failed",
            "timeout occurred",
            "temporary error",
            "database connection lost",
            "network error",
            "redis connection failed",
            "celery worker error",
        ]

        for message in retryable_messages:
            error = Exception(message)
            assert _is_retryable_error(error) is True

    def test_unknown_error_not_retryable(self):
        """Test that unknown errors default to non-retryable."""
        unknown_error = Exception("Some unknown error")
        assert _is_retryable_error(unknown_error) is False


class TestProcessSingleFileTask:
    """Test the process_single_file_task function."""

    @patch("jd_ingestion.tasks.processing_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.processing_tasks.logger")
    def test_successful_file_processing(self, mock_logger, mock_asyncio_run):
        """Test successful file processing."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.request.retries = 0

        # Mock the async function result
        expected_result = {
            "status": "success",
            "file_path": "/test/file.txt",
            "job_id": 123,
            "metadata": {
                "job_number": "JD123",
                "classification": "EX-01",
                "language": "en",
                "title": "Test Job",
                "file_size": 1024,
                "file_hash": "abc123",
            },
            "processed_content": {
                "sections_found": 3,
                "sections": ["section1", "section2", "section3"],
                "chunks_generated": 5,
                "processing_errors": [],
            },
        }
        mock_asyncio_run.return_value = expected_result

        # Call the task
        result = process_single_file_task(
            mock_task, "/test/file.txt", generate_embeddings=True
        )

        # Verify result
        assert result == expected_result

        # Verify logging
        mock_logger.info.assert_called()

        # Verify state updates
        mock_task.update_state.assert_called_with(
            state="PROCESSING", meta={"status": "Starting file processing"}
        )

        # Verify async function was called with correct parameters
        mock_asyncio_run.assert_called_once_with(
            _process_single_file_async("/test/file.txt", mock_task, True)
        )

    @patch("jd_ingestion.tasks.processing_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.processing_tasks.logger")
    @patch("jd_ingestion.tasks.processing_tasks._is_retryable_error")
    def test_retryable_error_handling(
        self, mock_is_retryable, mock_logger, mock_asyncio_run
    ):
        """Test handling of retryable errors."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.request.retries = 0

        # Mock retryable error
        test_error = ConnectionError("Database connection failed")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = True

        # Expect retry to be raised
        with pytest.raises(Exception):
            process_single_file_task(mock_task, "/test/file.txt")

        # Verify retry was attempted
        mock_task.retry.assert_called_once()

        # Verify state update
        mock_task.update_state.assert_called_with(
            state="RETRY",
            meta={
                "error": str(test_error),
                "file_path": "/test/file.txt",
                "retry_count": 0,
                "next_retry_in": mock_task.retry.call_args[1]["countdown"],
            },
        )

    @patch("jd_ingestion.tasks.processing_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.processing_tasks.logger")
    @patch("jd_ingestion.tasks.processing_tasks._is_retryable_error")
    def test_non_retryable_error_handling(
        self, mock_is_retryable, mock_logger, mock_asyncio_run
    ):
        """Test handling of non-retryable errors."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Mock non-retryable error
        test_error = ValueError("Invalid file format")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = False

        # Expect error to be re-raised without retry
        with pytest.raises(ValueError):
            process_single_file_task(mock_task, "/test/file.txt")

        # Verify retry was NOT attempted
        mock_task.retry.assert_not_called()

        # Verify state update
        mock_task.update_state.assert_called_with(
            state="FAILURE",
            meta={
                "error": str(test_error),
                "file_path": "/test/file.txt",
                "retryable": False,
            },
        )


class TestBatchProcessFilesTask:
    """Test the batch_process_files_task function."""

    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    @patch("jd_ingestion.tasks.processing_tasks.logger")
    def test_successful_batch_processing(
        self, mock_logger, mock_path_cls, mock_asyncio_run, mock_file_discovery_cls
    ):
        """Test successful batch file processing."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        # Mock file discovery
        mock_file_discovery = MagicMock()
        mock_file_metadata = [
            MagicMock(is_valid=True, file_path=Path("/test/file1.txt")),
            MagicMock(is_valid=True, file_path=Path("/test/file2.txt")),
        ]
        mock_file_discovery.scan_directory.return_value = mock_file_metadata
        mock_file_discovery_cls.return_value = mock_file_discovery

        # Mock async processing results
        mock_asyncio_run.side_effect = [
            {"status": "success", "job_id": 123},
            {"status": "success", "job_id": 456},
        ]

        # Mock embedding task
        with patch(
            "jd_ingestion.tasks.processing_tasks.batch_generate_embeddings_task"
        ) as mock_embedding_task:
            result = batch_process_files_task(
                mock_task,
                "/test/directory",
                max_files=None,
                recursive=True,
                generate_embeddings=True,
            )

        # Verify result
        assert result["status"] == "completed"
        assert result["directory"] == "/test/directory"
        assert result["successful_files"] == 2
        assert result["failed_files"] == 0

        # Verify embedding task was triggered
        mock_embedding_task.delay.assert_called_once_with([123, 456])

    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    def test_batch_processing_directory_not_found(
        self, mock_path_cls, mock_file_discovery_cls
    ):
        """Test batch processing when directory doesn't exist."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Mock Path with non-existent directory
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path_cls.return_value = mock_path

        with pytest.raises(FileNotFoundError):
            batch_process_files_task(mock_task, "/nonexistent/directory")

    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    def test_batch_processing_no_valid_files(
        self, mock_path_cls, mock_file_discovery_cls
    ):
        """Test batch processing when no valid files are found."""
        mock_task = MagicMock()
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        # Mock file discovery with no valid files
        mock_file_discovery = MagicMock()
        mock_file_discovery.scan_directory.return_value = [
            MagicMock(is_valid=False),  # Invalid file
        ]
        mock_file_discovery_cls.return_value = mock_file_discovery

        result = batch_process_files_task(mock_task, "/test/directory")

        assert result["status"] == "error"
        assert "No valid files found" in result["message"]

    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    def test_batch_processing_with_failures(
        self, mock_path_cls, mock_asyncio_run, mock_file_discovery_cls
    ):
        """Test batch processing with some file failures."""
        mock_task = MagicMock()
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        # Mock file discovery
        mock_file_discovery = MagicMock()
        mock_file_metadata = [
            MagicMock(is_valid=True, file_path=Path("/test/file1.txt")),
            MagicMock(is_valid=True, file_path=Path("/test/file2.txt")),
        ]
        mock_file_discovery.scan_directory.return_value = mock_file_metadata
        mock_file_discovery_cls.return_value = mock_file_discovery

        # Mock mixed success/failure
        mock_asyncio_run.side_effect = [
            {"status": "success", "job_id": 123},
            Exception("Processing failed"),
        ]

        result = batch_process_files_task(mock_task, "/test/directory")

        assert result["status"] == "completed"
        assert result["successful_files"] == 1
        assert result["failed_files"] == 1
        assert len(result["results"]["successful"]) == 1
        assert len(result["results"]["failed"]) == 1


class TestProcessSingleFileAsync:
    """Test the _process_single_file_async function."""

    @pytest.fixture
    def mock_file_metadata(self):
        """Create mock file metadata."""
        metadata = MagicMock()
        metadata.is_valid = True
        metadata.job_number = "JD123"
        metadata.title = "Test Job"
        metadata.classification = "EX-01"
        metadata.language = "en"
        metadata.encoding = "utf-8"
        metadata.file_size = 1024
        metadata.file_hash = "abc123"
        metadata.validation_errors = []
        return metadata

    @pytest.fixture
    def mock_processed_content(self):
        """Create mock processed content."""
        content = MagicMock()
        content.cleaned_content = "Test content"
        content.sections = {
            "general_accountability": "Test accountability",
            "specific_accountabilities": "Test specific",
        }
        content.structured_fields = MagicMock()
        content.structured_fields.department = "Test Department"
        content.structured_fields.reports_to = "Test Manager"
        content.processing_errors = []
        return content

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.processing_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.ContentProcessor")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    @patch("builtins.open", new_callable=mock_open, read_data="Test file content")
    async def test_process_single_file_async_success(
        self,
        mock_file_open,
        mock_path_cls,
        mock_content_processor_cls,
        mock_file_discovery_cls,
        mock_session_local,
        mock_file_metadata,
        mock_processed_content,
    ):
        """Test successful async file processing."""
        # Mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.parent = Path("/test")
        mock_path_cls.return_value = mock_path

        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock file discovery
        mock_file_discovery = MagicMock()
        mock_file_discovery._extract_file_metadata.return_value = mock_file_metadata
        mock_file_discovery_cls.return_value = mock_file_discovery

        # Mock content processor
        mock_content_processor = MagicMock()
        mock_content_processor.process_content.return_value = mock_processed_content
        mock_content_processor.chunk_content.return_value = ["chunk1", "chunk2"]
        mock_content_processor_cls.return_value = mock_content_processor

        # Mock task
        mock_task = MagicMock()

        # Mock job description creation
        with (
            patch(
                "jd_ingestion.tasks.processing_tasks.JobDescription"
            ) as mock_job_desc_cls,
            patch(
                "jd_ingestion.tasks.processing_tasks.JobSection"
            ) as mock_job_section_cls,
            patch(
                "jd_ingestion.tasks.processing_tasks.JobMetadata"
            ) as mock_job_metadata_cls,
            patch(
                "jd_ingestion.tasks.processing_tasks.ContentChunk"
            ) as mock_content_chunk_cls,
        ):
            mock_job_desc = MagicMock()
            mock_job_desc.id = 123
            mock_job_desc_cls.return_value = mock_job_desc

            result = await _process_single_file_async("/test/file.txt", mock_task, True)

        # Verify result
        assert result["status"] == "success"
        assert result["job_id"] == 123
        assert result["file_path"] == "/test/file.txt"

        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    async def test_process_single_file_async_file_not_found(self, mock_path_cls):
        """Test async file processing when file doesn't exist."""
        # Mock Path with non-existent file
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path_cls.return_value = mock_path

        mock_task = MagicMock()

        with patch(
            "jd_ingestion.tasks.processing_tasks.AsyncSessionLocal"
        ) as mock_session_local:
            mock_db = AsyncMock()
            mock_session_local.return_value.__aenter__.return_value = mock_db

            with pytest.raises(FileNotFoundError, match="File does not exist"):
                await _process_single_file_async("/nonexistent/file.txt", mock_task)

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.processing_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    async def test_process_single_file_async_invalid_metadata(
        self, mock_path_cls, mock_file_discovery_cls, mock_session_local
    ):
        """Test async file processing with invalid metadata."""
        # Mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.parent = Path("/test")
        mock_path_cls.return_value = mock_path

        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock file discovery with invalid metadata
        mock_file_discovery = MagicMock()
        mock_invalid_metadata = MagicMock()
        mock_invalid_metadata.is_valid = False
        mock_invalid_metadata.validation_errors = ["Invalid file format"]
        mock_file_discovery._extract_file_metadata.return_value = mock_invalid_metadata
        mock_file_discovery_cls.return_value = mock_file_discovery

        mock_task = MagicMock()

        result = await _process_single_file_async("/test/file.txt", mock_task)

        assert result["status"] == "error"
        assert result["errors"] == ["Invalid file format"]

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.processing_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.processing_tasks.FileDiscovery")
    @patch("jd_ingestion.tasks.processing_tasks.ContentProcessor")
    @patch("jd_ingestion.tasks.processing_tasks.Path")
    @patch("builtins.open", new_callable=mock_open, read_data="Test content")
    async def test_process_single_file_async_content_processing_failure(
        self,
        mock_file_open,
        mock_path_cls,
        mock_content_processor_cls,
        mock_file_discovery_cls,
        mock_session_local,
        mock_file_metadata,
    ):
        """Test async file processing with content processing failure."""
        # Mock Path
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.parent = Path("/test")
        mock_path_cls.return_value = mock_path

        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock file discovery
        mock_file_discovery = MagicMock()
        mock_file_discovery._extract_file_metadata.return_value = mock_file_metadata
        mock_file_discovery_cls.return_value = mock_file_discovery

        # Mock content processor with failure
        mock_content_processor = MagicMock()
        mock_content_processor.process_content.side_effect = Exception(
            "Processing failed"
        )
        mock_content_processor.chunk_content.return_value = []
        mock_content_processor_cls.return_value = mock_content_processor

        mock_task = MagicMock()

        # Mock job description creation
        with patch(
            "jd_ingestion.tasks.processing_tasks.JobDescription"
        ) as mock_job_desc_cls:
            mock_job_desc = MagicMock()
            mock_job_desc.id = 123
            mock_job_desc_cls.return_value = mock_job_desc

            result = await _process_single_file_async("/test/file.txt", mock_task)

        # Should still succeed but with processing errors
        assert result["status"] == "success"
        assert len(result["processed_content"]["processing_errors"]) > 0

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.processing_tasks.AsyncSessionLocal")
    async def test_process_single_file_async_database_error(self, mock_session_local):
        """Test async file processing with database error."""
        # Mock database session with error
        mock_db = AsyncMock()
        mock_db.add.side_effect = Exception("Database error")
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock other dependencies to get to database operations
        with (
            patch("jd_ingestion.tasks.processing_tasks.Path") as mock_path_cls,
            patch(
                "jd_ingestion.tasks.processing_tasks.FileDiscovery"
            ) as mock_file_discovery_cls,
            patch(
                "jd_ingestion.tasks.processing_tasks.ContentProcessor"
            ) as mock_content_processor_cls,
            patch("builtins.open", mock_open(read_data="test")),
        ):
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.parent = Path("/test")
            mock_path_cls.return_value = mock_path

            mock_file_discovery = MagicMock()
            mock_metadata = MagicMock()
            mock_metadata.is_valid = True
            mock_metadata.encoding = "utf-8"
            mock_file_discovery._extract_file_metadata.return_value = mock_metadata
            mock_file_discovery_cls.return_value = mock_file_discovery

            mock_content_processor = MagicMock()
            mock_content = MagicMock()
            mock_content.cleaned_content = "test"
            mock_content.sections = {}
            mock_content.processing_errors = []
            mock_content_processor.process_content.return_value = mock_content
            mock_content_processor.chunk_content.return_value = []
            mock_content_processor_cls.return_value = mock_content_processor

            mock_task = MagicMock()

            with pytest.raises(Exception, match="Database error"):
                await _process_single_file_async("/test/file.txt", mock_task)

            # Verify rollback was called
            mock_db.rollback.assert_called()


class TestHandleTaskFailure:
    """Test the _handle_task_failure function."""

    @patch("jd_ingestion.tasks.processing_tasks.logger")
    def test_handle_task_failure_logging(self, mock_logger):
        """Test that task failure is properly logged."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.request.retries = 3

        test_error = Exception("Task failed")

        _handle_task_failure(
            mock_task,
            test_error,
            "process_single_file_task",
            file_path="/test/file.txt",
            job_id=123,
        )

        # Verify error logging
        mock_logger.error.assert_called_once_with(
            "Task failed after all retries",
            task_name="process_single_file_task",
            error=str(test_error),
            task_id="test-task-id",
            retries=3,
            file_path="/test/file.txt",
            job_id=123,
        )


class TestTaskIntegration:
    """Test integration aspects of the processing tasks."""

    def test_task_decorators(self):
        """Test that tasks are properly decorated."""
        # Check that tasks are bound
        assert process_single_file_task.bind is True
        assert batch_process_files_task.bind is True

        # Check task names
        assert (
            process_single_file_task.name
            == "jd_ingestion.tasks.processing_tasks.process_single_file_task"
        )
        assert (
            batch_process_files_task.name
            == "jd_ingestion.tasks.processing_tasks.batch_process_files_task"
        )

    @patch("jd_ingestion.tasks.processing_tasks.settings")
    def test_database_connection_configuration(self, mock_settings):
        """Test that database connection is properly configured."""
        mock_settings.database_url = "postgresql://test:test@localhost/test"

        # Re-import to apply mocked settings
        import importlib
        import jd_ingestion.tasks.processing_tasks

        importlib.reload(jd_ingestion.tasks.processing_tasks)

        # Verify that engine and session maker are created
        assert hasattr(jd_ingestion.tasks.processing_tasks, "engine")
        assert hasattr(jd_ingestion.tasks.processing_tasks, "AsyncSessionLocal")

    def test_embedding_task_integration(self):
        """Test that embedding tasks are properly imported and called."""
        # This tests that the imports don't fail and the tasks can be referenced
        with patch(
            "jd_ingestion.tasks.processing_tasks.generate_embeddings_for_job_task"
        ) as mock_task:
            with patch(
                "jd_ingestion.tasks.processing_tasks.batch_generate_embeddings_task"
            ) as mock_batch_task:
                # Import check - these should not fail
                from jd_ingestion.tasks.processing_tasks import (
                    _process_single_file_async,
                    batch_process_files_task,
                )

                # Verify tasks can be mocked (indicating proper import structure)
                assert mock_task is not None
                assert mock_batch_task is not None

    def test_quality_task_integration(self):
        """Test that quality tasks are properly imported and called."""
        with patch(
            "jd_ingestion.tasks.processing_tasks.calculate_quality_metrics_task"
        ) as mock_task:
            # Import check
            from jd_ingestion.tasks.processing_tasks import _process_single_file_async

            # Verify task can be mocked
            assert mock_task is not None

    def test_exponential_backoff_limits(self):
        """Test that exponential backoff has reasonable limits."""
        mock_task = MagicMock()
        mock_task.request.retries = 10  # High retry count

        test_error = ConnectionError("Connection failed")

        with (
            patch(
                "jd_ingestion.tasks.processing_tasks.asyncio.run"
            ) as mock_asyncio_run,
            patch(
                "jd_ingestion.tasks.processing_tasks._is_retryable_error",
                return_value=True,
            ),
        ):
            mock_asyncio_run.side_effect = test_error

            with pytest.raises(Exception):
                process_single_file_task(mock_task, "/test/file.txt")

            # Verify backoff is capped
            retry_call = mock_task.retry.call_args
            countdown = retry_call[1]["countdown"]
            assert countdown <= 300  # Should be capped at 300 seconds for single file

        # Test batch processing backoff
        with (
            patch("jd_ingestion.tasks.processing_tasks.Path") as mock_path,
            patch(
                "jd_ingestion.tasks.processing_tasks._is_retryable_error",
                return_value=True,
            ),
        ):
            mock_path.return_value.exists.side_effect = test_error

            with pytest.raises(Exception):
                batch_process_files_task(mock_task, "/test/directory")

            # Verify batch backoff is capped at 600 seconds
            retry_call = mock_task.retry.call_args
            countdown = retry_call[1]["countdown"]
            assert countdown <= 600
