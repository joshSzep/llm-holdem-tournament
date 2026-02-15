/**
 * PokerTable — the main oval poker table with dynamic seat positioning.
 * Arranges 2-6 player seats around an elliptical table, with community cards
 * and pot display in the center.
 */

import "./PokerTable.css";
import type { PlayerState, Card as CardType, Pot } from "../../types/game";
import { PlayerSeat } from "./PlayerSeat";
import { CommunityCards } from "./CommunityCards";
import { PotDisplay } from "./PotDisplay";

interface PokerTableProps {
  players: PlayerState[];
  communityCards: CardType[];
  pots: Pot[];
  currentPlayerIndex: number | null;
  humanSeatIndex: number | null;
  timerSeatIndex?: number | null;
  timerSeconds?: number | null;
}

/**
 * Seat positions as percentages of the table container.
 * Arranged in an ellipse; index 0 is bottom center (human seat).
 * Positions are tuned per player count for visual balance.
 */
const SEAT_POSITIONS: Record<number, Array<{ x: number; y: number }>> = {
  2: [
    { x: 50, y: 85 }, // bottom center
    { x: 50, y: 8 }, // top center
  ],
  3: [
    { x: 50, y: 85 },
    { x: 15, y: 25 },
    { x: 85, y: 25 },
  ],
  4: [
    { x: 50, y: 85 },
    { x: 10, y: 50 },
    { x: 50, y: 8 },
    { x: 90, y: 50 },
  ],
  5: [
    { x: 50, y: 85 },
    { x: 10, y: 55 },
    { x: 22, y: 10 },
    { x: 78, y: 10 },
    { x: 90, y: 55 },
  ],
  6: [
    { x: 50, y: 85 },
    { x: 8, y: 55 },
    { x: 18, y: 10 },
    { x: 82, y: 10 },
    { x: 92, y: 55 },
    { x: 50, y: 8 },
  ],
};

/**
 * Rotate seat positions so the human player appears at the bottom.
 */
function getSeatPositions(
  playerCount: number,
  humanSeatIndex: number | null,
): Array<{ x: number; y: number }> {
  const positions = SEAT_POSITIONS[playerCount] ?? SEAT_POSITIONS[6]!;
  if (humanSeatIndex === null || humanSeatIndex === 0) return positions;

  // Rotate so human's seat index maps to position 0 (bottom center)
  const result: Array<{ x: number; y: number }> = [];
  for (let i = 0; i < playerCount; i++) {
    const posIndex = (i - humanSeatIndex + playerCount) % playerCount;
    result.push(positions[posIndex]!);
  }
  return result;
}

export function PokerTable({
  players,
  communityCards,
  pots,
  currentPlayerIndex,
  humanSeatIndex,
  timerSeatIndex,
  timerSeconds,
}: PokerTableProps): React.ReactElement {
  const positions = getSeatPositions(players.length, humanSeatIndex);

  return (
    <div className="poker-table">
      <div className="poker-table__felt">
        {/* Center area: community cards + pot */}
        <div className="poker-table__center">
          <PotDisplay pots={pots} />
          <CommunityCards cards={communityCards} />
        </div>

        {/* Player seats arranged around the table */}
        {players.map((player, i) => (
          <PlayerSeat
            key={player.seat_index}
            player={player}
            isCurrentTurn={currentPlayerIndex === player.seat_index}
            isHuman={humanSeatIndex === player.seat_index}
            seatPosition={positions[i]!}
            timerSeconds={
              timerSeatIndex === player.seat_index
                ? timerSeconds
                : null
            }
          />
        ))}
      </div>
    </div>
  );
}
