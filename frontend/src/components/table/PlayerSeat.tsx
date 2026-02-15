/**
 * PlayerSeat — individual seat around the poker table.
 * Shows avatar, name, chip count, hole cards, dealer button, and turn timer.
 */

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

export function PlayerSeat({
  player,
  isCurrentTurn,
  isHuman,
  seatPosition,
  timerSeconds,
}: PlayerSeatProps): React.ReactElement {
  const avatarState = getAvatarState(player, isCurrentTurn);
  const showCards = !player.is_eliminated;

  return (
    <div
      className={`player-seat ${isCurrentTurn ? "player-seat--active" : ""} ${isHuman ? "player-seat--human" : ""}`}
      style={{
        left: `${seatPosition.x}%`,
        top: `${seatPosition.y}%`,
      }}
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
        <span className="player-seat__chips">
          {player.is_eliminated
            ? "Out"
            : player.chips.toLocaleString()}
        </span>
      </div>

      {showCards && (
        <div className="player-seat__cards">
          <HoleCards cards={player.hole_cards} small />
        </div>
      )}

      {player.current_bet > 0 && (
        <div className="player-seat__bet">
          <span className="player-seat__bet-amount">
            {player.current_bet.toLocaleString()}
          </span>
        </div>
      )}

      {isCurrentTurn && timerSeconds != null && (
        <div
          className={`player-seat__timer ${timerSeconds <= 10 ? "player-seat__timer--urgent" : ""}`}
        >
          {timerSeconds}s
        </div>
      )}
    </div>
  );
}
