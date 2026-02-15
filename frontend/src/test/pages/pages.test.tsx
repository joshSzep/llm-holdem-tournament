/**
 * Tests for page components: Lobby, GameTable, PostGame, GameReview.
 * These tests mock external dependencies (react-router-dom, stores, hooks, API).
 */

import { render, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";

// ─── Mock react-router-dom navigate ──────────────────

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: vi.fn(() => ({ id: "1" })),
  };
});

// ─── Mock API ────────────────────────────────────────

vi.mock("../../services/api", () => ({
  fetchAgents: vi.fn().mockResolvedValue({ agents: [] }),
  fetchGames: vi.fn().mockResolvedValue([]),
  fetchGameDetail: vi.fn().mockResolvedValue(null),
  createGame: vi.fn().mockResolvedValue({ game_id: 1 }),
  fetchHands: vi.fn().mockResolvedValue([]),
  fetchHand: vi.fn().mockResolvedValue(null),
  fetchCosts: vi.fn().mockResolvedValue({
    summary: { total_cost: 0, total_input_tokens: 0, total_output_tokens: 0, call_count: 0 },
    records: [],
  }),
  fetchProviders: vi.fn(),
}));

// ─── Mock websocket ─────────────────────────────────

vi.mock("../../services/websocket", () => ({
  wsService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    onMessage: vi.fn(() => vi.fn()),
    onConnectionChange: vi.fn(() => vi.fn()),
  },
}));

import { PostGame } from "../../pages/PostGame/PostGame";
import { GameReview } from "../../pages/GameReview/GameReview";
import { useGameStore } from "../../stores/gameStore";
import { useLobbyStore } from "../../stores/lobbyStore";
import { fetchGameDetail, fetchHands, fetchHand } from "../../services/api";

const mockFetchGameDetail = vi.mocked(fetchGameDetail);
const mockFetchHands = vi.mocked(fetchHands);
const mockFetchHand = vi.mocked(fetchHand);

// ─── PostGame ────────────────────────────────────────

describe("PostGame", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useGameStore.getState().reset();
  });

  it("renders game over title", () => {
    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );
    expect(container.querySelector(".post-game__title")).toHaveTextContent(
      "Game Over",
    );
  });

  it("shows winner when gameOver is set", () => {
    useGameStore.setState({
      gameOver: {
        winner_seat: 0,
        winner_name: "SuperBot",
        final_standings: [],
      },
    });

    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );

    expect(
      container.querySelector(".post-game__winner-name"),
    ).toHaveTextContent("SuperBot");
  });

  it("renders standings table", () => {
    useGameStore.setState({
      gameOver: {
        winner_seat: 0,
        winner_name: "Bot",
        final_standings: [
          {
            seat_index: 0,
            name: "Bot",
            final_chips: 2000,
            finish_position: 1,
          },
          {
            seat_index: 1,
            name: "Bot2",
            final_chips: 0,
            finish_position: 2,
          },
        ],
      },
    });

    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );

    const rows = container.querySelectorAll(".post-game__table tbody tr");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveClass("post-game__row--winner");
  });

  it("navigates to lobby on back button", () => {
    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );

    const backBtn = container.querySelector(
      ".post-game__btn--primary",
    )!;
    fireEvent.click(backBtn);
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });

  it("navigates to review on review button", () => {
    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );

    const reviewBtn = container.querySelector(
      ".post-game__btn--secondary",
    )!;
    fireEvent.click(reviewBtn);
    expect(mockNavigate).toHaveBeenCalledWith("/game/1/review");
  });

  it("shows game stats when detail is loaded", async () => {
    mockFetchGameDetail.mockResolvedValue({
      id: 1,
      game_uuid: "uuid-1",
      mode: "player",
      status: "completed",
      total_hands: 25,
      created_at: "2024-01-01T00:00:00",
      finished_at: "2024-01-01T01:00:00",
      winner_seat: 0,
      config_json: "{}",
      players: [
        { seat_index: 0, agent_id: null, name: "You", avatar_url: "/a.png", starting_chips: 1000, final_chips: 2000, finish_position: 1, is_human: true },
        { seat_index: 1, agent_id: "bot1", name: "Bot", avatar_url: "/b.png", starting_chips: 1000, final_chips: 0, finish_position: 2, is_human: false },
      ],
    });

    const { container } = render(
      <MemoryRouter>
        <PostGame />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".post-game__stats"),
      ).toBeInTheDocument();
    });
  });
});

// ─── GameReview ──────────────────────────────────────

describe("GameReview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockFetchHands.mockReturnValue(new Promise(() => {})); // never resolves

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-review__status"),
    ).toHaveTextContent("Loading");
  });

  it("shows empty state when no hands", async () => {
    mockFetchHands.mockResolvedValue([]);

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".game-review__status"),
      ).toHaveTextContent("No hands");
    });
  });

  it("renders hand navigator when hands loaded", async () => {
    mockFetchHands.mockResolvedValue([
      {
        id: 1,
        hand_number: 1,
        dealer_position: 0,
        small_blind: 10,
        big_blind: 20,
        phase: "showdown",
        community_cards_json: "[]",
        pots_json: "[]",
        winners_json: "[]",
      },
      {
        id: 2,
        hand_number: 2,
        dealer_position: 1,
        small_blind: 10,
        big_blind: 20,
        phase: "showdown",
        community_cards_json: "[]",
        pots_json: "[]",
        winners_json: "[]",
      },
    ]);
    mockFetchHand.mockResolvedValue({
      id: 1,
      hand_number: 1,
      dealer_position: 0,
      small_blind: 10,
      big_blind: 20,
      phase: "showdown",
      community_cards_json: "[]",
      pots_json: "[]",
      winners_json: "[]",
      showdown_json: null,
      actions: [],
    });

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".game-review__navigator"),
      ).toBeInTheDocument();
    });

    expect(
      container.querySelector(".game-review__hand-label"),
    ).toHaveTextContent("Hand 1 of 2");
  });

  it("navigates between hands", async () => {
    mockFetchHands.mockResolvedValue([
      {
        id: 1,
        hand_number: 1,
        dealer_position: 0,
        small_blind: 10,
        big_blind: 20,
        phase: "showdown",
        community_cards_json: "[]",
        pots_json: "[]",
        winners_json: "[]",
      },
      {
        id: 2,
        hand_number: 2,
        dealer_position: 1,
        small_blind: 10,
        big_blind: 20,
        phase: "showdown",
        community_cards_json: "[]",
        pots_json: "[]",
        winners_json: "[]",
      },
    ]);
    mockFetchHand.mockResolvedValue({
      id: 1,
      hand_number: 1,
      dealer_position: 0,
      small_blind: 10,
      big_blind: 20,
      phase: "showdown",
      community_cards_json: "[]",
      pots_json: "[]",
      winners_json: "[]",
      showdown_json: null,
      actions: [],
    });

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".game-review__navigator"),
      ).toBeInTheDocument();
    });

    // Click "Next Hand"
    const nextBtn = container.querySelectorAll(".game-review__nav-btn")[1]!;
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(mockFetchHand).toHaveBeenCalledTimes(2);
    });
  });

  it("renders actions when hand detail has actions", async () => {
    mockFetchHands.mockResolvedValue([
      {
        id: 1,
        hand_number: 1,
        dealer_position: 0,
        small_blind: 10,
        big_blind: 20,
        phase: "showdown",
        community_cards_json: "[]",
        pots_json: "[]",
        winners_json: "[]",
      },
    ]);
    mockFetchHand.mockResolvedValue({
      id: 1,
      hand_number: 1,
      dealer_position: 0,
      small_blind: 10,
      big_blind: 20,
      phase: "showdown",
      community_cards_json: '[{"rank":"A","suit":"hearts"}]',
      pots_json: "[]",
      winners_json: "[]",
      showdown_json: null,
      actions: [
        { seat_index: 0, action_type: "call", amount: 20, phase: "pre_flop", sequence: 0, timestamp: "2024-01-01T00:00:00" },
        { seat_index: 1, action_type: "raise", amount: 40, phase: "pre_flop", sequence: 1, timestamp: "2024-01-01T00:00:01" },
      ],
    });

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        container.querySelector(".game-review__action-list"),
      ).toBeInTheDocument();
    });

    const actionItems = container.querySelectorAll(
      ".game-review__action-item",
    );
    expect(actionItems).toHaveLength(2);
    expect(actionItems[0]).toHaveClass(
      "game-review__action-item--active",
    );
  });

  it("back button navigates to lobby", async () => {
    mockFetchHands.mockResolvedValue([]);

    const { container } = render(
      <MemoryRouter>
        <GameReview />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const backBtn = container.querySelector(".game-review__back-btn");
      expect(backBtn).toBeInTheDocument();
    });

    fireEvent.click(container.querySelector(".game-review__back-btn")!);
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });
});

// ─── Lobby ───────────────────────────────────────────

// Import Lobby dynamically since it uses lobbyStore
import { Lobby } from "../../pages/Lobby/Lobby";

describe("Lobby", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLobbyStore.setState({
      agents: [
        {
          id: "bot1",
          name: "TestBot",
          avatar_url: "/a.png",
          provider: "openai",
          model: "gpt-4",
          backstory: "",
        },
      ],
      games: [],
      selectedMode: "player",
      seats: [
        { agentId: "random" },
        { agentId: "random" },
        { agentId: "random" },
        { agentId: "random" },
        { agentId: "random" },
      ],
      startingChips: 1000,
      isLoadingAgents: false,
      isLoadingGames: false,
    });
  });

  it("renders lobby title", () => {
    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    expect(container.querySelector(".lobby__title")).toHaveTextContent(
      "LLM Hold",
    );
  });

  it("renders game mode selector", () => {
    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".game-mode-selector"),
    ).toBeInTheDocument();
  });

  it("renders seat configurators", () => {
    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    const seats = container.querySelectorAll(".seat-configurator");
    expect(seats.length).toBeGreaterThan(0);
  });

  it("renders start button", () => {
    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    const startBtn = container.querySelector(".lobby__start-button");
    expect(startBtn).toBeInTheDocument();
    expect(startBtn).not.toBeDisabled();
  });

  it("disables start when no agents", () => {
    useLobbyStore.setState({ agents: [] });

    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    const startBtn = container.querySelector(".lobby__start-button");
    expect(startBtn).toBeDisabled();
  });

  it("renders in-progress games when available", () => {
    useLobbyStore.setState({
      games: [
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
      ],
    });

    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".lobby__resume-button"),
    ).toBeInTheDocument();
  });

  it("renders completed games in history", () => {
    useLobbyStore.setState({
      games: [
        {
          id: 1,
          game_uuid: "uuid-1",
          mode: "player",
          status: "completed",
          player_count: 4,
          total_hands: 50,
          created_at: "2024-01-01",
          finished_at: "2024-01-01T01:00:00",
          winner_seat: 0,
        },
      ],
    });

    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".lobby__review-button"),
    ).toBeInTheDocument();
  });

  it("navigates to game on resume click", () => {
    useLobbyStore.setState({
      games: [
        {
          id: 42,
          game_uuid: "uuid-42",
          mode: "player",
          status: "active",
          player_count: 4,
          total_hands: 10,
          created_at: "2024-01-01",
          finished_at: null,
          winner_seat: null,
        },
      ],
    });

    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    fireEvent.click(container.querySelector(".lobby__resume-button")!);
    expect(mockNavigate).toHaveBeenCalledWith("/game/42");
  });

  it("shows 'You' label for player seat in player mode", () => {
    const { container } = render(
      <MemoryRouter>
        <Lobby />
      </MemoryRouter>,
    );
    expect(
      container.querySelector(".lobby__your-seat-name"),
    ).toHaveTextContent("You");
  });
});
