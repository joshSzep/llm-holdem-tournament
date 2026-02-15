/**
 * Tests for lobbyStore async methods and selectors.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  useLobbyStore,
  selectInProgressGames,
  selectCompletedGames,
} from "../../stores/lobbyStore";
import { fetchAgents, fetchGames } from "../../services/api";
import type { GameSummary } from "../../types/api";

vi.mock("../../services/api", () => ({
  fetchAgents: vi.fn(),
  fetchGames: vi.fn(),
}));

const mockFetchAgents = vi.mocked(fetchAgents);
const mockFetchGames = vi.mocked(fetchGames);

describe("lobbyStore async methods", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLobbyStore.setState({
      agents: [],
      games: [],
      isLoadingAgents: false,
      isLoadingGames: false,
    });
  });

  it("loadAgents sets agents from API", async () => {
    mockFetchAgents.mockResolvedValue({
      agents: [
        {
          id: "a1",
          name: "Bot A",
          avatar_url: "/a.png",
          provider: "openai",
          model: "gpt-4",
          backstory: "",
        },
      ],
    });

    await useLobbyStore.getState().loadAgents();

    expect(useLobbyStore.getState().agents).toHaveLength(1);
    expect(useLobbyStore.getState().agents[0]?.name).toBe("Bot A");
    expect(useLobbyStore.getState().isLoadingAgents).toBe(false);
  });

  it("loadAgents handles error", async () => {
    mockFetchAgents.mockRejectedValue(new Error("Network error"));

    await useLobbyStore.getState().loadAgents();

    expect(useLobbyStore.getState().agents).toHaveLength(0);
    expect(useLobbyStore.getState().isLoadingAgents).toBe(false);
  });

  it("loadGames sets games from API", async () => {
    mockFetchGames.mockResolvedValue([
      {
        id: 1,
        game_uuid: "uuid-1",
        mode: "player",
        status: "active",
        player_count: 4,
        total_hands: 10,
        created_at: "2024-01-01",
        finished_at: null,
        winner_seat: null,
      },
    ]);

    await useLobbyStore.getState().loadGames();

    expect(useLobbyStore.getState().games).toHaveLength(1);
    expect(useLobbyStore.getState().isLoadingGames).toBe(false);
  });

  it("loadGames handles error", async () => {
    mockFetchGames.mockRejectedValue(new Error("fail"));

    await useLobbyStore.getState().loadGames();

    expect(useLobbyStore.getState().games).toHaveLength(0);
    expect(useLobbyStore.getState().isLoadingGames).toBe(false);
  });
});

describe("lobbyStore selectors", () => {
  const games: GameSummary[] = [
    {
      id: 1,
      game_uuid: "uuid-1",
      mode: "player",
      status: "active",
      player_count: 4,
      total_hands: 10,
      created_at: "2024-01-01",
      finished_at: null,
      winner_seat: null,
    },
    {
      id: 2,
      game_uuid: "uuid-2",
      mode: "spectator",
      status: "paused",
      player_count: 2,
      total_hands: 5,
      created_at: "2024-01-02",
      finished_at: null,
      winner_seat: null,
    },
    {
      id: 3,
      game_uuid: "uuid-3",
      mode: "player",
      status: "completed",
      player_count: 6,
      total_hands: 50,
      created_at: "2024-01-03",
      finished_at: "2024-01-03T02:00:00",
      winner_seat: 0,
    },
  ];

  it("selectInProgressGames returns active and paused", () => {
    const result = selectInProgressGames(games);
    expect(result).toHaveLength(2);
    expect(result.map((g) => g.id)).toEqual([1, 2]);
  });

  it("selectCompletedGames returns completed only", () => {
    const result = selectCompletedGames(games);
    expect(result).toHaveLength(1);
    expect(result[0]?.id).toBe(3);
  });

  it("selectInProgressGames returns empty for no matches", () => {
    const completed: GameSummary[] = [
      {
        id: 1,
        game_uuid: "uuid-1",
        mode: "player",
        status: "completed",
        player_count: 2,
        total_hands: 10,
        created_at: "2024-01-01",
        finished_at: "2024-01-01T01:00:00",
        winner_seat: 0,
      },
    ];
    expect(selectInProgressGames(completed)).toHaveLength(0);
  });
});
