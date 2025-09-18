"""
Enhanced error handling utilities with structured logging and recovery mechanisms.

This module provides comprehensive error handling patterns, structured logging,
and automatic error recovery mechanisms for the JDDB application.
"""

import asyncio
import functools
import traceback
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from fastapi import HTTPException, Request
from sqlalchemy.exc import (
    DatabaseError,
    DisconnectionError,
    IntegrityError,
    OperationalError,
    SQLAlchemyError,
)

from .exceptions import (
    BusinessLogicException,
    ConfigurationException,
    DatabaseConnectionException,
    DatabaseException,
    DatabaseQueryException,
    ExternalAPIException,
    FileProcessingException,
    JDDBBaseException,
    MemoryException,
    OpenAIAPIException,
    RateLimitExceededException,
    SystemResourceException,
    ValidationException,
)
from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class ErrorHandler:
    """
    Centralized error handling with structured logging and recovery mechanisms.

    Provides consistent error handling patterns across the application with
    automatic logging, error categorization, and recovery suggestions.
    """

    def __init__(self):
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {},
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }

    async def handle_async_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        raise_http: bool = True,
    ) -> Optional[JDDBBaseException]:
        """
        Handle exceptions in async contexts with structured logging and conversion.

        Args:
            exception: The exception to handle
            context: Additional context information
            raise_http: Whether to raise HTTPException for API endpoints

        Returns:
            Converted JDDB exception or None if HTTP exception was raised
        """
        jddb_exception = self._convert_to_jddb_exception(exception, context)
        await self._log_exception(jddb_exception)
        self._update_error_stats(jddb_exception)

        if raise_http and hasattr(jddb_exception, "to_http_exception"):
            raise jddb_exception.to_http_exception()

        return jddb_exception

    def handle_sync_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        raise_http: bool = True,
    ) -> Optional[JDDBBaseException]:
        """
        Handle exceptions in synchronous contexts.

        Args:
            exception: The exception to handle
            context: Additional context information
            raise_http: Whether to raise HTTPException for API endpoints

        Returns:
            Converted JDDB exception or None if HTTP exception was raised
        """
        jddb_exception = self._convert_to_jddb_exception(exception, context)
        self._log_exception_sync(jddb_exception)
        self._update_error_stats(jddb_exception)

        if raise_http and hasattr(jddb_exception, "to_http_exception"):
            raise jddb_exception.to_http_exception()

        return jddb_exception

    def _convert_to_jddb_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> JDDBBaseException:
        """Convert standard exceptions to JDDB exceptions with context."""
        if isinstance(exception, JDDBBaseException):
            # Already a JDDB exception, just add context if provided
            if context:
                exception.context.update(context)
            return exception

        # Convert SQLAlchemy exceptions
        if isinstance(exception, (DisconnectionError, OperationalError)):
            return DatabaseConnectionException(
                message=str(exception),
                context=context,
                original_exception=exception,
            )
        elif isinstance(exception, IntegrityError):
            return DatabaseQueryException(
                query=getattr(exception, "statement", "Unknown"),
                message=f"Database integrity constraint violation: {str(exception)}",
                context=context,
                original_exception=exception,
            )
        elif isinstance(exception, SQLAlchemyError):
            return DatabaseException(
                message=f"Database operation failed: {str(exception)}",
                context=context,
                original_exception=exception,
            )

        # Convert file-related exceptions
        elif isinstance(exception, FileNotFoundError):
            return FileProcessingException(
                file_path=getattr(exception, "filename", "Unknown"),
                message=str(exception),
                context=context,
                original_exception=exception,
            )
        elif isinstance(exception, PermissionError):
            return FileProcessingException(
                file_path=getattr(exception, "filename", "Unknown"),
                message=f"Permission denied: {str(exception)}",
                context=context,
                original_exception=exception,
            )

        # Convert memory-related exceptions
        elif isinstance(exception, MemoryError):
            return MemoryException(
                operation=context.get("operation", "Unknown") if context else "Unknown",
                context=context,
                original_exception=exception,
            )

        # Convert validation exceptions
        elif isinstance(exception, ValueError):
            return ValidationException(
                message=str(exception),
                context=context,
                original_exception=exception,
            )

        # Default conversion for unknown exceptions
        else:
            return JDDBBaseException(
                message=f"Unexpected error: {str(exception)}",
                context=context,
                original_exception=exception,
            )

    async def _log_exception(self, exception: JDDBBaseException) -> None:
        """Log exception with structured information asynchronously."""
        error_data = exception.to_dict()

        # Use appropriate log level based on severity
        if exception.severity.value == "critical":
            logger.critical("Critical error occurred", **error_data)
        elif exception.severity.value == "high":
            logger.error("High severity error occurred", **error_data)
        elif exception.severity.value == "medium":
            logger.warning("Medium severity error occurred", **error_data)
        else:
            logger.info("Low severity error occurred", **error_data)

    def _log_exception_sync(self, exception: JDDBBaseException) -> None:
        """Log exception with structured information synchronously."""
        error_data = exception.to_dict()

        # Use appropriate log level based on severity
        if exception.severity.value == "critical":
            logger.critical("Critical error occurred", **error_data)
        elif exception.severity.value == "high":
            logger.error("High severity error occurred", **error_data)
        elif exception.severity.value == "medium":
            logger.warning("Medium severity error occurred", **error_data)
        else:
            logger.info("Low severity error occurred", **error_data)

    def _update_error_stats(self, exception: JDDBBaseException) -> None:
        """Update error statistics for monitoring and reporting."""
        self.error_stats["total_errors"] += 1

        category = exception.category.value
        self.error_stats["by_category"][category] = (
            self.error_stats["by_category"].get(category, 0) + 1
        )

        severity = exception.severity.value
        self.error_stats["by_severity"][severity] = (
            self.error_stats["by_severity"].get(severity, 0) + 1
        )

    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics."""
        return self.error_stats.copy()

    @asynccontextmanager
    async def async_error_context(
        self,
        operation_name: str,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ):
        """
        Async context manager for handling errors in operations.

        Args:
            operation_name: Name of the operation for logging
            context: Additional context information
            raise_on_error: Whether to re-raise exceptions
        """
        operation_context = {"operation": operation_name}
        if context:
            operation_context.update(context)

        try:
            logger.info(f"Starting operation: {operation_name}", **operation_context)
            yield
            logger.info(f"Operation completed successfully: {operation_name}")
        except Exception as e:
            logger.error(f"Operation failed: {operation_name}", error=str(e))
            if raise_on_error:
                await self.handle_async_exception(e, operation_context)
            else:
                await self.handle_async_exception(
                    e, operation_context, raise_http=False
                )

    @contextmanager
    def sync_error_context(
        self,
        operation_name: str,
        context: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
    ):
        """
        Synchronous context manager for handling errors in operations.

        Args:
            operation_name: Name of the operation for logging
            context: Additional context information
            raise_on_error: Whether to re-raise exceptions
        """
        operation_context = {"operation": operation_name}
        if context:
            operation_context.update(context)

        try:
            logger.info(f"Starting operation: {operation_name}", **operation_context)
            yield
            logger.info(f"Operation completed successfully: {operation_name}")
        except Exception as e:
            logger.error(f"Operation failed: {operation_name}", error=str(e))
            if raise_on_error:
                self.handle_sync_exception(e, operation_context)
            else:
                self.handle_sync_exception(e, operation_context, raise_http=False)


class RetryHandler:
    """
    Retry mechanism with exponential backoff and error recovery.

    Provides configurable retry logic for operations that may fail temporarily,
    with different strategies for different types of errors.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base

    async def retry_async(
        self,
        func: Callable[..., T],
        *args,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> T:
        """
        Retry an async function with exponential backoff.

        Args:
            func: The async function to retry
            *args: Arguments for the function
            retryable_exceptions: List of exception types that should trigger retry
            context: Additional context for logging
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            The last exception if all retries fail
        """
        if retryable_exceptions is None:
            retryable_exceptions = [
                DatabaseConnectionException,
                ExternalAPIException,
                RateLimitExceededException,
                SystemResourceException,
            ]

        last_exception = None
        operation_name = func.__name__ if hasattr(func, "__name__") else "unknown"

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = min(
                        self.base_delay * (self.exponential_base ** (attempt - 1)),
                        self.max_delay,
                    )
                    logger.info(
                        f"Retrying {operation_name} (attempt {attempt + 1}/{self.max_retries + 1}) "
                        f"after {delay:.2f}s delay",
                        context=context or {},
                    )
                    await asyncio.sleep(delay)

                result = await func(*args, **kwargs)

                if attempt > 0:
                    logger.info(
                        f"Operation {operation_name} succeeded on attempt {attempt + 1}",
                        context=context or {},
                    )
                    error_handler.error_stats["successful_recoveries"] += 1

                return result

            except Exception as e:
                last_exception = e
                error_handler.error_stats["recovery_attempts"] += 1

                # Check if this exception type is retryable
                if not any(
                    isinstance(e, exc_type) for exc_type in retryable_exceptions
                ):
                    logger.warning(
                        f"Non-retryable exception in {operation_name}: {type(e).__name__}",
                        error=str(e),
                        context=context or {},
                    )
                    raise e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Retryable error in {operation_name} (attempt {attempt + 1}): {str(e)}",
                        context=context or {},
                    )
                else:
                    logger.error(
                        f"All retry attempts exhausted for {operation_name}",
                        error=str(e),
                        context=context or {},
                    )

        # All retries exhausted, raise the last exception
        if last_exception:
            raise last_exception

    def retry_sync(
        self,
        func: Callable[..., T],
        *args,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> T:
        """
        Retry a synchronous function with exponential backoff.

        Args:
            func: The function to retry
            *args: Arguments for the function
            retryable_exceptions: List of exception types that should trigger retry
            context: Additional context for logging
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            The last exception if all retries fail
        """
        import time

        if retryable_exceptions is None:
            retryable_exceptions = [
                DatabaseConnectionException,
                ExternalAPIException,
                RateLimitExceededException,
                SystemResourceException,
            ]

        last_exception = None
        operation_name = func.__name__ if hasattr(func, "__name__") else "unknown"

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = min(
                        self.base_delay * (self.exponential_base ** (attempt - 1)),
                        self.max_delay,
                    )
                    logger.info(
                        f"Retrying {operation_name} (attempt {attempt + 1}/{self.max_retries + 1}) "
                        f"after {delay:.2f}s delay",
                        context=context or {},
                    )
                    time.sleep(delay)

                result = func(*args, **kwargs)

                if attempt > 0:
                    logger.info(
                        f"Operation {operation_name} succeeded on attempt {attempt + 1}",
                        context=context or {},
                    )
                    error_handler.error_stats["successful_recoveries"] += 1

                return result

            except Exception as e:
                last_exception = e
                error_handler.error_stats["recovery_attempts"] += 1

                # Check if this exception type is retryable
                if not any(
                    isinstance(e, exc_type) for exc_type in retryable_exceptions
                ):
                    logger.warning(
                        f"Non-retryable exception in {operation_name}: {type(e).__name__}",
                        error=str(e),
                        context=context or {},
                    )
                    raise e

                if attempt < self.max_retries:
                    logger.warning(
                        f"Retryable error in {operation_name} (attempt {attempt + 1}): {str(e)}",
                        context=context or {},
                    )
                else:
                    logger.error(
                        f"All retry attempts exhausted for {operation_name}",
                        error=str(e),
                        context=context or {},
                    )

        # All retries exhausted, raise the last exception
        if last_exception:
            raise last_exception


# Global instances
error_handler = ErrorHandler()
retry_handler = RetryHandler()


def handle_errors(
    raise_on_error: bool = True,
    context: Optional[Dict[str, Any]] = None,
    operation_name: Optional[str] = None,
):
    """
    Decorator for automatic error handling in functions and methods.

    Args:
        raise_on_error: Whether to re-raise exceptions as HTTP exceptions
        context: Additional context for error logging
        operation_name: Name of the operation (defaults to function name)
    """

    def decorator(func: F) -> F:
        op_name = operation_name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with error_handler.async_error_context(
                    op_name, context, raise_on_error
                ):
                    return await func(*args, **kwargs)

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with error_handler.sync_error_context(op_name, context, raise_on_error):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        retryable_exceptions: List of exception types that should trigger retry
        context: Additional context for logging
    """

    def decorator(func: F) -> F:
        local_retry_handler = RetryHandler(
            max_retries=max_retries, base_delay=base_delay
        )

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await local_retry_handler.retry_async(
                    func,
                    *args,
                    retryable_exceptions=retryable_exceptions,
                    context=context,
                    **kwargs,
                )

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return local_retry_handler.retry_sync(
                    func,
                    *args,
                    retryable_exceptions=retryable_exceptions,
                    context=context,
                    **kwargs,
                )

            return sync_wrapper

    return decorator


async def create_error_response(
    request: Request, exception: Exception
) -> Dict[str, Any]:
    """
    Create a standardized error response for API endpoints.

    Args:
        request: FastAPI request object
        exception: The exception that occurred

    Returns:
        Standardized error response dictionary
    """
    context = {
        "url": str(request.url),
        "method": request.method,
        "client_ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow().isoformat(),
    }

    jddb_exception = error_handler._convert_to_jddb_exception(exception, context)
    await error_handler._log_exception(jddb_exception)
    error_handler._update_error_stats(jddb_exception)

    return {
        "error": {
            "id": jddb_exception.error_id,
            "message": jddb_exception.user_message,
            "code": jddb_exception.error_code,
            "category": jddb_exception.category.value,
            "recoverable": jddb_exception.recoverable,
            "recovery_suggestions": jddb_exception.recovery_suggestions,
            "timestamp": jddb_exception.timestamp.isoformat(),
        }
    }
