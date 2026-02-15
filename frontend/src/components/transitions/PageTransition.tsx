/**
 * PageTransition — wraps page content with enter/exit animations.
 */

import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface PageTransitionProps {
  children: ReactNode;
  /** Animation variant: 'fade' (default) or 'slide' */
  variant?: "fade" | "slide";
}

const fadeVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.3, ease: "easeOut" as const },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2, ease: "easeIn" as const },
  },
};

const slideVariants = {
  initial: { opacity: 0, x: 20 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number] },
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: { duration: 0.25, ease: "easeIn" as const },
  },
};

export function PageTransition({
  children,
  variant = "fade",
}: PageTransitionProps): React.ReactElement {
  const variants = variant === "slide" ? slideVariants : fadeVariants;

  return (
    <motion.div
      className="page-transition"
      variants={variants}
      initial="initial"
      animate="animate"
      exit="exit"
      style={{ height: "100%", display: "flex", flexDirection: "column" }}
    >
      {children}
    </motion.div>
  );
}
