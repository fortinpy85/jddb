"""Utility functions and helpers for the JD ingestion engine."""

from .error_handler import (
    ErrorHandler,
    RetryHandler,
    create_error_response,
    error_handler,
    handle_errors,
    retry_handler,
    retry_on_failure,
)
from .exceptions import (
    BusinessLogicException,
    ConfigurationException,
    DatabaseConnectionException,
    DatabaseException,
    DatabaseQueryException,
    ErrorCategory,
    ErrorSeverity,
    ExternalAPIException,
    FileCorruptedException,
    FileNotFoundException,
    FileProcessingException,
    FileValidationException,
    InsufficientPermissionsException,
    JDDBBaseException,
    MemoryException,
    OpenAIAPIException,
    RateLimitExceededException,
    SystemResourceException,
    ValidationException,
)

__all__ = [
    # Error handling utilities
    "ErrorHandler",
    "RetryHandler",
    "error_handler",
    "retry_handler",
    "handle_errors",
    "retry_on_failure",
    "create_error_response",
    # Exception classes
    "JDDBBaseException",
    "DatabaseException",
    "DatabaseConnectionException",
    "DatabaseQueryException",
    "ValidationException",
    "FileValidationException",
    "FileProcessingException",
    "FileNotFoundException",
    "FileCorruptedException",
    "ExternalAPIException",
    "OpenAIAPIException",
    "RateLimitExceededException",
    "BusinessLogicException",
    "InsufficientPermissionsException",
    "ConfigurationException",
    "SystemResourceException",
    "MemoryException",
    # Enums
    "ErrorCategory",
    "ErrorSeverity",
]
