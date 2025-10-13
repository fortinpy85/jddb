"""
WebSocket endpoints for real-time collaborative editing.

This module provides WebSocket connections for:
- Real-time collaborative editing sessions
- Document change synchronization
- User presence awareness
- Operational transformation for conflict resolution
"""

import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import uuid

from ...database.connection import get_async_session
from ...utils.logging import get_logger
from ...utils.operational_transform import (
    Operation,
    apply_operation,
    transform_against_history,
    validate_operation,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for real-time collaboration."""

    def __init__(self):
        # Active connections by session_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # User information by connection
        self.user_sessions: Dict[WebSocket, Dict] = {}
        # Document editing sessions
        self.editing_sessions: Dict[str, Dict] = {}

    async def connect(
        self, websocket: WebSocket, session_id: str, user_id: int, job_id: int
    ):
        """Accept a new WebSocket connection and add to session."""
        await websocket.accept()

        # Initialize session if it doesn't exist
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
            self.editing_sessions[session_id] = {
                "job_id": job_id,
                "created_at": datetime.utcnow(),
                "participants": set(),
                "document_state": "",
                "operation_count": 0,
                "operation_history": [],  # Track all operations for OT
            }

        # Add connection to session
        self.active_connections[session_id].append(websocket)
        self.user_sessions[websocket] = {
            "user_id": user_id,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }

        # Add user to session participants
        self.editing_sessions[session_id]["participants"].add(user_id)

        logger.info(f"User {user_id} connected to session {session_id}")

        # Notify other participants about new user
        await self.broadcast_to_session(
            session_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "participants": list(self.editing_sessions[session_id]["participants"]),
            },
            exclude=websocket,
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.user_sessions:
            user_info = self.user_sessions[websocket]
            session_id = user_info["session_id"]
            user_id = user_info["user_id"]

            # Remove from active connections
            if session_id in self.active_connections:
                if websocket in self.active_connections[session_id]:
                    self.active_connections[session_id].remove(websocket)

                # Remove from participants
                if session_id in self.editing_sessions:
                    self.editing_sessions[session_id]["participants"].discard(user_id)

                # Clean up empty sessions
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    if session_id in self.editing_sessions:
                        del self.editing_sessions[session_id]

            # Remove user session info
            del self.user_sessions[websocket]

            logger.info(f"User {user_id} disconnected from session {session_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")

    async def broadcast_to_session(
        self, session_id: str, message: dict, exclude: WebSocket = None
    ):
        """Broadcast a message to all connections in a session."""
        if session_id not in self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[session_id]:
            if connection == exclude:
                continue

            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    def _apply_insert_operation(self, document: str, operation: dict) -> str:
        """Apply an insert operation to a document."""
        position = operation.get("position", 0)
        text = operation.get("text", "")

        # Validate position
        if position < 0 or position > len(document):
            return document  # Invalid position, no change

        # Empty text insertion
        if not text:
            return document

        # Insert text at position
        return document[:position] + text + document[position:]

    def _apply_delete_operation(self, document: str, operation: dict) -> str:
        """Apply a delete operation to a document."""
        start = operation.get("start", 0)
        end = operation.get("end", 0)

        # Validate range
        if start < 0 or end < 0 or start >= end or start >= len(document):
            return document  # Invalid range, no change

        # Out of bounds check
        if end > len(document):
            return document  # No change

        # Delete text from start to end
        return document[:start] + document[end:]

    async def apply_operation(
        self, session_id: str, operation: dict, websocket: WebSocket
    ):
        """Apply an operational transformation and broadcast to other participants."""
        if session_id not in self.editing_sessions:
            logger.error(f"Session {session_id} not found for operation")
            return

        session = self.editing_sessions[session_id]
        user_info = self.user_sessions.get(websocket, {})
        user_id = user_info.get("user_id")

        try:
            # Convert dict to Operation object
            op = Operation.from_dict(operation)

            # Validate operation
            if not validate_operation(op, len(session["document_state"])):
                logger.error(f"Invalid operation received: {operation}")
                await self.send_personal_message(
                    {
                        "type": "operation_error",
                        "error": "Invalid operation",
                    },
                    websocket,
                )
                return

            # Transform operation against concurrent operations if needed
            # If client has pending operations, transform against them
            client_sequence = operation.get("base_sequence", session["operation_count"])
            if client_sequence < session["operation_count"]:
                # Client is behind - transform against missed operations
                missed_ops = session["operation_history"][client_sequence:]
                op = transform_against_history(op, missed_ops)
                logger.info(
                    f"Transformed operation against {len(missed_ops)} concurrent operations"
                )

            # Apply operation to document
            session["document_state"] = apply_operation(session["document_state"], op)

            # Generate operation ID and increment counter
            operation_id = str(uuid.uuid4())
            session["operation_count"] += 1

            # Store operation in history
            session["operation_history"].append(op)

            # Keep history manageable (last 1000 operations)
            if len(session["operation_history"]) > 1000:
                session["operation_history"] = session["operation_history"][-1000:]

            # Enhance operation with metadata
            enhanced_operation = {
                **op.to_dict(),
                "operation_id": operation_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "sequence_number": session["operation_count"],
            }

            logger.info(
                f"Applied operation {operation_id} in session {session_id} "
                f"(seq: {session['operation_count']})"
            )

            # Broadcast operation to other participants
            await self.broadcast_to_session(
                session_id,
                {"type": "operation", "operation": enhanced_operation},
                exclude=websocket,
            )

            # Acknowledge operation to sender
            await self.send_personal_message(
                {
                    "type": "operation_ack",
                    "operation_id": operation_id,
                    "sequence_number": session["operation_count"],
                },
                websocket,
            )

        except Exception as e:
            logger.error(f"Error applying operation: {e}")
            await self.send_personal_message(
                {
                    "type": "operation_error",
                    "error": str(e),
                },
                websocket,
            )


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/edit/{session_id}")
async def websocket_edit_session(
    websocket: WebSocket,
    session_id: str,
    user_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """
    WebSocket endpoint for collaborative editing sessions.

    Parameters:
    - session_id: Unique identifier for the editing session
    - user_id: ID of the user connecting (would normally come from auth)
    - job_id: ID of the job description being edited
    """

    # Verify job exists
    result = await db.execute(
        text("SELECT id FROM job_descriptions WHERE id = :job_id"), {"job_id": job_id}
    )
    job = result.fetchone()
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    try:
        await manager.connect(websocket, session_id, user_id, job_id)

        # Send initial session state
        await manager.send_personal_message(
            {
                "type": "session_state",
                "session_id": session_id,
                "job_id": job_id,
                "document_state": manager.editing_sessions[session_id][
                    "document_state"
                ],
                "participants": list(
                    manager.editing_sessions[session_id]["participants"]
                ),
                "operation_count": manager.editing_sessions[session_id][
                    "operation_count"
                ],
            },
            websocket,
        )

        # Main message loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "operation":
                # Handle document operations (insert, delete, format, etc.)
                operation = message.get("operation", {})
                await manager.apply_operation(session_id, operation, websocket)

            elif message_type == "cursor_update":
                # Handle cursor position updates
                position = message.get("position")
                if websocket in manager.user_sessions:
                    manager.user_sessions[websocket]["cursor_position"] = position

                await manager.broadcast_to_session(
                    session_id,
                    {
                        "type": "cursor_update",
                        "user_id": manager.user_sessions[websocket]["user_id"],
                        "position": position,
                    },
                    exclude=websocket,
                )

            elif message_type == "ping":
                # Handle keep-alive pings
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
                    websocket,
                )

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error in session {session_id}: {e}")
    finally:
        manager.disconnect(websocket)


@router.get("/sessions/active")
async def get_active_sessions():
    """Get information about currently active editing sessions."""
    sessions = []
    for session_id, session_info in manager.editing_sessions.items():
        sessions.append(
            {
                "session_id": session_id,
                "job_id": session_info["job_id"],
                "participant_count": len(session_info["participants"]),
                "participants": list(session_info["participants"]),
                "created_at": session_info["created_at"].isoformat(),
                "operation_count": session_info["operation_count"],
            }
        )

    return {"active_sessions": sessions}


@router.get("/sessions/{session_id}/state")
async def get_session_state(session_id: str):
    """Get the current state of an editing session."""
    if session_id not in manager.editing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = manager.editing_sessions[session_id]
    return {
        "session_id": session_id,
        "job_id": session["job_id"],
        "document_state": session["document_state"],
        "participants": list(session["participants"]),
        "operation_count": session["operation_count"],
        "created_at": session["created_at"].isoformat(),
    }
