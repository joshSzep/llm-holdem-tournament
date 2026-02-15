/**
 * Game state types — mirrors backend Pydantic models (state.py).
 * The backend is the single source of truth; these types are for display only.
 */

export type Rank =
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "7"
  | "8"
  | "9"
  | "T"
  | "J"
  | "Q"
  | "K"
  | "A";
export type Suit = "h" | "d" | "c" | "s";
export type GameMode = "player" | "spectator";
export type GameStatus = "waiting" | "active" | "paused" | "completed";
export type GamePhase =
  | "pre_flop"
  | "flop"
  | "turn"
  | "river"
  | "showdown"
  | "between_hands";
export type ActionType = "fold" | "check" | "call" | "raise" | "post_blind";

export interface Card {
  rank: Rank;
  suit: Suit;
}

export interface Pot {
  amount: number;
  eligible_players: number[];
}

export interface Action {
  player_index: number;
  action_type: ActionType;
  amount: number | null;
  timestamp: string;
}

export interface PlayerState {
  seat_index: number;
  agent_id: string | null;
  name: string;
  avatar_url: string;
  chips: number;
  hole_cards: Card[] | null;
  is_folded: boolean;
  is_eliminated: boolean;
  is_all_in: boolean;
  current_bet: number;
  is_dealer: boolean;
  has_acted: boolean;
}

export interface HandResult {
  player_index: number;
  hand_rank: number;
  hand_name: string;
  hand_description: string;
}

export interface ShowdownResult {
  winners: number[];
  hand_results: HandResult[];
  pot_distributions: Record<string, number | number[]>[];
}

export interface GameState {
  game_id: string;
  mode: GameMode;
  status: GameStatus;
  players: PlayerState[];
  dealer_position: number;
  small_blind: number;
  big_blind: number;
  hand_number: number;
  community_cards: Card[];
  pots: Pot[];
  current_bet: number;
  current_player_index: number | null;
  phase: GamePhase;
  current_hand_actions: Action[];
  showdown_result: ShowdownResult | null;
  total_hands_played: number;
  eliminated_players: number[];
}
