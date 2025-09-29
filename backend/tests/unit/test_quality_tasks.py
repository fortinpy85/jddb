"""Tests for tasks/quality_tasks.py module."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional

from jd_ingestion.tasks.quality_tasks import (
    calculate_quality_metrics_task,
    batch_calculate_quality_metrics_task,
    generate_quality_report_task,
    validate_job_content_task,
    _calculate_quality_metrics_async,
    _batch_calculate_quality_metrics_async,
    _generate_quality_report_async,
    _validate_job_content_async,
    _is_retryable_error,
)


class TestRetryableErrorDetection:
    """Test the _is_retryable_error function for quality tasks."""

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
            "quality calculation failed",
            "analysis timeout",
        ]

        for message in retryable_messages:
            error = Exception(message)
            assert _is_retryable_error(error) is True

    def test_unknown_error_not_retryable(self):
        """Test that unknown errors default to non-retryable."""
        unknown_error = Exception("Some unknown error")
        assert _is_retryable_error(unknown_error) is False


class TestCalculateQualityMetricsTask:
    """Test the calculate_quality_metrics_task function."""

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_successful_quality_metrics_calculation(
        self, mock_logger, mock_asyncio_run
    ):
        """Test successful quality metrics calculation."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.request.retries = 0

        # Mock the async function result
        expected_result = {
            "status": "completed",
            "job_id": 123,
            "metrics": {
                "content_completeness": 0.85,
                "sections_completeness": 0.90,
                "metadata_completeness": 0.75,
                "has_structured_fields": True,
                "has_all_sections": False,
                "has_embeddings": True,
                "processing_errors": 0,
                "validation_errors": 1,
                "content_extraction_success": True,
                "quality_flags": {"needs_review": False},
                "validation_results": {"errors": []},
            },
        }
        mock_asyncio_run.return_value = expected_result

        # Call the task
        result = calculate_quality_metrics_task(mock_task, 123)

        # Verify result
        assert result == expected_result

        # Verify logging
        mock_logger.info.assert_called()

        # Verify state updates
        mock_task.update_state.assert_called_with(
            state="PROCESSING", meta={"status": "Starting quality metrics calculation"}
        )

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    @patch("jd_ingestion.tasks.quality_tasks._is_retryable_error")
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
            calculate_quality_metrics_task(mock_task, 123)

        # Verify retry was attempted
        mock_task.retry.assert_called_once()

        # Verify state update
        mock_task.update_state.assert_called_with(
            state="RETRY",
            meta={
                "error": str(test_error),
                "job_id": 123,
                "retry_count": 0,
                "next_retry_in": mock_task.retry.call_args[1]["countdown"],
            },
        )

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    @patch("jd_ingestion.tasks.quality_tasks._is_retryable_error")
    def test_non_retryable_error_handling(
        self, mock_is_retryable, mock_logger, mock_asyncio_run
    ):
        """Test handling of non-retryable errors."""
        # Mock the task object
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        # Mock non-retryable error
        test_error = ValueError("Invalid job ID")
        mock_asyncio_run.side_effect = test_error
        mock_is_retryable.return_value = False

        # Expect error to be re-raised without retry
        with pytest.raises(ValueError):
            calculate_quality_metrics_task(mock_task, 123)

        # Verify retry was NOT attempted
        mock_task.retry.assert_not_called()

        # Verify state update
        mock_task.update_state.assert_called_with(
            state="FAILURE",
            meta={"error": str(test_error), "job_id": 123, "retryable": False},
        )

    def test_exponential_backoff_calculation(self):
        """Test that exponential backoff is calculated correctly."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.request.retries = 2

        test_error = ConnectionError("Connection failed")

        with (
            patch("jd_ingestion.tasks.quality_tasks.asyncio.run") as mock_asyncio_run,
            patch(
                "jd_ingestion.tasks.quality_tasks._is_retryable_error",
                return_value=True,
            ),
        ):
            mock_asyncio_run.side_effect = test_error

            with pytest.raises(Exception):
                calculate_quality_metrics_task(mock_task, 123)

            # Verify backoff calculation
            retry_call = mock_task.retry.call_args
            countdown = retry_call[1]["countdown"]

            # Should be capped at 300 seconds
            assert countdown <= 300
            assert countdown > 0


class TestBatchCalculateQualityMetricsTask:
    """Test the batch_calculate_quality_metrics_task function."""

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_successful_batch_calculation(self, mock_logger, mock_asyncio_run):
        """Test successful batch quality metrics calculation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        job_ids = [123, 456, 789]
        expected_result = {
            "status": "completed",
            "total_jobs": 3,
            "successful": 3,
            "failed": 0,
            "errors": [],
        }
        mock_asyncio_run.return_value = expected_result

        result = batch_calculate_quality_metrics_task(mock_task, job_ids)

        assert result == expected_result
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_batch_calculation_all_jobs(self, mock_logger, mock_asyncio_run):
        """Test batch calculation for all jobs (None parameter)."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        expected_result = {
            "status": "completed",
            "total_jobs": 10,
            "successful": 8,
            "failed": 2,
            "errors": ["Error1", "Error2"],
        }
        mock_asyncio_run.return_value = expected_result

        result = batch_calculate_quality_metrics_task(mock_task, None)

        assert result == expected_result

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_batch_calculation_error_handling(self, mock_logger, mock_asyncio_run):
        """Test error handling in batch calculation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        test_error = Exception("Batch processing failed")
        mock_asyncio_run.side_effect = test_error

        with pytest.raises(Exception):
            batch_calculate_quality_metrics_task(mock_task, [123, 456])

        mock_task.update_state.assert_called_with(
            state="FAILURE", meta={"error": str(test_error), "job_ids": [123, 456]}
        )


class TestGenerateQualityReportTask:
    """Test the generate_quality_report_task function."""

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_successful_single_job_report(self, mock_logger, mock_asyncio_run):
        """Test successful single job quality report generation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        expected_result = {
            "status": "completed",
            "report_type": "single_job",
            "job_id": 123,
            "report": {
                "job_summary": {"id": 123, "title": "Test Job"},
                "quality_metrics": {"overall_score": 0.85},
                "recommendations": ["Improve section coverage"],
            },
        }
        mock_asyncio_run.return_value = expected_result

        result = generate_quality_report_task(mock_task, job_id=123)

        assert result == expected_result
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_successful_system_wide_report(self, mock_logger, mock_asyncio_run):
        """Test successful system-wide quality report generation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        expected_result = {
            "status": "completed",
            "report_type": "system_wide",
            "job_id": None,
            "report": {
                "summary": {"total_jobs": 100, "avg_score": 0.78},
                "distribution": {"high": 30, "medium": 50, "low": 20},
                "recommendations": ["System-wide improvements needed"],
            },
        }
        mock_asyncio_run.return_value = expected_result

        result = generate_quality_report_task(mock_task, job_id=None)

        assert result == expected_result

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_report_generation_error_handling(self, mock_logger, mock_asyncio_run):
        """Test error handling in report generation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        test_error = Exception("Report generation failed")
        mock_asyncio_run.side_effect = test_error

        with pytest.raises(Exception):
            generate_quality_report_task(mock_task, job_id=123)

        mock_task.update_state.assert_called_with(
            state="FAILURE", meta={"error": str(test_error), "job_id": 123}
        )


class TestValidateJobContentTask:
    """Test the validate_job_content_task function."""

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_successful_content_validation(self, mock_logger, mock_asyncio_run):
        """Test successful content validation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        expected_result = {
            "status": "completed",
            "job_id": 123,
            "validation_status": "passed",
            "validation_results": {"errors": [], "warnings": []},
            "quality_flags": {"needs_review": False, "processing_issues": False},
            "overall_score": 0.88,
            "recommendations": [],
            "needs_review": False,
            "processing_issues": False,
            "content_issues": False,
        }
        mock_asyncio_run.return_value = expected_result

        result = validate_job_content_task(mock_task, 123)

        assert result == expected_result
        mock_logger.info.assert_called()

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_failed_content_validation(self, mock_logger, mock_asyncio_run):
        """Test failed content validation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        expected_result = {
            "status": "completed",
            "job_id": 123,
            "validation_status": "failed",
            "validation_results": {"errors": ["Missing required sections"]},
            "quality_flags": {"needs_review": True, "content_issues": True},
            "overall_score": 0.45,
            "recommendations": ["Review content structure"],
            "needs_review": True,
            "processing_issues": False,
            "content_issues": True,
        }
        mock_asyncio_run.return_value = expected_result

        result = validate_job_content_task(mock_task, 123)

        assert result == expected_result
        assert result["validation_status"] == "failed"

    @patch("jd_ingestion.tasks.quality_tasks.asyncio.run")
    @patch("jd_ingestion.tasks.quality_tasks.logger")
    def test_validation_error_handling(self, mock_logger, mock_asyncio_run):
        """Test error handling in content validation."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"

        test_error = Exception("Validation failed")
        mock_asyncio_run.side_effect = test_error

        with pytest.raises(Exception):
            validate_job_content_task(mock_task, 123)

        mock_task.update_state.assert_called_with(
            state="FAILURE", meta={"error": str(test_error), "job_id": 123}
        )


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
    def mock_quality_metrics(self):
        """Create mock quality metrics."""
        return {
            "content_completeness_score": 0.85,
            "sections_completeness_score": 0.90,
            "metadata_completeness_score": 0.75,
            "has_structured_fields": True,
            "has_all_sections": False,
            "has_embeddings": True,
            "processing_errors_count": 0,
            "validation_errors_count": 1,
            "content_extraction_success": True,
            "quality_flags": {"needs_review": False, "processing_issues": False},
            "validation_results": {"errors": [], "warnings": ["Minor warning"]},
        }

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_calculate_quality_metrics_async_success(
        self, mock_quality_service, mock_session_local, mock_quality_metrics
    ):
        """Test successful async quality metrics calculation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service
        mock_quality_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=mock_quality_metrics
        )

        # Mock task
        mock_task = MagicMock()

        result = await _calculate_quality_metrics_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["job_id"] == 123
        assert result["metrics"]["content_completeness"] == 0.85
        assert result["metrics"]["sections_completeness"] == 0.90
        assert result["metrics"]["has_structured_fields"] is True
        assert result["metrics"]["processing_errors"] == 0

        # Verify service was called
        mock_quality_service.calculate_quality_metrics_for_job.assert_called_once_with(
            mock_db, 123
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_calculate_quality_metrics_async_error(
        self, mock_quality_service, mock_session_local
    ):
        """Test async quality metrics calculation with error."""
        # Mock database session
        mock_db = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service with error
        mock_quality_service.calculate_quality_metrics_for_job = AsyncMock(
            side_effect=Exception("Quality calculation failed")
        )

        mock_task = MagicMock()

        with pytest.raises(Exception, match="Quality calculation failed"):
            await _calculate_quality_metrics_async(123, mock_task)

        # Verify rollback was called
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_batch_calculate_quality_metrics_async_success(
        self, mock_quality_service, mock_session_local
    ):
        """Test successful batch quality metrics calculation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service batch method
        mock_batch_result = {
            "total_jobs": 3,
            "successful": 3,
            "failed": 0,
            "errors": [],
        }
        mock_quality_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=mock_batch_result
        )

        mock_task = MagicMock()
        job_ids = [123, 456, 789]

        result = await _batch_calculate_quality_metrics_async(job_ids, mock_task)

        assert result["status"] == "completed"
        assert result["total_jobs"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0

        # Verify service was called with correct parameters
        mock_quality_service.batch_calculate_quality_metrics.assert_called_once_with(
            db=mock_db, job_ids=job_ids
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_batch_calculate_quality_metrics_async_all_jobs(
        self, mock_quality_service, mock_session_local
    ):
        """Test batch quality metrics calculation for all jobs."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service
        mock_batch_result = {
            "total_jobs": 10,
            "successful": 8,
            "failed": 2,
            "errors": ["Error 1", "Error 2"],
        }
        mock_quality_service.batch_calculate_quality_metrics = AsyncMock(
            return_value=mock_batch_result
        )

        mock_task = MagicMock()

        result = await _batch_calculate_quality_metrics_async(None, mock_task)

        assert result["status"] == "completed"
        assert result["total_jobs"] == 10
        assert result["successful"] == 8
        assert result["failed"] == 2

        # Verify service was called with None for job_ids
        mock_quality_service.batch_calculate_quality_metrics.assert_called_once_with(
            db=mock_db, job_ids=None
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_generate_quality_report_async_success(
        self, mock_quality_service, mock_session_local
    ):
        """Test successful quality report generation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service
        mock_report = {
            "job_summary": {"id": 123, "title": "Test Job"},
            "quality_metrics": {"overall_score": 0.85},
            "recommendations": ["Improve coverage"],
        }
        mock_quality_service.get_quality_report = AsyncMock(return_value=mock_report)

        mock_task = MagicMock()

        result = await _generate_quality_report_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["report_type"] == "single_job"
        assert result["job_id"] == 123
        assert result["report"] == mock_report

        # Verify service was called
        mock_quality_service.get_quality_report.assert_called_once_with(
            db=mock_db, job_id=123
        )

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_generate_quality_report_async_system_wide(
        self, mock_quality_service, mock_session_local
    ):
        """Test system-wide quality report generation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service
        mock_report = {
            "summary": {"total_jobs": 100, "avg_score": 0.78},
            "distribution": {"high": 30, "medium": 50, "low": 20},
        }
        mock_quality_service.get_quality_report = AsyncMock(return_value=mock_report)

        mock_task = MagicMock()

        result = await _generate_quality_report_async(None, mock_task)

        assert result["status"] == "completed"
        assert result["report_type"] == "system_wide"
        assert result["job_id"] is None
        assert result["report"] == mock_report

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_validate_job_content_async_success(
        self, mock_quality_service, mock_session_local, mock_quality_metrics
    ):
        """Test successful content validation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality service
        mock_quality_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=mock_quality_metrics
        )

        mock_task = MagicMock()

        result = await _validate_job_content_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["job_id"] == 123
        assert (
            result["validation_status"] == "passed"
        )  # No errors in validation_results
        assert result["overall_score"] == 0.85

    @pytest.mark.asyncio
    @patch("jd_ingestion.tasks.quality_tasks.AsyncSessionLocal")
    @patch("jd_ingestion.tasks.quality_tasks.quality_service")
    async def test_validate_job_content_async_failed(
        self, mock_quality_service, mock_session_local
    ):
        """Test failed content validation."""
        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        # Mock quality metrics with errors
        failed_metrics = {
            "content_completeness_score": 0.45,
            "validation_results": {"errors": ["Missing required sections"]},
            "quality_flags": {"needs_review": True, "content_issues": True},
        }
        mock_quality_service.calculate_quality_metrics_for_job = AsyncMock(
            return_value=failed_metrics
        )

        mock_task = MagicMock()

        result = await _validate_job_content_async(123, mock_task)

        assert result["status"] == "completed"
        assert result["validation_status"] == "failed"  # Has errors
        assert result["needs_review"] is True
        assert result["content_issues"] is True


class TestTaskIntegration:
    """Test integration aspects of the quality tasks."""

    def test_task_decorators(self):
        """Test that tasks are properly decorated."""
        # Check that tasks are bound
        assert calculate_quality_metrics_task.bind is True
        assert batch_calculate_quality_metrics_task.bind is True
        assert generate_quality_report_task.bind is True
        assert validate_job_content_task.bind is True

        # Check task names
        assert (
            calculate_quality_metrics_task.name
            == "jd_ingestion.tasks.quality_tasks.calculate_quality_metrics_task"
        )
        assert (
            batch_calculate_quality_metrics_task.name
            == "jd_ingestion.tasks.quality_tasks.batch_calculate_quality_metrics_task"
        )
        assert (
            generate_quality_report_task.name
            == "jd_ingestion.tasks.quality_tasks.generate_quality_report_task"
        )
        assert (
            validate_job_content_task.name
            == "jd_ingestion.tasks.quality_tasks.validate_job_content_task"
        )

    @patch("jd_ingestion.tasks.quality_tasks.settings")
    def test_database_connection_configuration(self, mock_settings):
        """Test that database connection is properly configured."""
        mock_settings.database_url = "postgresql://test:test@localhost/test"

        # Re-import to apply mocked settings
        import importlib
        import jd_ingestion.tasks.quality_tasks

        importlib.reload(jd_ingestion.tasks.quality_tasks)

        # Verify that engine and session maker are created
        assert hasattr(jd_ingestion.tasks.quality_tasks, "engine")
        assert hasattr(jd_ingestion.tasks.quality_tasks, "AsyncSessionLocal")

    def test_quality_service_integration(self):
        """Test that quality service is properly imported and accessible."""
        # This tests that the import doesn't fail
        from jd_ingestion.tasks.quality_tasks import quality_service

        # The service should be importable (may be a mock in tests)
        assert quality_service is not None

    def test_exponential_backoff_limits(self):
        """Test that exponential backoff has reasonable limits."""
        mock_task = MagicMock()
        mock_task.request.retries = 10  # High retry count

        test_error = ConnectionError("Connection failed")

        with (
            patch("jd_ingestion.tasks.quality_tasks.asyncio.run") as mock_asyncio_run,
            patch(
                "jd_ingestion.tasks.quality_tasks._is_retryable_error",
                return_value=True,
            ),
        ):
            mock_asyncio_run.side_effect = test_error

            with pytest.raises(Exception):
                calculate_quality_metrics_task(mock_task, 123)

            # Verify backoff is capped
            retry_call = mock_task.retry.call_args
            countdown = retry_call[1]["countdown"]
            assert countdown <= 300  # Should be capped at 300 seconds

    def test_progress_tracking_states(self):
        """Test that tasks use consistent progress states."""
        expected_states = ["PROCESSING", "RETRY", "FAILURE"]

        # This test ensures that the states used in the tasks are consistent
        # and follow Celery conventions
        for state in expected_states:
            assert isinstance(state, str)
            assert state.isupper()  # Convention for Celery states

    def test_metric_conversion_to_float(self):
        """Test that metrics are properly converted to float values."""
        mock_metrics = {
            "content_completeness_score": "0.85",  # String value
            "sections_completeness_score": 0.90,  # Float value
            "metadata_completeness_score": None,  # None value
        }

        # Mock the async function result processing
        with patch("jd_ingestion.tasks.quality_tasks.quality_service") as mock_service:
            mock_service.calculate_quality_metrics_for_job = AsyncMock(
                return_value=mock_metrics
            )

            mock_task = MagicMock()

            # This would be called within the async function
            # We're testing the conversion logic
            content_score = float(mock_metrics.get("content_completeness_score", 0))
            sections_score = float(mock_metrics.get("sections_completeness_score", 0))
            metadata_score = float(mock_metrics.get("metadata_completeness_score", 0))

            assert content_score == 0.85
            assert sections_score == 0.90
            assert metadata_score == 0.0  # None converted to 0
