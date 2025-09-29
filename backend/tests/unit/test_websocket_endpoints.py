"""
Tests for WebSocket endpoints and real-time collaboration functionality.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from jd_ingestion.api.main import app
from jd_ingestion.api.endpoints.websocket import ConnectionManager, manager


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def connection_manager():
    """Fresh connection manager for testing."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = Mock()
    websocket.accept = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestConnectionManager:
    """Test ConnectionManager class functionality."""

    @pytest.mark.asyncio
    async def test_connect_new_session(self, connection_manager, mock_websocket):
        """Test connecting to a new editing session."""
        session_id = "session_123"
        user_id = 1
        job_id = 456

        await connection_manager.connect(mock_websocket, session_id, user_id, job_id)

        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()

        # Verify session was created
        assert session_id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[session_id]
        assert session_id in connection_manager.editing_sessions
        assert connection_manager.editing_sessions[session_id]["job_id"] == job_id
        assert (
            user_id in connection_manager.editing_sessions[session_id]["participants"]
        )

        # Verify user session info was stored
        assert mock_websocket in connection_manager.user_sessions
        assert connection_manager.user_sessions[mock_websocket]["user_id"] == user_id
        assert (
            connection_manager.user_sessions[mock_websocket]["session_id"] == session_id
        )

    @pytest.mark.asyncio
    async def test_connect_existing_session(self, connection_manager, mock_websocket):
        """Test connecting to an existing editing session."""
        session_id = "session_123"
        user_id_1 = 1
        user_id_2 = 2
        job_id = 456

        # Create first connection
        websocket_1 = Mock()
        websocket_1.accept = AsyncMock()
        websocket_1.send_text = AsyncMock()
        await connection_manager.connect(websocket_1, session_id, user_id_1, job_id)

        # Create second connection to same session
        await connection_manager.connect(mock_websocket, session_id, user_id_2, job_id)

        # Verify both connections are in the same session
        assert len(connection_manager.active_connections[session_id]) == 2
        assert mock_websocket in connection_manager.active_connections[session_id]
        assert websocket_1 in connection_manager.active_connections[session_id]

        # Verify both users are participants
        participants = connection_manager.editing_sessions[session_id]["participants"]
        assert user_id_1 in participants
        assert user_id_2 in participants

        # Verify broadcast message was sent to first user
        websocket_1.send_text.assert_called()

    def test_disconnect_user(self, connection_manager, mock_websocket):
        """Test disconnecting a user from a session."""
        # First set up a connection
        session_id = "session_123"
        user_id = 1
        connection_manager.active_connections[session_id] = [mock_websocket]
        connection_manager.user_sessions[mock_websocket] = {
            "user_id": user_id,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.editing_sessions[session_id] = {
            "job_id": 456,
            "created_at": datetime.utcnow(),
            "participants": {user_id},
            "document_state": "",
            "operation_count": 0,
        }

        # Disconnect the user
        connection_manager.disconnect(mock_websocket)

        # Verify cleanup
        assert session_id not in connection_manager.active_connections
        assert session_id not in connection_manager.editing_sessions
        assert mock_websocket not in connection_manager.user_sessions

    def test_disconnect_partial_session(self, connection_manager):
        """Test disconnecting one user when multiple users in session."""
        session_id = "session_123"
        user_id_1 = 1
        user_id_2 = 2

        websocket_1 = Mock()
        websocket_2 = Mock()

        # Set up session with two users
        connection_manager.active_connections[session_id] = [websocket_1, websocket_2]
        connection_manager.user_sessions[websocket_1] = {
            "user_id": user_id_1,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.user_sessions[websocket_2] = {
            "user_id": user_id_2,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.editing_sessions[session_id] = {
            "job_id": 456,
            "created_at": datetime.utcnow(),
            "participants": {user_id_1, user_id_2},
            "document_state": "",
            "operation_count": 0,
        }

        # Disconnect one user
        connection_manager.disconnect(websocket_1)

        # Verify partial cleanup
        assert session_id in connection_manager.active_connections
        assert len(connection_manager.active_connections[session_id]) == 1
        assert websocket_2 in connection_manager.active_connections[session_id]
        assert (
            user_id_2 in connection_manager.editing_sessions[session_id]["participants"]
        )
        assert (
            user_id_1
            not in connection_manager.editing_sessions[session_id]["participants"]
        )
        assert websocket_1 not in connection_manager.user_sessions

    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket):
        """Test sending personal message to WebSocket."""
        message = {"type": "test", "data": "hello"}

        await connection_manager.send_personal_message(message, mock_websocket)

        mock_websocket.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_personal_message_error(
        self, connection_manager, mock_websocket
    ):
        """Test handling error when sending personal message."""
        mock_websocket.send_text.side_effect = Exception("Connection lost")
        message = {"type": "test", "data": "hello"}

        # Should not raise exception
        await connection_manager.send_personal_message(message, mock_websocket)

    @pytest.mark.asyncio
    async def test_broadcast_to_session(self, connection_manager):
        """Test broadcasting message to all connections in session."""
        session_id = "session_123"
        websocket_1 = Mock()
        websocket_2 = Mock()
        websocket_3 = Mock()

        websocket_1.send_text = AsyncMock()
        websocket_2.send_text = AsyncMock()
        websocket_3.send_text = AsyncMock()

        connection_manager.active_connections[session_id] = [
            websocket_1,
            websocket_2,
            websocket_3,
        ]

        message = {"type": "broadcast", "data": "hello all"}

        await connection_manager.broadcast_to_session(
            session_id, message, exclude=websocket_2
        )

        # Verify message sent to all except excluded
        websocket_1.send_text.assert_called_once_with(json.dumps(message))
        websocket_2.send_text.assert_not_called()
        websocket_3.send_text.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_session(self, connection_manager):
        """Test broadcasting to non-existent session."""
        message = {"type": "test"}

        # Should not raise exception
        await connection_manager.broadcast_to_session("nonexistent", message)

    @pytest.mark.asyncio
    async def test_broadcast_with_connection_errors(self, connection_manager):
        """Test broadcasting when some connections fail."""
        session_id = "session_123"
        websocket_1 = Mock()
        websocket_2 = Mock()

        websocket_1.send_text = AsyncMock()
        websocket_2.send_text = AsyncMock(side_effect=Exception("Connection lost"))

        connection_manager.active_connections[session_id] = [websocket_1, websocket_2]
        connection_manager.user_sessions[websocket_1] = {
            "user_id": 1,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.user_sessions[websocket_2] = {
            "user_id": 2,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }

        message = {"type": "test"}

        await connection_manager.broadcast_to_session(session_id, message)

        # Verify good connection still works
        websocket_1.send_text.assert_called_once()
        # Failed connection should be cleaned up
        assert websocket_2 not in connection_manager.user_sessions

    @pytest.mark.asyncio
    async def test_apply_operation_insert(self, connection_manager, mock_websocket):
        """Test applying an insert operation."""
        session_id = "session_123"
        user_id = 1

        # Set up session
        connection_manager.editing_sessions[session_id] = {
            "job_id": 456,
            "created_at": datetime.utcnow(),
            "participants": {user_id},
            "document_state": "Hello world",
            "operation_count": 0,
        }
        connection_manager.user_sessions[mock_websocket] = {
            "user_id": user_id,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.active_connections[session_id] = [mock_websocket]

        operation = {"type": "insert", "position": 5, "text": " beautiful"}

        await connection_manager.apply_operation(session_id, operation, mock_websocket)

        # Verify document state was updated
        expected_state = "Hello beautiful world"
        assert (
            connection_manager.editing_sessions[session_id]["document_state"]
            == expected_state
        )
        assert connection_manager.editing_sessions[session_id]["operation_count"] == 1

        # Verify acknowledgment was sent
        mock_websocket.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_apply_operation_delete(self, connection_manager, mock_websocket):
        """Test applying a delete operation."""
        session_id = "session_123"
        user_id = 1

        # Set up session
        connection_manager.editing_sessions[session_id] = {
            "job_id": 456,
            "created_at": datetime.utcnow(),
            "participants": {user_id},
            "document_state": "Hello world",
            "operation_count": 0,
        }
        connection_manager.user_sessions[mock_websocket] = {
            "user_id": user_id,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        connection_manager.active_connections[session_id] = [mock_websocket]

        operation = {"type": "delete", "start": 5, "end": 6}

        await connection_manager.apply_operation(session_id, operation, mock_websocket)

        # Verify document state was updated (removed the space)
        expected_state = "Helloworld"
        assert (
            connection_manager.editing_sessions[session_id]["document_state"]
            == expected_state
        )

    @pytest.mark.asyncio
    async def test_apply_operation_nonexistent_session(
        self, connection_manager, mock_websocket
    ):
        """Test applying operation to non-existent session."""
        operation = {"type": "insert", "position": 0, "text": "test"}

        # Should not raise exception
        await connection_manager.apply_operation(
            "nonexistent", operation, mock_websocket
        )

    def test_apply_insert_operation_edge_cases(self, connection_manager):
        """Test insert operation edge cases."""
        # Insert at beginning
        result = connection_manager._apply_insert_operation(
            "world", {"position": 0, "text": "Hello "}
        )
        assert result == "Hello world"

        # Insert at end
        result = connection_manager._apply_insert_operation(
            "Hello", {"position": 5, "text": " world"}
        )
        assert result == "Hello world"

        # Insert beyond document length (should append)
        result = connection_manager._apply_insert_operation(
            "Hello", {"position": 100, "text": " world"}
        )
        assert result == "Hello"  # Invalid position, no change

        # Empty text insertion
        result = connection_manager._apply_insert_operation(
            "Hello", {"position": 2, "text": ""}
        )
        assert result == "Hello"

    def test_apply_delete_operation_edge_cases(self, connection_manager):
        """Test delete operation edge cases."""
        # Delete from beginning
        result = connection_manager._apply_delete_operation(
            "Hello world", {"start": 0, "end": 6}
        )
        assert result == "world"

        # Delete from end
        result = connection_manager._apply_delete_operation(
            "Hello world", {"start": 5, "end": 11}
        )
        assert result == "Hello"

        # Invalid range (start > end)
        result = connection_manager._apply_delete_operation(
            "Hello", {"start": 3, "end": 1}
        )
        assert result == "Hello"  # No change

        # Out of bounds
        result = connection_manager._apply_delete_operation(
            "Hello", {"start": 10, "end": 15}
        )
        assert result == "Hello"  # No change


class TestWebSocketEndpoints:
    """Test WebSocket endpoint functionality."""

    def test_get_active_sessions_empty(self, client):
        """Test getting active sessions when none exist."""
        # Reset global manager state
        manager.editing_sessions.clear()

        response = client.get("/api/ws/sessions/active")
        assert response.status_code == 200
        data = response.json()
        assert data["active_sessions"] == []

    def test_get_active_sessions_with_data(self, client):
        """Test getting active sessions with existing sessions."""
        # Set up test data in global manager
        manager.editing_sessions["session_1"] = {
            "job_id": 123,
            "created_at": datetime(2023, 1, 1, 12, 0, 0),
            "participants": {1, 2},
            "document_state": "test document",
            "operation_count": 5,
        }
        manager.editing_sessions["session_2"] = {
            "job_id": 456,
            "created_at": datetime(2023, 1, 1, 13, 0, 0),
            "participants": {3},
            "document_state": "",
            "operation_count": 0,
        }

        response = client.get("/api/ws/sessions/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["active_sessions"]) == 2

        # Verify session data
        sessions = {s["session_id"]: s for s in data["active_sessions"]}
        assert "session_1" in sessions
        assert sessions["session_1"]["job_id"] == 123
        assert sessions["session_1"]["participant_count"] == 2
        assert sessions["session_1"]["operation_count"] == 5

        # Clean up
        manager.editing_sessions.clear()

    def test_get_session_state_success(self, client):
        """Test getting session state for existing session."""
        session_id = "test_session"
        manager.editing_sessions[session_id] = {
            "job_id": 789,
            "created_at": datetime(2023, 1, 1, 14, 0, 0),
            "participants": {1, 2, 3},
            "document_state": "Current document content",
            "operation_count": 10,
        }

        response = client.get(f"/api/ws/sessions/{session_id}/state")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["job_id"] == 789
        assert data["document_state"] == "Current document content"
        assert data["participants"] == [1, 2, 3]
        assert data["operation_count"] == 10

        # Clean up
        del manager.editing_sessions[session_id]

    def test_get_session_state_not_found(self, client):
        """Test getting session state for non-existent session."""
        response = client.get("/api/ws/sessions/nonexistent/state")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


class TestWebSocketIntegration:
    """Test WebSocket integration scenarios."""

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.websocket.get_async_session")
    async def test_websocket_connection_job_exists(self, mock_session):
        """Test WebSocket connection when job exists."""
        # Mock database session and query result
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_result = Mock()
        mock_result.fetchone.return_value = {"id": 123}  # Job exists
        mock_db.execute.return_value = mock_result

        from jd_ingestion.api.endpoints.websocket import websocket_edit_session

        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Mock WebSocketDisconnect to end the connection loop
        from fastapi import WebSocketDisconnect

        mock_websocket.receive_text.side_effect = WebSocketDisconnect()

        # Test the WebSocket handler
        await websocket_edit_session(
            websocket=mock_websocket,
            session_id="test_session",
            user_id=1,
            job_id=123,
            db=mock_db,
        )

        # Verify job verification was performed
        mock_db.execute.assert_called_once()
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    @patch("jd_ingestion.api.endpoints.websocket.get_async_session")
    async def test_websocket_connection_job_not_found(self, mock_session):
        """Test WebSocket connection when job doesn't exist."""
        # Mock database session and query result
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_db

        mock_result = Mock()
        mock_result.fetchone.return_value = None  # Job doesn't exist
        mock_db.execute.return_value = mock_result

        from jd_ingestion.api.endpoints.websocket import websocket_edit_session

        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.close = AsyncMock()

        # Test the WebSocket handler
        await websocket_edit_session(
            websocket=mock_websocket,
            session_id="test_session",
            user_id=1,
            job_id=999,
            db=mock_db,
        )

        # Verify connection was rejected
        mock_websocket.close.assert_called_once_with(code=4004, reason="Job not found")
        mock_websocket.accept.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_message_handling_operation(self):
        """Test handling of operation messages in WebSocket."""
        from jd_ingestion.api.endpoints.websocket import manager

        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock()

        # Set up session
        session_id = "test_session"
        user_id = 1
        manager.editing_sessions[session_id] = {
            "job_id": 123,
            "created_at": datetime.utcnow(),
            "participants": {user_id},
            "document_state": "",
            "operation_count": 0,
        }
        manager.user_sessions[mock_websocket] = {
            "user_id": user_id,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        manager.active_connections[session_id] = [mock_websocket]

        # Simulate operation message
        operation_message = {
            "type": "operation",
            "operation": {"type": "insert", "position": 0, "text": "Hello"},
        }

        # Apply the operation directly (simulating WebSocket message handling)
        await manager.apply_operation(
            session_id, operation_message["operation"], mock_websocket
        )

        # Verify operation was processed
        assert manager.editing_sessions[session_id]["document_state"] == "Hello"
        assert manager.editing_sessions[session_id]["operation_count"] == 1

        # Clean up
        manager.editing_sessions.clear()
        manager.user_sessions.clear()
        manager.active_connections.clear()

    @pytest.mark.asyncio
    async def test_websocket_cursor_update_handling(self):
        """Test handling of cursor update messages."""
        from jd_ingestion.api.endpoints.websocket import manager

        mock_websocket_1 = Mock()
        mock_websocket_1.send_text = AsyncMock()
        mock_websocket_2 = Mock()
        mock_websocket_2.send_text = AsyncMock()

        # Set up session with two users
        session_id = "test_session"
        user_id_1 = 1
        user_id_2 = 2

        manager.active_connections[session_id] = [mock_websocket_1, mock_websocket_2]
        manager.user_sessions[mock_websocket_1] = {
            "user_id": user_id_1,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        manager.user_sessions[mock_websocket_2] = {
            "user_id": user_id_2,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }

        # Update cursor position for user 1
        new_position = {"line": 5, "column": 10}
        manager.user_sessions[mock_websocket_1]["cursor_position"] = new_position

        # Broadcast cursor update
        await manager.broadcast_to_session(
            session_id,
            {"type": "cursor_update", "user_id": user_id_1, "position": new_position},
            exclude=mock_websocket_1,
        )

        # Verify cursor position was stored
        assert (
            manager.user_sessions[mock_websocket_1]["cursor_position"] == new_position
        )

        # Verify other user received the update
        mock_websocket_2.send_text.assert_called()

        # Clean up
        manager.editing_sessions.clear()
        manager.user_sessions.clear()
        manager.active_connections.clear()


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios."""

    @pytest.mark.asyncio
    async def test_connection_manager_error_recovery(self, connection_manager):
        """Test connection manager recovery from various errors."""
        session_id = "error_session"

        # Test with invalid session data
        connection_manager.editing_sessions[session_id] = None

        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()

        # Should not raise exception
        await connection_manager.apply_operation(
            session_id, {"type": "test"}, mock_websocket
        )

    def test_connection_manager_state_consistency(self, connection_manager):
        """Test that connection manager maintains consistent state."""
        session_id = "consistency_test"
        websocket_1 = Mock()
        websocket_2 = Mock()

        # Manually create inconsistent state
        connection_manager.active_connections[session_id] = [websocket_1]
        connection_manager.user_sessions[websocket_1] = {
            "user_id": 1,
            "session_id": session_id,
            "joined_at": datetime.utcnow(),
            "cursor_position": None,
        }
        # Missing editing_sessions entry

        # Disconnect should handle missing editing session gracefully
        connection_manager.disconnect(websocket_1)

        # Verify cleanup still occurred
        assert session_id not in connection_manager.active_connections
        assert websocket_1 not in connection_manager.user_sessions

    @pytest.mark.asyncio
    async def test_websocket_malformed_message_handling(self):
        """Test handling of malformed WebSocket messages."""
        from jd_ingestion.api.endpoints.websocket import manager

        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()

        # Test with message missing required fields
        await manager.apply_operation("session", {}, mock_websocket)

        # Should not raise exception and should handle gracefully
