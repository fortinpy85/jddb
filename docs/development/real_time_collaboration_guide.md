# Real-Time Collaboration Guide

## 1. Overview

This document provides a technical guide to the real-time collaboration features being built in Phase 2 of the JDDB project. The core of this system is a WebSocket connection that allows for low-latency, bidirectional communication between clients and the server.

## 2. Architecture

- **Server:** The FastAPI backend exposes a WebSocket endpoint at `ws://localhost:8000/ws/editor/{document_id}`.
- **Connection Management:** A central `ConnectionManager` class on the backend keeps track of all active WebSocket connections for each document.
- **Client:** The React frontend uses a WebSocket wrapper service to connect to the server and send/receive messages.
- **State Management:** The frontend uses a Zustand store (`collaborationStore`) to manage the real-time state of the document and the presence of other users.

## 3. WebSocket Messaging Protocol

Communication over the WebSocket is done via a standardized JSON message format. Every message has a `type` field that indicates its purpose.

### 3.1. Client-to-Server Messages

- **`user.join`**: Sent when a user first connects to the WebSocket.
    - **Payload:** `{ "user_id": string, "username": string }`

- **`editor.update`**: Sent whenever the user makes a change to the document.
    - **Payload:** `{ "content": string }` (The full content of the editor)

- **`comment.new`**: Sent when a user adds a new comment.
    - **Payload:** `{ "text": string, "selection_start": int, "selection_end": int }`

### 3.2. Server-to-Client Messages

- **`user.list.update`**: Sent to all clients in a room when a user joins or leaves.
    - **Payload:** `[{ "user_id": string, "username": string }, ...]` (A list of all current users)

- **`editor.broadcast`**: Sent to all other clients in a room when one user sends an `editor.update` message.
    - **Payload:** `{ "content": string }` (The updated content of the editor)

- **`comment.broadcast.new`**: Sent to all clients in a room when a new comment is added.
    - **Payload:** `{ "id": int, "text": string, ... }` (The full comment object)

## 4. Workflow Example: A User Edits a Document

1.  **User A** and **User B** are both connected to `ws://localhost:8000/ws/editor/123`.
2.  **User A** types a character in the editor.
3.  The React component's `onChange` handler is triggered.
4.  The frontend sends an `editor.update` message to the server with the full new content of the editor.
    ```json
    { "type": "editor.update", "payload": { "content": "The new document text..." } }
    ```
5.  The server receives the message and identifies the sender (**User A**).
6.  The server broadcasts an `editor.broadcast` message to all *other* clients in the room for document `123` (i.e., to **User B**).
    ```json
    { "type": "editor.broadcast", "payload": { "content": "The new document text..." } }
    ```
7.  **User B**'s client receives the `editor.broadcast` message.
8.  The frontend updates the `collaborationStore` with the new content.
9.  The React editor component, which is subscribed to the store, re-renders to display the updated content from **User A**.

## 5. Conflict Resolution

- **Strategy:** Last-Write-Wins.
- **Rationale:** For the initial prototype, we are using a simple "last-write-wins" strategy. Since the updates happen very quickly, the chances of a meaningful conflict are low for a small number of collaborators. The user who saves last will have their changes overwrite others.
- **Future Improvements:** For the full production version, we will investigate more advanced conflict resolution strategies like Operational Transformation (OT) or Conflict-free Replicated Data Types (CRDTs) if necessary.
