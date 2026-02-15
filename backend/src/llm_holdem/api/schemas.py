"""API request and response schemas."""

from pydantic import BaseModel, Field

# ─── Agent Schemas ────────────────────────────────────


class AgentSummary(BaseModel):
    """Summary of an agent for listing."""

    id: str
    name: str
    avatar_url: str = ""
    provider: str = ""
    model: str = ""
    backstory: str = ""


class AgentListResponse(BaseModel):
    """Response for listing available agents."""

    agents: list[AgentSummary] = Field(default_factory=list)


# ─── Game Schemas ─────────────────────────────────────


class CreateGameRequest(BaseModel):
    """Request to create a new game."""

    mode: str = Field(default="player", description="Game mode: 'player' or 'spectator'")
    agent_ids: list[str] = Field(
        default_factory=list,
        description="Agent IDs to include in the game",
    )
    starting_chips: int = Field(default=1000, ge=100, description="Starting chip count")
    num_players: int = Field(default=6, ge=2, le=8, description="Number of players")


class GameSummary(BaseModel):
    """Summary of a game for listing."""

    id: int
    game_uuid: str
    mode: str
    status: str
    created_at: str
    finished_at: str | None = None
    winner_seat: int | None = None
    total_hands: int | None = None
    player_count: int = 0


class GameDetail(BaseModel):
    """Full detail of a game."""

    id: int
    game_uuid: str
    mode: str
    status: str
    created_at: str
    finished_at: str | None = None
    winner_seat: int | None = None
    total_hands: int | None = None
    config_json: str = "{}"
    players: list["GamePlayerSummary"] = Field(default_factory=list)


class GamePlayerSummary(BaseModel):
    """Summary of a player in a game."""

    seat_index: int
    name: str
    agent_id: str | None = None
    avatar_url: str = ""
    starting_chips: int = 0
    final_chips: int | None = None
    finish_position: int | None = None
    is_human: bool = False


class CreateGameResponse(BaseModel):
    """Response after creating a game."""

    game_uuid: str
    game_id: int


# ─── Hand Schemas ─────────────────────────────────────


class HandSummary(BaseModel):
    """Summary of a hand."""

    id: int
    hand_number: int
    dealer_position: int
    small_blind: int
    big_blind: int
    phase: str = ""
    community_cards_json: str = "[]"
    pots_json: str = "[]"
    winners_json: str = "[]"


class HandDetail(BaseModel):
    """Full detail of a hand including actions."""

    id: int
    hand_number: int
    dealer_position: int
    small_blind: int
    big_blind: int
    phase: str = ""
    community_cards_json: str = "[]"
    pots_json: str = "[]"
    winners_json: str = "[]"
    showdown_json: str | None = None
    actions: list["ActionSummary"] = Field(default_factory=list)


class ActionSummary(BaseModel):
    """Summary of a hand action."""

    seat_index: int
    action_type: str
    amount: int | None = None
    phase: str = ""
    sequence: int = 0
    timestamp: str = ""


# ─── Cost Schemas ─────────────────────────────────────


class CostSummaryResponse(BaseModel):
    """Summarized cost data."""

    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    call_count: int = 0


class CostRecordSummary(BaseModel):
    """A single cost record."""

    id: int
    game_id: int
    agent_id: str
    call_type: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    timestamp: str = ""


class CostListResponse(BaseModel):
    """Response for cost data including summary and records."""

    summary: CostSummaryResponse
    records: list[CostRecordSummary] = Field(default_factory=list)


# ─── Game Stats Schemas ───────────────────────────────


class GameStatsResponse(BaseModel):
    """Rich game statistics for post-game summary."""

    total_hands: int = 0
    biggest_pot: int = 0
    biggest_pot_hand: int = 0
    best_hand_name: str = ""
    best_hand_player: str = ""
    best_hand_number: int = 0
    most_aggressive_name: str = ""
    most_aggressive_raises: int = 0
    most_hands_won_name: str = ""
    most_hands_won_count: int = 0


# ─── Chat Schemas ─────────────────────────────────────


class ChatMessageResponse(BaseModel):
    """A chat message record for game review."""

    seat_index: int
    name: str = ""
    message: str = ""
    hand_number: int | None = None
    timestamp: str = ""
    trigger_event: str = ""


# ─── Provider Schemas ─────────────────────────────────


class ProvidersResponse(BaseModel):
    """Response for available providers."""

    providers: list[str] = Field(default_factory=list)
