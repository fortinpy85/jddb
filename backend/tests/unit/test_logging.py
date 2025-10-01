"""
Tests for logging utility module.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from jd_ingestion.utils.logging import (
    configure_logging,
    get_logger,
    get_task_logger,
    log_performance_metric,
    log_business_metric,
    log_error_with_context,
    PerformanceTimer,
    setup_health_check_logging,
)


class TestConfigureLogging:
    """Test logging configuration functionality."""

    @patch("jd_ingestion.utils.logging.settings")
    @patch("structlog.configure")
    @patch("logging.basicConfig")
    @patch("pathlib.Path.mkdir")
    def test_configure_logging_development(
        self, mock_mkdir, mock_basic_config, mock_structlog_config, mock_settings
    ):
        """Test logging configuration for development environment."""
        mock_settings.is_development = True
        mock_settings.is_production = False
        mock_settings.is_staging = False
        mock_settings.debug = True
        mock_settings.log_level = "debug"
        mock_settings.environment = "development"

        configure_logging()

        # Verify basic logging configuration was called
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.DEBUG
        assert call_kwargs["format"] == "%(message)s"
        assert len(call_kwargs["handlers"]) == 1  # Console handler only

        # Verify structlog configuration
        mock_structlog_config.assert_called_once()
        structlog_kwargs = mock_structlog_config.call_args[1]
        assert structlog_kwargs["context_class"] is dict
        assert structlog_kwargs["cache_logger_on_first_use"] is True

        # Directory creation should not be called in development
        mock_mkdir.assert_not_called()

    @patch("jd_ingestion.utils.logging.settings")
    @patch("structlog.configure")
    @patch("logging.basicConfig")
    @patch("pathlib.Path.mkdir")
    def test_configure_logging_production(
        self, mock_mkdir, mock_basic_config, mock_structlog_config, mock_settings
    ):
        """Test logging configuration for production environment."""
        mock_settings.is_development = False
        mock_settings.is_production = True
        mock_settings.is_staging = False
        mock_settings.debug = False
        mock_settings.log_level = "info"
        mock_settings.environment = "production"

        configure_logging()

        # Verify logs directory was created
        mock_mkdir.assert_called_once_with(exist_ok=True)

        # Verify basic logging configuration with file handlers
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.INFO
        assert len(call_kwargs["handlers"]) == 3  # Main, error, and task handlers

    @patch("jd_ingestion.utils.logging.settings")
    @patch("structlog.configure")
    @patch("logging.basicConfig")
    @patch("pathlib.Path.mkdir")
    def test_configure_logging_staging(
        self, mock_mkdir, mock_basic_config, mock_structlog_config, mock_settings
    ):
        """Test logging configuration for staging environment."""
        mock_settings.is_development = False
        mock_settings.is_production = False
        mock_settings.is_staging = True
        mock_settings.debug = False
        mock_settings.log_level = "warning"
        mock_settings.environment = "staging"

        configure_logging()

        # Verify logs directory was created
        mock_mkdir.assert_called_once_with(exist_ok=True)

        # Verify basic logging configuration
        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == logging.WARNING

    @patch("jd_ingestion.utils.logging.settings")
    @patch("structlog.configure")
    @patch("logging.basicConfig")
    @patch("os.getpid", return_value=12345)
    def test_structlog_processors_configuration(
        self, mock_getpid, mock_basic_config, mock_structlog_config, mock_settings
    ):
        """Test structlog processors are properly configured."""
        mock_settings.is_development = True
        mock_settings.is_production = False
        mock_settings.is_staging = False
        mock_settings.debug = False
        mock_settings.log_level = "info"
        mock_settings.environment = "development"

        configure_logging()

        # Verify structlog configuration includes all required processors
        mock_structlog_config.assert_called_once()
        structlog_kwargs = mock_structlog_config.call_args[1]
        processors = structlog_kwargs["processors"]

        # Should have at least 9 processors (including context processor and renderer)
        assert len(processors) >= 9

        # Test context processor adds expected fields
        context_processor = processors[-2]  # Second to last processor
        mock_logger = Mock()
        result = context_processor(mock_logger, "info", {"test": "data"})

        assert result["test"] == "data"
        assert result["environment"] == "development"
        assert result["service"] == "jd-ingestion"
        assert result["pid"] == 12345


class TestGetLogger:
    """Test logger creation functionality."""

    @patch("structlog.get_logger")
    def test_get_logger_basic(self, mock_get_logger):
        """Test basic logger creation."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        result = get_logger("test.module")

        mock_get_logger.assert_called_once_with("test.module")
        assert result == mock_logger

    @patch("structlog.get_logger")
    def test_get_logger_with_context(self, mock_get_logger):
        """Test logger creation with initial context."""
        mock_logger = Mock()
        mock_bound_logger = Mock()
        mock_logger.bind.return_value = mock_bound_logger
        mock_get_logger.return_value = mock_logger

        context = {"user_id": "123", "session": "abc"}
        result = get_logger("test.module", **context)

        mock_get_logger.assert_called_once_with("test.module")
        mock_logger.bind.assert_called_once_with(**context)
        assert result == mock_bound_logger

    @patch("jd_ingestion.utils.logging.get_logger")
    def test_get_task_logger_basic(self, mock_get_logger):
        """Test task logger creation."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        result = get_task_logger("process_file")

        mock_get_logger.assert_called_once_with("celery.task", task_name="process_file")
        assert result == mock_logger

    @patch("jd_ingestion.utils.logging.get_logger")
    def test_get_task_logger_with_id(self, mock_get_logger):
        """Test task logger creation with task ID."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        result = get_task_logger("process_file", task_id="task-123")

        mock_get_logger.assert_called_once_with(
            "celery.task", task_name="process_file", task_id="task-123"
        )
        assert result == mock_logger


class TestMetricsLogging:
    """Test metrics logging functionality."""

    @patch("jd_ingestion.utils.logging.get_logger")
    @patch("jd_ingestion.utils.logging.datetime")
    def test_log_performance_metric_basic(self, mock_datetime, mock_get_logger):
        """Test basic performance metric logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        log_performance_metric("api_response_time", 150.5)

        mock_get_logger.assert_called_once_with("metrics")
        mock_logger.info.assert_called_once_with(
            "performance_metric",
            metric_type="performance",
            metric_name="api_response_time",
            value=150.5,
            unit="ms",
            timestamp="2023-01-01T12:00:00",
        )

    @patch("jd_ingestion.utils.logging.get_logger")
    @patch("jd_ingestion.utils.logging.datetime")
    def test_log_performance_metric_with_tags(self, mock_datetime, mock_get_logger):
        """Test performance metric logging with tags."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        tags = {"endpoint": "/api/jobs", "method": "GET"}
        log_performance_metric("api_response_time", 75.2, "ms", tags, "custom_logger")

        mock_get_logger.assert_called_once_with("custom_logger")
        mock_logger.info.assert_called_once_with(
            "performance_metric",
            metric_type="performance",
            metric_name="api_response_time",
            value=75.2,
            unit="ms",
            tags=tags,
            timestamp="2023-01-01T12:00:00",
        )

    @patch("jd_ingestion.utils.logging.get_logger")
    @patch("jd_ingestion.utils.logging.datetime")
    def test_log_business_metric_basic(self, mock_datetime, mock_get_logger):
        """Test basic business metric logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        log_business_metric("jobs_processed", 42)

        mock_get_logger.assert_called_once_with("business_metrics")
        mock_logger.info.assert_called_once_with(
            "business_metric",
            metric_type="business",
            metric_name="jobs_processed",
            value=42,
            type="counter",
            timestamp="2023-01-01T12:00:00",
        )

    @patch("jd_ingestion.utils.logging.get_logger")
    @patch("jd_ingestion.utils.logging.datetime")
    def test_log_business_metric_with_tags(self, mock_datetime, mock_get_logger):
        """Test business metric logging with tags and custom type."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        tags = {"department": "HR", "region": "west"}
        log_business_metric("upload_size", 1024.5, "gauge", tags, "upload_metrics")

        mock_get_logger.assert_called_once_with("upload_metrics")
        mock_logger.info.assert_called_once_with(
            "business_metric",
            metric_type="business",
            metric_name="upload_size",
            value=1024.5,
            type="gauge",
            tags=tags,
            timestamp="2023-01-01T12:00:00",
        )


class TestErrorLogging:
    """Test error logging functionality."""

    def test_log_error_with_context_basic(self):
        """Test basic error logging."""
        mock_logger = Mock()
        error = ValueError("Test error message")

        log_error_with_context(mock_logger, error)

        mock_logger.error.assert_called_once_with(
            "application_error",
            exc_info=True,
            error_type="ValueError",
            error_message="Test error message",
        )

    def test_log_error_with_context_full(self):
        """Test error logging with full context."""
        mock_logger = Mock()
        error = RuntimeError("Runtime issue")
        context = {"file_path": "/test/file.txt", "operation": "upload"}

        log_error_with_context(
            mock_logger,
            error,
            context=context,
            user_id="user-123",
            request_id="req-456",
        )

        mock_logger.error.assert_called_once_with(
            "application_error",
            exc_info=True,
            error_type="RuntimeError",
            error_message="Runtime issue",
            context=context,
            user_id="user-123",
            request_id="req-456",
        )


class TestPerformanceTimer:
    """Test PerformanceTimer context manager."""

    def test_performance_timer_initialization(self):
        """Test performance timer initialization."""
        with patch("jd_ingestion.utils.logging.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            timer = PerformanceTimer("test_operation")

            assert timer.operation_name == "test_operation"
            assert timer.logger == mock_logger
            assert timer.tags == {}
            assert timer.start_time is None
            assert timer._elapsed_ms == 0.0

    def test_performance_timer_with_custom_params(self):
        """Test performance timer with custom parameters."""
        mock_logger = Mock()
        tags = {"category": "test"}

        timer = PerformanceTimer("test_operation", mock_logger, tags)

        assert timer.operation_name == "test_operation"
        assert timer.logger == mock_logger
        assert timer.tags == tags

    @patch("jd_ingestion.utils.logging.datetime")
    @patch("jd_ingestion.utils.logging.log_performance_metric")
    def test_performance_timer_success_flow(self, mock_log_metric, mock_datetime):
        """Test performance timer successful execution flow."""
        mock_logger = Mock()

        # Mock datetime to return predictable values
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 1, 500000)  # 1.5 seconds later
        mock_datetime.utcnow.side_effect = [start_time, end_time]

        timer = PerformanceTimer("test_operation", mock_logger)

        with timer:
            pass  # Simulate successful operation

        # Verify debug log on start
        mock_logger.debug.assert_called_once_with(
            "operation_started", operation="test_operation"
        )

        # Verify info log on completion
        mock_logger.info.assert_called_once_with(
            "operation_completed",
            operation="test_operation",
            duration_ms=1500.0,
            status="success",
        )

        # Verify performance metric was logged
        mock_log_metric.assert_called_once_with(
            "test_operation_duration", 1500.0, "ms", {}
        )

        assert timer.elapsed_ms == 1500.0

    @patch("jd_ingestion.utils.logging.datetime")
    def test_performance_timer_error_flow(self, mock_datetime):
        """Test performance timer with exception."""
        mock_logger = Mock()

        # Mock datetime to return predictable values
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        end_time = datetime(2023, 1, 1, 12, 0, 0, 750000)  # 750ms later
        mock_datetime.utcnow.side_effect = [start_time, end_time]

        timer = PerformanceTimer("test_operation", mock_logger, {"tag": "value"})

        with pytest.raises(ValueError):
            with timer:
                raise ValueError("Test error")

        # Verify debug log on start
        mock_logger.debug.assert_called_once_with(
            "operation_started", operation="test_operation", tag="value"
        )

        # Verify error log on exception
        mock_logger.error.assert_called_once_with(
            "operation_failed",
            operation="test_operation",
            duration_ms=750.0,
            status="error",
            error_type="ValueError",
            tag="value",
        )

        assert timer.elapsed_ms == 750.0

    @patch("jd_ingestion.utils.logging.datetime")
    def test_performance_timer_elapsed_ms_property(self, mock_datetime):
        """Test elapsed_ms property behavior."""
        mock_logger = Mock()
        timer = PerformanceTimer("test_operation", mock_logger)

        # Before starting
        assert timer.elapsed_ms == 0.0

        # During execution
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        current_time = datetime(2023, 1, 1, 12, 0, 0, 250000)  # 250ms later
        mock_datetime.utcnow.side_effect = [start_time, current_time]

        timer.start_time = start_time
        assert timer.elapsed_ms == 250.0

        # After completion
        timer._elapsed_ms = 500.0
        assert timer.elapsed_ms == 500.0


class TestHealthCheckLogging:
    """Test health check logging functionality."""

    @patch("jd_ingestion.utils.logging.get_logger")
    @patch("jd_ingestion.utils.logging.datetime")
    def test_setup_health_check_logging(self, mock_datetime, mock_get_logger):
        """Test health check logging setup and usage."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_datetime.utcnow.return_value.isoformat.return_value = "2023-01-01T12:00:00"

        log_component_health = setup_health_check_logging()

        # Verify logger was created
        mock_get_logger.assert_called_once_with("health_check")

        # Test logging component health without details
        log_component_health("database", "healthy")

        mock_logger.info.assert_called_with(
            "component_health",
            component="database",
            status="healthy",
            timestamp="2023-01-01T12:00:00",
        )

        # Test logging component health with details
        mock_logger.reset_mock()
        details = {"connection_time": 15.2, "query_count": 5}
        log_component_health("database", "degraded", details)

        mock_logger.info.assert_called_with(
            "component_health",
            component="database",
            status="degraded",
            timestamp="2023-01-01T12:00:00",
            details=details,
        )


class TestLoggingIntegration:
    """Test logging module integration scenarios."""

    @patch("jd_ingestion.utils.logging.settings")
    def test_logging_module_imports_settings_correctly(self, mock_settings):
        """Test that logging module correctly imports settings."""
        # Verify settings is accessible
        from jd_ingestion.utils.logging import settings as imported_settings

        assert imported_settings == mock_settings

    @patch("structlog.get_logger")
    def test_logger_creation_consistency(self, mock_get_logger):
        """Test that logger creation is consistent across functions."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Test different logger creation methods return same instance
        _logger1 = get_logger("test")
        _logger2 = get_task_logger("test_task")

        assert mock_get_logger.call_count == 2
        mock_get_logger.assert_any_call("test")
        mock_get_logger.assert_any_call("celery.task")

    def test_performance_timer_can_be_used_as_decorator(self):
        """Test that PerformanceTimer works correctly as a context manager."""
        mock_logger = Mock()

        # Should not raise any exceptions when used as context manager
        try:
            with PerformanceTimer("test_operation", mock_logger):
                # Simulate some work
                result = 2 + 2
            assert result == 4
        except Exception as e:
            pytest.fail(f"PerformanceTimer context manager failed: {e}")
