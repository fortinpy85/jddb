/**
 * React Hook for Collaborative Editing
 *
 * Manages collaborative editing sessions with:
 * - Real-time document synchronization
 * - User presence tracking
 * - Operational transformation for concurrent edits
 * - Cursor position sharing
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import { WebSocketMessage } from '@/lib/websocket-client';

export interface Participant {
  userId: number;
  cursorPosition: number | null;
}

export interface Operation {
  type: 'insert' | 'delete';
  position?: number;
  start?: number;
  end?: number;
  text?: string;
}

export interface SessionState {
  sessionId: string;
  jobId: number;
  documentState: string;
  participants: number[];
  operationCount: number;
}

export interface UseCollaborativeEditorOptions {
  sessionId: string;
  userId: number;
  jobId: number;
  apiUrl?: string;
  onDocumentChange?: (content: string) => void;
  onParticipantsChange?: (participants: number[]) => void;
  onOperationApplied?: (operation: Operation) => void;
}

export interface UseCollaborativeEditorReturn {
  isConnected: boolean;
  sessionState: SessionState | null;
  participants: Participant[];
  applyOperation: (operation: Operation) => void;
  updateCursorPosition: (position: number) => void;
  connectionState: string;
}

/**
 * Hook for managing collaborative editing sessions
 */
export function useCollaborativeEditor(
  options: UseCollaborativeEditorOptions | null
): UseCollaborativeEditorReturn {
  // Handle null options (when collaboration is disabled)
  if (!options) {
    return {
      isConnected: false,
      sessionState: null,
      participants: [],
      applyOperation: () => {},
      updateCursorPosition: () => {},
      connectionState: 'disconnected',
    };
  }

  const {
    sessionId,
    userId,
    jobId,
    apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    onDocumentChange,
    onParticipantsChange,
    onOperationApplied,
  } = options;

  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const operationQueueRef = useRef<Operation[]>([]);

  // Construct WebSocket URL
  const wsUrl = `${apiUrl.replace('http', 'ws').replace('/api', '')}/api/ws/edit/${sessionId}?user_id=${userId}&job_id=${jobId}`;

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case 'session_state':
          // Initial session state received
          setSessionState({
            sessionId: message.session_id,
            jobId: message.job_id,
            documentState: message.document_state,
            participants: message.participants || [],
            operationCount: message.operation_count || 0,
          });
          onParticipantsChange?.(message.participants || []);
          onDocumentChange?.(message.document_state);
          break;

        case 'operation':
          // Remote operation received from another user
          const operation = message.operation as Operation;
          if (operation && sessionState) {
            // Apply operation to local state
            const newDocumentState = applyOperationToDocument(
              sessionState.documentState,
              operation
            );
            setSessionState((prev) =>
              prev
                ? {
                    ...prev,
                    documentState: newDocumentState,
                    operationCount: prev.operationCount + 1,
                  }
                : null
            );
            onDocumentChange?.(newDocumentState);
            onOperationApplied?.(operation);
          }
          break;

        case 'operation_ack':
          // Operation acknowledged by server
          console.log('Operation acknowledged:', message.operation_id);
          break;

        case 'user_joined':
          // New user joined the session
          const newParticipants = message.participants as number[];
          setSessionState((prev) =>
            prev ? { ...prev, participants: newParticipants } : null
          );
          onParticipantsChange?.(newParticipants);
          break;

        case 'cursor_update':
          // Update cursor position for a participant
          setParticipants((prev) => {
            const updated = prev.filter((p) => p.userId !== message.user_id);
            return [
              ...updated,
              { userId: message.user_id, cursorPosition: message.position },
            ];
          });
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    },
    [sessionState, onDocumentChange, onParticipantsChange, onOperationApplied]
  );

  const { connectionState, isConnected, send } = useWebSocket(wsUrl, {
    enabled: true,
    onMessage: handleMessage,
    onOpen: () => {
      console.log(`Connected to collaborative session: ${sessionId}`);
      // Process any queued operations
      while (operationQueueRef.current.length > 0) {
        const op = operationQueueRef.current.shift();
        if (op) {
          send({ type: 'operation', operation: op });
        }
      }
    },
    onClose: () => {
      console.log(`Disconnected from session: ${sessionId}`);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
  });

  /**
   * Apply a local operation and broadcast to other participants
   */
  const applyOperation = useCallback(
    (operation: Operation) => {
      if (isConnected) {
        send({ type: 'operation', operation });

        // Optimistically apply to local state
        if (sessionState) {
          const newDocumentState = applyOperationToDocument(
            sessionState.documentState,
            operation
          );
          setSessionState((prev) =>
            prev
              ? {
                  ...prev,
                  documentState: newDocumentState,
                  operationCount: prev.operationCount + 1,
                }
              : null
          );
          onDocumentChange?.(newDocumentState);
        }
      } else {
        // Queue operation for later if not connected
        operationQueueRef.current.push(operation);
      }
    },
    [isConnected, send, sessionState, onDocumentChange]
  );

  /**
   * Update cursor position and broadcast to other participants
   */
  const updateCursorPosition = useCallback(
    (position: number) => {
      if (isConnected) {
        send({ type: 'cursor_update', position });
      }
    },
    [isConnected, send]
  );

  return {
    isConnected,
    sessionState,
    participants,
    applyOperation,
    updateCursorPosition,
    connectionState,
  };
}

/**
 * Apply an operation to a document string
 */
function applyOperationToDocument(document: string, operation: Operation): string {
  if (operation.type === 'insert') {
    const position = operation.position ?? 0;
    const text = operation.text ?? '';
    return document.slice(0, position) + text + document.slice(position);
  } else if (operation.type === 'delete') {
    const start = operation.start ?? 0;
    const end = operation.end ?? start + 1;
    return document.slice(0, start) + document.slice(end);
  }
  return document;
}