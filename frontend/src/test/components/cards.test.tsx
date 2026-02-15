/**
 * Tests for Card, CardBack, and HoleCards components.
 */

import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { Card } from "../../components/cards/Card";
import { CardBack } from "../../components/cards/CardBack";
import { HoleCards } from "../../components/cards/HoleCards";
import type { Card as CardType } from "../../types/game";

describe("Card", () => {
  it("renders rank and suit", () => {
    const card: CardType = { rank: "A", suit: "h" };
    const { container } = render(<Card card={card} />);
    expect(container.querySelector(".card__rank")).toHaveTextContent("A");
    expect(container.querySelector(".card__suit")).toHaveTextContent("♥");
  });

  it("applies red class for hearts", () => {
    const { container } = render(<Card card={{ rank: "K", suit: "h" }} />);
    expect(container.querySelector(".card")).toHaveClass("card--red");
  });

  it("applies red class for diamonds", () => {
    const { container } = render(<Card card={{ rank: "Q", suit: "d" }} />);
    expect(container.querySelector(".card")).toHaveClass("card--red");
  });

  it("applies black class for clubs", () => {
    const { container } = render(<Card card={{ rank: "J", suit: "c" }} />);
    expect(container.querySelector(".card")).toHaveClass("card--black");
  });

  it("applies black class for spades", () => {
    const { container } = render(<Card card={{ rank: "T", suit: "s" }} />);
    expect(container.querySelector(".card")).toHaveClass("card--black");
  });

  it("renders correct suit symbols", () => {
    const suits: Array<{ suit: CardType["suit"]; symbol: string }> = [
      { suit: "h", symbol: "♥" },
      { suit: "d", symbol: "♦" },
      { suit: "c", symbol: "♣" },
      { suit: "s", symbol: "♠" },
    ];
    for (const { suit, symbol } of suits) {
      const { container, unmount } = render(
        <Card card={{ rank: "2", suit }} />,
      );
      expect(container.querySelector(".card__suit")).toHaveTextContent(symbol);
      unmount();
    }
  });
});

describe("CardBack", () => {
  it("renders a face-down card", () => {
    const { container } = render(<CardBack />);
    expect(container.querySelector(".card-back")).toBeInTheDocument();
  });

  it("contains the pattern element", () => {
    const { container } = render(<CardBack />);
    expect(
      container.querySelector(".card-back__pattern"),
    ).toBeInTheDocument();
  });
});

describe("HoleCards", () => {
  it("renders face-up cards when cards are provided", () => {
    const cards: CardType[] = [
      { rank: "A", suit: "s" },
      { rank: "K", suit: "s" },
    ];
    const { container } = render(<HoleCards cards={cards} />);
    expect(container.querySelectorAll(".card")).toHaveLength(2);
  });

  it("renders face-down cards when no cards provided", () => {
    const { container } = render(<HoleCards cards={null} />);
    expect(container.querySelectorAll(".card-back")).toHaveLength(2);
  });

  it("renders face-down cards when cards array is empty", () => {
    const { container } = render(<HoleCards cards={[]} />);
    expect(container.querySelectorAll(".card-back")).toHaveLength(2);
  });

  it("applies small class when small prop is true", () => {
    const { container } = render(<HoleCards cards={null} small />);
    expect(container.querySelector(".hole-cards")).toHaveClass(
      "hole-cards--small",
    );
  });

  it("does not apply small class by default", () => {
    const { container } = render(<HoleCards cards={null} />);
    expect(container.querySelector(".hole-cards")).not.toHaveClass(
      "hole-cards--small",
    );
  });
});
