/**
 * HoleCards — displays the two hole cards for a player.
 * Shows face-up cards if visible, face-down otherwise.
 * Supports staggered deal animations.
 */

import { AnimatePresence, motion } from "framer-motion";
import type { Card as CardType } from "../../types/game";
import { Card } from "./Card";
import { CardBack } from "./CardBack";
import "./Card.css";

interface HoleCardsProps {
  cards: CardType[] | null;
  small?: boolean;
  /** Whether to animate cards being dealt */
  animate?: boolean;
  /** Base delay for staggered animations */
  dealDelay?: number;
  /** Showdown highlight level */
  highlight?: "none" | "subtle" | "moderate" | "impressive" | "spectacular";
}

const foldVariants = {
  exit: {
    opacity: 0,
    y: -20,
    scale: 0.8,
    transition: { duration: 0.3, ease: "easeIn" as const },
  },
};

export function HoleCards({
  cards,
  small = false,
  animate = false,
  dealDelay = 0,
  highlight = "none",
}: HoleCardsProps): React.ReactElement {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        className={`hole-cards ${small ? "hole-cards--small" : ""}`}
        key={cards ? "visible" : "hidden"}
        variants={foldVariants}
        exit="exit"
      >
        {cards && cards.length >= 2 ? (
          <>
            <Card
              card={cards[0]!}
              animate={animate}
              dealDelay={dealDelay}
              highlight={highlight}
            />
            <Card
              card={cards[1]!}
              animate={animate}
              dealDelay={dealDelay + 0.1}
              highlight={highlight}
            />
          </>
        ) : (
          <>
            <CardBack animate={animate} dealDelay={dealDelay} />
            <CardBack animate={animate} dealDelay={dealDelay + 0.1} />
          </>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
