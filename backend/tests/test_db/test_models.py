"""Tests for database models and connection management."""

import pytest

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.models import ChatMessage
from llm_holdem.db.models import CostRecord
from llm_holdem.db.models import Game
from llm_holdem.db.models import GamePlayer
from llm_holdem.db.models import Hand
from llm_holdem.db.models import HandAction


@pytest.fixture()
async def engine() -> AsyncEngine:
    """Create an in-memory async engine for testing."""
    import llm_holdem.db.models  # noqa: F401

    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng  # type: ignore[misc]
    await eng.dispose()


@pytest.fixture()
async def session(engine: AsyncEngine) -> AsyncSession:
    """Create an async session for testing."""
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess  # type: ignore[misc]


class TestDatabaseInit:
    """Tests for database initialization."""

    async def test_engine_created(self, engine: AsyncEngine) -> None:
        """Engine should be created successfully."""
        assert engine is not None

    async def test_session_works(self, session: AsyncSession) -> None:
        """Session should be usable."""
        assert isinstance(session, AsyncSession)

    async def test_tables_exist(self, session: AsyncSession) -> None:
        """All tables should exist after init."""
        result = await session.exec(select(Game))
        assert result is not None


class TestGameModel:
    """Tests for the Game table model."""

    async def test_create_game(self, session: AsyncSession) -> None:
        """Should create a game record."""
        game = Game(game_uuid="test-uuid-1", mode="player", status="waiting")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        assert game.id is not None
        assert game.game_uuid == "test-uuid-1"
        assert game.mode == "player"
        assert game.status == "waiting"
        assert game.created_at != ""

    async def test_game_defaults(self) -> None:
        """Game should have sensible defaults."""
        game = Game(game_uuid="test-uuid-2")
        assert game.mode == "player"
        assert game.status == "waiting"
        assert game.total_hands == 0
        assert game.winner_seat is None
        assert game.finished_at is None

    async def test_query_game(self, session: AsyncSession) -> None:
        """Should be able to query games."""
        game = Game(game_uuid="query-test", mode="spectator", status="active")
        session.add(game)
        await session.commit()

        result = await session.exec(select(Game).where(Game.game_uuid == "query-test"))
        found = result.first()
        assert found is not None
        assert found.mode == "spectator"


class TestGamePlayerModel:
    """Tests for the GamePlayer table model."""

    async def test_create_game_player(self, session: AsyncSession) -> None:
        """Should create a game player record."""
        game = Game(game_uuid="player-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        player = GamePlayer(
            game_id=game.id,  # type: ignore[arg-type]
            seat_index=0,
            agent_id="agent-1",
            name="Test Agent",
            starting_chips=1000,
        )
        session.add(player)
        await session.commit()
        await session.refresh(player)

        assert player.id is not None
        assert player.game_id == game.id
        assert player.seat_index == 0
        assert player.agent_id == "agent-1"

    async def test_human_player_no_agent_id(self, session: AsyncSession) -> None:
        """Human players should have agent_id=None."""
        game = Game(game_uuid="human-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        player = GamePlayer(
            game_id=game.id,  # type: ignore[arg-type]
            seat_index=0,
            name="Human",
            starting_chips=1000,
        )
        session.add(player)
        await session.commit()
        await session.refresh(player)

        assert player.agent_id is None

    async def test_query_players_by_game(self, session: AsyncSession) -> None:
        """Should query all players for a game."""
        game = Game(game_uuid="multi-player")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        for i in range(3):
            session.add(GamePlayer(
                game_id=game.id,  # type: ignore[arg-type]
                seat_index=i,
                name=f"Player {i}",
                starting_chips=1000,
            ))
        await session.commit()

        result = await session.exec(
            select(GamePlayer).where(GamePlayer.game_id == game.id)
        )
        players = list(result)
        assert len(players) == 3


class TestHandModel:
    """Tests for the Hand table model."""

    async def test_create_hand(self, session: AsyncSession) -> None:
        """Should create a hand record."""
        game = Game(game_uuid="hand-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        hand = Hand(
            game_id=game.id,  # type: ignore[arg-type]
            hand_number=1,
            dealer_position=0,
            small_blind=10,
            big_blind=20,
        )
        session.add(hand)
        await session.commit()
        await session.refresh(hand)

        assert hand.id is not None
        assert hand.hand_number == 1

    async def test_hand_defaults(self) -> None:
        """Hand should have sensible defaults."""
        hand = Hand(game_id=1, hand_number=1)
        assert hand.community_cards_json == "[]"
        assert hand.pots_json == "[]"
        assert hand.winners_json == "[]"
        assert hand.phase == "between_hands"


class TestHandActionModel:
    """Tests for the HandAction table model."""

    async def test_create_action(self, session: AsyncSession) -> None:
        """Should create a hand action record."""
        game = Game(game_uuid="action-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        hand = Hand(game_id=game.id, hand_number=1)  # type: ignore[arg-type]
        session.add(hand)
        await session.commit()
        await session.refresh(hand)

        action = HandAction(
            hand_id=hand.id,  # type: ignore[arg-type]
            seat_index=0,
            action_type="raise",
            amount=60,
            phase="pre_flop",
            sequence=1,
        )
        session.add(action)
        await session.commit()
        await session.refresh(action)

        assert action.id is not None
        assert action.action_type == "raise"
        assert action.amount == 60

    async def test_query_actions_by_hand(self, session: AsyncSession) -> None:
        """Should query actions for a hand in order."""
        game = Game(game_uuid="actions-query")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        hand = Hand(game_id=game.id, hand_number=1)  # type: ignore[arg-type]
        session.add(hand)
        await session.commit()
        await session.refresh(hand)

        for i, action_type in enumerate(["post_blind", "post_blind", "call", "raise"]):
            session.add(HandAction(
                hand_id=hand.id,  # type: ignore[arg-type]
                seat_index=i % 3,
                action_type=action_type,
                sequence=i,
            ))
        await session.commit()

        result = await session.exec(
            select(HandAction)
            .where(HandAction.hand_id == hand.id)
            .order_by(HandAction.sequence)  # type: ignore[arg-type]
        )
        actions = list(result)
        assert len(actions) == 4
        assert actions[0].action_type == "post_blind"
        assert actions[3].action_type == "raise"


class TestChatMessageModel:
    """Tests for the ChatMessage table model."""

    async def test_create_chat_message(self, session: AsyncSession) -> None:
        """Should create a chat message."""
        game = Game(game_uuid="chat-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        msg = ChatMessage(
            game_id=game.id,  # type: ignore[arg-type]
            hand_number=1,
            seat_index=0,
            name="Bot",
            message="Nice hand!",
            trigger_event="showdown",
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        assert msg.id is not None
        assert msg.message == "Nice hand!"

    async def test_query_chat_by_game(self, session: AsyncSession) -> None:
        """Should query chat messages for a game."""
        game = Game(game_uuid="chat-query")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        for i in range(3):
            session.add(ChatMessage(
                game_id=game.id,  # type: ignore[arg-type]
                seat_index=i,
                name=f"Player {i}",
                message=f"Message {i}",
            ))
        await session.commit()

        result = await session.exec(
            select(ChatMessage).where(ChatMessage.game_id == game.id)
        )
        messages = list(result)
        assert len(messages) == 3


class TestCostRecordModel:
    """Tests for the CostRecord table model."""

    async def test_create_cost_record(self, session: AsyncSession) -> None:
        """Should create a cost record."""
        game = Game(game_uuid="cost-test")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        cost = CostRecord(
            game_id=game.id,  # type: ignore[arg-type]
            agent_id="agent-1",
            call_type="action",
            model="openai:gpt-4o",
            input_tokens=500,
            output_tokens=50,
            estimated_cost=0.005,
        )
        session.add(cost)
        await session.commit()
        await session.refresh(cost)

        assert cost.id is not None
        assert cost.estimated_cost == pytest.approx(0.005)

    async def test_query_costs_by_game(self, session: AsyncSession) -> None:
        """Should query costs for a game."""
        game = Game(game_uuid="cost-query")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        for i in range(5):
            session.add(CostRecord(
                game_id=game.id,  # type: ignore[arg-type]
                agent_id=f"agent-{i}",
                call_type="action" if i % 2 == 0 else "chat",
                model="openai:gpt-4o",
                input_tokens=100,
                output_tokens=20,
                estimated_cost=0.001,
            ))
        await session.commit()

        result = await session.exec(
            select(CostRecord).where(CostRecord.game_id == game.id)
        )
        costs = list(result)
        assert len(costs) == 5


class TestRelationships:
    """Tests for cross-table queries."""

    async def test_full_game_hierarchy(self, session: AsyncSession) -> None:
        """Should create a game with players, hands, actions, chat, costs."""
        game = Game(game_uuid="full-hierarchy", mode="player", status="active")
        session.add(game)
        await session.commit()
        await session.refresh(game)

        for i in range(3):
            session.add(GamePlayer(
                game_id=game.id,  # type: ignore[arg-type]
                seat_index=i,
                name=f"Player {i}",
                starting_chips=1000,
            ))

        hand = Hand(
            game_id=game.id,  # type: ignore[arg-type]
            hand_number=1,
            dealer_position=0,
        )
        session.add(hand)
        await session.commit()
        await session.refresh(hand)

        session.add(HandAction(
            hand_id=hand.id,  # type: ignore[arg-type]
            seat_index=0,
            action_type="post_blind",
            amount=10,
            sequence=0,
        ))
        session.add(HandAction(
            hand_id=hand.id,  # type: ignore[arg-type]
            seat_index=1,
            action_type="post_blind",
            amount=20,
            sequence=1,
        ))
        session.add(ChatMessage(
            game_id=game.id,  # type: ignore[arg-type]
            hand_number=1,
            seat_index=2,
            name="Player 2",
            message="Good luck!",
        ))
        session.add(CostRecord(
            game_id=game.id,  # type: ignore[arg-type]
            agent_id="agent-0",
            call_type="action",
            model="openai:gpt-4o",
            input_tokens=200,
            output_tokens=30,
            estimated_cost=0.002,
        ))
        await session.commit()

        players = list(await session.exec(
            select(GamePlayer).where(GamePlayer.game_id == game.id)
        ))
        hands = list(await session.exec(
            select(Hand).where(Hand.game_id == game.id)
        ))
        actions = list(await session.exec(
            select(HandAction).where(HandAction.hand_id == hand.id)
        ))
        chats = list(await session.exec(
            select(ChatMessage).where(ChatMessage.game_id == game.id)
        ))
        costs = list(await session.exec(
            select(CostRecord).where(CostRecord.game_id == game.id)
        ))

        assert len(players) == 3
        assert len(hands) == 1
        assert len(actions) == 2
        assert len(chats) == 1
        assert len(costs) == 1
