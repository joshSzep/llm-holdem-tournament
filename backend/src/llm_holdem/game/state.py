"""Game state models — the single source of truth for all game data."""

from typing import Literal

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
# Card Primitives
# ──────────────────────────────────────────────

Rank = Literal["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
Suit = Literal["h", "d", "c", "s"]

RANKS: list[Rank] = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
SUITS: list[Suit] = ["h", "d", "c", "s"]

RANK_NAMES: dict[str, str] = {
    "2": "Two",
    "3": "Three",
    "4": "Four",
    "5": "Five",
    "6": "Six",
    "7": "Seven",
    "8": "Eight",
    "9": "Nine",
    "T": "Ten",
    "J": "Jack",
    "Q": "Queen",
    "K": "King",
    "A": "Ace",
}

SUIT_NAMES: dict[str, str] = {
    "h": "Hearts",
    "d": "Diamonds",
    "c": "Clubs",
    "s": "Spades",
}


class Card(BaseModel):
    """A single playing card."""

    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return f"Card(rank='{self.rank}', suit='{self.suit}')"

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    @property
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Ace of Spades'."""
        return f"{RANK_NAMES[self.rank]} of {SUIT_NAMES[self.suit]}"


# ──────────────────────────────────────────────
# Game State Models
# ──────────────────────────────────────────────

GameMode = Literal["player", "spectator"]
GameStatus = Literal["waiting", "active", "paused", "completed"]
GamePhase = Literal["pre_flop", "flop", "turn", "river", "showdown", "between_hands"]
ActionType = Literal["fold", "check", "call", "raise", "post_blind"]


class Pot(BaseModel):
    """A pot (main or side) with the amount and eligible players."""

    amount: int = Field(ge=0)
    eligible_players: list[int] = Field(
        default_factory=list,
        description="Seat indices of players eligible for this pot",
    )


class Action(BaseModel):
    """A single game action taken by a player."""

    player_index: int
    action_type: ActionType
    amount: int | None = None
    timestamp: str = ""


class PlayerState(BaseModel):
    """The state of a single player at the table."""

    seat_index: int
    agent_id: str | None = None  # None for human player
    name: str = ""
    avatar_url: str = ""
    chips: int = 0
    hole_cards: list[Card] | None = None  # None if hidden from viewer
    is_folded: bool = False
    is_eliminated: bool = False
    is_all_in: bool = False
    current_bet: int = 0
    is_dealer: bool = False
    has_acted: bool = False


class HandResult(BaseModel):
    """Result of hand evaluation for a single player."""

    player_index: int
    hand_rank: int  # Numerical rank (lower is better in treys)
    hand_name: str  # e.g., "Full House, Kings full of Sevens"
    hand_description: str = ""  # Additional detail


class ShowdownResult(BaseModel):
    """Complete showdown results for a hand."""

    winners: list[int]  # Seat indices of winners
    hand_results: list[HandResult] = Field(default_factory=list)
    pot_distributions: list[dict[str, int | list[int]]] = Field(default_factory=list)


class GameState(BaseModel):
    """Complete game state — the single source of truth sent to the frontend."""

    game_id: str = ""
    mode: GameMode = "player"
    status: GameStatus = "waiting"

    # Table
    players: list[PlayerState] = Field(default_factory=list)
    dealer_position: int = 0
    small_blind: int = 10
    big_blind: int = 20
    hand_number: int = 0

    # Current Hand
    community_cards: list[Card] = Field(default_factory=list)
    pots: list[Pot] = Field(default_factory=list)
    current_bet: int = 0
    current_player_index: int | None = None
    phase: GamePhase = "between_hands"

    # History for current hand
    current_hand_actions: list[Action] = Field(default_factory=list)

    # Showdown
    showdown_result: ShowdownResult | None = None

    # Tournament
    total_hands_played: int = 0
    eliminated_players: list[int] = Field(default_factory=list)
