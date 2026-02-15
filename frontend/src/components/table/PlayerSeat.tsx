/**
 * PlayerSeat — individual seat around the poker table.
 * Shows avatar, name, chip count, hole cards, dealer button, and turn timer.
 * Includes Framer Motion animations for actions, eliminations, and chip changes.
 */

import { motion, AnimatePresence } from "framer-motion";
import "./PlayerSeat.css";
import type { PlayerState } from "../../types/game";
import { Avatar } from "../avatars/Avatar";
import { HoleCards } from "../cards/HoleCards";
import { DealerButton } from "./DealerButton";

interface PlayerSeatProps {
  player: PlayerState;
  isCurrentTurn: boolean;
  isHuman: boolean;
  seatPosition: { x: number; y: number };
  timerSeconds?: number | null;
  /** Last action performed by this player (for action animation) */
  lastAction?: string | null;
  /** Showdown highlight level */
  showdownHighlight?: "none" | "subtle" | "moderate" | "impressive" | "spectacular";
}

function getAvatarState(
  player: PlayerState,
  isCurrentTurn: boolean,
): "active" | "folded" | "all-in" | "eliminated" | "low-chips" | "default" {
  if (player.is_eliminated) return "eliminated";
  if (player.is_folded) return "folded";
  if (isCurrentTurn) return "active";
  if (player.is_all_in) return "all-in";
  if (player.chips > 0 && player.chips <= 100) return "low-chips";
  return "default";
}

const seatVariants = {
  default: { scale: 1, opacity: 1 },
  eliminated: {
    scale: 0.92,
    opacity: 0.4,
    filter: "grayscale(100%)",
    transition: { duration: 0.8, ease: "easeOut" as const },
  },
};

const betVariants = {
  initial: { scale: 0, opacity: 0, y: 8 },
  animate: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 400, damping: 20 },
  },
  exit: {
    scale: 0.5,
    opacity: 0,
    y: -12,
    transition: { duration: 0.3, ease: "easeIn" as const },
  },
};

const actionBadgeVariants = {
  initial: { scale: 0.5, opacity: 0, y: 6 },
  animate: {
    scale: 1,
    opacity: 1,
    y: 0,
    transition: { type: "spring" as const, stiffness: 500, damping: 25 },
  },
  exit: {
    scale: 0.8,
    opacity: 0,
    y: -8,
    transition: { duration: 0.4, ease: "easeIn" as const },
  },
};

const chipCountVariants = {
  initial: { scale: 1.25, color: "#3fb950" },
  animate: {
    scale: 1,
    color: "#d29922",
    transition: { duration: 0.35, ease: "easeOut" as const },
  },
};

export function PlayerSeat({
  player,
  isCurrentTurn,
  isHuman,
  seatPosition,
  timerSeconds,
  lastAction = null,
  showdownHighlight = "none",
}: PlayerSeatProps): React.ReactElement {
  const avatarState = getAvatarState(player, isCurrentTurn);
  const showCards = !player.is_eliminated;

  return (
    <motion.div
      className={`player-seat ${isCurrentTurn ? "player-seat--active" : ""} ${isHuman ? "player-seat--human" : ""}`}
      style={{
        left: `${seatPosition.x}%`,
        top: `${seatPosition.y}%`,
      }}
      variants={seatVariants}
      animate={player.is_eliminated ? "eliminated" : "default"}
      transition={{ duration: 0.5 }}
      layout
    >
      <div className="player-seat__avatar-area">
        <Avatar
          src={player.avatar_url}
          name={player.name}
          state={avatarState}
          size="medium"
        />
        <DealerButton visible={player.is_dealer} />
      </div>

      <div className="player-seat__info">
        <span className="player-seat__name" title={player.name}>
          {player.name}
        </span>
        <motion.span
          className="player-seat__chips"
          key={`chips-${player.chips}`}
          variants={chipCountVariants}
          initial="initial"
          animate="animate"
        >
          {player.is_eliminated
            ? "Out"
            : player.chips.toLocaleString()}
        </motion.span>
      </div>

      {showCards && (
        <div className="player-seat__cards">
          <HoleCards
            cards={player.hole_cards}
            small
            animate
            highlight={showdownHighlight}
          />
        </div>
      )}

      {/* Bet chip animation */}
      <AnimatePresence>
        {player.current_bet > 0 && (
          <motion.div
            className="player-seat__bet"
            variants={betVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            key={`bet-${player.current_bet}`}
          >
            <span className="player-seat__bet-amount">
              {player.current_bet.toLocaleString()}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action badge (fold/check/call/raise/all-in) */}
      <AnimatePresence>
        {lastAction && (
          <motion.div
            className={`player-seat__action-badge player-seat__action-badge--${lastAction}`}
            variants={actionBadgeVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            key={`action-${lastAction}-${Date.now()}`}
          >
            {lastAction.replace("_", " ")}
          </motion.div>
        )}
      </AnimatePresence>

      {isCurrentTurn && timerSeconds != null && (
        <div
          className={`player-seat__timer ${timerSeconds <= 10 ? "player-seat__timer--urgent" : ""}`}
        >
          {timerSeconds}s
        </div>
      )}
    </motion.div>
  );
}
