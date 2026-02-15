/**
 * WebSocket message types — mirrors backend messages.py.
 * Discriminated union on the `type` field.
 */

import type { GameState } from "./game";

// ─── Server → Client Messages ────────────────────────

export interface GameStateMessage {
  type: "game_state";
  state: GameState;
}

export interface ChatMessageData {
  type: "chat_message";
  seat_index: number;
  name: string;
  message: string;
  timestamp: string;
}

export interface TimerUpdateMessage {
  type: "timer_update";
  seat_index: number;
  seconds_remaining: number;
}

export interface GameOverData {
  winner_seat: number;
  winner_name: string;
  final_standings: FinalStanding[];
}

export interface GameOverMessage {
  type: "game_over";
  winner_seat: number;
  winner_name: string;
  final_standings: FinalStanding[];
}

export interface FinalStanding {
  seat_index: number;
  name: string;
  finish_position: number;
  final_chips: number;
}

export interface ErrorMessage {
  type: "error";
  message: string;
  code: string;
}

export interface GamePausedMessage {
  type: "game_paused";
  reason: string;
}

export interface GameResumedMessage {
  type: "game_resumed";
}

export type ServerMessage =
  | GameStateMessage
  | ChatMessageData
  | TimerUpdateMessage
  | GameOverMessage
  | ErrorMessage
  | GamePausedMessage
  | GameResumedMessage;

// ─── Client → Server Messages ────────────────────────

export interface PlayerActionMessage {
  type: "player_action";
  action_type: "fold" | "check" | "call" | "raise";
  amount?: number;
}

export interface ChatMessageOut {
  type: "chat_message";
  message: string;
}

export type ClientMessage = PlayerActionMessage | ChatMessageOut;
