/**
 * Game state Zustand store — holds the live game state received via WebSocket.
 */

import { create } from "zustand";

import type { GameState, PlayerState } from "../types/game";
import type { FinalStanding } from "../types/messages";

interface GameStore {
  /** Current game state from WebSocket */
  gameState: GameState | null;

  /** WebSocket connection status */
  isConnected: boolean;

  /** Game over data */
  gameOver: {
    winner_seat: number;
    winner_name: string;
    final_standings: FinalStanding[];
  } | null;

  /** Timer state */
  timer: {
    seat_index: number;
    seconds_remaining: number;
  } | null;

  /** Pause state */
  isPaused: boolean;
  pauseReason: string;

  /** Error message */
  error: string | null;

  /** Actions */
  setGameState: (state: GameState) => void;
  setConnected: (connected: boolean) => void;
  setGameOver: (data: {
    winner_seat: number;
    winner_name: string;
    final_standings: FinalStanding[];
  }) => void;
  setTimer: (seat_index: number, seconds_remaining: number) => void;
  clearTimer: () => void;
  setPaused: (paused: boolean, reason?: string) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  isConnected: false,
  gameOver: null,
  timer: null,
  isPaused: false,
  pauseReason: "",
  error: null,

  setGameState: (state) => set({ gameState: state, error: null }),
  setConnected: (connected) => set({ isConnected: connected }),
  setGameOver: (data) => set({ gameOver: data }),
  setTimer: (seat_index, seconds_remaining) =>
    set({ timer: { seat_index, seconds_remaining } }),
  clearTimer: () => set({ timer: null }),
  setPaused: (paused, reason = "") =>
    set({ isPaused: paused, pauseReason: reason }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      gameState: null,
      isConnected: false,
      gameOver: null,
      timer: null,
      isPaused: false,
      pauseReason: "",
      error: null,
    }),
}));

// ─── Derived Selectors ───────────────────────────────

/**
 * Get the human player (seat with no agent_id).
 */
export function selectHumanPlayer(
  state: GameState | null,
): PlayerState | null {
  if (!state) return null;
  return state.players.find((p) => p.agent_id === null) ?? null;
}

/**
 * Get the currently active player.
 */
export function selectCurrentPlayer(
  state: GameState | null,
): PlayerState | null {
  if (!state || state.current_player_index === null) return null;
  return (
    state.players.find(
      (p) => p.seat_index === state.current_player_index,
    ) ?? null
  );
}

/**
 * Check if it's the human player's turn.
 */
export function selectIsHumanTurn(state: GameState | null): boolean {
  if (!state || state.current_player_index === null) return false;
  const current = state.players.find(
    (p) => p.seat_index === state.current_player_index,
  );
  return current?.agent_id === null;
}
