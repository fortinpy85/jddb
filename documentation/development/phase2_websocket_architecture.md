# Phase 2 WebSocket Architecture Design
*Real-time Collaborative Editing Infrastructure*

## Overview

This document outlines the WebSocket-based real-time collaboration architecture for JDDB Phase 2, enabling side-by-side editing, translation concordance, and multi-user collaboration.

## WebSocket Infrastructure Components

### 1. FastAPI WebSocket Manager

```python
# backend/src/jd_ingestion/websocket/manager.py
from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    # Document editing
    DOCUMENT_CHANGE = "document_change"
    CURSOR_POSITION = "cursor_position"
    SELECTION_CHANGE = "selection_change"

    # Collaboration
    USER_JOIN = "user_join"
    USER_LEAVE = "user_leave"
    USER_TYPING = "user_typing"

    # Translation
    TRANSLATION_UPDATE = "translation_update"
    ALIGNMENT_CHANGE = "alignment_change"

    # System
    SESSION_STATE = "session_state"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

@dataclass
class EditingSession:
    session_id: str
    job_id: int
    created_by: int
    collaborators: Set[int]
    websockets: Dict[int, WebSocket]
    document_state: Dict
    last_activity: float

class WebSocketManager:
    def __init__(self):
        self.active_sessions: Dict[str, EditingSession] = {}
        self.user_sessions: Dict[int, str] = {}

    async def connect_user(self, websocket: WebSocket, session_id: str, user_id: int):
        """Connect a user to an editing session."""
        await websocket.accept()

        if session_id not in self.active_sessions:
            # Create new session
            session = EditingSession(
                session_id=session_id,
                job_id=await self._get_job_id_from_session(session_id),
                created_by=user_id,
                collaborators={user_id},
                websockets={user_id: websocket},
                document_state={},
                last_activity=time.time()
            )
            self.active_sessions[session_id] = session
        else:
            # Join existing session
            session = self.active_sessions[session_id]
            session.collaborators.add(user_id)
            session.websockets[user_id] = websocket

        self.user_sessions[user_id] = session_id

        # Notify other users
        await self._broadcast_to_session(session_id, {
            "type": MessageType.USER_JOIN.value,
            "user_id": user_id,
            "collaborators": list(session.collaborators)
        }, exclude_user=user_id)

        # Send current session state to new user
        await self._send_to_user(user_id, {
            "type": MessageType.SESSION_STATE.value,
            "session_id": session_id,
            "collaborators": list(session.collaborators),
            "document_state": session.document_state
        })

    async def disconnect_user(self, user_id: int):
        """Disconnect a user from their session."""
        if user_id not in self.user_sessions:
            return

        session_id = self.user_sessions[user_id]
        session = self.active_sessions.get(session_id)

        if session:
            session.collaborators.discard(user_id)
            del session.websockets[user_id]

            # Notify other users
            await self._broadcast_to_session(session_id, {
                "type": MessageType.USER_LEAVE.value,
                "user_id": user_id,
                "collaborators": list(session.collaborators)
            })

            # Clean up empty sessions
            if not session.collaborators:
                del self.active_sessions[session_id]

        del self.user_sessions[user_id]

    async def handle_message(self, user_id: int, message: dict):
        """Handle incoming WebSocket message."""
        session_id = self.user_sessions.get(user_id)
        if not session_id:
            return

        session = self.active_sessions.get(session_id)
        if not session:
            return

        message_type = message.get("type")

        if message_type == MessageType.DOCUMENT_CHANGE.value:
            await self._handle_document_change(session, user_id, message)
        elif message_type == MessageType.CURSOR_POSITION.value:
            await self._handle_cursor_change(session, user_id, message)
        elif message_type == MessageType.TRANSLATION_UPDATE.value:
            await self._handle_translation_update(session, user_id, message)
        elif message_type == MessageType.HEARTBEAT.value:
            await self._handle_heartbeat(session, user_id)

    async def _handle_document_change(self, session: EditingSession, user_id: int, message: dict):
        """Handle document change operations."""
        change_data = message.get("data", {})

        # Apply operational transformation for conflict resolution
        transformed_change = await self._transform_change(session, change_data)

        # Update session document state
        session.document_state = await self._apply_change(session.document_state, transformed_change)
        session.last_activity = time.time()

        # Persist change to database
        await self._persist_document_change(session.session_id, user_id, transformed_change)

        # Broadcast to other users
        await self._broadcast_to_session(session.session_id, {
            "type": MessageType.DOCUMENT_CHANGE.value,
            "user_id": user_id,
            "data": transformed_change
        }, exclude_user=user_id)
```

### 2. Operational Transformation for Conflict Resolution

```python
# backend/src/jd_ingestion/websocket/operational_transform.py
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class OperationType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"

@dataclass
class Operation:
    type: OperationType
    position: int
    content: str = ""
    length: int = 0

class OperationalTransform:
    """Operational Transformation for real-time collaborative editing."""

    @staticmethod
    def transform_operations(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two concurrent operations."""
        if op1.type == OperationType.INSERT and op2.type == OperationType.INSERT:
            return OperationalTransform._transform_insert_insert(op1, op2)
        elif op1.type == OperationType.DELETE and op2.type == OperationType.DELETE:
            return OperationalTransform._transform_delete_delete(op1, op2)
        elif op1.type == OperationType.INSERT and op2.type == OperationType.DELETE:
            return OperationalTransform._transform_insert_delete(op1, op2)
        elif op1.type == OperationType.DELETE and op2.type == OperationType.INSERT:
            op2_prime, op1_prime = OperationalTransform._transform_insert_delete(op2, op1)
            return op1_prime, op2_prime
        else:
            return op1, op2

    @staticmethod
    def _transform_insert_insert(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two concurrent insert operations."""
        if op1.position <= op2.position:
            return op1, Operation(
                type=OperationType.INSERT,
                position=op2.position + len(op1.content),
                content=op2.content
            )
        else:
            return Operation(
                type=OperationType.INSERT,
                position=op1.position + len(op2.content),
                content=op1.content
            ), op2

    @staticmethod
    def _transform_delete_delete(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two concurrent delete operations."""
        if op1.position + op1.length <= op2.position:
            return op1, Operation(
                type=OperationType.DELETE,
                position=op2.position - op1.length,
                length=op2.length
            )
        elif op2.position + op2.length <= op1.position:
            return Operation(
                type=OperationType.DELETE,
                position=op1.position - op2.length,
                length=op1.length
            ), op2
        else:
            # Overlapping deletes - complex transformation needed
            return OperationalTransform._handle_overlapping_deletes(op1, op2)
```

### 3. FastAPI WebSocket Endpoints

```python
# backend/src/jd_ingestion/api/endpoints/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
import jwt

from ...database.connection import get_async_session
from ...websocket.manager import WebSocketManager, MessageType
from ...websocket.auth import authenticate_websocket_user
from ...models.editing import EditingSession as DBEditingSession

router = APIRouter()
websocket_manager = WebSocketManager()

@router.websocket("/editing/{session_id}")
async def websocket_editing_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """WebSocket endpoint for real-time collaborative editing."""
    try:
        # Authenticate user
        user_id = await authenticate_websocket_user(token, db)
        if not user_id:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # Validate session access
        session_access = await validate_session_access(session_id, user_id, db)
        if not session_access:
            await websocket.close(code=4003, reason="Session access denied")
            return

        # Connect user to session
        await websocket_manager.connect_user(websocket, session_id, user_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle message
                await websocket_manager.handle_message(user_id, message)

        except WebSocketDisconnect:
            await websocket_manager.disconnect_user(user_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")

@router.websocket("/translation/{translation_pair_id}")
async def websocket_translation_endpoint(
    websocket: WebSocket,
    translation_pair_id: str,
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """WebSocket endpoint for real-time translation editing."""
    # Similar implementation for translation-specific operations
    pass

async def validate_session_access(session_id: str, user_id: int, db: AsyncSession) -> bool:
    """Validate user access to editing session."""
    # Check if user has permission to access this editing session
    # Implementation depends on access control requirements
    return True
```

### 4. Database Schema Extensions

```sql
-- Enhanced editing sessions table
CREATE TABLE editing_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) UNIQUE NOT NULL,
    job_id INTEGER REFERENCES job_descriptions(id),
    created_by INTEGER NOT NULL, -- References users table when implemented
    session_type VARCHAR(20) DEFAULT 'editing', -- 'editing', 'translation', 'review'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'paused', 'completed'
    collaborators INTEGER[] DEFAULT '{}',
    document_state JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Real-time document changes with operational transform support
CREATE TABLE document_changes (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    user_id INTEGER NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'insert', 'delete', 'retain', 'format'
    operation_data JSONB NOT NULL, -- Operational transform data
    position INTEGER NOT NULL,
    content_before TEXT,
    content_after TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    transformed_from INTEGER REFERENCES document_changes(id),
    conflict_resolved BOOLEAN DEFAULT FALSE
);

-- WebSocket connection tracking
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    user_id INTEGER NOT NULL,
    connection_id VARCHAR(128) UNIQUE,
    connected_at TIMESTAMP DEFAULT NOW(),
    last_heartbeat TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

-- Translation-specific session data
CREATE TABLE translation_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) REFERENCES editing_sessions(session_id),
    source_job_id INTEGER REFERENCES job_descriptions(id),
    target_job_id INTEGER REFERENCES job_descriptions(id),
    source_language VARCHAR(5) NOT NULL,
    target_language VARCHAR(5) NOT NULL,
    alignment_data JSONB DEFAULT '{}',
    translation_memory_hits INTEGER DEFAULT 0,
    ai_suggestions_used INTEGER DEFAULT 0,
    human_overrides INTEGER DEFAULT 0,
    quality_score DECIMAL(3,2),
    translator_id INTEGER,
    reviewer_id INTEGER
);
```

### 5. Frontend WebSocket Client

```typescript
// src/services/websocket/collaborationClient.ts
export enum MessageType {
  DOCUMENT_CHANGE = 'document_change',
  CURSOR_POSITION = 'cursor_position',
  USER_JOIN = 'user_join',
  USER_LEAVE = 'user_leave',
  SESSION_STATE = 'session_state',
  ERROR = 'error',
  HEARTBEAT = 'heartbeat'
}

export interface DocumentChange {
  type: 'insert' | 'delete' | 'retain';
  position: number;
  content?: string;
  length?: number;
  timestamp: number;
}

export class CollaborationClient {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private userId: number;
  private token: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  private eventHandlers: Map<MessageType, Function[]> = new Map();

  constructor(sessionId: string, userId: number, token: string) {
    this.sessionId = sessionId;
    this.userId = userId;
    this.token = token;
  }

  async connect(): Promise<void> {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/editing/${this.sessionId}?token=${this.token}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected', event.code, event.reason);
      this.stopHeartbeat();

      if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => this.reconnect(), Math.pow(2, this.reconnectAttempts) * 1000);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private async reconnect(): Promise<void> {
    this.reconnectAttempts++;
    console.log(`Reconnecting attempt ${this.reconnectAttempts}...`);
    await this.connect();
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.sendMessage({
        type: MessageType.HEARTBEAT,
        timestamp: Date.now()
      });
    }, 30000); // 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  sendDocumentChange(change: DocumentChange): void {
    this.sendMessage({
      type: MessageType.DOCUMENT_CHANGE,
      data: change,
      timestamp: Date.now()
    });
  }

  sendCursorPosition(position: number, selection?: {start: number, end: number}): void {
    this.sendMessage({
      type: MessageType.CURSOR_POSITION,
      data: { position, selection },
      timestamp: Date.now()
    });
  }

  private sendMessage(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  private handleMessage(message: any): void {
    const handlers = this.eventHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message));
    }
  }

  on(eventType: MessageType, handler: Function): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
  }

  off(eventType: MessageType, handler: Function): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
}
```

## Scalability Considerations

### Redis Integration for Session Management

```python
# backend/src/jd_ingestion/websocket/redis_manager.py
import redis.asyncio as redis
import json
from typing import Dict, List, Optional

class RedisSessionManager:
    """Redis-based session management for horizontal scaling."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def store_session(self, session_id: str, session_data: dict):
        """Store session data in Redis."""
        await self.redis.hset(
            f"session:{session_id}",
            mapping={
                "data": json.dumps(session_data),
                "last_activity": str(time.time())
            }
        )
        await self.redis.expire(f"session:{session_id}", 86400)  # 24 hours

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data from Redis."""
        data = await self.redis.hget(f"session:{session_id}", "data")
        if data:
            return json.loads(data)
        return None

    async def add_user_to_session(self, session_id: str, user_id: int, server_id: str):
        """Track which server a user is connected to."""
        await self.redis.hset(f"session:{session_id}:users", str(user_id), server_id)

    async def remove_user_from_session(self, session_id: str, user_id: int):
        """Remove user from session."""
        await self.redis.hdel(f"session:{session_id}:users", str(user_id))

    async def publish_message(self, session_id: str, message: dict):
        """Publish message to all servers handling this session."""
        await self.redis.publish(f"session:{session_id}", json.dumps(message))
```

## Performance Optimizations

### Message Batching and Compression

```python
# backend/src/jd_ingestion/websocket/optimizations.py
import gzip
import json
from typing import List, Dict
import asyncio
from dataclasses import dataclass, asdict

@dataclass
class BatchedMessage:
    type: str
    messages: List[Dict]
    timestamp: float

class MessageBatcher:
    """Batch multiple operations for efficient transmission."""

    def __init__(self, batch_size: int = 10, batch_timeout: float = 0.1):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_messages: Dict[str, List[Dict]] = {}
        self.batch_timers: Dict[str, asyncio.Task] = {}

    async def add_message(self, session_id: str, message: Dict):
        """Add message to batch for session."""
        if session_id not in self.pending_messages:
            self.pending_messages[session_id] = []

        self.pending_messages[session_id].append(message)

        # Start batch timer if first message
        if len(self.pending_messages[session_id]) == 1:
            self.batch_timers[session_id] = asyncio.create_task(
                self._batch_timeout(session_id)
            )

        # Send immediately if batch is full
        if len(self.pending_messages[session_id]) >= self.batch_size:
            await self._send_batch(session_id)

    async def _batch_timeout(self, session_id: str):
        """Send batch after timeout."""
        await asyncio.sleep(self.batch_timeout)
        await self._send_batch(session_id)

    async def _send_batch(self, session_id: str):
        """Send batched messages."""
        if session_id in self.pending_messages and self.pending_messages[session_id]:
            messages = self.pending_messages[session_id].copy()
            self.pending_messages[session_id].clear()

            # Cancel timer
            if session_id in self.batch_timers:
                self.batch_timers[session_id].cancel()
                del self.batch_timers[session_id]

            # Send batched message
            batched = BatchedMessage(
                type="batch",
                messages=messages,
                timestamp=time.time()
            )

            await self._send_to_session(session_id, asdict(batched))

def compress_message(message: Dict) -> bytes:
    """Compress large messages for transmission."""
    json_str = json.dumps(message)
    if len(json_str) > 1024:  # Only compress large messages
        return gzip.compress(json_str.encode('utf-8'))
    return json_str.encode('utf-8')
```

## Security Considerations

### Authentication and Authorization

```python
# backend/src/jd_ingestion/websocket/auth.py
import jwt
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

async def authenticate_websocket_user(token: Optional[str], db: AsyncSession) -> Optional[int]:
    """Authenticate WebSocket user from JWT token."""
    if not token:
        return None

    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")

        # Validate user exists and is active
        # (Implementation depends on user management system)

        return user_id
    except jwt.InvalidTokenError:
        return None

async def authorize_session_access(session_id: str, user_id: int, db: AsyncSession) -> bool:
    """Check if user has access to editing session."""
    # Implementation depends on access control requirements
    # Could check:
    # - Document ownership
    # - Collaboration permissions
    # - Organization membership
    return True
```

## Monitoring and Metrics

### WebSocket Health Monitoring

```python
# backend/src/jd_ingestion/websocket/monitoring.py
from dataclasses import dataclass
from typing import Dict
import time

@dataclass
class WebSocketMetrics:
    active_connections: int
    active_sessions: int
    messages_per_second: float
    average_response_time: float
    error_rate: float

class WebSocketMonitor:
    """Monitor WebSocket performance and health."""

    def __init__(self):
        self.metrics = WebSocketMetrics(0, 0, 0.0, 0.0, 0.0)
        self.message_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.last_reset = time.time()

    def record_message(self, response_time: float):
        """Record successful message processing."""
        self.message_count += 1
        self.response_times.append(response_time)

    def record_error(self):
        """Record error occurrence."""
        self.error_count += 1

    def get_current_metrics(self) -> WebSocketMetrics:
        """Get current performance metrics."""
        now = time.time()
        time_delta = now - self.last_reset

        if time_delta > 0:
            self.metrics.messages_per_second = self.message_count / time_delta
            self.metrics.error_rate = self.error_count / max(self.message_count, 1)

        if self.response_times:
            self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)

        return self.metrics

    def reset_metrics(self):
        """Reset metrics for next measurement period."""
        self.message_count = 0
        self.error_count = 0
        self.response_times.clear()
        self.last_activity = time.time()
```

## Next Steps

1. **Implement Core WebSocket Infrastructure** - Set up basic FastAPI WebSocket endpoints
2. **Database Schema Migration** - Add editing sessions and document changes tables
3. **Frontend WebSocket Client** - Implement React hooks for real-time collaboration
4. **Operational Transformation** - Implement conflict resolution algorithms
5. **Redis Integration** - Add horizontal scaling support
6. **Testing Strategy** - Comprehensive testing for real-time features

This architecture provides a robust foundation for real-time collaborative editing while maintaining scalability and performance requirements for government-level usage.
