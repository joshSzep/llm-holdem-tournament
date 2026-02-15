"""REST API routes."""

import logging
import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.api.schemas import ActionSummary
from llm_holdem.api.schemas import AgentListResponse
from llm_holdem.api.schemas import AgentSummary
from llm_holdem.api.schemas import CostListResponse
from llm_holdem.api.schemas import CostRecordSummary
from llm_holdem.api.schemas import CostSummaryResponse
from llm_holdem.api.schemas import CreateGameRequest
from llm_holdem.api.schemas import CreateGameResponse
from llm_holdem.api.schemas import GameDetail
from llm_holdem.api.schemas import GamePlayerSummary
from llm_holdem.api.schemas import GameSummary
from llm_holdem.api.schemas import HandDetail
from llm_holdem.api.schemas import HandSummary
from llm_holdem.db.repository import create_game
from llm_holdem.db.repository import create_game_player
from llm_holdem.db.repository import get_actions_for_hand
from llm_holdem.db.repository import get_cost_records
from llm_holdem.db.repository import get_cost_summary
from llm_holdem.db.repository import get_game_by_id
from llm_holdem.db.repository import get_game_players
from llm_holdem.db.repository import get_hand_by_number
from llm_holdem.db.repository import get_hands_for_game
from llm_holdem.db.repository import list_games
from llm_holdem.main import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


# ─── Stub Agent Data ──────────────────────────────────

_STUB_AGENTS: list[AgentSummary] = [
    AgentSummary(
        id="agent-tight-tony",
        name="Tight Tony",
        avatar_url="/avatars/tight-tony.png",
        provider="openai",
        model="gpt-4o",
        backstory="A conservative player who only plays premium hands.",
    ),
    AgentSummary(
        id="agent-bluff-betty",
        name="Bluff Betty",
        avatar_url="/avatars/bluff-betty.png",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        backstory="Lives for the bluff. Will bet big with nothing.",
    ),
    AgentSummary(
        id="agent-math-mike",
        name="Math Mike",
        avatar_url="/avatars/math-mike.png",
        provider="google",
        model="gemini-2.0-flash",
        backstory="Plays by the numbers. Calculates pot odds in milliseconds.",
    ),
]


# ─── Agent Routes ─────────────────────────────────────


@router.get("/agents", response_model=AgentListResponse)
async def list_agents() -> AgentListResponse:
    """List available agents (stub data for now)."""
    return AgentListResponse(agents=_STUB_AGENTS)


@router.get("/agents/{agent_id}", response_model=AgentSummary)
async def get_agent(agent_id: str) -> AgentSummary:
    """Get agent profile details."""
    for agent in _STUB_AGENTS:
        if agent.id == agent_id:
            return agent
    raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")


# ─── Game Routes ──────────────────────────────────────


@router.get("/games", response_model=list[GameSummary])
async def list_all_games(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[GameSummary]:
    """List all games, optionally filtered by status."""
    games = await list_games(session, status=status)
    result: list[GameSummary] = []
    for g in games:
        players = await get_game_players(session, g.id)
        result.append(GameSummary(
            id=g.id,
            game_uuid=g.game_uuid,
            mode=g.mode,
            status=g.status,
            created_at=g.created_at,
            finished_at=g.finished_at,
            winner_seat=g.winner_seat,
            total_hands=g.total_hands,
            player_count=len(players),
        ))
    return result


@router.get("/games/{game_id}", response_model=GameDetail)
async def get_game(
    game_id: int,
    session: AsyncSession = Depends(get_session),
) -> GameDetail:
    """Get game details with player information."""
    game = await get_game_by_id(session, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    db_players = await get_game_players(session, game.id)
    players = [
        GamePlayerSummary(
            seat_index=p.seat_index,
            name=p.name,
            agent_id=p.agent_id,
            avatar_url=p.avatar_url,
            starting_chips=p.starting_chips,
            final_chips=p.final_chips,
            finish_position=p.finish_position,
            is_human=p.agent_id is None,
        )
        for p in db_players
    ]

    return GameDetail(
        id=game.id,
        game_uuid=game.game_uuid,
        mode=game.mode,
        status=game.status,
        created_at=game.created_at,
        finished_at=game.finished_at,
        winner_seat=game.winner_seat,
        total_hands=game.total_hands,
        config_json=game.config_json,
        players=players,
    )


@router.post("/games", response_model=CreateGameResponse, status_code=201)
async def create_new_game(
    request: CreateGameRequest,
    session: AsyncSession = Depends(get_session),
) -> CreateGameResponse:
    """Create a new game."""
    game_uuid = str(uuid.uuid4())

    game = await create_game(
        session,
        game_uuid=game_uuid,
        mode=request.mode,
        config={
            "starting_chips": request.starting_chips,
            "num_players": request.num_players,
            "agent_ids": request.agent_ids,
        },
    )

    # Create human player at seat 0 (if player mode)
    if request.mode == "player":
        await create_game_player(
            session,
            game_id=game.id,
            seat_index=0,
            name="You",
            starting_chips=request.starting_chips,
            agent_id=None,
        )

    # Create AI players
    for i, agent_id in enumerate(request.agent_ids):
        seat = i + 1 if request.mode == "player" else i
        # Find agent name from stubs
        agent_name = agent_id
        for stub in _STUB_AGENTS:
            if stub.id == agent_id:
                agent_name = stub.name
                break

        await create_game_player(
            session,
            game_id=game.id,
            seat_index=seat,
            name=agent_name,
            starting_chips=request.starting_chips,
            agent_id=agent_id,
        )

    logger.info("Created game %s with %d players", game_uuid, request.num_players)
    return CreateGameResponse(game_uuid=game_uuid, game_id=game.id)


# ─── Hand History Routes ─────────────────────────────


@router.get("/games/{game_id}/hands", response_model=list[HandSummary])
async def get_game_hands(
    game_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[HandSummary]:
    """Get hand history for a game."""
    game = await get_game_by_id(session, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    hands = await get_hands_for_game(session, game.id)
    return [
        HandSummary(
            id=h.id,
            hand_number=h.hand_number,
            dealer_position=h.dealer_position,
            small_blind=h.small_blind,
            big_blind=h.big_blind,
            phase=h.phase or "",
            community_cards_json=h.community_cards_json or "[]",
            pots_json=h.pots_json or "[]",
            winners_json=h.winners_json or "[]",
        )
        for h in hands
    ]


@router.get("/games/{game_id}/hands/{hand_num}", response_model=HandDetail)
async def get_game_hand(
    game_id: int,
    hand_num: int,
    session: AsyncSession = Depends(get_session),
) -> HandDetail:
    """Get specific hand with actions."""
    game = await get_game_by_id(session, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    hand = await get_hand_by_number(session, game.id, hand_num)
    if hand is None:
        raise HTTPException(status_code=404, detail="Hand not found")

    actions = await get_actions_for_hand(session, hand.id)
    return HandDetail(
        id=hand.id,
        hand_number=hand.hand_number,
        dealer_position=hand.dealer_position,
        small_blind=hand.small_blind,
        big_blind=hand.big_blind,
        phase=hand.phase or "",
        community_cards_json=hand.community_cards_json or "[]",
        pots_json=hand.pots_json or "[]",
        winners_json=hand.winners_json or "[]",
        showdown_json=hand.showdown_json,
        actions=[
            ActionSummary(
                seat_index=a.seat_index,
                action_type=a.action_type,
                amount=a.amount,
                phase=a.phase,
                sequence=a.sequence,
                timestamp=a.timestamp,
            )
            for a in actions
        ],
    )


# ─── Cost Routes ─────────────────────────────────────


@router.get("/costs", response_model=CostListResponse)
async def get_costs(
    game_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> CostListResponse:
    """Get cost tracking data with summary."""
    summary = await get_cost_summary(session)
    records = await get_cost_records(session, game_id=game_id)

    return CostListResponse(
        summary=CostSummaryResponse(**summary),
        records=[
            CostRecordSummary(
                id=r.id,
                game_id=r.game_id,
                agent_id=r.agent_id,
                call_type=r.call_type,
                model=r.model,
                input_tokens=r.input_tokens,
                output_tokens=r.output_tokens,
                estimated_cost=r.estimated_cost,
                timestamp=r.timestamp,
            )
            for r in records
        ],
    )
