/**
 * Tests for Phase 5 animation components:
 * ShowdownOverlay, PageTransition, LoadingSpinner,
 * and animation-related props on existing components.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import {
  ShowdownOverlay,
  getShowdownTier,
} from "../../components/table/ShowdownOverlay";
import type { ShowdownTier } from "../../components/table/ShowdownOverlay";
import { PageTransition } from "../../components/transitions/PageTransition";
import { LoadingSpinner } from "../../components/transitions/LoadingSpinner";
import { Card } from "../../components/cards/Card";
import { CardBack } from "../../components/cards/CardBack";
import { HoleCards } from "../../components/cards/HoleCards";
import { DealerButton } from "../../components/table/DealerButton";
import { PlayerSeat } from "../../components/table/PlayerSeat";
import type {
  ShowdownResult,
  PlayerState,
  Card as CardType,
} from "../../types/game";

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

function makeShowdownResult(
  overrides: Partial<ShowdownResult> = {},
): ShowdownResult {
  return {
    winners: [0],
    hand_results: [
      {
        player_index: 0,
        hand_rank: 6,
        hand_name: "Three of a Kind",
        hand_description: "Trip Aces",
      },
      {
        player_index: 1,
        hand_rank: 8,
        hand_name: "One Pair",
        hand_description: "Pair of Kings",
      },
    ],
    pot_distributions: [],
    ...overrides,
  };
}

// ─── getShowdownTier ─────────────────────────────────

describe("getShowdownTier", () => {
  it("returns spectacular for rank 1 (Straight Flush/Royal Flush)", () => {
    expect(getShowdownTier(1)).toBe("spectacular");
  });

  it("returns impressive for rank 2 (Four of a Kind)", () => {
    expect(getShowdownTier(2)).toBe("impressive");
  });

  it("returns impressive for rank 3 (Full House)", () => {
    expect(getShowdownTier(3)).toBe("impressive");
  });

  it("returns moderate for rank 4 (Flush)", () => {
    expect(getShowdownTier(4)).toBe("moderate");
  });

  it("returns moderate for rank 5 (Straight)", () => {
    expect(getShowdownTier(5)).toBe("moderate");
  });

  it("returns subtle for rank 6 (Three of a Kind)", () => {
    expect(getShowdownTier(6)).toBe("subtle");
  });

  it("returns subtle for rank 7 (Two Pair)", () => {
    expect(getShowdownTier(7)).toBe("subtle");
  });

  it("returns none for rank 8 (One Pair)", () => {
    expect(getShowdownTier(8)).toBe("none");
  });

  it("returns none for rank 9 (High Card)", () => {
    expect(getShowdownTier(9)).toBe("none");
  });
});

// ─── ShowdownOverlay ─────────────────────────────────

describe("ShowdownOverlay", () => {
  it("renders nothing when result is null", () => {
    const { container } = render(
      <ShowdownOverlay result={null} visible={false} />,
    );
    expect(
      container.querySelector(".showdown-overlay"),
    ).not.toBeInTheDocument();
  });

  it("renders nothing when visible is false (even with result)", () => {
    const result = makeShowdownResult();
    const { container } = render(
      <ShowdownOverlay result={result} visible={false} />,
    );
    expect(
      container.querySelector(".showdown-overlay__card"),
    ).not.toBeInTheDocument();
  });

  it("renders overlay when visible with result", () => {
    const result = makeShowdownResult();
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    expect(container.querySelector(".showdown-overlay")).toBeInTheDocument();
    expect(
      container.querySelector(".showdown-overlay__card"),
    ).toBeInTheDocument();
  });

  it("renders winner badge", () => {
    const result = makeShowdownResult();
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    expect(
      container.querySelector(".showdown-overlay__winner-badge"),
    ).toHaveTextContent("Winner");
  });

  it("renders hand results for all players", () => {
    const result = makeShowdownResult();
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    const hands = container.querySelectorAll(".showdown-overlay__hand");
    expect(hands).toHaveLength(2);
  });

  it("marks winner hand result correctly", () => {
    const result = makeShowdownResult();
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    const winnerHand = container.querySelector(
      ".showdown-overlay__hand--winner",
    );
    expect(winnerHand).toBeInTheDocument();
    expect(
      winnerHand?.querySelector(".showdown-overlay__hand-name"),
    ).toHaveTextContent("Three of a Kind");
  });

  it("applies correct tier class based on best hand", () => {
    const result = makeShowdownResult({
      hand_results: [
        {
          player_index: 0,
          hand_rank: 1,
          hand_name: "Royal Flush",
          hand_description: "A K Q J T of spades",
        },
      ],
    });
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    expect(
      container.querySelector(".showdown-overlay--spectacular"),
    ).toBeInTheDocument();
  });

  it("renders particles for impressive tier", () => {
    const result = makeShowdownResult({
      hand_results: [
        {
          player_index: 0,
          hand_rank: 2,
          hand_name: "Four of a Kind",
          hand_description: "Quad Aces",
        },
      ],
    });
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    const particles = container.querySelectorAll(
      ".showdown-overlay__particle--impressive",
    );
    expect(particles).toHaveLength(6);
  });

  it("renders 12 particles for spectacular tier", () => {
    const result = makeShowdownResult({
      hand_results: [
        {
          player_index: 0,
          hand_rank: 1,
          hand_name: "Royal Flush",
          hand_description: "A K Q J T of spades",
        },
      ],
    });
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    const particles = container.querySelectorAll(
      ".showdown-overlay__particle--spectacular",
    );
    expect(particles).toHaveLength(12);
  });

  it("does not render particles for none/subtle tiers", () => {
    const result = makeShowdownResult({
      hand_results: [
        {
          player_index: 0,
          hand_rank: 8,
          hand_name: "One Pair",
          hand_description: "Pair of 2s",
        },
      ],
    });
    const { container } = render(
      <ShowdownOverlay result={result} visible />,
    );
    expect(
      container.querySelector(".showdown-overlay__particles"),
    ).not.toBeInTheDocument();
  });
});

// ─── PageTransition ──────────────────────────────────

describe("PageTransition", () => {
  it("renders children", () => {
    render(
      <PageTransition>
        <div data-testid="child">Hello</div>
      </PageTransition>,
    );
    expect(screen.getByTestId("child")).toBeInTheDocument();
  });

  it("wraps content in a motion div with page-transition class", () => {
    const { container } = render(
      <PageTransition>
        <span>Content</span>
      </PageTransition>,
    );
    expect(
      container.querySelector(".page-transition"),
    ).toBeInTheDocument();
  });

  it("accepts fade variant (default)", () => {
    const { container } = render(
      <PageTransition variant="fade">
        <span>Fade</span>
      </PageTransition>,
    );
    expect(
      container.querySelector(".page-transition"),
    ).toBeInTheDocument();
  });

  it("accepts slide variant", () => {
    const { container } = render(
      <PageTransition variant="slide">
        <span>Slide</span>
      </PageTransition>,
    );
    expect(
      container.querySelector(".page-transition"),
    ).toBeInTheDocument();
  });
});

// ─── LoadingSpinner ──────────────────────────────────

describe("LoadingSpinner", () => {
  it("renders the spinner ring", () => {
    const { container } = render(<LoadingSpinner />);
    expect(
      container.querySelector(".loading-spinner__ring"),
    ).toBeInTheDocument();
  });

  it("renders default message", () => {
    const { container } = render(<LoadingSpinner />);
    expect(
      container.querySelector(".loading-spinner__message"),
    ).toBeInTheDocument();
  });

  it("renders custom message text", () => {
    const { container } = render(
      <LoadingSpinner message="Connecting…" />,
    );
    expect(
      container.querySelector(".loading-spinner__message"),
    ).toHaveTextContent("Connecting");
  });

  it("applies small size class", () => {
    const { container } = render(<LoadingSpinner size="small" />);
    expect(container.querySelector(".loading-spinner")).toHaveClass(
      "loading-spinner--small",
    );
  });

  it("applies medium size class (default)", () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector(".loading-spinner")).toHaveClass(
      "loading-spinner--medium",
    );
  });

  it("applies large size class", () => {
    const { container } = render(<LoadingSpinner size="large" />);
    expect(container.querySelector(".loading-spinner")).toHaveClass(
      "loading-spinner--large",
    );
  });

  it("renders animated dots", () => {
    const { container } = render(<LoadingSpinner />);
    const dots = container.querySelector(".loading-spinner__dots");
    expect(dots).toBeInTheDocument();
    expect(dots?.children).toHaveLength(3);
  });
});

// ─── Card animation props ────────────────────────────

describe("Card animation props", () => {
  it("renders with animate prop", () => {
    const card: CardType = { rank: "A", suit: "h" };
    const { container } = render(<Card card={card} animate />);
    expect(container.querySelector(".card")).toBeInTheDocument();
    expect(container.querySelector(".card__rank")).toHaveTextContent("A");
  });

  it("renders with highlight prop", () => {
    const card: CardType = { rank: "K", suit: "s" };
    const { container } = render(
      <Card card={card} highlight="impressive" />,
    );
    expect(container.querySelector(".card")).toHaveClass(
      "card--highlight-impressive",
    );
  });

  it("does not apply highlight when set to none", () => {
    const card: CardType = { rank: "Q", suit: "d" };
    const { container } = render(<Card card={card} highlight="none" />);
    const cardEl = container.querySelector(".card");
    expect(cardEl?.className).not.toContain("highlight");
  });

  it("renders all highlight levels", () => {
    const tiers: Array<Exclude<ShowdownTier, "none">> = [
      "subtle",
      "moderate",
      "impressive",
      "spectacular",
    ];
    for (const tier of tiers) {
      const { container, unmount } = render(
        <Card card={{ rank: "A", suit: "h" }} highlight={tier} />,
      );
      expect(container.querySelector(".card")).toHaveClass(
        `card--highlight-${tier}`,
      );
      unmount();
    }
  });
});

// ─── CardBack animation props ────────────────────────

describe("CardBack animation props", () => {
  it("renders with animate prop", () => {
    const { container } = render(<CardBack animate />);
    expect(container.querySelector(".card-back")).toBeInTheDocument();
  });

  it("renders with dealDelay prop", () => {
    const { container } = render(<CardBack animate dealDelay={0.5} />);
    expect(container.querySelector(".card-back")).toBeInTheDocument();
  });
});

// ─── HoleCards animation props ───────────────────────

describe("HoleCards animation props", () => {
  it("renders with animate and highlight props", () => {
    const cards: CardType[] = [
      { rank: "A", suit: "s" },
      { rank: "K", suit: "s" },
    ];
    const { container } = render(
      <HoleCards cards={cards} animate highlight="moderate" />,
    );
    const cardEls = container.querySelectorAll(".card");
    expect(cardEls).toHaveLength(2);
    for (const el of cardEls) {
      expect(el).toHaveClass("card--highlight-moderate");
    }
  });

  it("renders with dealDelay prop", () => {
    const { container } = render(
      <HoleCards cards={null} animate dealDelay={0.3} />,
    );
    expect(container.querySelectorAll(".card-back")).toHaveLength(2);
  });
});

// ─── DealerButton animation ──────────────────────────

describe("DealerButton animation", () => {
  it("renders D text when visible", () => {
    const { container } = render(<DealerButton visible />);
    expect(container.querySelector(".dealer-button")).toHaveTextContent("D");
  });

  it("renders nothing in DOM when not visible", () => {
    const { container } = render(<DealerButton visible={false} />);
    expect(
      container.querySelector(".dealer-button"),
    ).not.toBeInTheDocument();
  });
});

// ─── PlayerSeat animation props ──────────────────────

describe("PlayerSeat animation props", () => {
  it("renders action badge when lastAction is provided", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        lastAction="raise"
      />,
    );
    const badge = container.querySelector(".player-seat__action-badge");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("player-seat__action-badge--raise");
  });

  it("does not render action badge when lastAction is null", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        lastAction={null}
      />,
    );
    expect(
      container.querySelector(".player-seat__action-badge"),
    ).not.toBeInTheDocument();
  });

  it("applies showdownHighlight to hole cards", () => {
    const player = makePlayer({
      hole_cards: [
        { rank: "A", suit: "s" },
        { rank: "K", suit: "s" },
      ],
    });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        showdownHighlight="impressive"
      />,
    );
    const cards = container.querySelectorAll(".card");
    for (const card of cards) {
      expect(card).toHaveClass("card--highlight-impressive");
    }
  });

  it("renders action badge with fold class", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        lastAction="fold"
      />,
    );
    expect(
      container.querySelector(".player-seat__action-badge--fold"),
    ).toBeInTheDocument();
  });

  it("renders action badge with check class", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        lastAction="check"
      />,
    );
    expect(
      container.querySelector(".player-seat__action-badge--check"),
    ).toBeInTheDocument();
  });

  it("renders action badge with call class", () => {
    const player = makePlayer();
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
        lastAction="call"
      />,
    );
    expect(
      container.querySelector(".player-seat__action-badge--call"),
    ).toBeInTheDocument();
  });

  it("does not show cards for eliminated players", () => {
    const player = makePlayer({ is_eliminated: true });
    const { container } = render(
      <PlayerSeat
        player={player}
        isCurrentTurn={false}
        isHuman={false}
        seatPosition={{ x: 50, y: 50 }}
      />,
    );
    expect(
      container.querySelector(".player-seat__cards"),
    ).not.toBeInTheDocument();
  });
});
