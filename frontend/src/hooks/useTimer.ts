/**
 * useTimer hook — tracks the turn timer synchronized with server updates.
 */

import { useEffect, useRef, useState } from "react";

import { useGameStore } from "../stores/gameStore";

interface TimerState {
  seatIndex: number | null;
  secondsRemaining: number;
  isActive: boolean;
  isUrgent: boolean;
}

const URGENT_THRESHOLD = 10;

/**
 * Returns a locally-ticking timer state synchronized with server timer updates.
 */
export function useTimer(): TimerState {
  const serverTimer = useGameStore((s) => s.timer);
  const [localSeconds, setLocalSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sync with server timer updates
  useEffect(() => {
    if (serverTimer) {
      setLocalSeconds(serverTimer.seconds_remaining);
    } else {
      setLocalSeconds(0);
    }
  }, [serverTimer]);

  // Local countdown between server ticks
  useEffect(() => {
    if (!serverTimer || localSeconds <= 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      setLocalSeconds((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [serverTimer, localSeconds]);

  return {
    seatIndex: serverTimer?.seat_index ?? null,
    secondsRemaining: localSeconds,
    isActive: serverTimer !== null && localSeconds > 0,
    isUrgent: localSeconds > 0 && localSeconds <= URGENT_THRESHOLD,
  };
}
