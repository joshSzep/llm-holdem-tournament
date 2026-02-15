/**
 * DealerButton — small circular dealer button indicator.
 * Smoothly animates in/out with Framer Motion.
 */

import { motion, AnimatePresence } from "framer-motion";

interface DealerButtonProps {
  visible: boolean;
}

const buttonVariants = {
  initial: { scale: 0, opacity: 0, rotate: -90 },
  animate: {
    scale: 1,
    opacity: 1,
    rotate: 0,
    transition: { type: "spring" as const, stiffness: 400, damping: 20, duration: 0.4 },
  },
  exit: {
    scale: 0,
    opacity: 0,
    rotate: 90,
    transition: { duration: 0.25, ease: "easeIn" as const },
  },
};

export function DealerButton({
  visible,
}: DealerButtonProps): React.ReactElement {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="dealer-button"
          variants={buttonVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          layout
        >
          D
        </motion.div>
      )}
    </AnimatePresence>
  );
}
