/**
 * CardBack — a face-down card with optional deal animation.
 */

import { motion } from "framer-motion";
import "./Card.css";

interface CardBackProps {
  /** Animation delay in seconds for staggered dealing */
  dealDelay?: number;
  /** Whether to animate the card appearing */
  animate?: boolean;
}

const dealVariants = {
  hidden: { scale: 0.3, opacity: 0, y: -40 },
  visible: (delay: number) => ({
    scale: 1,
    opacity: 1,
    y: 0,
    transition: {
      delay,
      duration: 0.35,
      ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
    },
  }),
};

export function CardBack({
  dealDelay = 0,
  animate = false,
}: CardBackProps): React.ReactElement {
  if (animate) {
    return (
      <motion.div
        className="card-back"
        variants={dealVariants}
        initial="hidden"
        animate="visible"
        custom={dealDelay}
      >
        <div className="card-back__pattern" />
      </motion.div>
    );
  }

  return (
    <div className="card-back">
      <div className="card-back__pattern" />
    </div>
  );
}
