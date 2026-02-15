/**
 * ShowdownOverlay — displays hand evaluation results during showdown.
 * Tiered animation intensity based on hand strength:
 *   - High Card / One Pair: minimal — simple reveal
 *   - Two Pair / Three of a Kind: subtle — slight glow
 *   - Straight / Flush: moderate — expanding highlight
 *   - Full House: impressive — dramatic reveal with strong glow
 *   - Four of a Kind / Straight Flush: very impressive — particles
 *   - Royal Flush: most spectacular — full celebration
 */

import { motion, AnimatePresence } from "framer-motion";
import type { ShowdownResult } from "../../types/game";
import "./ShowdownOverlay.css";

interface ShowdownOverlayProps {
  result: ShowdownResult | null;
  /** Whether the showdown is currently being displayed */
  visible: boolean;
}

export type ShowdownTier =
  | "none"
  | "subtle"
  | "moderate"
  | "impressive"
  | "spectacular";

/**
 * Map hand rank (lower is better in treys) to a visual tier.
 * treys ranking: 1 = Royal Flush, higher = weaker.
 * We use hand_rank from the backend which is the treys rank class (1-9):
 * 1 = Straight Flush/Royal Flush, 2 = Four of a Kind, 3 = Full House,
 * 4 = Flush, 5 = Straight, 6 = Three of a Kind, 7 = Two Pair,
 * 8 = One Pair, 9 = High Card
 */
export function getShowdownTier(handRank: number): ShowdownTier {
  if (handRank <= 1) return "spectacular"; // Straight Flush / Royal Flush
  if (handRank <= 2) return "impressive"; // Four of a Kind
  if (handRank <= 3) return "impressive"; // Full House
  if (handRank <= 5) return "moderate"; // Flush, Straight
  if (handRank <= 7) return "subtle"; // Three of a Kind, Two Pair
  return "none"; // One Pair, High Card
}

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.5, delay: 0.3 },
  },
};

const resultCardVariants = {
  hidden: { scale: 0.7, opacity: 0, y: 20 },
  visible: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: {
      type: "spring" as const,
      stiffness: 300,
      damping: 20,
      delay: 0.2,
    },
  },
  exit: {
    scale: 0.9,
    opacity: 0,
    y: -10,
    transition: { duration: 0.3 },
  },
};

const handNameVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.4 + i * 0.15, duration: 0.4 },
  }),
};

const winnerBadgeVariants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: "spring" as const,
      stiffness: 400,
      damping: 15,
      delay: 0.8,
    },
  },
};

const particleVariants = {
  initial: { opacity: 0, scale: 0 },
  animate: (i: number) => ({
    opacity: [0, 1, 0],
    scale: [0, 1, 0.5],
    x: [0, (i % 2 === 0 ? 1 : -1) * (30 + i * 15)],
    y: [0, -(20 + i * 10)],
    transition: {
      duration: 1.2,
      delay: 0.6 + i * 0.08,
      ease: "easeOut" as const,
    },
  }),
};

export function ShowdownOverlay({
  result,
  visible,
}: ShowdownOverlayProps): React.ReactElement {
  if (!result) return <></>;

  const bestHandResult = result.hand_results.reduce(
    (best, hr) => (hr.hand_rank < best.hand_rank ? hr : best),
    result.hand_results[0]!,
  );
  const tier = getShowdownTier(bestHandResult.hand_rank);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={`showdown-overlay showdown-overlay--${tier}`}
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          <motion.div
            className="showdown-overlay__card"
            variants={resultCardVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {/* Winner badge */}
            <motion.div
              className="showdown-overlay__winner-badge"
              variants={winnerBadgeVariants}
              initial="hidden"
              animate="visible"
            >
              Winner
            </motion.div>

            {/* Hand results */}
            <div className="showdown-overlay__results">
              {result.hand_results.map((hr, i) => (
                <motion.div
                  key={hr.player_index}
                  className={`showdown-overlay__hand ${
                    result.winners.includes(hr.player_index)
                      ? "showdown-overlay__hand--winner"
                      : ""
                  }`}
                  variants={handNameVariants}
                  initial="hidden"
                  animate="visible"
                  custom={i}
                >
                  <span className="showdown-overlay__hand-name">
                    {hr.hand_name}
                  </span>
                  <span className="showdown-overlay__hand-desc">
                    {hr.hand_description}
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Particles for impressive/spectacular hands */}
            {(tier === "impressive" || tier === "spectacular") && (
              <div className="showdown-overlay__particles">
                {Array.from({ length: tier === "spectacular" ? 12 : 6 }).map(
                  (_, i) => (
                    <motion.div
                      key={i}
                      className={`showdown-overlay__particle showdown-overlay__particle--${tier}`}
                      variants={particleVariants}
                      initial="initial"
                      animate="animate"
                      custom={i}
                    />
                  ),
                )}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
