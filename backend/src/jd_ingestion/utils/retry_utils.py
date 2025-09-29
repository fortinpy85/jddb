"""
Retry utilities for Celery tasks.

This module provides shared logic for determining if errors are retryable
across different task types.
"""


def is_retryable_error(exc: Exception) -> bool:
    """
    Determine if an exception should trigger a task retry.

    Args:
        exc: The exception that occurred

    Returns:
        True if the error is retryable, False otherwise
    """
    # Non-retryable errors (permanent failures)
    non_retryable_errors = (
        FileNotFoundError,  # File doesn't exist
        PermissionError,  # Permission denied
        ValueError,  # Invalid data/parameters
        TypeError,  # Type mismatches
        KeyError,  # Missing required data
    )

    if isinstance(exc, non_retryable_errors):
        return False

    # Retryable errors (temporary failures)
    retryable_errors = (
        ConnectionError,  # Network/database connection issues
        TimeoutError,  # Operation timeouts
        OSError,  # I/O errors
        ImportError,  # Module loading issues
        RuntimeError,  # General runtime issues
    )

    if isinstance(exc, retryable_errors):
        return True

    # Check error message for specific patterns (especially for OpenAI API and services)
    error_message = str(exc).lower()
    retryable_patterns = [
        "connection",
        "timeout",
        "temporary",
        "rate limit",
        "service unavailable",
        "internal server error",
        "database",
        "network",
        "redis",
        "celery",
        "openai",
        "api",
        "quota",
        "token",
        "embedding",
        "server error",
        "bad gateway",
        "service timeout",
    ]

    for pattern in retryable_patterns:
        if pattern in error_message:
            return True

    # Default to non-retryable for safety
    return False
