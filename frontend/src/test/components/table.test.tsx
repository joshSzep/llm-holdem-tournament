/**
 * Tests for table components: DealerButton, CommunityCards, PotDisplay, PlayerSeat, PokerTable.
 */

import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { DealerButton } from "../../components/table/DealerButton";
import { CommunityCards } from "../../components/table/CommunityCards";
import { PotDisplay } from "../../components/table/PotDisplay";
import { PlayerSeat } from "../../components/table/PlayerSeat";
import { PokerTable } from "../../components/table/PokerTable";
import type { PlayerState, Card as CardType, Pot } from "../../types/game";

// ─── Factories ───────────────────────────────────────

function makePlayer(overrides: Partial<PlayerState> = {}): PlayerState {
  return {
    seat_index: 0,
    agent_id: null,
    name: "TestPlayer",
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

// ─── DealerButton ────────────────────────────────────

describe("DealerButton", () => {
  it("renders when visible", () => {
    const { container } = render(<DealerButton visible />);
    const btn = container.querySelector(".dealer-button");
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveTextContent("D");
  });

  it("returns null when not visible", () => {
    const { container } = render(<DealerButton visible={false} />);
    expect(container.querySelector(".dealer-button")).not.toBeInTheDocument();
  });
});

// ─── CommunityCards ──────────────────────────────────

describe("CommunityCards", () => {
  it("renders all 5 placeholders when no cards", () => {
    const { container } = render(<CommunityCards cards={[]} />);
    expect(
      container.querySelectorAll(".community-cards__placeholder"),
    ).toHaveLength(5);
  });

  it("renders 3 cards + 2 placeholders on flop", () => {
    const cards: CardType[] = [
      { rank: "A", suit: "h" },
      { rank: "K", suit: "s" },
      { rank: "Q", suit: "d" },
    ];
    const { container } = render(<CommunityCards cards={cards} />);
    expect(container.querySelectorAll(".card")).toHaveLength(3);
    expect(
      container.querySelectorAll(".community-cards__placeholder"),
    ).toHaveLength(2);
  });

  it("renders all 5 cards on river", () => {
    const cards: CardType[] = [
      { rank: "A", suit: "h" },
      { rank: "K", suit: "s" },
      { rank: "Q", suit: "d" },
      { rank: "J", suit: "c" },
      { rank: "T", suit: "h" },
    ];
    const { container } = render(<CommunityCards cards={cards} />);
    expect(container.querySelectorAll(".card")).toHaveLength(5);
    expect(
      container.querySelectorAll(".community-cards__placeholder"),
    ).toHaveLength(0);
  });
});

// ─── PotDisplay ──────────────────────────────────────

describe("PotDisplay", () => {
  it("returns null when pot total is 0", () => {
    const { container } = render(<PotDisplay pots={[]} />);
    expect(container.querySelector(".pot-display")).not.toBeInTheDocument();
  });

  it("returns null for empty pots", () => {
    const { container } = render(
      <PotDisplay pots={[{ amount: 0, eligible_players: [0, 1] }]} />,
    );
    expect(container.querySelector(".pot-display")).not.toBeInTheDocument();
  });

  it("shows total pot amount", () => {
    const pots: Pot[] = [{ amount: 500, eligible_players: [0, 1] }];
    const { container } = render(<PotDisplay pots={pots} />);
    expect(container.querySelector(".pot-display__amount")).toHaveTextContent(
      "500",
    );
  });

  it("shows breakdown for multiple pots", () => {
    const pots: Pot[] = [
      { amount: 300, eligible_players: [0, 1] },
      { amount: 200, eligible_players: [0] },
    ];
    const { container } = render(<PotDisplay pots={pots} />);
    expect(container.querySelector(".pot-display__amount")).toHaveTextContent(
      "500",
    );
    const sidePots = container.querySelectorAll(".pot-display__side-pot");
    expect(sidePots).toHaveLength(2);
  });

  it("does not show breakdown for single pot", () => {
    const pots: Pot[] = [{ amount: 1000, eligible_players: [0, 1] }];
    const { container } = render(<PotDisplay pots={pots} />);
    expect(
      container.querySelector(".pot-display__breakdown"),
    ).not.toBeInTheDocument();
  });
});

// ─── PlayerSeat ──────────────────────────────────────

describe("PlayerSeat", () => {
  it("renders player name and chips", () => {
    const player = makePlayer({ name: "Alice", chips: 1500 });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(container.querySelector(".player-seat__name")).toHaveTextContent(
      "Alice",
    );
    expect(container.querySelector(".player-seat__chips")).toHaveTextContent(
      "1,500",
    );
  });

  it('shows "Out" for eliminated players', () => {
    const player = makePlayer({ is_eliminated: true, chips: 0 });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(container.querySelector(".player-seat__chips")).toHaveTextContent(
      "Out",
    );
  });

  it("shows active class when current turn", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(container.querySelector(".player-seat")).toHaveClass(
      "player-seat--active",
    );
  });

  it("renders current bet when > 0", () => {
    const player = makePlayer({ current_bet: 100 });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(
      container.querySelector(".player-seat__bet-amount"),
    ).toHaveTextContent("100");
  });

  it("does not render bet when 0", () => {
    const player = makePlayer({ current_bet: 0 });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(
      container.querySelector(".player-seat__bet"),
    ).not.toBeInTheDocument();
  });

  it("renders timer when provided and current turn", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn
        isHuman
        seatPosition={{ x: 50, y: 50 }}
        timerSeconds={25}
      />,
    );
    expect(container.querySelector(".player-seat__timer")).toHaveTextContent(
      "25s",
    );
  });

  it("applies urgent class when timer <= 10", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn
        isHuman
        seatPosition={{ x: 50, y: 50 }}
        timerSeconds={5}
      />,
    );
    expect(container.querySelector(".player-seat__timer")).toHaveClass(
      "player-seat__timer--urgent",
    );
  });

  it("positions using seatPosition percentages", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 25, y: 75 }}
      />,
    );
    const seat = container.querySelector(".player-seat") as HTMLElement;
    expect(seat.style.left).toBe("25%");
    expect(seat.style.top).toBe("75%");
  });
});

// ─── PokerTable ──────────────────────────────────────

describe("PokerTable", () => {
  it("renders correct number of player seats", () => {
    const players = [makePlayer({ seat_index: 0 }), makePlayer({ seat_index: 1, name: "Bot" })];
    const { container } = render(
      <PokerTable
        players={players}
        communityCards={[]}
        pots={[]}
        currentPlayerIndex={null}
        humanSeatIndex={null}
      />,
    );
    expect(container.querySelectorAll(".player-seat")).toHaveLength(2);
  });

  it("renders community cards area", () => {
    const players = [makePlayer()];
    const { container } = render(
      <PokerTable
        players={players}
        communityCards={[]}
        pots={[]}
        currentPlayerIndex={null}
        humanSeatIndex={null}
      />,
    );
    expect(container.querySelector(".community-cards")).toBeInTheDocument();
  });

  it("renders pot display when pots have value", () => {
    const players = [makePlayer()];
    const pots: Pot[] = [{ amount: 500, eligible_players: [0] }];
    const { container } = render(
      <PokerTable
        players={players}
        communityCards={[]}
        pots={pots}
        currentPlayerIndex={null}
        humanSeatIndex={null}
      />,
    );
    expect(container.querySelector(".pot-display")).toBeInTheDocument();
  });

  it("renders the felt area", () => {
    const { container } = render(
      <PokerTable
        players={[makePlayer()]}
        communityCards={[]}
        pots={[]}
        currentPlayerIndex={null}
        humanSeatIndex={null}
      />,
    );
    expect(container.querySelector(".poker-table__felt")).toBeInTheDocument();
  });
});
