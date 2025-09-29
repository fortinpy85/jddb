# Real-time API Endpoints Documentation

## Table of Contents
1. [Overview](#overview)
2. [WebSocket Endpoints](#websocket-endpoints)
3. [HTTP API Endpoints](#http-api-endpoints)
4. [Message Protocol](#message-protocol)
5. [Authentication](#authentication)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)
9. [Client Libraries](#client-libraries)
10. [Testing](#testing)

## Overview

The JDDB real-time API provides WebSocket connections for collaborative editing, live presence awareness, and instant synchronization. This documentation covers all real-time endpoints, message formats, and integration patterns.

### Base URLs

- **Production**: `wss://api.jddb.gc.ca`
- **Staging**: `wss://api-staging.jddb.gc.ca`
- **Development**: `ws://localhost:8000`

### Protocol Support

- **WebSocket**: Primary real-time communication
- **HTTP/REST**: Fallback and supplementary operations
- **Server-Sent Events**: Alternative for read-only real-time data

## WebSocket Endpoints

### Document Collaboration

#### Connect to Document Session

```
WSS /ws/document/{document_id}
```

Establishes a WebSocket connection for collaborative editing of a specific document.

**Parameters:**
- `document_id` (string): Unique identifier for the job description document
- `token` (query string): JWT authentication token

**Example:**
```
wss://api.jddb.gc.ca/ws/document/jd_12345?token=eyJhbGciOiJIUzI1NiIs...
```

**Connection Flow:**
1. Client connects with authentication token
2. Server validates permissions for document access
3. Server sends initial document state
4. Real-time message exchange begins

#### Global Presence

```
WSS /ws/presence
```

Connect to global presence system to see all active users across the platform.

**Use Cases:**
- Administrative dashboards
- System monitoring
- Global user activity tracking

### Translation Memory

#### Translation Session

```
WSS /ws/translation/{project_id}
```

Real-time translation memory updates and suggestions.

**Parameters:**
- `project_id` (string): Translation project identifier
- `source_lang` (query): Source language code (e.g., 'en')
- `target_lang` (query): Target language code (e.g., 'fr')

**Features:**
- Live translation suggestions
- Collaborative glossary updates
- Translation quality feedback
- Batch translation status

### System Monitoring

#### Health Monitoring

```
WSS /ws/monitoring
```

Real-time system health and performance metrics.

**Access Level:** Admin only

**Metrics Provided:**
- Connection counts
- Message throughput
- Error rates
- Resource utilization

## HTTP API Endpoints

### Session Management

#### Start Editing Session

```http
POST /api/sessions
```

Create a new collaborative editing session.

**Request Body:**
```json
{
  "document_id": "jd_12345",
  "session_type": "collaborative_edit",
  "participants": ["user_1", "user_2"],
  "settings": {
    "auto_save_interval": 30,
    "max_participants": 10,
    "public_session": false
  }
}
```

**Response:**
```json
{
  "session_id": "sess_67890",
  "websocket_url": "wss://api.jddb.gc.ca/ws/document/jd_12345",
  "expires_at": "2025-09-21T18:00:00Z",
  "participants": [
    {
      "user_id": "user_1",
      "display_name": "John Doe",
      "role": "editor",
      "joined_at": "2025-09-21T12:00:00Z"
    }
  ]
}
```

#### Get Active Sessions

```http
GET /api/sessions/active
```

Retrieve list of currently active editing sessions.

**Query Parameters:**
- `user_id` (optional): Filter by specific user
- `document_id` (optional): Filter by document
- `page` (optional): Page number for pagination
- `limit` (optional): Items per page (max 100)

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "sess_67890",
      "document_id": "jd_12345",
      "document_title": "Director, Business Analysis",
      "participant_count": 3,
      "started_at": "2025-09-21T12:00:00Z",
      "last_activity": "2025-09-21T12:45:00Z",
      "status": "active"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "pages": 3,
    "per_page": 10
  }
}
```

#### End Session

```http
DELETE /api/sessions/{session_id}
```

Terminate an active editing session.

**Response:**
```json
{
  "message": "Session terminated successfully",
  "final_save_completed": true,
  "participants_notified": 3
}
```

### Document Operations

#### Get Document State

```http
GET /api/documents/{document_id}/state
```

Retrieve the current state of a document including all edits.

**Query Parameters:**
- `version` (optional): Specific version number
- `include_metadata` (optional): Include edit metadata

**Response:**
```json
{
  "document_id": "jd_12345",
  "version": 42,
  "content": {
    "sections": {
      "general_accountability": "Manages the overall...",
      "organization_structure": "Reports to Deputy Minister...",
      "nature_and_scope": "The position is responsible..."
    }
  },
  "metadata": {
    "last_modified": "2025-09-21T12:45:30Z",
    "last_modified_by": "user_123",
    "word_count": 1205,
    "language": "en",
    "translation_status": "in_progress"
  },
  "active_editors": [
    {
      "user_id": "user_123",
      "display_name": "Jane Smith",
      "cursor_position": 1250,
      "selection": {"start": 1200, "end": 1250},
      "last_activity": "2025-09-21T12:45:25Z"
    }
  ]
}
```

#### Apply Document Changes

```http
POST /api/documents/{document_id}/changes
```

Apply a batch of changes to a document (alternative to WebSocket for bulk operations).

**Request Body:**
```json
{
  "changes": [
    {
      "operation": "insert",
      "position": 1250,
      "content": "Additional responsibility: ",
      "metadata": {
        "user_id": "user_123",
        "timestamp": "2025-09-21T12:45:30Z",
        "client_id": "client_abc123"
      }
    },
    {
      "operation": "delete",
      "position": 800,
      "length": 25,
      "metadata": {
        "user_id": "user_123",
        "timestamp": "2025-09-21T12:45:32Z",
        "client_id": "client_abc123"
      }
    }
  ],
  "base_version": 41,
  "conflict_resolution": "operational_transform"
}
```

**Response:**
```json
{
  "applied_changes": 2,
  "new_version": 42,
  "conflicts_resolved": 1,
  "operational_transforms": [
    {
      "original_position": 1250,
      "transformed_position": 1225,
      "reason": "prior_deletion"
    }
  ]
}
```

### Presence and Activity

#### Update User Presence

```http
PUT /api/presence/{user_id}
```

Update user's presence status and activity.

**Request Body:**
```json
{
  "status": "active",
  "current_document": "jd_12345",
  "cursor_position": 1250,
  "selection": {"start": 1200, "end": 1250},
  "activity": "editing"
}
```

**Response:**
```json
{
  "updated": true,
  "broadcast_sent": true,
  "active_users_in_document": 3
}
```

#### Get Document Presence

```http
GET /api/documents/{document_id}/presence
```

Get all users currently active in a document.

**Response:**
```json
{
  "document_id": "jd_12345",
  "active_users": [
    {
      "user_id": "user_123",
      "display_name": "Jane Smith",
      "avatar_url": "https://avatars.example.com/user_123.jpg",
      "status": "active",
      "cursor_position": 1250,
      "selection": {"start": 1200, "end": 1250},
      "last_activity": "2025-09-21T12:45:25Z",
      "color": "#ff6b6b"
    }
  ],
  "total_viewers": 7,
  "total_editors": 3
}
```

### Translation Memory

#### Get Translation Suggestions

```http
POST /api/translation/suggestions
```

Get translation suggestions for specific text.

**Request Body:**
```json
{
  "source_text": "The incumbent is responsible for strategic planning",
  "source_language": "en",
  "target_language": "fr",
  "context": {
    "document_type": "job_description",
    "section": "general_accountability",
    "domain": "government"
  },
  "max_suggestions": 5,
  "min_confidence": 0.7
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "translated_text": "Le titulaire est responsable de la planification stratégique",
      "confidence": 0.95,
      "match_type": "exact",
      "source": "translation_memory",
      "usage_count": 15,
      "last_used": "2025-09-15T10:30:00Z",
      "contributors": ["translator_456"]
    },
    {
      "translated_text": "L'occupant du poste est responsable de la planification stratégique",
      "confidence": 0.88,
      "match_type": "fuzzy",
      "similarity": 0.92,
      "source": "similar_document",
      "context_match": true
    }
  ],
  "glossary_terms": [
    {
      "term": "incumbent",
      "translation": "titulaire",
      "mandatory": true,
      "domain": "government_hr"
    }
  ]
}
```

#### Submit Translation

```http
POST /api/translation/submit
```

Submit a new translation to the translation memory.

**Request Body:**
```json
{
  "source_text": "The incumbent is responsible for strategic planning",
  "translated_text": "Le titulaire est responsable de la planification stratégique",
  "source_language": "en",
  "target_language": "fr",
  "context": {
    "document_id": "jd_12345",
    "document_type": "job_description",
    "section": "general_accountability"
  },
  "quality_rating": 5,
  "reviewed": true
}
```

**Response:**
```json
{
  "translation_id": "trans_98765",
  "status": "accepted",
  "added_to_memory": true,
  "confidence_score": 0.95,
  "requires_review": false
}
```

## Message Protocol

### WebSocket Message Format

All WebSocket messages follow a consistent JSON structure:

```json
{
  "type": "message_type",
  "payload": {
    // Message-specific data
  },
  "metadata": {
    "timestamp": "2025-09-21T12:45:30.123Z",
    "user_id": "user_123",
    "session_id": "sess_67890",
    "client_id": "client_abc123",
    "version": 1,
    "correlation_id": "corr_xyz789"
  }
}
```

### Message Types

#### Document Operations

##### Document Change
```json
{
  "type": "document.change",
  "payload": {
    "operation": "insert|delete|replace",
    "position": 1250,
    "content": "New content",
    "length": 15,
    "section": "general_accountability"
  }
}
```

##### Document Save
```json
{
  "type": "document.save",
  "payload": {
    "version": 42,
    "saved_sections": ["general_accountability", "organization_structure"],
    "save_type": "auto|manual",
    "success": true
  }
}
```

#### Collaboration Messages

##### Cursor Position
```json
{
  "type": "cursor.position",
  "payload": {
    "position": 1250,
    "section": "general_accountability"
  }
}
```

##### Text Selection
```json
{
  "type": "selection.change",
  "payload": {
    "start": 1200,
    "end": 1250,
    "section": "general_accountability"
  }
}
```

##### User Presence
```json
{
  "type": "user.presence",
  "payload": {
    "user_id": "user_456",
    "status": "joined|active|idle|left",
    "display_name": "John Doe",
    "avatar_url": "https://avatars.example.com/user_456.jpg",
    "color": "#51cf66"
  }
}
```

#### System Messages

##### Heartbeat
```json
{
  "type": "system.heartbeat",
  "payload": {
    "server_time": "2025-09-21T12:45:30.123Z",
    "connection_id": "conn_123abc"
  }
}
```

##### Error
```json
{
  "type": "system.error",
  "payload": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many messages sent",
    "retry_after": 60,
    "severity": "warning|error|critical"
  }
}
```

##### Synchronization Request
```json
{
  "type": "sync.request",
  "payload": {
    "last_known_version": 40,
    "sections": ["general_accountability"]
  }
}
```

##### Synchronization Response
```json
{
  "type": "sync.response",
  "payload": {
    "current_version": 42,
    "changes_since_version": [
      {
        "version": 41,
        "operation": "insert",
        "position": 1200,
        "content": "New text",
        "user_id": "user_789",
        "timestamp": "2025-09-21T12:40:00Z"
      }
    ],
    "full_document_state": {
      // Complete document content
    }
  }
}
```

#### Translation Messages

##### Translation Request
```json
{
  "type": "translation.request",
  "payload": {
    "source_text": "Strategic planning responsibility",
    "source_language": "en",
    "target_language": "fr",
    "context": {
      "section": "general_accountability"
    }
  }
}
```

##### Translation Suggestion
```json
{
  "type": "translation.suggestion",
  "payload": {
    "suggestions": [
      {
        "text": "Responsabilité de planification stratégique",
        "confidence": 0.95,
        "match_type": "exact"
      }
    ],
    "correlation_id": "corr_xyz789"
  }
}
```

## Authentication

### JWT Token Authentication

WebSocket connections require JWT authentication via query parameter:

```
wss://api.jddb.gc.ca/ws/document/jd_12345?token=eyJhbGciOiJIUzI1NiIs...
```

### Token Requirements

- **Valid JWT token** with appropriate scopes
- **Non-expired** token (check `exp` claim)
- **Document access permissions** for the specific resource

### Token Refresh

```javascript
// Client-side token refresh
const refreshToken = async () => {
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshToken}`
    }
  });

  const { access_token } = await response.json();

  // Reconnect WebSocket with new token
  await websocket.reconnect(`?token=${access_token}`);
};
```

### Permission Scopes

Required scopes for different operations:

- `document:read` - View document content
- `document:write` - Edit document content
- `document:admin` - Administrative operations
- `translation:read` - Access translation memory
- `translation:write` - Submit translations
- `presence:read` - View user presence
- `presence:write` - Update own presence

## Error Handling

### WebSocket Error Codes

| Code | Name | Description | Client Action |
|------|------|-------------|---------------|
| 1000 | Normal Closure | Session ended normally | None required |
| 1001 | Going Away | Server shutting down | Reconnect after delay |
| 1006 | Abnormal Closure | Connection lost | Reconnect with backoff |
| 1008 | Policy Violation | Authentication failed | Refresh token and retry |
| 1011 | Server Error | Internal server error | Report to support |
| 4000 | Rate Limited | Too many messages | Wait and retry |
| 4001 | Unauthorized | Invalid permissions | Refresh permissions |
| 4002 | Document Locked | Document is locked | Retry later |

### HTTP Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid document ID format",
    "details": {
      "field": "document_id",
      "expected": "string matching pattern jd_[0-9]+"
    },
    "request_id": "req_123456789",
    "timestamp": "2025-09-21T12:45:30Z"
  }
}
```

### Error Recovery Strategies

#### Connection Loss
1. **Detect disconnection** via heartbeat timeout
2. **Save current state** locally
3. **Attempt reconnection** with exponential backoff
4. **Sync state** after successful reconnection

#### Conflict Resolution
1. **Receive conflict notification**
2. **Apply operational transformation**
3. **Merge changes** automatically
4. **Notify user** if manual resolution needed

#### Authentication Errors
1. **Attempt token refresh**
2. **Reconnect with new token**
3. **Redirect to login** if refresh fails

## Rate Limiting

### Connection Limits

- **Per User**: 10 concurrent WebSocket connections
- **Per Document**: 50 concurrent editors
- **Global**: 10,000 concurrent connections

### Message Rate Limits

- **Per Connection**: 100 messages per minute
- **Burst Limit**: 10 messages per second
- **Large Messages**: 1 per second (>10KB)

### Rate Limit Headers

HTTP endpoints include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1632150000
X-RateLimit-Retry-After: 60
```

### Rate Limit Exceeded Response

```json
{
  "type": "system.error",
  "payload": {
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "retry_after": 60,
    "limit_type": "message_rate",
    "current_rate": "105 messages/minute",
    "allowed_rate": "100 messages/minute"
  }
}
```

## Examples

### JavaScript Client

```javascript
class JDDBRealtimeClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.websocket = null;
    this.messageHandlers = new Map();
  }

  async connectToDocument(documentId) {
    const wsUrl = `${this.baseUrl}/ws/document/${documentId}?token=${this.token}`;

    this.websocket = new WebSocket(wsUrl);

    this.websocket.onopen = () => {
      console.log('Connected to document:', documentId);
      this.startHeartbeat();
    };

    this.websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.websocket.onclose = (event) => {
      console.log('Disconnected:', event.code, event.reason);
      this.handleReconnection();
    };

    this.websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  sendDocumentChange(operation, position, content) {
    const message = {
      type: 'document.change',
      payload: {
        operation,
        position,
        content
      },
      metadata: {
        timestamp: new Date().toISOString(),
        client_id: this.clientId
      }
    };

    this.send(message);
  }

  updateCursorPosition(position, section) {
    const message = {
      type: 'cursor.position',
      payload: { position, section }
    };

    this.send(message);
  }

  send(message) {
    if (this.websocket?.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  onMessage(type, handler) {
    this.messageHandlers.set(type, handler);
  }

  handleMessage(message) {
    const handler = this.messageHandlers.get(message.type);
    if (handler) {
      handler(message.payload, message.metadata);
    }
  }

  startHeartbeat() {
    setInterval(() => {
      this.send({
        type: 'system.heartbeat',
        payload: { client_time: Date.now() }
      });
    }, 30000);
  }
}

// Usage example
const client = new JDDBRealtimeClient('wss://api.jddb.gc.ca', authToken);

await client.connectToDocument('jd_12345');

// Handle incoming document changes
client.onMessage('document.change', (payload, metadata) => {
  applyChangeToEditor(payload.operation, payload.position, payload.content);
  showUserActivity(metadata.user_id, payload);
});

// Handle user presence updates
client.onMessage('user.presence', (payload) => {
  updateUserPresence(payload.user_id, payload.status);
});

// Send a document change
client.sendDocumentChange('insert', 1250, 'New text content');
```

### Python Client

```python
import asyncio
import websockets
import json
from typing import Callable, Dict, Any

class JDDBRealtimeClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.websocket = None
        self.message_handlers: Dict[str, Callable] = {}

    async def connect_to_document(self, document_id: str):
        ws_url = f"{self.base_url}/ws/document/{document_id}?token={self.token}"

        self.websocket = await websockets.connect(ws_url)

        # Start message handler
        asyncio.create_task(self._handle_messages())

        # Start heartbeat
        asyncio.create_task(self._heartbeat())

    async def _handle_messages(self):
        async for message in self.websocket:
            data = json.loads(message)
            await self._process_message(data)

    async def _process_message(self, message: Dict[str, Any]):
        msg_type = message.get('type')
        handler = self.message_handlers.get(msg_type)

        if handler:
            await handler(message['payload'], message.get('metadata', {}))

    async def send_document_change(self, operation: str, position: int, content: str):
        message = {
            'type': 'document.change',
            'payload': {
                'operation': operation,
                'position': position,
                'content': content
            },
            'metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id
            }
        }

        await self.send(message)

    async def send(self, message: Dict[str, Any]):
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    def on_message(self, message_type: str, handler: Callable):
        self.message_handlers[message_type] = handler

    async def _heartbeat(self):
        while True:
            await asyncio.sleep(30)
            await self.send({
                'type': 'system.heartbeat',
                'payload': {'client_time': time.time()}
            })

# Usage example
async def main():
    client = JDDBRealtimeClient('wss://api.jddb.gc.ca', auth_token)

    await client.connect_to_document('jd_12345')

    # Handle document changes
    async def handle_document_change(payload, metadata):
        print(f"Document change: {payload}")
        # Apply change to local document

    client.on_message('document.change', handle_document_change)

    # Send a change
    await client.send_document_change('insert', 1250, 'New content')

    # Keep connection alive
    await asyncio.sleep(3600)  # 1 hour

asyncio.run(main())
```

## Client Libraries

### Official Libraries

#### JavaScript/TypeScript
```bash
npm install @jddb/realtime-client
```

```typescript
import { JDDBRealtimeClient } from '@jddb/realtime-client';

const client = new JDDBRealtimeClient({
  baseUrl: 'wss://api.jddb.gc.ca',
  token: authToken,
  autoReconnect: true,
  heartbeatInterval: 30000
});
```

#### Python
```bash
pip install jddb-realtime-client
```

```python
from jddb_realtime import RealtimeClient

client = RealtimeClient(
    base_url='wss://api.jddb.gc.ca',
    token=auth_token,
    auto_reconnect=True
)
```

### Configuration Options

```javascript
const client = new JDDBRealtimeClient({
  baseUrl: 'wss://api.jddb.gc.ca',
  token: authToken,

  // Connection options
  autoReconnect: true,
  maxReconnectAttempts: 10,
  reconnectDelay: 1000,
  maxReconnectDelay: 30000,

  // Message options
  messageQueueSize: 1000,
  enableCompression: true,
  batchMessages: true,
  batchDelay: 50,

  // Debug options
  debug: false,
  logLevel: 'info'
});
```

## Testing

### WebSocket Testing with Jest

```javascript
// __tests__/websocket.test.js
import { JDDBRealtimeClient } from '../src/realtime-client';
import WS from 'jest-websocket-mock';

describe('JDDB Realtime Client', () => {
  let server;
  let client;

  beforeEach(async () => {
    server = new WS('ws://localhost:8000');
    client = new JDDBRealtimeClient('ws://localhost:8000', 'test-token');
  });

  afterEach(() => {
    WS.clean();
  });

  test('should connect and receive initial state', async () => {
    await client.connectToDocument('jd_test');

    expect(server).toHaveReceivedMessages([
      expect.objectContaining({
        type: 'document.join',
        payload: { document_id: 'jd_test' }
      })
    ]);

    // Simulate server response
    server.send(JSON.stringify({
      type: 'document.state',
      payload: {
        version: 1,
        content: 'Initial document content'
      }
    }));

    expect(client.documentState.version).toBe(1);
  });

  test('should handle document changes', async () => {
    await client.connectToDocument('jd_test');

    const changeHandler = jest.fn();
    client.onMessage('document.change', changeHandler);

    // Simulate incoming change
    server.send(JSON.stringify({
      type: 'document.change',
      payload: {
        operation: 'insert',
        position: 10,
        content: 'New text'
      }
    }));

    expect(changeHandler).toHaveBeenCalledWith(
      expect.objectContaining({
        operation: 'insert',
        position: 10,
        content: 'New text'
      }),
      expect.any(Object)
    );
  });
});
```

### Load Testing with Artillery

```yaml
# load-test.yml
config:
  target: 'wss://api.jddb.gc.ca'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50
      name: "Load test"
  ws:
    headers:
      Authorization: "Bearer {{ $env.TEST_TOKEN }}"

scenarios:
  - name: "Collaborative editing"
    weight: 70
    engine: ws
    flow:
      - connect:
          url: "/ws/document/test_doc_{{ $randomInt(1, 100) }}"
      - think: 1
      - send:
          message: |
            {
              "type": "document.change",
              "payload": {
                "operation": "insert",
                "position": {{ $randomInt(0, 1000) }},
                "content": "Test content {{ $timestamp }}"
              }
            }
      - think: 2
      - send:
          message: |
            {
              "type": "cursor.position",
              "payload": {
                "position": {{ $randomInt(0, 1000) }}
              }
            }
      - think: 5

  - name: "Translation requests"
    weight: 30
    engine: ws
    flow:
      - connect:
          url: "/ws/translation/test_project"
      - think: 1
      - send:
          message: |
            {
              "type": "translation.request",
              "payload": {
                "source_text": "Test text for translation",
                "source_language": "en",
                "target_language": "fr"
              }
            }
      - think: 3
```

### Integration Tests

```python
# test_realtime_integration.py
import pytest
import asyncio
import websockets
import json

@pytest.mark.asyncio
async def test_multiple_users_collaboration():
    """Test multiple users editing the same document"""

    # Connect three users to the same document
    user1_ws = await websockets.connect(
        f"ws://localhost:8000/ws/document/test_doc?token={user1_token}"
    )
    user2_ws = await websockets.connect(
        f"ws://localhost:8000/ws/document/test_doc?token={user2_token}"
    )
    user3_ws = await websockets.connect(
        f"ws://localhost:8000/ws/document/test_doc?token={user3_token}"
    )

    # User 1 makes a change
    change_message = {
        "type": "document.change",
        "payload": {
            "operation": "insert",
            "position": 0,
            "content": "Hello "
        }
    }
    await user1_ws.send(json.dumps(change_message))

    # User 2 and 3 should receive the change
    user2_response = await user2_ws.recv()
    user3_response = await user3_ws.recv()

    user2_data = json.loads(user2_response)
    user3_data = json.loads(user3_response)

    assert user2_data["type"] == "document.change"
    assert user2_data["payload"]["content"] == "Hello "
    assert user3_data["type"] == "document.change"
    assert user3_data["payload"]["content"] == "Hello "

    # Test concurrent changes
    await asyncio.gather(
        user2_ws.send(json.dumps({
            "type": "document.change",
            "payload": {
                "operation": "insert",
                "position": 6,
                "content": "World"
            }
        })),
        user3_ws.send(json.dumps({
            "type": "document.change",
            "payload": {
                "operation": "insert",
                "position": 6,
                "content": "Everyone"
            }
        }))
    )

    # Verify operational transformation handled conflicts
    # Both users should receive both changes with adjusted positions
    user1_msg1 = json.loads(await user1_ws.recv())
    user1_msg2 = json.loads(await user1_ws.recv())

    # Final document should contain both changes
    # Exact order depends on timestamp or user priority
    assert "World" in [user1_msg1["payload"]["content"], user1_msg2["payload"]["content"]]
    assert "Everyone" in [user1_msg1["payload"]["content"], user1_msg2["payload"]["content"]]
```

## Performance Considerations

### Connection Scaling

- **Sticky Sessions**: Required for WebSocket connections
- **Load Balancing**: Use Redis pub/sub for cross-server communication
- **Connection Pooling**: Reuse database connections efficiently

### Memory Management

- **Message History**: Limit stored message history per session
- **Presence Data**: Clean up stale presence information
- **Document State**: Use efficient diff algorithms

### Network Optimization

- **Message Compression**: Enable for messages >1KB
- **Batching**: Group multiple small changes
- **Heartbeat Optimization**: Adjust frequency based on load

### Monitoring Metrics

- **Connection Count**: Track active WebSocket connections
- **Message Throughput**: Messages per second by type
- **Latency**: Round-trip time for message delivery
- **Error Rates**: Failed connections and message errors
- **Resource Usage**: CPU, memory, and network utilization

---

*This documentation covers the complete real-time API for JDDB collaborative editing. For additional technical details, consult the OpenAPI specification or contact the development team.*