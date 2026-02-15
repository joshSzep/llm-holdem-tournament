/**
 * PotDisplay — shows main pot and side pots in the center of the table.
 * Animates chip amount changes smoothly.
 */

import { motion, AnimatePresence } from "framer-motion";
import type { Pot } from "../../types/game";

interface PotDisplayProps {
  pots: Pot[];
}

const potVariants = {
  initial: { scale: 0.8, opacity: 0, y: 10 },
  animate: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" as const },
  },
  exit: {
    scale: 0.6,
    opacity: 0,
    y: -15,
    transition: { duration: 0.3, ease: "easeIn" as const },
  },
};

const amountVariants = {
  initial: { scale: 1.3, color: "#3fb950" },
  animate: {
    scale: 1,
    color: "#d29922",
    transition: { duration: 0.4, ease: "easeOut" as const },
  },
};

export function PotDisplay({
  pots,
}: PotDisplayProps): React.ReactElement | null {
  const total = pots.reduce((sum, p) => sum + p.amount, 0);
  if (total === 0) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        className="pot-display"
        key={total}
        variants={potVariants}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        <div className="pot-display__total">
          <span className="pot-display__label">Pot</span>
          <motion.span
            className="pot-display__amount"
            key={`amount-${total}`}
            variants={amountVariants}
            initial="initial"
            animate="animate"
          >
            {total.toLocaleString()}
          </motion.span>
        </div>
        {pots.length > 1 && (
          <div className="pot-display__breakdown">
            {pots.map((pot, i) => (
              <motion.span
                key={i}
                className="pot-display__side-pot"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1, duration: 0.25 }}
              >
                {i === 0 ? "Main" : `Side ${i}`}: {pot.amount.toLocaleString()}
              </motion.span>
            ))}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
