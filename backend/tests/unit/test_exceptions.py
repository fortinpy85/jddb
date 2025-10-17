"""
Tests for custom exception classes.
"""

from datetime import datetime
from unittest.mock import patch
from fastapi import HTTPException

from jd_ingestion.utils.exceptions import (
    ErrorSeverity,
    ErrorCategory,
    JDDBBaseException,
    DatabaseException,
    DatabaseConnectionException,
    DatabaseQueryException,
    ValidationException,
    FileValidationException,
    FileProcessingException,
    FileNotFoundException,
    FileCorruptedException,
    ExternalAPIException,
    OpenAIAPIException,
    RateLimitExceededException,
    BusinessLogicException,
    InsufficientPermissionsException,
    ConfigurationException,
    SystemResourceException,
    DiskSpaceException,
    MemoryException,
)


class TestErrorEnums:
    """Test error severity and category enums."""

    def test_error_severity_values(self):
        """Test error severity enum values."""
        assert ErrorSeverity.LOW == "low"
        assert ErrorSeverity.MEDIUM == "medium"
        assert ErrorSeverity.HIGH == "high"
        assert ErrorSeverity.CRITICAL == "critical"

    def test_error_category_values(self):
        """Test error category enum values."""
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.EXTERNAL_API == "external_api"
        assert ErrorCategory.FILE_PROCESSING == "file_processing"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.AUTHORIZATION == "authorization"
        assert ErrorCategory.BUSINESS_LOGIC == "business_logic"
        assert ErrorCategory.SYSTEM == "system"
        assert ErrorCategory.NETWORK == "network"
        assert ErrorCategory.CONFIGURATION == "configuration"


class TestJDDBBaseException:
    """Test base exception class functionality."""

    def test_base_exception_creation_minimal(self):
        """Test base exception with minimal parameters."""
        exc = JDDBBaseException("Test error message")

        assert exc.message == "Test error message"
        assert exc.category == ErrorCategory.SYSTEM
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.recoverable is True
        assert isinstance(exc.error_id, str)
        assert len(exc.error_id) == 36  # UUID4 length
        assert isinstance(exc.timestamp, datetime)
        assert exc.context == {}
        assert exc.recovery_suggestions == []

    def test_base_exception_creation_full(self):
        """Test base exception with all parameters."""
        context = {"user_id": "123", "operation": "test_op"}
        recovery_suggestions = ["Try again", "Contact support"]

        exc = JDDBBaseException(
            message="Detailed error message",
            error_code="CUSTOM_ERROR_001",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            context=context,
            recoverable=False,
            recovery_suggestions=recovery_suggestions,
            user_message="Please check your input",
            original_exception=ValueError("Original error"),
        )

        assert exc.message == "Detailed error message"
        assert exc.error_code == "CUSTOM_ERROR_001"
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.context == context
        assert exc.recoverable is False
        assert exc.recovery_suggestions == recovery_suggestions
        assert exc.user_message == "Please check your input"
        assert isinstance(exc.original_exception, ValueError)

    def test_error_code_generation(self):
        """Test automatic error code generation."""
        exc = JDDBBaseException("Test message")
        assert exc.error_code == "JDDB_JDDBBASE_ERROR"

        class CustomTestException(JDDBBaseException):
            pass

        custom_exc = CustomTestException("Custom test")
        assert custom_exc.error_code == "JDDB_CUSTOMTEST_ERROR"

    def test_user_message_generation(self):
        """Test automatic user message generation."""
        exc = JDDBBaseException("Technical error message")
        assert (
            exc.user_message
            == "An error occurred while processing your request. Please try again."
        )

    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        original_exception = ValueError("Original error")
        context = {"test_key": "test_value"}

        exc = JDDBBaseException(
            message="Test message",
            error_code="TEST_001",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context=context,
            recoverable=False,
            recovery_suggestions=["Suggestion 1"],
            user_message="User friendly message",
            original_exception=original_exception,
        )

        result = exc.to_dict()

        assert result["error_id"] == exc.error_id
        assert result["message"] == "Test message"
        assert result["error_code"] == "TEST_001"
        assert result["category"] == "database"
        assert result["severity"] == "high"
        assert result["context"] == context
        assert result["recoverable"] is False
        assert result["recovery_suggestions"] == ["Suggestion 1"]
        assert result["user_message"] == "User friendly message"
        assert result["original_exception"] == "Original error"
        assert "timestamp" in result

    def test_http_status_code_determination(self):
        """Test HTTP status code determination logic."""
        # Validation error
        exc = JDDBBaseException("Test", category=ErrorCategory.VALIDATION)
        assert exc._get_http_status_code() == 400

        # Authentication error
        exc = JDDBBaseException("Test", category=ErrorCategory.AUTHENTICATION)
        assert exc._get_http_status_code() == 401

        # Authorization error
        exc = JDDBBaseException("Test", category=ErrorCategory.AUTHORIZATION)
        assert exc._get_http_status_code() == 403

        # Non-recoverable database error
        exc = JDDBBaseException(
            "Test", category=ErrorCategory.DATABASE, recoverable=False
        )
        assert exc._get_http_status_code() == 503

        # Critical severity
        exc = JDDBBaseException("Test", severity=ErrorSeverity.CRITICAL)
        assert exc._get_http_status_code() == 503

        # Default case
        exc = JDDBBaseException("Test", category=ErrorCategory.SYSTEM)
        assert exc._get_http_status_code() == 500

    def test_to_http_exception_conversion(self):
        """Test conversion to FastAPI HTTPException."""
        exc = JDDBBaseException(
            message="Test message",
            error_code="TEST_001",
            category=ErrorCategory.VALIDATION,
            recovery_suggestions=["Check input"],
        )

        http_exc = exc.to_http_exception()

        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 400
        assert http_exc.detail["error_id"] == exc.error_id
        assert http_exc.detail["error_code"] == "TEST_001"
        assert http_exc.detail["recoverable"] is True
        assert http_exc.detail["recovery_suggestions"] == ["Check input"]


class TestDatabaseExceptions:
    """Test database-related exceptions."""

    def test_database_exception_creation(self):
        """Test DatabaseException creation."""
        exc = DatabaseException("Database error occurred")

        assert exc.message == "Database error occurred"
        assert exc.category == ErrorCategory.DATABASE
        assert (
            exc.user_message
            == "A database error occurred. The issue has been logged and will be addressed shortly."
        )

    def test_database_connection_exception(self):
        """Test DatabaseConnectionException specifics."""
        exc = DatabaseConnectionException()

        assert exc.message == "Database connection failed"
        assert exc.category == ErrorCategory.DATABASE
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.recoverable is True
        assert "Check database connection settings" in exc.recovery_suggestions
        assert len(exc.recovery_suggestions) == 3

    def test_database_connection_exception_custom_message(self):
        """Test DatabaseConnectionException with custom message."""
        exc = DatabaseConnectionException("Connection timeout")

        assert exc.message == "Connection timeout"
        assert exc.category == ErrorCategory.DATABASE

    def test_database_query_exception(self):
        """Test DatabaseQueryException with query context."""
        query = "SELECT * FROM users WHERE id = %s"
        exc = DatabaseQueryException(query=query, message="Query execution failed")

        assert exc.message == "Query execution failed"
        assert exc.context["failed_query"] == query
        assert "Verify query syntax and parameters" in exc.recovery_suggestions


class TestValidationExceptions:
    """Test validation-related exceptions."""

    def test_validation_exception_basic(self):
        """Test basic ValidationException creation."""
        exc = ValidationException("Validation failed")

        assert exc.message == "Validation failed"
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.severity == ErrorSeverity.LOW
        assert exc.recoverable is True
        assert (
            exc.user_message
            == "Please check your input and correct any validation errors."
        )

    def test_validation_exception_with_field_errors(self):
        """Test ValidationException with field errors."""
        field_errors = {
            "email": ["Invalid email format", "Email already exists"],
            "password": ["Password too short"],
        }

        exc = ValidationException(
            "Multiple validation errors", field_errors=field_errors
        )

        assert exc.context["field_errors"] == field_errors

    def test_file_validation_exception(self):
        """Test FileValidationException specifics."""
        file_path = "/path/to/file.txt"
        validation_errors = ["Missing header", "Invalid format"]

        exc = FileValidationException(
            file_path=file_path, validation_errors=validation_errors
        )

        assert exc.message == f"File validation failed: {file_path}"
        assert exc.context["file_path"] == file_path
        assert exc.context["validation_errors"] == validation_errors
        assert "Check file format and structure" in exc.recovery_suggestions


class TestFileProcessingExceptions:
    """Test file processing related exceptions."""

    def test_file_processing_exception_basic(self):
        """Test FileProcessingException creation."""
        file_path = "/path/to/file.txt"
        exc = FileProcessingException(file_path=file_path, message="Processing failed")

        assert exc.message == "Processing failed"
        assert exc.category == ErrorCategory.FILE_PROCESSING
        assert exc.context["file_path"] == file_path
        assert (
            exc.user_message
            == "File processing failed. Please ensure the file is valid and try again."
        )

    def test_file_not_found_exception(self):
        """Test FileNotFoundException specifics."""
        file_path = "/nonexistent/file.txt"
        exc = FileNotFoundException(file_path=file_path)

        assert exc.message == f"File not found: {file_path}"
        assert exc.context["file_path"] == file_path
        assert exc.severity == ErrorSeverity.LOW
        assert exc.recoverable is True
        assert "Verify the file path is correct" in exc.recovery_suggestions

    def test_file_corrupted_exception(self):
        """Test FileCorruptedException specifics."""
        file_path = "/path/to/corrupted.txt"
        corruption_details = "Invalid file header"

        exc = FileCorruptedException(
            file_path=file_path, corruption_details=corruption_details
        )

        assert exc.message == f"File is corrupted or unreadable: {file_path}"
        assert exc.context["corruption_details"] == corruption_details
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.recoverable is False
        assert "Obtain a new copy of the file" in exc.recovery_suggestions

    def test_file_corrupted_exception_no_details(self):
        """Test FileCorruptedException without corruption details."""
        file_path = "/path/to/corrupted.txt"
        exc = FileCorruptedException(file_path=file_path)

        assert exc.context["file_path"] == file_path
        assert "corruption_details" not in exc.context


class TestExternalAPIExceptions:
    """Test external API related exceptions."""

    def test_external_api_exception_basic(self):
        """Test ExternalAPIException creation."""
        exc = ExternalAPIException(api_name="TestAPI", message="API call failed")

        assert exc.message == "API call failed"
        assert exc.category == ErrorCategory.EXTERNAL_API
        assert exc.context["api_name"] == "TestAPI"
        assert (
            exc.user_message
            == "An external service is currently unavailable. Please try again later."
        )

    def test_openai_api_exception(self):
        """Test OpenAIAPIException specifics."""
        exc = OpenAIAPIException(message="API quota exceeded", api_response_code=429)

        assert exc.message == "API quota exceeded"
        assert exc.context["api_name"] == "OpenAI"
        assert exc.context["api_response_code"] == 429
        assert "Check API key configuration" in exc.recovery_suggestions

    def test_openai_api_exception_no_response_code(self):
        """Test OpenAIAPIException without response code."""
        exc = OpenAIAPIException(message="API error")

        assert exc.context["api_name"] == "OpenAI"
        assert "api_response_code" not in exc.context

    def test_rate_limit_exceeded_exception(self):
        """Test RateLimitExceededException specifics."""
        api_name = "TestAPI"
        retry_after = 60

        exc = RateLimitExceededException(api_name=api_name, retry_after=retry_after)

        assert exc.message == f"Rate limit exceeded for {api_name}"
        assert exc.context["api_name"] == api_name
        assert exc.context["retry_after_seconds"] == retry_after
        assert exc.severity == ErrorSeverity.MEDIUM
        assert exc.recoverable is True
        assert "Wait 60 seconds before retrying" in exc.recovery_suggestions

    def test_rate_limit_exceeded_exception_no_retry_after(self):
        """Test RateLimitExceededException without retry_after."""
        exc = RateLimitExceededException(api_name="TestAPI")

        assert "retry_after_seconds" not in exc.context
        assert "Wait before retrying" in exc.recovery_suggestions


class TestBusinessLogicExceptions:
    """Test business logic related exceptions."""

    def test_business_logic_exception_basic(self):
        """Test BusinessLogicException creation."""
        exc = BusinessLogicException("Business rule violation")

        assert exc.message == "Business rule violation"
        assert exc.category == ErrorCategory.BUSINESS_LOGIC
        assert (
            exc.user_message
            == "The operation could not be completed due to business rules."
        )

    def test_insufficient_permissions_exception(self):
        """Test InsufficientPermissionsException specifics."""
        required_permission = "admin_access"
        user_id = "user123"

        exc = InsufficientPermissionsException(
            required_permission=required_permission, user_id=user_id
        )

        assert exc.message == f"Insufficient permissions: {required_permission}"
        assert exc.category == ErrorCategory.AUTHORIZATION
        assert exc.context["required_permission"] == required_permission
        assert exc.context["user_id"] == user_id
        assert exc.severity == ErrorSeverity.LOW
        assert exc.recoverable is False
        assert exc._get_http_status_code() == 403

    def test_insufficient_permissions_exception_no_user(self):
        """Test InsufficientPermissionsException without user_id."""
        exc = InsufficientPermissionsException(required_permission="admin_access")

        assert exc.context["required_permission"] == "admin_access"
        assert exc.context["user_id"] is None


class TestConfigurationExceptions:
    """Test configuration related exceptions."""

    def test_configuration_exception(self):
        """Test ConfigurationException creation."""
        config_key = "database.url"
        exc = ConfigurationException(
            config_key=config_key, message="Invalid database URL"
        )

        assert exc.message == "Invalid database URL"
        assert exc.category == ErrorCategory.CONFIGURATION
        assert exc.context["config_key"] == config_key
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.recoverable is True
        assert "Check configuration file settings" in exc.recovery_suggestions
        assert (
            exc.user_message
            == "A configuration error occurred. Please contact support."
        )


class TestSystemResourceExceptions:
    """Test system resource related exceptions."""

    def test_system_resource_exception_basic(self):
        """Test SystemResourceException creation."""
        resource_type = "cpu"
        exc = SystemResourceException(
            resource_type=resource_type, message="High CPU usage"
        )

        assert exc.message == "High CPU usage"
        assert exc.category == ErrorCategory.SYSTEM
        assert exc.context["resource_type"] == resource_type
        assert exc.severity == ErrorSeverity.HIGH
        assert (
            exc.user_message
            == "System resources are currently limited. Please try again later."
        )

    def test_disk_space_exception(self):
        """Test DiskSpaceException specifics."""
        available_space = 100 * 1024 * 1024  # 100MB
        required_space = 500 * 1024 * 1024  # 500MB

        exc = DiskSpaceException(
            available_space=available_space, required_space=required_space
        )

        assert exc.message == "Insufficient disk space"
        assert exc.context["resource_type"] == "disk_space"
        assert exc.context["available_space_bytes"] == available_space
        assert exc.context["required_space_bytes"] == required_space
        assert exc.recoverable is True
        assert "Free up disk space" in exc.recovery_suggestions

    def test_disk_space_exception_no_sizes(self):
        """Test DiskSpaceException without size information."""
        exc = DiskSpaceException()

        assert exc.message == "Insufficient disk space"
        assert "available_space_bytes" not in exc.context
        assert "required_space_bytes" not in exc.context

    def test_memory_exception(self):
        """Test MemoryException specifics."""
        operation = "large_file_processing"
        exc = MemoryException(operation=operation)

        assert exc.message == f"Insufficient memory for operation: {operation}"
        assert exc.context["resource_type"] == "memory"
        assert exc.context["operation"] == operation
        assert exc.severity == ErrorSeverity.HIGH
        assert exc.recoverable is True
        assert "Reduce batch size or chunk size" in exc.recovery_suggestions


class TestExceptionInheritance:
    """Test exception inheritance and method overrides."""

    def test_inheritance_chain(self):
        """Test that all exceptions inherit from JDDBBaseException."""
        exceptions_to_test = [
            DatabaseException,
            DatabaseConnectionException,
            DatabaseQueryException,
            ValidationException,
            FileValidationException,
            FileProcessingException,
            FileNotFoundException,
            FileCorruptedException,
            ExternalAPIException,
            OpenAIAPIException,
            RateLimitExceededException,
            BusinessLogicException,
            InsufficientPermissionsException,
            ConfigurationException,
            SystemResourceException,
            DiskSpaceException,
            MemoryException,
        ]

        for exception_class in exceptions_to_test:
            # Create instance with minimal parameters
            if exception_class == DatabaseQueryException:
                exc = exception_class(query="SELECT 1", message="Test")
            elif exception_class == FileValidationException:
                exc = exception_class(
                    file_path="/test/path", validation_errors=["Test error"]
                )
            elif exception_class in [
                FileProcessingException,
                FileNotFoundException,
                FileCorruptedException,
            ]:
                exc = exception_class(file_path="/test/path")
            elif exception_class in [
                ExternalAPIException,
                OpenAIAPIException,
                RateLimitExceededException,
            ]:
                if exception_class == ExternalAPIException:
                    exc = exception_class(api_name="TestAPI", message="Test")
                elif exception_class == OpenAIAPIException:
                    exc = exception_class(message="Test")
                else:  # RateLimitExceededException
                    exc = exception_class(api_name="TestAPI")
            elif exception_class == InsufficientPermissionsException:
                exc = exception_class(required_permission="test_permission")
            elif exception_class == ConfigurationException:
                exc = exception_class(config_key="test.key", message="Test")
            elif exception_class in [
                SystemResourceException,
                DiskSpaceException,
                MemoryException,
            ]:
                if exception_class == SystemResourceException:
                    exc = exception_class(resource_type="test", message="Test")
                elif exception_class == MemoryException:
                    exc = exception_class(operation="test_operation")
                else:  # DiskSpaceException
                    exc = exception_class()
            else:
                exc = exception_class("Test message")

            assert isinstance(exc, JDDBBaseException)
            assert isinstance(exc, Exception)

    def test_method_overrides(self):
        """Test that subclasses properly override methods."""
        # Test user message override
        db_exc = DatabaseException("Test")
        assert "database error occurred" in db_exc.user_message.lower()

        validation_exc = ValidationException("Test")
        assert "check your input" in validation_exc.user_message.lower()

        # Test HTTP status code override
        permission_exc = InsufficientPermissionsException(required_permission="test")
        assert permission_exc._get_http_status_code() == 403

    def test_context_merging(self):
        """Test that context is properly merged in subclasses."""
        # Test FileValidationException context merging
        existing_context = {"existing_key": "existing_value"}
        validation_errors = ["error1", "error2"]

        exc = FileValidationException(
            file_path="/test/path",
            validation_errors=validation_errors,
            context=existing_context,
        )

        assert exc.context["existing_key"] == "existing_value"
        assert exc.context["file_path"] == "/test/path"
        assert exc.context["validation_errors"] == validation_errors


class TestExceptionUtilityMethods:
    """Test utility methods and edge cases."""

    def test_exception_str_representation(self):
        """Test string representation of exceptions."""
        exc = JDDBBaseException("Test error message")
        assert str(exc) == "Test error message"

    def test_exception_with_none_values(self):
        """Test exception handling of None values."""
        exc = JDDBBaseException(
            message="Test",
            context=None,
            recovery_suggestions=None,
            user_message=None,
            original_exception=None,
        )

        assert exc.context == {}
        assert exc.recovery_suggestions == []
        assert exc.user_message == exc._generate_user_message()
        assert exc.original_exception is None

    def test_to_dict_with_none_original_exception(self):
        """Test to_dict method with no original exception."""
        exc = JDDBBaseException("Test", original_exception=None)
        result = exc.to_dict()

        assert result["original_exception"] is None
        assert result["stack_trace"] is None

    @patch("jd_ingestion.utils.exceptions.traceback.format_exc")
    def test_stack_trace_capture(self, mock_format_exc):
        """Test stack trace capture when original exception is present."""
        mock_format_exc.return_value = "Mock stack trace"
        original_exception = ValueError("Original error")

        exc = JDDBBaseException("Test", original_exception=original_exception)

        mock_format_exc.assert_called_once()
        assert exc.stack_trace == "Mock stack trace"

    def test_error_id_uniqueness(self):
        """Test that error IDs are unique across instances."""
        exc1 = JDDBBaseException("Test 1")
        exc2 = JDDBBaseException("Test 2")

        assert exc1.error_id != exc2.error_id
        assert len(exc1.error_id) == 36  # UUID4 format
        assert len(exc2.error_id) == 36
