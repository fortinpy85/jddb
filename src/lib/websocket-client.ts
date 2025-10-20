/**
 * WebSocket Client for Real-Time Collaborative Editing
 *
 * Provides a robust WebSocket client with:
 * - Automatic reconnection with exponential backoff
 * - Message queuing and delivery guarantees
 * - Connection state management
 * - Event-driven message handling
 */

import { logger } from "@/utils/logger";

export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export interface WebSocketEventHandlers {
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onStateChange?: (state: ConnectionState) => void;
}

export class CollaborativeWebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private handlers: WebSocketEventHandlers = {};
  private state: ConnectionState = "disconnected";
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private messageQueue: WebSocketMessage[] = [];
  private isManualClose = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval ?? 3000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
    };
  }

  /**
   * Register event handlers for WebSocket events
   */
  on(handlers: WebSocketEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Connect to the WebSocket server
   */
  connect(): void {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING ||
        this.ws.readyState === WebSocket.OPEN)
    ) {
      logger.warn("WebSocket is already connecting or connected");
      return;
    }

    this.isManualClose = false;
    this.setState("connecting");

    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      logger.error("Failed to create WebSocket connection:", error);
      this.setState("error");
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.isManualClose = true;
    this.clearReconnectTimeout();
    this.clearHeartbeat();

    if (this.ws) {
      this.ws.close(1000, "Client disconnect");
      this.ws = null;
    }

    this.setState("disconnected");
  }

  /**
   * Send a message to the server
   * Messages are queued if connection is not ready
   */
  send(message: WebSocketMessage): void {
    if (
      this.state === "connected" &&
      this.ws &&
      this.ws.readyState === WebSocket.OPEN
    ) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        logger.error("Failed to send message:", error);
        this.messageQueue.push(message);
      }
    } else {
      // Queue message for later delivery
      this.messageQueue.push(message);
    }
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Check if client is connected
   */
  isConnected(): boolean {
    return this.state === "connected" && this.ws?.readyState === WebSocket.OPEN;
  }

  private handleOpen(): void {
    logger.info("WebSocket connected");
    this.reconnectAttempts = 0;
    this.setState("connected");
    this.startHeartbeat();

    // Process queued messages
    this.processMessageQueue();

    if (this.handlers.onOpen) {
      this.handlers.onOpen();
    }
  }

  private handleClose(event: CloseEvent): void {
    logger.info("WebSocket closed", { code: event.code, reason: event.reason });
    this.clearHeartbeat();

    if (this.handlers.onClose) {
      this.handlers.onClose(event);
    }

    if (!this.isManualClose) {
      this.setState("reconnecting");
      this.scheduleReconnect();
    } else {
      this.setState("disconnected");
    }
  }

  private handleError(error: Event): void {
    logger.error("WebSocket error:", error);
    this.setState("error");

    if (this.handlers.onError) {
      this.handlers.onError(error);
    }
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;

      if (this.handlers.onMessage) {
        this.handlers.onMessage(message);
      }

      // Handle pong messages for heartbeat
      if (message.type === "pong") {
        // Heartbeat acknowledged
        return;
      }
    } catch (error) {
      logger.error("Failed to parse WebSocket message:", error);
    }
  }

  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;

      if (this.handlers.onStateChange) {
        this.handlers.onStateChange(newState);
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      logger.error("Max reconnect attempts reached");
      this.setState("error");
      return;
    }

    this.clearReconnectTimeout();

    // Exponential backoff: 3s, 6s, 12s, 24s, etc.
    const delay =
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    logger.info(
      `Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`,
    );

    this.reconnectTimeout = setTimeout(() => {
      logger.info(
        `Attempting reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`,
      );
      this.connect();
    }, delay);
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: "ping" });
      }
    }, this.config.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }
}
