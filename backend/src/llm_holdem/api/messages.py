"""WebSocket message types for client-server communication."""

from typing import Literal

from pydantic import BaseModel, Field

from llm_holdem.game.state import GameState

# ─── Server → Client Messages ────────────────────────


class GameStateMessage(BaseModel):
    """Full game state broadcast."""

    type: Literal["game_state"] = "game_state"
    state: GameState


class ChatMessageOut(BaseModel):
    """Chat message from AI or system."""

    type: Literal["chat_message"] = "chat_message"
    seat_index: int
    name: str
    message: str
    timestamp: str = ""


class TimerUpdateMessage(BaseModel):
    """Turn timer tick."""

    type: Literal["timer_update"] = "timer_update"
    seat_index: int
    seconds_remaining: int


class GameOverMessage(BaseModel):
    """Tournament ended."""

    type: Literal["game_over"] = "game_over"
    winner_seat: int
    winner_name: str
    final_standings: list[dict] = Field(default_factory=list)


class ErrorMessage(BaseModel):
    """Error notification."""

    type: Literal["error"] = "error"
    message: str
    code: str = ""


class GamePausedMessage(BaseModel):
    """Game paused notification."""

    type: Literal["game_paused"] = "game_paused"
    reason: str = ""


class GameResumedMessage(BaseModel):
    """Game resumed notification."""

    type: Literal["game_resumed"] = "game_resumed"


# ─── Client → Server Messages ────────────────────────


class PlayerActionMessage(BaseModel):
    """Human player's game action."""

    type: Literal["player_action"] = "player_action"
    action_type: Literal["fold", "check", "call", "raise"]
    amount: int | None = None


class ChatMessageIn(BaseModel):
    """Human player's chat message."""

    type: Literal["chat_message"] = "chat_message"
    message: str


class PauseGameMessage(BaseModel):
    """Request to pause the game."""

    type: Literal["pause_game"] = "pause_game"


# ─── Union types for parsing ─────────────────────────

ServerMessage = (
    GameStateMessage
    | ChatMessageOut
    | TimerUpdateMessage
    | GameOverMessage
    | ErrorMessage
    | GamePausedMessage
    | GameResumedMessage
)

ClientMessage = PlayerActionMessage | ChatMessageIn | PauseGameMessage
