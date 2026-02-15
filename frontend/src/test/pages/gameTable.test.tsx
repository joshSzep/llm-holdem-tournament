/**
 * Tests for GameTable page.
 */

import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: vi.fn(() => ({ id: "1" })),
  };
});

vi.mock("../../services/api", () => ({
  fetchCosts: vi.fn().mockResolvedValue({
    summary: { total_cost: 0, record_count: 0 },
    records: [],
  }),
}));

vi.mock("../../services/websocket", () => ({
  wsService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    onMessage: vi.fn(() => vi.fn()),
    onConnectionChange: vi.fn(() => vi.fn()),
  },
}));

import { GameTable } from "../../pages/GameTable/GameTable";
import { useGameStore } from "../../stores/gameStore";
import type { GameState, PlayerState } from "../../types/game";

function makePlayer(overrides: Partial<PlayerState> = {}): PlayerState {
  return {
    seat_index: 0,
    name: "Player",
    avatar_url: "/avatars/default.png",
    chips: 1000,
    current_bet: 0,
    is_folded: false,
    is_all_in: false,
    is_eliminated: false,
    hole_cards: [],
    agent_id: null,
    is_dealer: false,
    has_acted: false,
    ...overrides,
  };
}

function makeGameState(overrides: Partial<GameState> = {}): GameState {
  return {
    game_id: "uuid-1",
    status: "active",
    mode: "player",
    phase: "pre_flop",
    hand_number: 1,
    dealer_position: 0,
    current_player_index: 0,
    current_bet: 20,
    small_blind: 10,
    big_blind: 20,
    community_cards: [],
    pots: [{ amount: 30, eligible_players: [0, 1] }],
    players: [
      makePlayer({ seat_index: 0, agent_id: null, name: "You" }),
      makePlayer({ seat_index: 1, agent_id: "bot1", name: "Bot" }),
    ],
    current_hand_actions: [],
    showdown_result: null,
    total_hands_played: 0,
    eliminated_players: [],
    ...overrides,
  };
}

describe("GameTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useGameStore.getState().reset();
  });

  it("shows connecting state when no game state", () => {
    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__status"),
    ).toBeInTheDocument();
  });

  it("shows waiting state when connected but no game state", () => {
    useGameStore.setState({ isConnected: true });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__status"),
    ).toHaveTextContent("Waiting");
  });

  it("renders game table when game state is present", () => {
    useGameStore.setState({
      gameState: makeGameState(),
      isConnected: true,
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__header"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".game-table__hand"),
    ).toHaveTextContent("Hand #1");
  });

  it("shows blinds info", () => {
    useGameStore.setState({
      gameState: makeGameState(),
      isConnected: true,
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__blinds"),
    ).toHaveTextContent("10/20");
  });

  it("shows error overlay", () => {
    useGameStore.setState({
      gameState: makeGameState(),
      error: "Connection lost",
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__overlay--error"),
    ).toHaveTextContent("Connection lost");
  });

  it("shows pause overlay", () => {
    useGameStore.setState({
      gameState: makeGameState(),
      isPaused: true,
      pauseReason: "Rate limit",
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__overlay--paused"),
    ).toHaveTextContent("Rate limit");
  });

  it("renders chat sidebar", () => {
    useGameStore.setState({
      gameState: makeGameState(),
      isConnected: true,
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__sidebar"),
    ).toBeInTheDocument();
  });

  it("shows action buttons when human turn", () => {
    useGameStore.setState({
      gameState: makeGameState({
        current_player_index: 0,
        players: [
          makePlayer({ seat_index: 0, agent_id: null }),
          makePlayer({ seat_index: 1, agent_id: "bot1" }),
        ],
      }),
      isConnected: true,
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__actions"),
    ).toBeInTheDocument();
  });

  it("hides action buttons in spectator mode", () => {
    useGameStore.setState({
      gameState: makeGameState({
        mode: "spectator",
        current_player_index: 0,
      }),
      isConnected: true,
    });

    const { container } = render(
      <MemoryRouter>
        <GameTable />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-table__actions"),
    ).not.toBeInTheDocument();
  });
});
