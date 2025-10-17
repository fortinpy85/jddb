"""
Custom exception classes for the JDDB application.

This module provides a comprehensive set of custom exception classes with
structured error handling, contextual information, and error recovery guidance.
"""

import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException


class ErrorSeverity(str, Enum):
    """Error severity levels for categorization and response handling."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for better organization and handling."""

    DATABASE = "database"
    VALIDATION = "validation"
    EXTERNAL_API = "external_api"
    FILE_PROCESSING = "file_processing"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    CONFIGURATION = "configuration"


class JDDBBaseException(Exception):
    """
    Base exception class for all JDDB-specific exceptions.

    Provides structured error information with context, recovery suggestions,
    and detailed logging capabilities.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        recovery_suggestions: Optional[List[str]] = None,
        user_message: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)

        self.error_id = str(uuid4())
        self.timestamp = datetime.utcnow()
        self.message = message
        self.error_code = error_code or self._generate_error_code()
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        self.recovery_suggestions = recovery_suggestions or []
        self.user_message = user_message or self._generate_user_message()
        self.original_exception = original_exception
        self.stack_trace = traceback.format_exc() if original_exception else None

    def _generate_error_code(self) -> str:
        """Generate a default error code based on the exception class name."""
        class_name = self.__class__.__name__
        return f"JDDB_{class_name.upper().replace('EXCEPTION', '_ERROR')}"

    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        return "An error occurred while processing your request. Please try again."

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging and API responses."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "error_code": self.error_code,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "recoverable": self.recoverable,
            "recovery_suggestions": self.recovery_suggestions,
            "user_message": self.user_message,
            "original_exception": (
                str(self.original_exception) if self.original_exception else None
            ),
            "stack_trace": self.stack_trace,
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException with appropriate status code."""
        status_code = self._get_http_status_code()
        detail = {
            "error_id": self.error_id,
            "message": self.user_message,
            "error_code": self.error_code,
            "recoverable": self.recoverable,
            "recovery_suggestions": self.recovery_suggestions,
        }
        return HTTPException(status_code=status_code, detail=detail)

    def _get_http_status_code(self) -> int:
        """Determine appropriate HTTP status code based on exception type and severity."""
        if self.category == ErrorCategory.VALIDATION:
            return 400
        elif self.category == ErrorCategory.AUTHENTICATION:
            return 401
        elif self.category == ErrorCategory.AUTHORIZATION:
            return 403
        elif self.category == ErrorCategory.DATABASE and not self.recoverable:
            return 503
        elif self.severity == ErrorSeverity.CRITICAL:
            return 503
        else:
            return 500


# Database-related exceptions
class DatabaseException(JDDBBaseException):
    """Exceptions related to database operations."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, category=ErrorCategory.DATABASE, **kwargs)

    def _generate_user_message(self) -> str:
        return "A database error occurred. The issue has been logged and will be addressed shortly."


class DatabaseConnectionException(DatabaseException):
    """Database connection failures."""

    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            recovery_suggestions=[
                "Check database connection settings",
                "Verify database server is running",
                "Retry the operation in a few moments",
            ],
            **kwargs,
        )


class DatabaseQueryException(DatabaseException):
    """Database query execution failures."""

    def __init__(self, query: str, message: str = "Database query failed", **kwargs):
        context = kwargs.get("context", {})
        context["failed_query"] = query
        kwargs["context"] = context

        super().__init__(
            message=message,
            recovery_suggestions=[
                "Verify query syntax and parameters",
                "Check data constraints and foreign keys",
                "Retry with valid parameters",
            ],
            **kwargs,
        )


# Validation-related exceptions
class ValidationException(JDDBBaseException):
    """Exceptions related to data validation."""

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, List[str]]] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        context["field_errors"] = field_errors or {}
        kwargs["context"] = context

        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverable=True,
            **kwargs,
        )

    def _generate_user_message(self) -> str:
        return "Please check your input and correct any validation errors."


class FileValidationException(ValidationException):
    """File validation failures."""

    def __init__(self, file_path: str, validation_errors: List[str], **kwargs):
        context = kwargs.get("context", {})
        context.update(
            {
                "file_path": file_path,
                "validation_errors": validation_errors,
            }
        )
        kwargs["context"] = context

        super().__init__(
            message=f"File validation failed: {file_path}",
            recovery_suggestions=[
                "Check file format and structure",
                "Ensure file meets required specifications",
                "Verify file is not corrupted",
            ],
            **kwargs,
        )


# File processing exceptions
class FileProcessingException(JDDBBaseException):
    """Exceptions related to file processing operations."""

    def __init__(
        self, file_path: str, message: str = "File processing failed", **kwargs
    ):
        context = kwargs.get("context", {})
        context["file_path"] = file_path
        kwargs["context"] = context

        super().__init__(
            message=message, category=ErrorCategory.FILE_PROCESSING, **kwargs
        )

    def _generate_user_message(self) -> str:
        return "File processing failed. Please ensure the file is valid and try again."


class FileNotFoundException(FileProcessingException):
    """File not found errors."""

    def __init__(self, file_path: str, **kwargs):
        super().__init__(
            file_path=file_path,
            message=f"File not found: {file_path}",
            severity=ErrorSeverity.LOW,
            recoverable=True,
            recovery_suggestions=[
                "Verify the file path is correct",
                "Check if the file exists",
                "Ensure proper file permissions",
            ],
            **kwargs,
        )


class FileCorruptedException(FileProcessingException):
    """File corruption errors."""

    def __init__(
        self, file_path: str, corruption_details: Optional[str] = None, **kwargs
    ):
        context = kwargs.get("context", {})
        if corruption_details:
            context["corruption_details"] = corruption_details
        kwargs["context"] = context

        super().__init__(
            file_path=file_path,
            message=f"File is corrupted or unreadable: {file_path}",
            severity=ErrorSeverity.MEDIUM,
            recoverable=False,
            recovery_suggestions=[
                "Obtain a new copy of the file",
                "Check file integrity",
                "Contact the file provider",
            ],
            **kwargs,
        )


# External API exceptions
class ExternalAPIException(JDDBBaseException):
    """Exceptions related to external API calls."""

    def __init__(self, api_name: str, message: str, **kwargs):
        context = kwargs.get("context", {})
        context["api_name"] = api_name
        kwargs["context"] = context

        super().__init__(message=message, category=ErrorCategory.EXTERNAL_API, **kwargs)

    def _generate_user_message(self) -> str:
        return "An external service is currently unavailable. Please try again later."


class OpenAIAPIException(ExternalAPIException):
    """OpenAI API specific exceptions."""

    def __init__(self, message: str, api_response_code: Optional[int] = None, **kwargs):
        context = kwargs.get("context", {})
        if api_response_code:
            context["api_response_code"] = api_response_code
        kwargs["context"] = context

        super().__init__(
            api_name="OpenAI",
            message=message,
            recovery_suggestions=[
                "Check API key configuration",
                "Verify API quota and limits",
                "Retry after a brief delay",
                "Contact support if issue persists",
            ],
            **kwargs,
        )


class RateLimitExceededException(ExternalAPIException):
    """Rate limit exceeded for external APIs."""

    def __init__(self, api_name: str, retry_after: Optional[int] = None, **kwargs):
        context = kwargs.get("context", {})
        if retry_after:
            context["retry_after_seconds"] = retry_after
        kwargs["context"] = context

        super().__init__(
            api_name=api_name,
            message=f"Rate limit exceeded for {api_name}",
            severity=ErrorSeverity.MEDIUM,
            recoverable=True,
            recovery_suggestions=[
                (
                    f"Wait {retry_after} seconds before retrying"
                    if retry_after
                    else "Wait before retrying"
                ),
                "Implement exponential backoff",
                "Consider upgrading API plan",
            ],
            **kwargs,
        )


# Business logic exceptions
class BusinessLogicException(JDDBBaseException):
    """Exceptions related to business logic violations."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message, category=ErrorCategory.BUSINESS_LOGIC, **kwargs
        )

    def _generate_user_message(self) -> str:
        return "The operation could not be completed due to business rules."


class InsufficientPermissionsException(JDDBBaseException):
    """User lacks required permissions for operation."""

    def __init__(
        self, required_permission: str, user_id: Optional[str] = None, **kwargs
    ):
        context = kwargs.get("context", {})
        context.update(
            {
                "required_permission": required_permission,
                "user_id": user_id,
            }
        )
        kwargs["context"] = context

        super().__init__(
            message=f"Insufficient permissions: {required_permission}",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.LOW,
            recoverable=False,
            recovery_suggestions=[
                "Contact administrator for required permissions",
                "Verify user role and access rights",
            ],
            **kwargs,
        )

    def _get_http_status_code(self) -> int:
        return 403


# Configuration exceptions
class ConfigurationException(JDDBBaseException):
    """Exceptions related to system configuration."""

    def __init__(self, config_key: str, message: str, **kwargs):
        context = kwargs.get("context", {})
        context["config_key"] = config_key
        kwargs["context"] = context

        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverable=True,
            recovery_suggestions=[
                "Check configuration file settings",
                "Verify environment variables",
                "Contact system administrator",
            ],
            **kwargs,
        )

    def _generate_user_message(self) -> str:
        return "A configuration error occurred. Please contact support."


# System exceptions
class SystemResourceException(JDDBBaseException):
    """System resource-related exceptions."""

    def __init__(self, resource_type: str, message: str, **kwargs):
        context = kwargs.get("context", {})
        context["resource_type"] = resource_type
        kwargs["context"] = context

        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs,
        )

    def _generate_user_message(self) -> str:
        return "System resources are currently limited. Please try again later."


class DiskSpaceException(SystemResourceException):
    """Insufficient disk space errors."""

    def __init__(
        self,
        available_space: Optional[int] = None,
        required_space: Optional[int] = None,
        **kwargs,
    ):
        context = kwargs.get("context", {})
        if available_space is not None:
            context["available_space_bytes"] = available_space
        if required_space is not None:
            context["required_space_bytes"] = required_space
        kwargs["context"] = context

        super().__init__(
            resource_type="disk_space",
            message="Insufficient disk space",
            recoverable=True,
            recovery_suggestions=[
                "Free up disk space",
                "Contact administrator to increase storage",
                "Move files to alternative storage",
            ],
            **kwargs,
        )


class MemoryException(SystemResourceException):
    """Memory-related exceptions."""

    def __init__(self, operation: str, **kwargs):
        context = kwargs.get("context", {})
        context["operation"] = operation
        kwargs["context"] = context

        # Set other parameters in kwargs (severity is set by parent)
        kwargs["recoverable"] = True
        kwargs["recovery_suggestions"] = [
            "Reduce batch size or chunk size",
            "Process data in smaller segments",
            "Restart the service",
            "Contact administrator to increase memory allocation",
        ]

        super().__init__(
            resource_type="memory",
            message=f"Insufficient memory for operation: {operation}",
            **kwargs,
        )
