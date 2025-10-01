/**
 * React Hook for WebSocket Connection Management
 *
 * Provides a simple interface for managing WebSocket connections in React components.
 * Handles connection lifecycle, message sending/receiving, and state management.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import {
  CollaborativeWebSocketClient,
  ConnectionState,
  WebSocketMessage,
  WebSocketConfig,
} from "@/lib/websocket-client";

export interface UseWebSocketOptions extends Omit<WebSocketConfig, "url"> {
  enabled?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
}

export interface UseWebSocketReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  send: (message: WebSocketMessage) => void;
  connect: () => void;
  disconnect: () => void;
  lastMessage: WebSocketMessage | null;
}

/**
 * Hook for managing WebSocket connections
 *
 * @param url - WebSocket URL to connect to
 * @param options - Configuration options
 * @returns WebSocket connection state and utilities
 */
export function useWebSocket(
  url: string | null,
  options: UseWebSocketOptions = {},
): UseWebSocketReturn {
  const {
    enabled = true,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeatInterval,
  } = options;

  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const clientRef = useRef<CollaborativeWebSocketClient | null>(null);

  // Initialize WebSocket client
  useEffect(() => {
    if (!url || !enabled) {
      return;
    }

    const client = new CollaborativeWebSocketClient({
      url,
      reconnectInterval,
      maxReconnectAttempts,
      heartbeatInterval,
    });

    client.on({
      onOpen: () => {
        onOpen?.();
      },
      onClose: (event) => {
        onClose?.(event);
      },
      onError: (error) => {
        onError?.(error);
      },
      onMessage: (message) => {
        setLastMessage(message);
        onMessage?.(message);
      },
      onStateChange: (state) => {
        setConnectionState(state);
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
    };
  }, [
    url,
    enabled,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval,
    maxReconnectAttempts,
    heartbeatInterval,
  ]);

  const send = useCallback((message: WebSocketMessage) => {
    clientRef.current?.send(message);
  }, []);

  const connect = useCallback(() => {
    clientRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  const isConnected = connectionState === "connected";

  return {
    connectionState,
    isConnected,
    send,
    connect,
    disconnect,
    lastMessage,
  };
}
