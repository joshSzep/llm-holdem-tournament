"""Tests for the game coordinator."""

import asyncio

import pytest
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from llm_holdem.api.messages import PlayerActionMessage
from llm_holdem.api.websocket_handler import ConnectionManager
from llm_holdem.db.persistence import save_new_game
from llm_holdem.db.repository import get_game_by_id
from llm_holdem.db.repository import get_game_players
from llm_holdem.db.repository import get_hands_for_game
from llm_holdem.db.repository import update_game_status
from llm_holdem.game.coordinator import GameCoordinator
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState


def _make_players(n: int = 4, chips: int = 1000) -> list[PlayerState]:
    """Create test players. Player 0 is human, rest are AI."""
    return [
        PlayerState(
            seat_index=i,
            name=f"Player {i}",
            chips=chips,
            agent_id=f"agent-{i}" if i > 0 else None,
        )
        for i in range(n)
    ]


def _make_all_ai_players(n: int = 2, chips: int = 1000) -> list[PlayerState]:
    """Create all-AI players for fast tests."""
    return [
        PlayerState(
            seat_index=i,
            name=f"AI {i}",
            chips=chips,
            agent_id=f"agent-{i}",
        )
        for i in range(n)
    ]


@pytest.fixture
async def db_engine():
    """Create an in-memory async engine with tables."""
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(db_engine):
    """Create an async session for testing."""
    async with AsyncSession(db_engine, expire_on_commit=False) as sess:
        yield sess


class TestCoordinatorInit:
    """Tests for coordinator initialization."""

    async def test_create_coordinator(self, session: AsyncSession) -> None:
        players = _make_players(2)
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(engine, game_db_id, mgr)
        assert coordinator.engine is engine
        assert coordinator.game_db_id == game_db_id
        assert not coordinator.is_paused


class TestCoordinatorPause:
    """Tests for pause/resume functionality."""

    async def test_pause_and_resume(self, session: AsyncSession) -> None:
        players = _make_players(2)
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(engine, game_db_id, mgr)
        assert not coordinator.is_paused

        coordinator.pause()
        assert coordinator.is_paused

        coordinator.resume()
        assert not coordinator.is_paused


class TestCoordinatorReceiveAction:
    """Tests for receiving player actions."""

    async def test_receive_action_sets_future(self, session: AsyncSession) -> None:
        players = _make_players(2)
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(engine, game_db_id, mgr)

        # Create a pending action future
        loop = asyncio.get_event_loop()
        coordinator._pending_action = loop.create_future()

        action = PlayerActionMessage(action_type="fold")
        coordinator.receive_player_action(action)

        result = await coordinator._pending_action
        assert result is not None
        assert result.action_type == "fold"

    async def test_receive_action_no_pending(self, session: AsyncSession) -> None:
        players = _make_players(2)
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(engine, game_db_id, mgr)

        # No pending future — should not raise
        action = PlayerActionMessage(action_type="call")
        coordinator.receive_player_action(action)


class TestCoordinatorAIGame:
    """Integration tests with all-AI players."""

    async def test_ai_only_game_completes(self, session: AsyncSession) -> None:
        """Test that an all-AI game runs to completion."""
        # Use very unequal stacks to ensure game ends quickly
        players = [
            PlayerState(seat_index=0, name="AI-0", chips=100, agent_id="agent-0"),
            PlayerState(seat_index=1, name="AI-1", chips=900, agent_id="agent-1"),
        ]
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(
            engine, game_db_id, mgr, timer_seconds=1, ai_delay=0,
        )

        # Run with timeout to prevent infinite loops
        try:
            await asyncio.wait_for(
                coordinator.run_game(session),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Game did not complete within timeout")

        # Verify game completed
        game = await get_game_by_id(session, game_db_id)
        assert game is not None
        assert game.status == "completed"

        # Verify hands were saved
        hands = await get_hands_for_game(session, game_db_id)
        assert len(hands) >= 1

    async def test_ai_game_saves_player_chips(self, session: AsyncSession) -> None:
        """Test that player chips are updated after each hand."""
        players = _make_all_ai_players(2, chips=200)
        engine = GameEngine(players, seed=123)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(
            engine, game_db_id, mgr, timer_seconds=1, ai_delay=0,
        )

        try:
            await asyncio.wait_for(
                coordinator.run_game(session),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Game did not complete within timeout")

        # Check that final chip counts are in DB
        db_players = await get_game_players(session, game_db_id)
        total_chips = sum(p.final_chips or 0 for p in db_players)
        # Total chips should be preserved (zero-sum game)
        assert total_chips == 400  # 200 * 2

    async def test_hand_is_over_detection(self, session: AsyncSession) -> None:
        """Test _hand_is_over helper."""
        players = _make_all_ai_players(3, chips=500)
        engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, engine)
        mgr = ConnectionManager()

        coordinator = GameCoordinator(engine, game_db_id, mgr)

        # Before any hand, no one is folded
        assert not coordinator._hand_is_over()

        # Fold all but one
        engine.players[0].is_folded = True
        engine.players[1].is_folded = True
        assert coordinator._hand_is_over()
