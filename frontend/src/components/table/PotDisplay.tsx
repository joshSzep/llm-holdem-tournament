/**
 * PotDisplay — shows main pot and side pots in the center of the table.
 */

import type { Pot } from "../../types/game";

interface PotDisplayProps {
  pots: Pot[];
}

export function PotDisplay({
  pots,
}: PotDisplayProps): React.ReactElement | null {
  const total = pots.reduce((sum, p) => sum + p.amount, 0);
  if (total === 0) return null;

  return (
    <div className="pot-display">
      <div className="pot-display__total">
        <span className="pot-display__label">Pot</span>
        <span className="pot-display__amount">
          {total.toLocaleString()}
        </span>
      </div>
      {pots.length > 1 && (
        <div className="pot-display__breakdown">
          {pots.map((pot, i) => (
            <span key={i} className="pot-display__side-pot">
              {i === 0 ? "Main" : `Side ${i}`}: {pot.amount.toLocaleString()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
