"""Tests for audit/logger.py module."""

import pytest
import json
import hashlib
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from jd_ingestion.audit.logger import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditLogger,
    audit_logger,
    log_user_login,
    log_document_edit,
    log_session_event,
    log_security_incident,
)


class TestAuditEventType:
    """Test AuditEventType enum."""

    def test_all_event_types_exist(self):
        """Test that all expected event types are defined."""
        expected_types = [
            "USER_LOGIN",
            "USER_LOGOUT",
            "USER_REGISTRATION",
            "PASSWORD_CHANGE",
            "DOCUMENT_VIEW",
            "DOCUMENT_OPEN",
            "DOCUMENT_CLOSE",
            "DOCUMENT_DOWNLOAD",
            "EDITING_SESSION_START",
            "EDITING_SESSION_JOIN",
            "EDITING_SESSION_LEAVE",
            "EDITING_SESSION_END",
            "DOCUMENT_INSERT",
            "DOCUMENT_DELETE",
            "DOCUMENT_MODIFY",
            "DOCUMENT_SAVE",
            "DOCUMENT_RESTORE",
            "TRANSLATION_REQUEST",
            "TRANSLATION_APPROVE",
            "TRANSLATION_REJECT",
            "TRANSLATION_MEMORY_ADD",
            "PERMISSION_GRANT",
            "PERMISSION_REVOKE",
            "ACCESS_DENIED",
            "PRIVILEGE_ESCALATION",
            "SYSTEM_BACKUP",
            "SYSTEM_RESTORE",
            "CONFIGURATION_CHANGE",
            "SECURITY_EVENT",
            "DATA_EXPORT",
            "DATA_IMPORT",
            "DATA_DELETE",
            "BULK_OPERATION",
        ]

        for event_type in expected_types:
            assert hasattr(AuditEventType, event_type)

    def test_event_type_values(self):
        """Test that event type values are correct."""
        assert AuditEventType.USER_LOGIN.value == "user_login"
        assert AuditEventType.DOCUMENT_VIEW.value == "document_view"
        assert AuditEventType.SECURITY_EVENT.value == "security_event"


class TestAuditSeverity:
    """Test AuditSeverity enum."""

    def test_all_severity_levels_exist(self):
        """Test that all expected severity levels are defined."""
        expected_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for level in expected_levels:
            assert hasattr(AuditSeverity, level)

    def test_severity_values(self):
        """Test that severity values are correct."""
        assert AuditSeverity.LOW.value == "low"
        assert AuditSeverity.MEDIUM.value == "medium"
        assert AuditSeverity.HIGH.value == "high"
        assert AuditSeverity.CRITICAL.value == "critical"


class TestAuditEvent:
    """Test AuditEvent dataclass."""

    @pytest.fixture
    def sample_event(self):
        """Create a sample audit event for testing."""
        return AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.MEDIUM,
            user_id=123,
            username="test_user",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            resource_type="user_account",
            resource_id=123,
            action="login",
            description="User login successful",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session_123",
            details={"browser": "Chrome", "version": "90.0"},
        )

    def test_audit_event_creation(self, sample_event):
        """Test creating an audit event."""
        assert sample_event.event_type == AuditEventType.USER_LOGIN
        assert sample_event.severity == AuditSeverity.MEDIUM
        assert sample_event.user_id == 123
        assert sample_event.username == "test_user"
        assert sample_event.success is True  # Default value

    def test_to_dict(self, sample_event):
        """Test converting audit event to dictionary."""
        result = sample_event.to_dict()

        assert isinstance(result, dict)
        assert result["event_type"] == "user_login"
        assert result["severity"] == "medium"
        assert result["user_id"] == 123
        assert result["username"] == "test_user"
        assert result["timestamp"] == "2023-01-01T12:00:00"
        assert result["details"] == {"browser": "Chrome", "version": "90.0"}

    def test_generate_hash(self, sample_event):
        """Test generating hash for audit event."""
        hash1 = sample_event.generate_hash()
        hash2 = sample_event.generate_hash()

        # Same event should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

        # Different event should produce different hash
        sample_event.user_id = 456
        hash3 = sample_event.generate_hash()
        assert hash1 != hash3

    def test_generate_hash_consistency(self):
        """Test that hash generation is consistent across identical events."""
        event1 = AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.MEDIUM,
            user_id=123,
            username="test",
            timestamp=datetime(2023, 1, 1),
            resource_type="user",
            resource_id=123,
            action="login",
            description="test",
            ip_address=None,
            user_agent=None,
            session_id=None,
            details={"key": "value"},
        )

        event2 = AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.MEDIUM,
            user_id=123,
            username="test",
            timestamp=datetime(2023, 1, 1),
            resource_type="user",
            resource_id=123,
            action="login",
            description="test",
            ip_address=None,
            user_agent=None,
            session_id=None,
            details={"key": "value"},
        )

        assert event1.generate_hash() == event2.generate_hash()


class TestAuditLogger:
    """Test AuditLogger class."""

    @pytest.fixture
    def logger(self):
        """Create a fresh audit logger for testing."""
        return AuditLogger()

    @pytest.fixture
    def sample_event(self):
        """Create a sample audit event."""
        return AuditEvent(
            event_type=AuditEventType.USER_LOGIN,
            severity=AuditSeverity.MEDIUM,
            user_id=123,
            username="test_user",
            timestamp=datetime.utcnow(),
            resource_type="user_account",
            resource_id=123,
            action="login",
            description="Test login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            session_id="session_123",
            details={},
        )

    @pytest.mark.asyncio
    async def test_log_event_success(self, logger, sample_event):
        """Test successful event logging."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger") as mock_logger,
        ):
            # Mock database session
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_event(sample_event)

            assert result is True
            assert len(logger.events_cache) == 1
            assert logger.events_cache[0] == sample_event

            # Verify database call
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

            # Verify logging call
            mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_database_error(self, logger, sample_event):
        """Test event logging with database error."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger") as mock_logger,
        ):
            # Mock database error
            mock_session.side_effect = Exception("Database error")

            result = await logger.log_event(sample_event)

            assert result is False
            assert len(logger.events_cache) == 0
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_event_cache_management(self, logger):
        """Test that event cache is properly managed."""
        logger.max_cache_size = 2

        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            # Mock successful database operations
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            # Add events beyond cache size
            for i in range(3):
                event = AuditEvent(
                    event_type=AuditEventType.USER_LOGIN,
                    severity=AuditSeverity.LOW,
                    user_id=i,
                    username=f"user_{i}",
                    timestamp=datetime.utcnow(),
                    resource_type="test",
                    resource_id=i,
                    action="test",
                    description=f"Test event {i}",
                    ip_address=None,
                    user_agent=None,
                    session_id=None,
                    details={},
                )
                await logger.log_event(event)

            # Cache should only contain last 2 events
            assert len(logger.events_cache) == 2
            assert logger.events_cache[0].user_id == 1
            assert logger.events_cache[1].user_id == 2

    @pytest.mark.asyncio
    async def test_log_event_severity_logging(self, logger):
        """Test that different severities use appropriate log levels."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger") as mock_logger,
        ):
            # Mock successful database operations
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            test_cases = [
                (AuditSeverity.CRITICAL, mock_logger.critical),
                (AuditSeverity.HIGH, mock_logger.error),
                (AuditSeverity.MEDIUM, mock_logger.warning),
                (AuditSeverity.LOW, mock_logger.info),
            ]

            for severity, expected_method in test_cases:
                mock_logger.reset_mock()

                event = AuditEvent(
                    event_type=AuditEventType.SECURITY_EVENT,
                    severity=severity,
                    user_id=123,
                    username="test",
                    timestamp=datetime.utcnow(),
                    resource_type="system",
                    resource_id=None,
                    action="test",
                    description=f"Test {severity.value} event",
                    ip_address=None,
                    user_agent=None,
                    session_id=None,
                    details={},
                )

                await logger.log_event(event)
                expected_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_user_authentication(self, logger):
        """Test logging user authentication events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_user_authentication(
                user_id=123,
                username="test_user",
                action="login",
                success=True,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                details={"method": "password"},
            )

            assert result is True
            assert len(logger.events_cache) == 1

            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.USER_LOGIN
            assert event.severity == AuditSeverity.MEDIUM
            assert event.user_id == 123
            assert event.username == "test_user"
            assert event.success is True

    @pytest.mark.asyncio
    async def test_log_user_authentication_failure(self, logger):
        """Test logging failed authentication."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_user_authentication(
                user_id=123, username="test_user", action="login", success=False
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.severity == AuditSeverity.HIGH  # Failed auth = high severity
            assert event.success is False

    @pytest.mark.asyncio
    async def test_log_document_access(self, logger):
        """Test logging document access events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_document_access(
                user_id=123,
                username="test_user",
                job_id=456,
                action="view",
                ip_address="192.168.1.1",
                session_id="session_123",
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.DOCUMENT_VIEW
            assert event.severity == AuditSeverity.LOW
            assert event.resource_type == "job_description"
            assert event.resource_id == 456

    @pytest.mark.asyncio
    async def test_log_editing_session(self, logger):
        """Test logging editing session events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_editing_session(
                user_id=123,
                username="test_user",
                session_id="session_123",
                job_id=456,
                action="start",
                participants=["user1", "user2"],
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.EDITING_SESSION_START
            assert event.severity == AuditSeverity.MEDIUM
            assert "participants" in event.details
            assert event.details["participants"] == ["user1", "user2"]

    @pytest.mark.asyncio
    async def test_log_document_change(self, logger):
        """Test logging document changes."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_document_change(
                user_id=123,
                username="test_user",
                job_id=456,
                session_id="session_123",
                change_type="insert",
                before_content="Hello",
                after_content="Hello World",
                position=5,
                length=6,
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.DOCUMENT_INSERT
            assert event.before_state == {"content": "Hello"}
            assert event.after_state == {"content": "Hello World"}
            assert event.details["position"] == 5
            assert event.details["length"] == 6

    @pytest.mark.asyncio
    async def test_log_permission_change(self, logger):
        """Test logging permission changes."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_permission_change(
                admin_user_id=123,
                admin_username="admin",
                target_user_id=456,
                target_username="user",
                action="grant",
                resource_type="document",
                resource_id=789,
                permission_type="read",
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.PERMISSION_GRANT
            assert event.severity == AuditSeverity.HIGH
            assert event.details["target_user_id"] == 456
            assert event.details["permission_type"] == "read"

    @pytest.mark.asyncio
    async def test_log_security_event(self, logger):
        """Test logging security events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            result = await logger.log_security_event(
                event_description="Suspicious login attempt",
                severity=AuditSeverity.CRITICAL,
                user_id=123,
                username="test_user",
                ip_address="192.168.1.100",
                details={"failed_attempts": 5},
            )

            assert result is True
            event = logger.events_cache[0]
            assert event.event_type == AuditEventType.SECURITY_EVENT
            assert event.severity == AuditSeverity.CRITICAL
            assert event.description == "Suspicious login attempt"
            assert event.details["failed_attempts"] == 5

    @pytest.mark.asyncio
    async def test_get_recent_events(self, logger):
        """Test retrieving recent events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            # Mock database response
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_rows = [
                (
                    1,
                    "user_login",
                    "medium",
                    123,
                    "test_user",
                    datetime(2023, 1, 1),
                    "user_account",
                    123,
                    "login",
                    "User login",
                    "192.168.1.1",
                    "Mozilla",
                    "session_123",
                    '{"key": "value"}',
                    None,
                    None,
                    True,
                    None,
                    "hash123",
                )
            ]
            mock_result.fetchall.return_value = mock_rows
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            events = await logger.get_recent_events(limit=10, user_id=123)

            assert len(events) == 1
            assert events[0]["event_type"] == "user_login"
            assert events[0]["user_id"] == 123
            assert events[0]["details"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_recent_events_with_filters(self, logger):
        """Test retrieving recent events with filters."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_result = AsyncMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            await logger.get_recent_events(
                limit=50,
                user_id=123,
                event_type=AuditEventType.USER_LOGIN,
                severity=AuditSeverity.HIGH,
            )

            # Verify that the query includes all filters
            call_args = mock_db.execute.call_args[0]
            query = call_args[0].text
            params = call_args[1]

            assert "user_id = :user_id" in query
            assert "event_type = :event_type" in query
            assert "severity = :severity" in query
            assert params["user_id"] == 123
            assert params["event_type"] == "user_login"
            assert params["severity"] == "high"

    @pytest.mark.asyncio
    async def test_get_recent_events_error(self, logger):
        """Test error handling in get_recent_events."""
        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger") as mock_logger,
        ):
            # Mock database error
            mock_session.side_effect = Exception("Database error")

            events = await logger.get_recent_events()

            assert events == []
            mock_logger.error.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_log_user_login(self):
        """Test log_user_login convenience function."""
        with patch.object(audit_logger, "log_user_authentication") as mock_method:
            mock_method.return_value = True

            result = await log_user_login(
                user_id=123,
                username="test_user",
                success=True,
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            assert result is True
            mock_method.assert_called_once_with(
                123, "test_user", "login", True, "192.168.1.1", "Mozilla/5.0"
            )

    @pytest.mark.asyncio
    async def test_log_document_edit(self):
        """Test log_document_edit convenience function."""
        with patch.object(audit_logger, "log_document_change") as mock_method:
            mock_method.return_value = True

            result = await log_document_edit(
                user_id=123,
                username="test_user",
                job_id=456,
                session_id="session_123",
                change_type="insert",
                position=10,
            )

            assert result is True
            mock_method.assert_called_once_with(
                123, "test_user", 456, "session_123", "insert", position=10
            )

    @pytest.mark.asyncio
    async def test_log_session_event(self):
        """Test log_session_event convenience function."""
        with patch.object(audit_logger, "log_editing_session") as mock_method:
            mock_method.return_value = True

            result = await log_session_event(
                user_id=123,
                username="test_user",
                session_id="session_123",
                job_id=456,
                action="start",
                participants=["user1", "user2"],
            )

            assert result is True
            mock_method.assert_called_once_with(
                123,
                "test_user",
                "session_123",
                456,
                "start",
                participants=["user1", "user2"],
            )

    @pytest.mark.asyncio
    async def test_log_security_incident(self):
        """Test log_security_incident convenience function."""
        with patch.object(audit_logger, "log_security_event") as mock_method:
            mock_method.return_value = True

            result = await log_security_incident(
                description="Test incident",
                severity=AuditSeverity.CRITICAL,
                user_id=123,
                ip_address="192.168.1.1",
            )

            assert result is True
            mock_method.assert_called_once_with(
                "Test incident",
                AuditSeverity.CRITICAL,
                user_id=123,
                ip_address="192.168.1.1",
            )


class TestEventTypeMappings:
    """Test event type mappings in logger methods."""

    @pytest.mark.asyncio
    async def test_authentication_event_mapping(self):
        """Test authentication event type mapping."""
        logger = AuditLogger()

        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            test_cases = [
                ("login", AuditEventType.USER_LOGIN),
                ("logout", AuditEventType.USER_LOGOUT),
                ("register", AuditEventType.USER_REGISTRATION),
                ("password_change", AuditEventType.PASSWORD_CHANGE),
                ("unknown_action", AuditEventType.USER_LOGIN),  # fallback
            ]

            for action, expected_type in test_cases:
                logger.events_cache.clear()

                await logger.log_user_authentication(
                    user_id=123, username="test", action=action
                )

                assert len(logger.events_cache) == 1
                assert logger.events_cache[0].event_type == expected_type

    @pytest.mark.asyncio
    async def test_document_access_event_mapping(self):
        """Test document access event type mapping."""
        logger = AuditLogger()

        with (
            patch("jd_ingestion.audit.logger.get_async_session") as mock_session,
            patch("jd_ingestion.audit.logger.logger"),
        ):
            mock_db = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db
            mock_session.return_value.__aiter__ = AsyncMock(return_value=[mock_db])

            test_cases = [
                ("view", AuditEventType.DOCUMENT_VIEW),
                ("open", AuditEventType.DOCUMENT_OPEN),
                ("close", AuditEventType.DOCUMENT_CLOSE),
                ("download", AuditEventType.DOCUMENT_DOWNLOAD),
                ("unknown_action", AuditEventType.DOCUMENT_VIEW),  # fallback
            ]

            for action, expected_type in test_cases:
                logger.events_cache.clear()

                await logger.log_document_access(
                    user_id=123, username="test", job_id=456, action=action
                )

                assert len(logger.events_cache) == 1
                assert logger.events_cache[0].event_type == expected_type
