/**
 * Card component — displays a single playing card with rank and suit.
 */

import type { Card as CardType } from "../../types/game";
import "./Card.css";

interface CardProps {
  card: CardType;
}

const SUIT_SYMBOLS: Record<string, string> = {
  h: "♥",
  d: "♦",
  c: "♣",
  s: "♠",
};

const SUIT_COLORS: Record<string, string> = {
  h: "red",
  d: "red",
  c: "black",
  s: "black",
};

export function Card({ card }: CardProps): React.ReactElement {
  const symbol = SUIT_SYMBOLS[card.suit] ?? card.suit;
  const colorClass = SUIT_COLORS[card.suit] === "red" ? "card--red" : "card--black";

  return (
    <div className={`card ${colorClass}`}>
      <span className="card__rank">{card.rank}</span>
      <span className="card__suit">{symbol}</span>
    </div>
  );
}
