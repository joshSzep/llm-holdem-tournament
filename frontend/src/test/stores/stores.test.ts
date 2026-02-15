/**
 * Tests for Zustand stores: gameStore, lobbyStore, chatStore.
 */

import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";

import {
  useGameStore,
  selectHumanPlayer,
  selectCurrentPlayer,
  selectIsHumanTurn,
} from "../../stores/gameStore";
import { useLobbyStore } from "../../stores/lobbyStore";
import { useChatStore } from "../../stores/chatStore";
import type { GameState, PlayerState } from "../../types/game";

// ─── Factory ─────────────────────────────────────────

function makeGameState(overrides: Partial<GameState> = {}): GameState {
  return {
    game_id: "test-uuid",
    mode: "player",
    status: "active",
    players: [],
    dealer_position: 0,
    small_blind: 10,
    big_blind: 20,
    hand_number: 1,
    community_cards: [],
    pots: [],
    current_bet: 0,
    current_player_index: null,
    phase: "pre_flop",
    current_hand_actions: [],
    showdown_result: null,
    total_hands_played: 0,
    eliminated_players: [],
    ...overrides,
  };
}

function makePlayer(overrides: Partial<PlayerState> = {}): PlayerState {
  return {
    seat_index: 0,
    agent_id: null,
    name: "Human",
    avatar_url: "/avatars/default.png",
    chips: 1000,
    hole_cards: null,
    is_folded: false,
    is_eliminated: false,
    is_all_in: false,
    current_bet: 0,
    is_dealer: false,
    has_acted: false,
    ...overrides,
  };
}

// ─── GameStore ───────────────────────────────────────

describe("gameStore", () => {
  beforeEach(() => {
    act(() => {
      useGameStore.getState().reset();
    });
  });

  it("starts with null game state", () => {
    expect(useGameStore.getState().gameState).toBeNull();
  });

  it("sets game state and clears error", () => {
    const state = makeGameState();
    act(() => {
      useGameStore.getState().setError("old error");
      useGameStore.getState().setGameState(state);
    });
    expect(useGameStore.getState().gameState).toBe(state);
    expect(useGameStore.getState().error).toBeNull();
  });

  it("sets connected status", () => {
    act(() => {
      useGameStore.getState().setConnected(true);
    });
    expect(useGameStore.getState().isConnected).toBe(true);
  });

  it("sets game over data", () => {
    const data = {
      winner_seat: 0,
      winner_name: "Alice",
      final_standings: [],
    };
    act(() => {
      useGameStore.getState().setGameOver(data);
    });
    expect(useGameStore.getState().gameOver).toEqual(data);
  });

  it("sets and clears timer", () => {
    act(() => {
      useGameStore.getState().setTimer(2, 30);
    });
    expect(useGameStore.getState().timer).toEqual({
      seat_index: 2,
      seconds_remaining: 30,
    });

    act(() => {
      useGameStore.getState().clearTimer();
    });
    expect(useGameStore.getState().timer).toBeNull();
  });

  it("sets pause state", () => {
    act(() => {
      useGameStore.getState().setPaused(true, "AI thinking");
    });
    expect(useGameStore.getState().isPaused).toBe(true);
    expect(useGameStore.getState().pauseReason).toBe("AI thinking");

    act(() => {
      useGameStore.getState().setPaused(false);
    });
    expect(useGameStore.getState().isPaused).toBe(false);
    expect(useGameStore.getState().pauseReason).toBe("");
  });

  it("resets all state", () => {
    act(() => {
      useGameStore.getState().setConnected(true);
      useGameStore.getState().setGameState(makeGameState());
      useGameStore.getState().setError("error");
      useGameStore.getState().reset();
    });
    const s = useGameStore.getState();
    expect(s.gameState).toBeNull();
    expect(s.isConnected).toBe(false);
    expect(s.gameOver).toBeNull();
    expect(s.error).toBeNull();
  });
});

// ─── Selectors ───────────────────────────────────────

describe("gameStore selectors", () => {
  it("selectHumanPlayer returns player without agent_id", () => {
    const human = makePlayer({ seat_index: 0, agent_id: null });
    const bot = makePlayer({ seat_index: 1, agent_id: "bot1", name: "Bot" });
    const state = makeGameState({ players: [human, bot] });
    expect(selectHumanPlayer(state)).toBe(human);
  });

  it("selectHumanPlayer returns null when no human", () => {
    const bot1 = makePlayer({ seat_index: 0, agent_id: "bot1" });
    const bot2 = makePlayer({ seat_index: 1, agent_id: "bot2" });
    const state = makeGameState({ players: [bot1, bot2] });
    expect(selectHumanPlayer(state)).toBeNull();
  });

  it("selectHumanPlayer returns null for null state", () => {
    expect(selectHumanPlayer(null)).toBeNull();
  });

  it("selectCurrentPlayer returns the active player", () => {
    const p1 = makePlayer({ seat_index: 0 });
    const p2 = makePlayer({ seat_index: 1, name: "Bot" });
    const state = makeGameState({
      players: [p1, p2],
      current_player_index: 1,
    });
    expect(selectCurrentPlayer(state)).toBe(p2);
  });

  it("selectCurrentPlayer returns null when no active player", () => {
    const state = makeGameState({ current_player_index: null });
    expect(selectCurrentPlayer(state)).toBeNull();
  });

  it("selectIsHumanTurn returns true when human is current", () => {
    const human = makePlayer({ seat_index: 0, agent_id: null });
    const state = makeGameState({
      players: [human],
      current_player_index: 0,
    });
    expect(selectIsHumanTurn(state)).toBe(true);
  });

  it("selectIsHumanTurn returns false when bot is current", () => {
    const bot = makePlayer({ seat_index: 0, agent_id: "bot1" });
    const state = makeGameState({
      players: [bot],
      current_player_index: 0,
    });
    expect(selectIsHumanTurn(state)).toBe(false);
  });

  it("selectIsHumanTurn returns false for null state", () => {
    expect(selectIsHumanTurn(null)).toBe(false);
  });
});

// ─── ChatStore ───────────────────────────────────────

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
  });

  it("starts with empty messages", () => {
    expect(useChatStore.getState().messages).toHaveLength(0);
  });

  it("adds messages", () => {
    act(() => {
      useChatStore.getState().addMessage({
        id: "1",
        seat_index: 0,
        name: "Alice",
        message: "Hello",
        timestamp: "2024-01-01T12:00:00Z",
        isSystem: false,
      });
    });
    expect(useChatStore.getState().messages).toHaveLength(1);
    expect(useChatStore.getState().messages[0]?.message).toBe("Hello");
  });

  it("clears messages", () => {
    act(() => {
      useChatStore.getState().addMessage({
        id: "1",
        seat_index: 0,
        name: "Alice",
        message: "Hello",
        timestamp: "2024-01-01T12:00:00Z",
        isSystem: false,
      });
      useChatStore.getState().clearMessages();
    });
    expect(useChatStore.getState().messages).toHaveLength(0);
  });
});

// ─── LobbyStore ──────────────────────────────────────

describe("lobbyStore", () => {
  beforeEach(() => {
    useLobbyStore.setState({
      agents: [],
      games: [],
      selectedMode: "player",
      seats: [{ agentId: "random" }],
      startingChips: 1000,
      isLoadingAgents: false,
      isLoadingGames: false,
    });
  });

  it("sets selected mode", () => {
    act(() => {
      useLobbyStore.getState().setSelectedMode("spectator");
    });
    expect(useLobbyStore.getState().selectedMode).toBe("spectator");
  });

  it("sets seat agent", () => {
    act(() => {
      useLobbyStore.getState().setSeatAgent(0, "bot1");
    });
    expect(useLobbyStore.getState().seats[0]?.agentId).toBe("bot1");
  });

  it("sets seat count", () => {
    act(() => {
      useLobbyStore.getState().setSeatCount(4);
    });
    expect(useLobbyStore.getState().seats).toHaveLength(4);
  });

  it("clamps seat count to valid range", () => {
    act(() => {
      useLobbyStore.getState().setSeatCount(1);
    });
    expect(useLobbyStore.getState().seats.length).toBeGreaterThanOrEqual(1);

    act(() => {
      useLobbyStore.getState().setSeatCount(10);
    });
    // Should be clamped to max
    expect(useLobbyStore.getState().seats.length).toBeLessThanOrEqual(6);
  });

  it("sets starting chips", () => {
    act(() => {
      useLobbyStore.getState().setStartingChips(5000);
    });
    expect(useLobbyStore.getState().startingChips).toBe(5000);
  });
});
