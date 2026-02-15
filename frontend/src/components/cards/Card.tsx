/**
 * Card component — displays a single playing card with rank and suit.
 * Supports Framer Motion animations for dealing and reveals.
 */

import { motion } from "framer-motion";
import type { Card as CardType } from "../../types/game";
import "./Card.css";

interface CardProps {
  card: CardType;
  /** Animation delay in seconds for staggered dealing */
  dealDelay?: number;
  /** Whether to animate the card appearing */
  animate?: boolean;
  /** Optional highlight class for showdown */
  highlight?: "none" | "subtle" | "moderate" | "impressive" | "spectacular";
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

const dealVariants = {
  hidden: { scale: 0.3, opacity: 0, y: -40, rotateY: 180 },
  visible: (delay: number) => ({
    scale: 1,
    opacity: 1,
    y: 0,
    rotateY: 0,
    transition: {
      delay,
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
    },
  }),
};

export function Card({
  card,
  dealDelay = 0,
  animate = false,
  highlight = "none",
}: CardProps): React.ReactElement {
  const symbol = SUIT_SYMBOLS[card.suit] ?? card.suit;
  const colorClass = SUIT_COLORS[card.suit] === "red" ? "card--red" : "card--black";
  const highlightClass = highlight !== "none" ? `card--highlight-${highlight}` : "";

  if (animate) {
    return (
      <motion.div
        className={`card ${colorClass} ${highlightClass}`}
        variants={dealVariants}
        initial="hidden"
        animate="visible"
        custom={dealDelay}
        layout
      >
        <span className="card__rank">{card.rank}</span>
        <span className="card__suit">{symbol}</span>
      </motion.div>
    );
  }

  return (
    <div className={`card ${colorClass} ${highlightClass}`}>
      <span className="card__rank">{card.rank}</span>
      <span className="card__suit">{symbol}</span>
    </div>
  );
}
