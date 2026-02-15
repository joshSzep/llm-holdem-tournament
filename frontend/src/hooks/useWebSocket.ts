/**
 * useWebSocket hook — manages WebSocket connection lifecycle
 * and dispatches incoming messages to Zustand stores.
 */

import { useEffect, useRef } from "react";

import { useChatStore } from "../stores/chatStore";
import { useGameStore } from "../stores/gameStore";
import { wsService } from "../services/websocket";
import type { ServerMessage } from "../types/messages";

/**
 * Connect to the game WebSocket and route messages to stores.
 * Automatically connects on mount and disconnects on unmount.
 */
export function useWebSocket(gameId: number | null): {
  isConnected: boolean;
  send: typeof wsService.send;
} {
  const isConnected = useGameStore((s) => s.isConnected);
  const setConnected = useGameStore((s) => s.setConnected);
  const setGameState = useGameStore((s) => s.setGameState);
  const setGameOver = useGameStore((s) => s.setGameOver);
  const setTimer = useGameStore((s) => s.setTimer);
  const setPaused = useGameStore((s) => s.setPaused);
  const setError = useGameStore((s) => s.setError);

  const addMessage = useChatStore((s) => s.addMessage);

  const gameIdRef = useRef(gameId);
  gameIdRef.current = gameId;

  useEffect(() => {
    if (gameId === null) return;

    const handleMessage = (message: ServerMessage): void => {
      switch (message.type) {
        case "game_state":
          setGameState(message.state);
          break;
        case "chat_message":
          addMessage({
            id: `${Date.now()}-${message.seat_index}`,
            seat_index: message.seat_index,
            name: message.name,
            message: message.message,
            timestamp: message.timestamp,
            isSystem: false,
          });
          break;
        case "timer_update":
          setTimer(message.seat_index, message.seconds_remaining);
          break;
        case "game_over":
          setGameOver({
            winner_seat: message.winner_seat,
            winner_name: message.winner_name,
            final_standings: message.final_standings,
          });
          break;
        case "error":
          setError(message.message);
          break;
        case "game_paused":
          setPaused(true, message.reason);
          break;
        case "game_resumed":
          setPaused(false);
          break;
      }
    };

    const handleConnection = (connected: boolean): void => {
      setConnected(connected);
    };

    const unsubMessage = wsService.onMessage(handleMessage);
    const unsubConnection = wsService.onConnectionChange(handleConnection);

    wsService.connect(gameId);

    return () => {
      unsubMessage();
      unsubConnection();
      wsService.disconnect();
    };
  }, [
    gameId,
    setConnected,
    setGameState,
    setGameOver,
    setTimer,
    setPaused,
    setError,
    addMessage,
  ]);

  return {
    isConnected,
    send: wsService.send.bind(wsService),
  };
}
