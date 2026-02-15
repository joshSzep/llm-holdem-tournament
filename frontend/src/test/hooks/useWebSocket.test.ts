/**
 * Tests for useWebSocket hook.
 */

import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useWebSocket } from "../../hooks/useWebSocket";
import { useGameStore } from "../../stores/gameStore";
import { useChatStore } from "../../stores/chatStore";
import { wsService } from "../../services/websocket";
import type { ServerMessage } from "../../types/messages";

vi.mock("../../services/websocket", () => {
  let messageCallbacks: Array<(msg: ServerMessage) => void> = [];
  let connectionCallbacks: Array<(connected: boolean) => void> = [];

  return {
    wsService: {
      connect: vi.fn(),
      disconnect: vi.fn(),
      send: vi.fn(),
      onMessage: vi.fn((cb: (msg: ServerMessage) => void) => {
        messageCallbacks.push(cb);
        return () => {
          messageCallbacks = messageCallbacks.filter((c) => c !== cb);
        };
      }),
      onConnectionChange: vi.fn((cb: (connected: boolean) => void) => {
        connectionCallbacks.push(cb);
        return () => {
          connectionCallbacks = connectionCallbacks.filter((c) => c !== cb);
        };
      }),
      // Test helpers
      _simulateMessage: (msg: ServerMessage) => {
        messageCallbacks.forEach((cb) => cb(msg));
      },
      _simulateConnection: (connected: boolean) => {
        connectionCallbacks.forEach((cb) => cb(connected));
      },
      _reset: () => {
        messageCallbacks = [];
        connectionCallbacks = [];
      },
    },
  };
});

const mockWsService = wsService as typeof wsService & {
  _simulateMessage: (msg: ServerMessage) => void;
  _simulateConnection: (connected: boolean) => void;
  _reset: () => void;
};

describe("useWebSocket", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockWsService._reset();
    useGameStore.getState().reset();
    useChatStore.getState().clearMessages();
  });

  it("does not connect when gameId is null", () => {
    renderHook(() => useWebSocket(null));
    expect(wsService.connect).not.toHaveBeenCalled();
  });

  it("connects with gameId on mount", () => {
    renderHook(() => useWebSocket(42));
    expect(wsService.connect).toHaveBeenCalledWith(42);
  });

  it("disconnects on unmount", () => {
    const { unmount } = renderHook(() => useWebSocket(42));
    unmount();
    expect(wsService.disconnect).toHaveBeenCalled();
  });

  it("routes game_state messages to gameStore", () => {
    renderHook(() => useWebSocket(1));

    const mockState = {
      game_id: "uuid-1",
      status: "active" as const,
      mode: "player" as const,
      phase: "pre_flop" as const,
      hand_number: 1,
      dealer_position: 0,
      current_player_index: 1,
      current_bet: 20,
      small_blind: 10,
      big_blind: 20,
      community_cards: [],
      pots: [{ amount: 30, eligible_players: [0, 1] }],
      players: [],
      current_hand_actions: [],
      showdown_result: null,
      total_hands_played: 0,
      eliminated_players: [],
    };

    act(() => {
      mockWsService._simulateMessage({
        type: "game_state",
        state: mockState,
      });
    });

    expect(useGameStore.getState().gameState).toEqual(mockState);
  });

  it("routes chat_message to chatStore", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateMessage({
        type: "chat_message",
        seat_index: 0,
        name: "Bot",
        message: "Hello",
        timestamp: "2024-01-01T00:00:00",
      });
    });

    const messages = useChatStore.getState().messages;
    expect(messages).toHaveLength(1);
    expect(messages[0]?.message).toBe("Hello");
  });

  it("routes timer_update to gameStore", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateMessage({
        type: "timer_update",
        seat_index: 2,
        seconds_remaining: 30,
      });
    });

    expect(useGameStore.getState().timer).toEqual({
      seat_index: 2,
      seconds_remaining: 30,
    });
  });

  it("routes game_over to gameStore", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateMessage({
        type: "game_over",
        winner_seat: 0,
        winner_name: "BotA",
        final_standings: [],
      });
    });

    expect(useGameStore.getState().gameOver).toEqual({
      winner_seat: 0,
      winner_name: "BotA",
      final_standings: [],
    });
  });

  it("routes error to gameStore", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateMessage({
        type: "error",
        message: "Something broke",
        code: "UNKNOWN_ERROR",
      });
    });

    expect(useGameStore.getState().error).toBe("Something broke");
  });

  it("routes game_paused / game_resumed to gameStore", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateMessage({
        type: "game_paused",
        reason: "Rate limit",
      });
    });
    expect(useGameStore.getState().isPaused).toBe(true);
    expect(useGameStore.getState().pauseReason).toBe("Rate limit");

    act(() => {
      mockWsService._simulateMessage({ type: "game_resumed" });
    });
    expect(useGameStore.getState().isPaused).toBe(false);
  });

  it("updates connected state via connection callback", () => {
    renderHook(() => useWebSocket(1));

    act(() => {
      mockWsService._simulateConnection(true);
    });
    expect(useGameStore.getState().isConnected).toBe(true);

    act(() => {
      mockWsService._simulateConnection(false);
    });
    expect(useGameStore.getState().isConnected).toBe(false);
  });

  it("returns send bound to wsService", () => {
    const { result } = renderHook(() => useWebSocket(1));
    expect(result.current.send).toBeDefined();
  });
});
