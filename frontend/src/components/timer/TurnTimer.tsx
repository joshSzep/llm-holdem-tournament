/**
 * TurnTimer — circular countdown timer displayed during a player's turn.
 */

import "./TurnTimer.css";
import { useTimer } from "../../hooks/useTimer";

const RADIUS = 20;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const MAX_SECONDS = 60;

export function TurnTimer(): React.ReactElement | null {
  const { secondsRemaining, isActive, isUrgent } = useTimer();

  if (!isActive || secondsRemaining === null) return null;

  const progress = Math.max(0, secondsRemaining / MAX_SECONDS);
  const dashOffset = CIRCUMFERENCE * (1 - progress);

  return (
    <div className={`turn-timer ${isUrgent ? "turn-timer--urgent" : ""}`}>
      <svg className="turn-timer__svg" viewBox="0 0 48 48">
        <circle
          className="turn-timer__track"
          cx="24"
          cy="24"
          r={RADIUS}
          fill="none"
          strokeWidth="3"
        />
        <circle
          className="turn-timer__progress"
          cx="24"
          cy="24"
          r={RADIUS}
          fill="none"
          strokeWidth="3"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 24 24)"
        />
      </svg>
      <span className="turn-timer__text">{secondsRemaining}</span>
    </div>
  );
}
