/**
 * WebSocket client service.
 * Handles connection, reconnection, and message dispatch.
 */

import type { ClientMessage, ServerMessage } from "../types/messages";

const WS_BASE =
  typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
    : "ws://localhost:8000";

const MAX_RECONNECT_DELAY = 30_000;
const BASE_RECONNECT_DELAY = 1_000;

export type MessageHandler = (message: ServerMessage) => void;
export type ConnectionHandler = (connected: boolean) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private gameId: number | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectAttempt = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  /**
   * Connect to the game WebSocket.
   */
  connect(gameId: number): void {
    this.intentionalClose = false;
    this.gameId = gameId;
    this.reconnectAttempt = 0;
    this.createConnection();
  }

  /**
   * Disconnect and stop reconnecting.
   */
  disconnect(): void {
    this.intentionalClose = true;
    this.gameId = null;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.notifyConnectionHandlers(false);
  }

  /**
   * Send a message to the server.
   */
  send(message: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  /**
   * Register a handler for incoming server messages.
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  /**
   * Register a handler for connection state changes.
   */
  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  /**
   * Check if currently connected.
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private createConnection(): void {
    if (this.gameId === null) return;

    const url = `${WS_BASE}/ws/game/${this.gameId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.notifyConnectionHandlers(true);
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data as string) as ServerMessage;
        for (const handler of this.messageHandlers) {
          handler(message);
        }
      } catch {
        // Silently ignore unparseable messages
      }
    };

    this.ws.onclose = () => {
      this.notifyConnectionHandlers(false);
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  private scheduleReconnect(): void {
    const delay = Math.min(
      BASE_RECONNECT_DELAY * Math.pow(2, this.reconnectAttempt),
      MAX_RECONNECT_DELAY,
    );
    this.reconnectAttempt++;
    this.reconnectTimeout = setTimeout(() => {
      this.createConnection();
    }, delay);
  }

  private notifyConnectionHandlers(connected: boolean): void {
    for (const handler of this.connectionHandlers) {
      handler(connected);
    }
  }
}

/** Singleton WebSocket service instance. */
export const wsService = new WebSocketService();
