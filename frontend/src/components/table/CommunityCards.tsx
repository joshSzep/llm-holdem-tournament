/**
 * CommunityCards — displays the 5-card community area in the center of the table.
 * Animates card reveals for flop (3 cards), turn, and river.
 */

import { AnimatePresence, motion } from "framer-motion";
import type { Card as CardType } from "../../types/game";
import { Card } from "../cards/Card";

interface CommunityCardsProps {
  cards: CardType[];
}

const placeholderVariants = {
  initial: { opacity: 0.3 },
  animate: { opacity: 0.3 },
  exit: {
    opacity: 0,
    scale: 0.8,
    transition: { duration: 0.2 },
  },
};

const cardRevealVariants = {
  hidden: { scale: 0.5, opacity: 0, y: -20, rotateY: 90 },
  visible: (i: number) => ({
    scale: 1,
    opacity: 1,
    y: 0,
    rotateY: 0,
    transition: {
      delay: i * 0.12,
      duration: 0.4,
      ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
    },
  }),
};

export function CommunityCards({
  cards,
}: CommunityCardsProps): React.ReactElement {
  return (
    <div className="community-cards">
      <AnimatePresence mode="popLayout">
        {cards.map((card, i) => (
          <motion.div
            key={`${card.rank}${card.suit}-${i}`}
            variants={cardRevealVariants}
            initial="hidden"
            animate="visible"
            custom={i}
            layout
          >
            <Card card={card} />
          </motion.div>
        ))}
        {/* Empty placeholders for undealt cards */}
        {Array.from({ length: 5 - cards.length }).map((_, i) => (
          <motion.div
            key={`empty-${i}`}
            className="community-cards__placeholder"
            variants={placeholderVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          />
        ))}
      </AnimatePresence>
    </div>
  );
}
