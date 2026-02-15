/**
 * Tests for WebSocket service.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { WebSocketService } from "../../services/websocket";

// Track created WebSocket instances
let instances: MockWebSocket[] = [];

class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  readonly CONNECTING = 0;
  readonly OPEN = 1;
  readonly CLOSING = 2;
  readonly CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
  });

  constructor(url: string) {
    this.url = url;
    instances.push(this);
  }

  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(data: unknown): void {
    const event = new MessageEvent("message", {
      data: JSON.stringify(data),
    });
    this.onmessage?.(event);
  }

  simulateClose(): void {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close"));
  }
}

describe("WebSocketService", () => {
  let service: WebSocketService;

  beforeEach(() => {
    vi.useFakeTimers();
    instances = [];
    service = new WebSocketService();
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    service.disconnect();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  function latestWs(): MockWebSocket {
    return instances[instances.length - 1]!;
  }

  it("starts not connected", () => {
    expect(service.isConnected).toBe(false);
  });

  it("connects to WebSocket with gameId", () => {
    service.connect(42);
    expect(latestWs().url).toContain("/ws/game/42");
  });

  it("sets connected on open", () => {
    const handler = vi.fn();
    service.onConnectionChange(handler);
    service.connect(1);
    latestWs().simulateOpen();
    expect(handler).toHaveBeenCalledWith(true);
    expect(service.isConnected).toBe(true);
  });

  it("routes messages to handlers", () => {
    const handler = vi.fn();
    service.onMessage(handler);
    service.connect(1);
    latestWs().simulateOpen();

    const msg = { type: "game_state", state: {} };
    latestWs().simulateMessage(msg);
    expect(handler).toHaveBeenCalledWith(msg);
  });

  it("sends messages when connected", () => {
    service.connect(1);
    latestWs().simulateOpen();
    service.send({ type: "player_action", action_type: "fold" });
    expect(latestWs().send).toHaveBeenCalledWith(
      JSON.stringify({ type: "player_action", action_type: "fold" }),
    );
  });

  it("disconnects cleanly", () => {
    const handler = vi.fn();
    service.onConnectionChange(handler);
    service.connect(1);
    latestWs().simulateOpen();

    service.disconnect();
    expect(latestWs().close).toHaveBeenCalled();
  });

  it("unsubscribes message handlers", () => {
    const handler = vi.fn();
    const unsub = service.onMessage(handler);
    unsub();

    service.connect(1);
    latestWs().simulateOpen();
    latestWs().simulateMessage({ type: "error", message: "test" });
    expect(handler).not.toHaveBeenCalled();
  });

  it("unsubscribes connection handlers", () => {
    const handler = vi.fn();
    const unsub = service.onConnectionChange(handler);
    unsub();

    service.connect(1);
    latestWs().simulateOpen();
    expect(handler).not.toHaveBeenCalled();
  });
});
