/**
 * Lobby Zustand store — holds lobby configuration, agents, and games list.
 */

import { create } from "zustand";

import type { AgentProfile } from "../types/agents";
import type { GameSummary } from "../types/api";
import { fetchAgents } from "../services/api";
import { fetchGames } from "../services/api";

interface SeatConfig {
  /** Agent ID, "random", or null (empty seat) */
  agentId: string | "random" | null;
}

interface LobbyStore {
  /** Available agents from API */
  agents: AgentProfile[];

  /** All games from API */
  games: GameSummary[];

  /** Game mode selection */
  selectedMode: "player" | "spectator";

  /** Seat configuration (2-6 seats) */
  seats: SeatConfig[];

  /** Starting chips */
  startingChips: number;

  /** Loading states */
  isLoadingAgents: boolean;
  isLoadingGames: boolean;

  /** Actions */
  setSelectedMode: (mode: "player" | "spectator") => void;
  setSeatAgent: (index: number, agentId: string | "random" | null) => void;
  setSeatCount: (count: number) => void;
  setStartingChips: (chips: number) => void;
  loadAgents: () => Promise<void>;
  loadGames: () => Promise<void>;
}

const DEFAULT_SEAT_COUNT = 6;

function createEmptySeats(count: number): SeatConfig[] {
  return Array.from({ length: count }, () => ({ agentId: "random" }));
}

export const useLobbyStore = create<LobbyStore>((set) => ({
  agents: [],
  games: [],
  selectedMode: "player",
  seats: createEmptySeats(DEFAULT_SEAT_COUNT),
  startingChips: 1000,
  isLoadingAgents: false,
  isLoadingGames: false,

  setSelectedMode: (mode) => set({ selectedMode: mode }),

  setSeatAgent: (index, agentId) =>
    set((state) => {
      const seats = [...state.seats];
      if (index >= 0 && index < seats.length) {
        seats[index] = { agentId };
      }
      return { seats };
    }),

  setSeatCount: (count) => {
    const clamped = Math.max(2, Math.min(6, count));
    set((state) => {
      const seats = createEmptySeats(clamped);
      // Preserve existing selections where possible
      for (let i = 0; i < Math.min(state.seats.length, clamped); i++) {
        seats[i] = state.seats[i] ?? { agentId: "random" };
      }
      return { seats };
    });
  },

  setStartingChips: (chips) => set({ startingChips: chips }),

  loadAgents: async () => {
    set({ isLoadingAgents: true });
    try {
      const data = await fetchAgents();
      set({ agents: data.agents, isLoadingAgents: false });
    } catch {
      set({ isLoadingAgents: false });
    }
  },

  loadGames: async () => {
    set({ isLoadingGames: true });
    try {
      const data = await fetchGames();
      set({ games: data, isLoadingGames: false });
    } catch {
      set({ isLoadingGames: false });
    }
  },
}));

// ─── Derived Selectors ───────────────────────────────

export function selectInProgressGames(
  games: GameSummary[],
): GameSummary[] {
  return games.filter((g) => g.status === "active" || g.status === "paused");
}

export function selectCompletedGames(
  games: GameSummary[],
): GameSummary[] {
  return games.filter((g) => g.status === "completed");
}
