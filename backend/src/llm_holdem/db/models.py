"""SQLModel table definitions for persistence."""

from datetime import datetime
from datetime import timezone
from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel


class Game(SQLModel, table=True):
    """A poker game/tournament session."""

    id: Optional[int] = Field(default=None, primary_key=True)
    game_uuid: str = Field(index=True, unique=True)
    mode: str = Field(default="player")  # "player" | "spectator"
    status: str = Field(default="waiting")  # "waiting" | "active" | "paused" | "completed"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: Optional[str] = None
    winner_seat: Optional[int] = None
    total_hands: int = 0
    config_json: str = Field(default="{}")  # JSON blob for game config


class GamePlayer(SQLModel, table=True):
    """A player in a game (human or AI agent)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    seat_index: int
    agent_id: Optional[str] = None  # None for human player
    name: str = ""
    avatar_url: str = ""
    starting_chips: int = 1000
    final_chips: Optional[int] = None
    finish_position: Optional[int] = None
    elimination_hand: Optional[int] = None


class Hand(SQLModel, table=True):
    """A single hand played in a game."""

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    hand_number: int
    dealer_position: int = 0
    small_blind: int = 10
    big_blind: int = 20
    community_cards_json: str = Field(default="[]")  # JSON list of card strings
    pots_json: str = Field(default="[]")  # JSON list of pot objects
    winners_json: str = Field(default="[]")  # JSON list of winner seat indices
    showdown_json: Optional[str] = None  # JSON showdown result
    phase: str = "between_hands"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HandAction(SQLModel, table=True):
    """A single action within a hand."""

    id: Optional[int] = Field(default=None, primary_key=True)
    hand_id: int = Field(foreign_key="hand.id", index=True)
    seat_index: int
    action_type: str  # "fold" | "check" | "call" | "raise" | "post_blind"
    amount: Optional[int] = None
    phase: str = ""  # Game phase when action occurred
    sequence: int = 0  # Order within the hand
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatMessage(SQLModel, table=True):
    """A chat message during a game."""

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    hand_number: Optional[int] = None
    seat_index: int
    name: str = ""
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    trigger_event: str = ""  # What triggered this message


class CostRecord(SQLModel, table=True):
    """API cost tracking for LLM calls."""

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(foreign_key="game.id", index=True)
    agent_id: str = ""
    call_type: str = ""  # "action" | "chat"
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
