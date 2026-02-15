/**
 * useGameActions hook — helpers for sending player actions.
 */

import { useCallback } from "react";

import type { ClientMessage } from "../types/messages";

interface UseGameActionsReturn {
  fold: () => void;
  check: () => void;
  call: () => void;
  raise: (amount: number) => void;
  sendChat: (message: string) => void;
}

/**
 * Provides action helpers that send messages via the WebSocket.
 */
export function useGameActions(
  send: (msg: ClientMessage) => void,
): UseGameActionsReturn {
  const fold = useCallback(() => {
    send({ type: "player_action", action_type: "fold" });
  }, [send]);

  const check = useCallback(() => {
    send({ type: "player_action", action_type: "check" });
  }, [send]);

  const call = useCallback(() => {
    send({ type: "player_action", action_type: "call" });
  }, [send]);

  const raise = useCallback(
    (amount: number) => {
      send({ type: "player_action", action_type: "raise", amount });
    },
    [send],
  );

  const sendChat = useCallback(
    (message: string) => {
      send({ type: "chat_message", message });
    },
    [send],
  );

  return { fold, check, call, raise, sendChat };
}
