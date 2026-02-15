/**
 * LoadingSpinner — animated loading indicator for connection/data states.
 */

import { motion } from "framer-motion";
import "./LoadingSpinner.css";

interface LoadingSpinnerProps {
  /** Text to display below the spinner */
  message?: string;
  /** Size of the spinner */
  size?: "small" | "medium" | "large";
}

const spinnerVariants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: "linear" as const,
    },
  },
};

const dotVariants = {
  animate: (i: number) => ({
    opacity: [0.3, 1, 0.3],
    transition: {
      duration: 1.2,
      repeat: Infinity,
      delay: i * 0.2,
    },
  }),
};

const containerVariants = {
  initial: { opacity: 0, scale: 0.9 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.3, ease: "easeOut" as const },
  },
};

export function LoadingSpinner({
  message = "Loading…",
  size = "medium",
}: LoadingSpinnerProps): React.ReactElement {
  return (
    <motion.div
      className={`loading-spinner loading-spinner--${size}`}
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <motion.div
        className="loading-spinner__ring"
        variants={spinnerVariants}
        animate="animate"
      />
      {message && (
        <div className="loading-spinner__message">
          {message.replace("…", "")}
          <span className="loading-spinner__dots">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                variants={dotVariants}
                animate="animate"
                custom={i}
              >
                .
              </motion.span>
            ))}
          </span>
        </div>
      )}
    </motion.div>
  );
}
