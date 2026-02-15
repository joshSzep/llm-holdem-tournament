/**
 * REST API types — mirrors backend API schemas.
 */

import type { AgentProfile } from "./agents";

// ─── Game Types ──────────────────────────────────────

export interface CreateGameRequest {
  mode: "player" | "spectator";
  agent_ids: string[];
  starting_chips: number;
  num_players: number;
}

export interface CreateGameResponse {
  game_uuid: string;
  game_id: number;
}

export interface GameSummary {
  id: number;
  game_uuid: string;
  mode: string;
  status: string;
  created_at: string;
  finished_at: string | null;
  winner_seat: number | null;
  total_hands: number | null;
  player_count: number;
}

export interface GamePlayerSummary {
  seat_index: number;
  name: string;
  agent_id: string | null;
  avatar_url: string;
  starting_chips: number;
  final_chips: number | null;
  finish_position: number | null;
  is_human: boolean;
}

export interface GameDetail {
  id: number;
  game_uuid: string;
  mode: string;
  status: string;
  created_at: string;
  finished_at: string | null;
  winner_seat: number | null;
  total_hands: number | null;
  config_json: string;
  players: GamePlayerSummary[];
}

// ─── Hand Types ──────────────────────────────────────

export interface HandSummary {
  id: number;
  hand_number: number;
  dealer_position: number;
  small_blind: number;
  big_blind: number;
  phase: string;
  community_cards_json: string;
  pots_json: string;
  winners_json: string;
}

export interface ActionSummary {
  seat_index: number;
  action_type: string;
  amount: number | null;
  phase: string;
  sequence: number;
  timestamp: string;
}

export interface HandDetail extends HandSummary {
  showdown_json: string | null;
  actions: ActionSummary[];
}

// ─── Cost Types ──────────────────────────────────────

export interface CostSummary {
  total_cost: number;
  total_input_tokens: number;
  total_output_tokens: number;
  call_count: number;
}

export interface CostRecord {
  id: number;
  game_id: number;
  agent_id: string;
  call_type: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  timestamp: string;
}

export interface CostListResponse {
  summary: CostSummary;
  records: CostRecord[];
}

// ─── Game Stats Types ────────────────────────────────

export interface GameStatsResponse {
  total_hands: number;
  biggest_pot: number;
  biggest_pot_hand: number;
  best_hand_name: string;
  best_hand_player: string;
  best_hand_number: number;
  most_aggressive_name: string;
  most_aggressive_raises: number;
  most_hands_won_name: string;
  most_hands_won_count: number;
}

// ─── Chat Types ──────────────────────────────────────

export interface ChatMessageRecord {
  seat_index: number;
  name: string;
  message: string;
  hand_number: number | null;
  timestamp: string;
  trigger_event: string;
}

// ─── Provider Types ──────────────────────────────────

export interface ProvidersResponse {
  providers: string[];
}

// ─── Re-exports ──────────────────────────────────────

export type { AgentProfile };
