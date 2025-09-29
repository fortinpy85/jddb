"""
Audit logging framework for Phase 2 collaborative editing.

This module provides comprehensive audit logging for all user actions,
document changes, and system events in the collaborative editing environment.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy import text

from ..database.connection import get_async_session
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of events that can be audited."""

    # User authentication events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    PASSWORD_CHANGE = "password_change"

    # Document access events
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_CLOSE = "document_close"
    DOCUMENT_DOWNLOAD = "document_download"

    # Collaborative editing events
    EDITING_SESSION_START = "editing_session_start"
    EDITING_SESSION_JOIN = "editing_session_join"
    EDITING_SESSION_LEAVE = "editing_session_leave"
    EDITING_SESSION_END = "editing_session_end"

    # Document modification events
    DOCUMENT_INSERT = "document_insert"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_MODIFY = "document_modify"
    DOCUMENT_SAVE = "document_save"
    DOCUMENT_RESTORE = "document_restore"

    # Translation events
    TRANSLATION_REQUEST = "translation_request"
    TRANSLATION_APPROVE = "translation_approve"
    TRANSLATION_REJECT = "translation_reject"
    TRANSLATION_MEMORY_ADD = "translation_memory_add"

    # Permission and access events
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"

    # System events
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"

    # Data events
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_DELETE = "data_delete"
    BULK_OPERATION = "bulk_operation"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event."""

    event_type: AuditEventType
    severity: AuditSeverity
    user_id: Optional[int]
    username: Optional[str]
    timestamp: datetime
    resource_type: Optional[str]
    resource_id: Optional[int]
    action: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    details: Dict[str, Any]
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for storage."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def generate_hash(self) -> str:
        """Generate a hash of the audit event for integrity verification."""
        # Create a canonical representation for hashing
        hash_data = {
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": json.dumps(self.details, sort_keys=True),
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()


class AuditLogger:
    """Main audit logging class for Phase 2 features."""

    def __init__(self):
        self.events_cache: List[AuditEvent] = []
        self.max_cache_size = 100

    async def log_event(self, event: AuditEvent) -> bool:
        """
        Log an audit event to the database and local cache.

        Returns True if successfully logged, False otherwise.
        """
        try:
            # Generate integrity hash
            event_hash = event.generate_hash()

            # Store in database
            async for db in get_async_session():
                await db.execute(
                    text(
                        """
                    INSERT INTO audit_log (
                        event_type, severity, user_id, username, timestamp,
                        resource_type, resource_id, action, description,
                        ip_address, user_agent, session_id, details,
                        before_state, after_state, success, error_message,
                        event_hash
                    ) VALUES (
                        :event_type, :severity, :user_id, :username, :timestamp,
                        :resource_type, :resource_id, :action, :description,
                        :ip_address, :user_agent, :session_id, :details,
                        :before_state, :after_state, :success, :error_message,
                        :event_hash
                    )
                """
                    ),
                    {
                        "event_type": event.event_type.value,
                        "severity": event.severity.value,
                        "user_id": event.user_id,
                        "username": event.username,
                        "timestamp": event.timestamp,
                        "resource_type": event.resource_type,
                        "resource_id": event.resource_id,
                        "action": event.action,
                        "description": event.description,
                        "ip_address": event.ip_address,
                        "user_agent": event.user_agent,
                        "session_id": event.session_id,
                        "details": json.dumps(event.details),
                        "before_state": (
                            json.dumps(event.before_state)
                            if event.before_state
                            else None
                        ),
                        "after_state": (
                            json.dumps(event.after_state) if event.after_state else None
                        ),
                        "success": event.success,
                        "error_message": event.error_message,
                        "event_hash": event_hash,
                    },
                )

                await db.commit()
                break

            # Add to local cache
            self.events_cache.append(event)
            if len(self.events_cache) > self.max_cache_size:
                self.events_cache.pop(0)

            # Log to application logger based on severity
            log_message = f"AUDIT: {event.action} by {event.username or 'system'} - {event.description}"

            if event.severity == AuditSeverity.CRITICAL:
                logger.critical(log_message, extra=event.to_dict())
            elif event.severity == AuditSeverity.HIGH:
                logger.error(log_message, extra=event.to_dict())
            elif event.severity == AuditSeverity.MEDIUM:
                logger.warning(log_message, extra=event.to_dict())
            else:
                logger.info(log_message, extra=event.to_dict())

            return True

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False

    async def log_user_authentication(
        self,
        user_id: int,
        username: str,
        action: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log user authentication events."""
        event_type_map = {
            "login": AuditEventType.USER_LOGIN,
            "logout": AuditEventType.USER_LOGOUT,
            "register": AuditEventType.USER_REGISTRATION,
            "password_change": AuditEventType.PASSWORD_CHANGE,
        }

        event = AuditEvent(
            event_type=event_type_map.get(action, AuditEventType.USER_LOGIN),
            severity=AuditSeverity.MEDIUM if success else AuditSeverity.HIGH,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow(),
            resource_type="user_account",
            resource_id=user_id,
            action=action,
            description=f"User {action} {'successful' if success else 'failed'}",
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=None,
            details=details or {},
            success=success,
        )

        return await self.log_event(event)

    async def log_document_access(
        self,
        user_id: int,
        username: str,
        job_id: int,
        action: str,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log document access events."""
        event_type_map = {
            "view": AuditEventType.DOCUMENT_VIEW,
            "open": AuditEventType.DOCUMENT_OPEN,
            "close": AuditEventType.DOCUMENT_CLOSE,
            "download": AuditEventType.DOCUMENT_DOWNLOAD,
        }

        event = AuditEvent(
            event_type=event_type_map.get(action, AuditEventType.DOCUMENT_VIEW),
            severity=AuditSeverity.LOW,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow(),
            resource_type="job_description",
            resource_id=job_id,
            action=action,
            description=f"Document {action} by user {username}",
            ip_address=ip_address,
            user_agent=None,
            session_id=session_id,
            details=details or {},
        )

        return await self.log_event(event)

    async def log_editing_session(
        self,
        user_id: int,
        username: str,
        session_id: str,
        job_id: int,
        action: str,
        participants: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log collaborative editing session events."""
        event_type_map = {
            "start": AuditEventType.EDITING_SESSION_START,
            "join": AuditEventType.EDITING_SESSION_JOIN,
            "leave": AuditEventType.EDITING_SESSION_LEAVE,
            "end": AuditEventType.EDITING_SESSION_END,
        }

        event_details = details or {}
        if participants:
            event_details["participants"] = participants

        event = AuditEvent(
            event_type=event_type_map.get(action, AuditEventType.EDITING_SESSION_START),
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow(),
            resource_type="editing_session",
            resource_id=None,
            action=action,
            description=f"Editing session {action} by {username}",
            ip_address=None,
            user_agent=None,
            session_id=session_id,
            details=event_details,
        )

        return await self.log_event(event)

    async def log_document_change(
        self,
        user_id: int,
        username: str,
        job_id: int,
        session_id: str,
        change_type: str,
        before_content: Optional[str] = None,
        after_content: Optional[str] = None,
        position: Optional[int] = None,
        length: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log document modification events."""
        event_type_map = {
            "insert": AuditEventType.DOCUMENT_INSERT,
            "delete": AuditEventType.DOCUMENT_DELETE,
            "modify": AuditEventType.DOCUMENT_MODIFY,
            "save": AuditEventType.DOCUMENT_SAVE,
        }

        event_details = details or {}
        if position is not None:
            event_details["position"] = position
        if length is not None:
            event_details["length"] = length

        before_state = {"content": before_content} if before_content else None
        after_state = {"content": after_content} if after_content else None

        event = AuditEvent(
            event_type=event_type_map.get(change_type, AuditEventType.DOCUMENT_MODIFY),
            severity=AuditSeverity.LOW,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow(),
            resource_type="job_description",
            resource_id=job_id,
            action=change_type,
            description=f"Document {change_type} operation by {username}",
            ip_address=None,
            user_agent=None,
            session_id=session_id,
            details=event_details,
            before_state=before_state,
            after_state=after_state,
        )

        return await self.log_event(event)

    async def log_permission_change(
        self,
        admin_user_id: int,
        admin_username: str,
        target_user_id: int,
        target_username: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        permission_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log permission and access control changes."""
        event_type_map = {
            "grant": AuditEventType.PERMISSION_GRANT,
            "revoke": AuditEventType.PERMISSION_REVOKE,
            "denied": AuditEventType.ACCESS_DENIED,
        }

        event_details = details or {}
        event_details.update(
            {
                "target_user_id": target_user_id,
                "target_username": target_username,
                "permission_type": permission_type,
            }
        )

        event = AuditEvent(
            event_type=event_type_map.get(action, AuditEventType.PERMISSION_GRANT),
            severity=AuditSeverity.HIGH,
            user_id=admin_user_id,
            username=admin_username,
            timestamp=datetime.utcnow(),
            resource_type=resource_type or "system",
            resource_id=resource_id,
            action=action,
            description=f"Permission {action} for {target_username} by {admin_username}",
            ip_address=None,
            user_agent=None,
            session_id=None,
            details=event_details,
        )

        return await self.log_event(event)

    async def log_security_event(
        self,
        event_description: str,
        severity: AuditSeverity,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log security-related events."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            severity=severity,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow(),
            resource_type="system",
            resource_id=None,
            action="security_event",
            description=event_description,
            ip_address=ip_address,
            user_agent=None,
            session_id=None,
            details=details or {},
        )

        return await self.log_event(event)

    async def get_recent_events(
        self,
        limit: int = 50,
        user_id: Optional[int] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit events with optional filtering."""
        try:
            conditions = []
            params: Dict[str, Any] = {"limit": limit}

            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id

            if event_type:
                conditions.append("event_type = :event_type")
                params["event_type"] = event_type.value

            if severity:
                conditions.append("severity = :severity")
                params["severity"] = severity.value

            where_clause = " AND ".join(conditions)
            if where_clause:
                where_clause = f"WHERE {where_clause}"

            query = f"""
                SELECT * FROM audit_log
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit
            """

            async for db in get_async_session():
                result = await db.execute(text(query), params)
                rows = result.fetchall()

                events = []
                for row in rows:
                    events.append(
                        {
                            "id": row[0],
                            "event_type": row[1],
                            "severity": row[2],
                            "user_id": row[3],
                            "username": row[4],
                            "timestamp": row[5].isoformat(),
                            "resource_type": row[6],
                            "resource_id": row[7],
                            "action": row[8],
                            "description": row[9],
                            "ip_address": row[10],
                            "details": json.loads(row[13]) if row[13] else {},
                        }
                    )

                return events

            return []

        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {e}")
            return []


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit operations
async def log_user_login(
    user_id: int,
    username: str,
    success: bool = True,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """Log user login event."""
    return await audit_logger.log_user_authentication(
        user_id, username, "login", success, ip_address, user_agent
    )


async def log_document_edit(
    user_id: int,
    username: str,
    job_id: int,
    session_id: str,
    change_type: str,
    **kwargs,
):
    """Log document editing event."""
    return await audit_logger.log_document_change(
        user_id, username, job_id, session_id, change_type, **kwargs
    )


async def log_session_event(
    user_id: int, username: str, session_id: str, job_id: int, action: str, **kwargs
):
    """Log editing session event."""
    return await audit_logger.log_editing_session(
        user_id, username, session_id, job_id, action, **kwargs
    )


async def log_security_incident(
    description: str, severity: AuditSeverity = AuditSeverity.HIGH, **kwargs
):
    """Log security incident."""
    return await audit_logger.log_security_event(description, severity, **kwargs)
