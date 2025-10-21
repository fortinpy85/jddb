import structlog
import logging
import logging.handlers
from typing import Any, Dict, MutableMapping, Optional, Union, cast
from pathlib import Path
from datetime import datetime
import sys
import os

from ..config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""

    # Create logs directory if it doesn't exist
    if settings.is_production or settings.is_staging:
        log_dir = Path("/app/logs") if settings.is_production else Path("./logs")
        log_dir.mkdir(exist_ok=True)

    # Configure stdlib logging with file handlers for production
    handlers: list[
        Union[logging.StreamHandler, logging.handlers.RotatingFileHandler]
    ] = []

    if settings.is_development or settings.debug:
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)
    else:
        # File handlers for production/staging/testing
        log_dir = Path("/app/logs") if settings.is_production else Path("./logs")
        log_dir.mkdir(exist_ok=True, parents=True)  # Ensure directory exists

        # Main application log
        main_handler = logging.handlers.RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=50 * 1024 * 1024,
            backupCount=10,  # 50MB
        )
        main_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(main_handler)

        # Error log
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / "error.log",
            maxBytes=50 * 1024 * 1024,
            backupCount=10,  # 50MB
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(error_handler)

        # Task log for Celery tasks
        task_handler = logging.handlers.RotatingFileHandler(
            log_dir / "tasks.log",
            maxBytes=50 * 1024 * 1024,
            backupCount=10,  # 50MB
        )
        task_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(task_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=handlers,
        format="%(message)s",
    )

    # Configure structlog processors based on environment
    processors: list[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add environment-specific context
    def add_context(
        logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        return {
            **event_dict,
            "environment": settings.environment,
            "service": "jd-ingestion",
            "pid": os.getpid(),
        }

    processors.append(add_context)

    # Choose renderer based on environment
    if settings.is_development and not settings.debug:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str, **initial_context: Any) -> structlog.BoundLogger:
    """Get a configured logger instance with optional initial context."""
    logger = structlog.get_logger(name)
    if initial_context:
        logger = logger.bind(**initial_context)
    return logger


def get_task_logger(
    task_name: str, task_id: Optional[str] = None
) -> structlog.BoundLogger:
    """Get a logger specifically configured for Celery tasks."""
    context = {"task_name": task_name}
    if task_id:
        context["task_id"] = task_id
    return get_logger("celery.task", **context)


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "ms",
    tags: Optional[Dict[str, Any]] = None,
    logger_name: str = "metrics",
) -> None:
    """Log a performance metric for monitoring systems to pick up."""
    logger = get_logger(logger_name)

    metric_data: Dict[str, Any] = {
        "metric_type": "performance",
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if tags:
        metric_data["tags"] = tags

    # Explicitly cast logger to Any to bypass MyPy's interpretation of structlog's dynamic info method
    # This is a common workaround for structlog with MyPy

    _metric_data: Dict[str, Any] = metric_data
    cast(Any, logger).info("performance_metric", **metric_data)  # type: ignore[call-arg]


def log_business_metric(
    metric_name: str,
    value: Any,
    metric_type: str = "counter",
    tags: Optional[Dict[str, Any]] = None,
    logger_name: str = "business_metrics",
) -> None:
    """Log a business metric (jobs processed, files uploaded, etc.)."""
    logger = get_logger(logger_name)

    metric_data: Dict[str, Any] = {
        "metric_type": "business",
        "metric_name": metric_name,
        "value": value,
        "type": metric_type,  # counter, gauge, histogram
        "timestamp": datetime.utcnow().isoformat(),
    }

    if tags:
        metric_data["tags"] = tags

    # Explicitly cast logger to Any to bypass MyPy's interpretation of structlog's dynamic info method
    # This is a common workaround for structlog with MyPy

    _metric_data: Dict[str, Any] = metric_data
    cast(Any, logger).info("business_metric", **metric_data)  # type: ignore[call-arg]


def log_error_with_context(
    logger: structlog.BoundLogger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """Log an error with rich context for debugging."""
    error_context: Dict[str, Any] = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if context:
        error_context["context"] = context
    if user_id:
        error_context["user_id"] = user_id
    if request_id:
        error_context["request_id"] = request_id

    logger.error("application_error", exc_info=True, **error_context)


class PerformanceTimer:
    """Context manager for timing operations and logging performance metrics."""

    def __init__(
        self,
        operation_name: str,
        logger: Optional[structlog.BoundLogger] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        self.operation_name = operation_name
        self.logger = logger or get_logger("performance")
        self.tags = tags or {}
        self.start_time: Optional[datetime] = None
        self._elapsed_ms = 0.0

    def __enter__(self) -> "PerformanceTimer":
        self.start_time = datetime.utcnow()
        self.logger.debug(
            "operation_started", operation=self.operation_name, **self.tags
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds() * 1000
            self._elapsed_ms = duration

            if exc_type is None:
                self.logger.info(
                    "operation_completed",
                    operation=self.operation_name,
                    duration_ms=duration,
                    status="success",
                    **self.tags,
                )
                log_performance_metric(
                    f"{self.operation_name}_duration", duration, "ms", self.tags
                )
            else:
                self.logger.error(
                    "operation_failed",
                    operation=self.operation_name,
                    duration_ms=duration,
                    status="error",
                    error_type=exc_type.__name__ if exc_type else None,
                    **self.tags,
                )

    @property
    def elapsed_ms(self) -> float:
        """Get the elapsed time in milliseconds."""
        if self.start_time is None:
            return 0.0
        if self._elapsed_ms > 0:
            return self._elapsed_ms
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000


def setup_health_check_logging() -> Any:
    """Configure logging specifically for health checks and monitoring."""
    health_logger = get_logger("health_check")

    def log_component_health(
        component: str, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        health_data: Dict[str, Any] = {
            "component": component,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if details:
            health_data["details"] = details

        health_logger.info("component_health", **health_data)

    return log_component_health


def redact_secret(value: str, show_last: int = 4) -> str:
    """Redact all but the last N characters of a secret value."""
    if not value or len(value) <= show_last:
        return "***"
    return f"***{value[-show_last:]}"
