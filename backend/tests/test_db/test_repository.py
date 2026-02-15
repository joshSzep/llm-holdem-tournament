"""Tests for the data repository CRUD operations."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.repository import (
    create_chat_message,
    create_cost_record,
    create_game,
    create_game_player,
    create_hand,
    create_hand_action,
    get_actions_for_hand,
    get_chat_messages,
    get_cost_records,
    get_cost_summary,
    get_game_by_id,
    get_game_by_uuid,
    get_game_players,
    get_hand_by_number,
    get_hands_for_game,
    list_games,
    update_game_player,
    update_game_status,
    update_hand,
)


@pytest.fixture
async def engine():
    """Create an in-memory async engine with tables."""
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Create an async session for testing."""
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess


# ─── Game Tests ───────────────────────────────────────


class TestCreateGame:
    """Tests for create_game."""

    async def test_create_game_defaults(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="uuid-1")
        assert game.id is not None
        assert game.game_uuid == "uuid-1"
        assert game.mode == "player"
        assert game.status == "waiting"
        assert game.config_json == "{}"

    async def test_create_game_with_config(self, session: AsyncSession) -> None:
        config = {"starting_chips": 2000, "blind_schedule": "fast"}
        game = await create_game(session, game_uuid="uuid-2", mode="spectator", config=config)
        assert game.mode == "spectator"
        assert '"starting_chips": 2000' in game.config_json

    async def test_create_multiple_games(self, session: AsyncSession) -> None:
        g1 = await create_game(session, game_uuid="uuid-a")
        g2 = await create_game(session, game_uuid="uuid-b")
        assert g1.id != g2.id


class TestGetGame:
    """Tests for get_game_by_uuid and get_game_by_id."""

    async def test_get_by_uuid_found(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="find-me")
        found = await get_game_by_uuid(session, "find-me")
        assert found is not None
        assert found.id == game.id

    async def test_get_by_uuid_not_found(self, session: AsyncSession) -> None:
        result = await get_game_by_uuid(session, "nonexistent")
        assert result is None

    async def test_get_by_id_found(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="by-id")
        found = await get_game_by_id(session, game.id)
        assert found is not None
        assert found.game_uuid == "by-id"

    async def test_get_by_id_not_found(self, session: AsyncSession) -> None:
        result = await get_game_by_id(session, 9999)
        assert result is None


class TestListGames:
    """Tests for list_games."""

    async def test_list_all(self, session: AsyncSession) -> None:
        await create_game(session, game_uuid="list-1")
        await create_game(session, game_uuid="list-2")
        games = await list_games(session)
        assert len(games) == 2

    async def test_list_by_status(self, session: AsyncSession) -> None:
        g1 = await create_game(session, game_uuid="s-1")
        await create_game(session, game_uuid="s-2")
        await update_game_status(session, g1.id, "in_progress")
        waiting = await list_games(session, status="waiting")
        assert len(waiting) == 1
        in_progress = await list_games(session, status="in_progress")
        assert len(in_progress) == 1

    async def test_list_empty(self, session: AsyncSession) -> None:
        games = await list_games(session)
        assert games == []

    async def test_list_order_newest_first(self, session: AsyncSession) -> None:
        g1 = await create_game(session, game_uuid="first")
        g2 = await create_game(session, game_uuid="second")
        games = await list_games(session)
        assert games[0].id == g2.id
        assert games[1].id == g1.id


class TestUpdateGameStatus:
    """Tests for update_game_status."""

    async def test_update_status(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="upd-1")
        updated = await update_game_status(session, game.id, "in_progress")
        assert updated is not None
        assert updated.status == "in_progress"

    async def test_update_with_winner(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="upd-2")
        updated = await update_game_status(
            session, game.id, "finished",
            winner_seat=0, total_hands=42,
            finished_at="2025-01-01T00:00:00Z",
        )
        assert updated is not None
        assert updated.winner_seat == 0
        assert updated.total_hands == 42
        assert updated.finished_at == "2025-01-01T00:00:00Z"

    async def test_update_nonexistent(self, session: AsyncSession) -> None:
        result = await update_game_status(session, 9999, "in_progress")
        assert result is None


# ─── GamePlayer Tests ─────────────────────────────────


class TestGamePlayer:
    """Tests for game player CRUD."""

    async def test_create_player(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="gp-1")
        player = await create_game_player(
            session, game.id, seat_index=0, name="Alice",
            starting_chips=1500, agent_id="agent-1",
        )
        assert player.id is not None
        assert player.game_id == game.id
        assert player.name == "Alice"
        assert player.starting_chips == 1500

    async def test_get_players_ordered(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="gp-2")
        await create_game_player(session, game.id, seat_index=2, name="Charlie")
        await create_game_player(session, game.id, seat_index=0, name="Alice")
        await create_game_player(session, game.id, seat_index=1, name="Bob")
        players = await get_game_players(session, game.id)
        assert len(players) == 3
        assert players[0].name == "Alice"
        assert players[1].name == "Bob"
        assert players[2].name == "Charlie"

    async def test_update_player_final_state(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="gp-3")
        player = await create_game_player(session, game.id, seat_index=0, name="Alice")
        updated = await update_game_player(
            session, player.id, final_chips=2500, finish_position=1,
        )
        assert updated is not None
        assert updated.final_chips == 2500
        assert updated.finish_position == 1

    async def test_update_player_elimination(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="gp-4")
        player = await create_game_player(session, game.id, seat_index=1, name="Bob")
        updated = await update_game_player(
            session, player.id, final_chips=0, finish_position=4,
            elimination_hand=15,
        )
        assert updated is not None
        assert updated.elimination_hand == 15

    async def test_update_nonexistent_player(self, session: AsyncSession) -> None:
        result = await update_game_player(session, 9999, final_chips=100)
        assert result is None


# ─── Hand Tests ───────────────────────────────────────


class TestHand:
    """Tests for hand CRUD."""

    async def test_create_hand(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="h-1")
        hand = await create_hand(
            session, game.id, hand_number=1,
            dealer_position=0, small_blind=10, big_blind=20,
        )
        assert hand.id is not None
        assert hand.game_id == game.id
        assert hand.hand_number == 1
        assert hand.big_blind == 20

    async def test_update_hand_results(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="h-2")
        hand = await create_hand(
            session, game.id, hand_number=1,
            dealer_position=0, small_blind=10, big_blind=20,
        )
        updated = await update_hand(
            session, hand.id,
            community_cards_json='["Ah", "Kh", "Qh", "Jh", "Th"]',
            pots_json='[{"amount": 40, "eligible": [0, 1]}]',
            winners_json='[0]',
            phase="showdown",
        )
        assert updated is not None
        assert updated.phase == "showdown"
        assert "Ah" in updated.community_cards_json

    async def test_update_nonexistent_hand(self, session: AsyncSession) -> None:
        result = await update_hand(session, 9999, phase="flop")
        assert result is None

    async def test_get_hands_for_game(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="h-3")
        await create_hand(session, game.id, 2, 1, 10, 20)
        await create_hand(session, game.id, 1, 0, 10, 20)
        await create_hand(session, game.id, 3, 2, 10, 20)
        hands = await get_hands_for_game(session, game.id)
        assert len(hands) == 3
        assert hands[0].hand_number == 1
        assert hands[2].hand_number == 3

    async def test_get_hand_by_number(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="h-4")
        await create_hand(session, game.id, 5, 0, 25, 50)
        found = await get_hand_by_number(session, game.id, 5)
        assert found is not None
        assert found.big_blind == 50

    async def test_get_hand_by_number_not_found(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="h-5")
        result = await get_hand_by_number(session, game.id, 99)
        assert result is None


# ─── HandAction Tests ─────────────────────────────────


class TestHandAction:
    """Tests for hand action CRUD."""

    async def test_create_action(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="ha-1")
        hand = await create_hand(session, game.id, 1, 0, 10, 20)
        action = await create_hand_action(
            session, hand.id, seat_index=0,
            action_type="raise", amount=60,
            phase="preflop", sequence=1,
        )
        assert action.id is not None
        assert action.action_type == "raise"
        assert action.amount == 60

    async def test_get_actions_ordered(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="ha-2")
        hand = await create_hand(session, game.id, 1, 0, 10, 20)
        await create_hand_action(session, hand.id, 0, "call", phase="preflop", sequence=2)
        await create_hand_action(session, hand.id, 1, "raise", amount=40, phase="preflop", sequence=1)
        await create_hand_action(session, hand.id, 0, "check", phase="flop", sequence=3)
        actions = await get_actions_for_hand(session, hand.id)
        assert len(actions) == 3
        assert actions[0].sequence == 1
        assert actions[1].sequence == 2
        assert actions[2].sequence == 3


# ─── ChatMessage Tests ────────────────────────────────


class TestChatMessage:
    """Tests for chat message CRUD."""

    async def test_create_chat_message(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="cm-1")
        msg = await create_chat_message(
            session, game.id, seat_index=0, name="Alice",
            message="Nice hand!", hand_number=3,
            trigger_event="hand_won",
        )
        assert msg.id is not None
        assert msg.message == "Nice hand!"
        assert msg.trigger_event == "hand_won"

    async def test_get_messages_ordered_and_limited(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="cm-2")
        for i in range(5):
            await create_chat_message(
                session, game.id, seat_index=0,
                name="Bot", message=f"msg-{i}",
            )
        # Get last 3 messages
        msgs = await get_chat_messages(session, game.id, limit=3)
        assert len(msgs) == 3
        # Should be in chronological order (oldest first)
        assert msgs[0].message == "msg-2"
        assert msgs[2].message == "msg-4"

    async def test_get_all_messages(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="cm-3")
        await create_chat_message(session, game.id, 0, "A", "hello")
        await create_chat_message(session, game.id, 1, "B", "hi")
        msgs = await get_chat_messages(session, game.id)
        assert len(msgs) == 2
        assert msgs[0].message == "hello"
        assert msgs[1].message == "hi"


# ─── CostRecord Tests ────────────────────────────────


class TestCostRecord:
    """Tests for cost record CRUD."""

    async def test_create_cost_record(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="cr-1")
        cost = await create_cost_record(
            session, game.id, agent_id="agent-1",
            call_type="action", model="gpt-4o",
            input_tokens=500, output_tokens=100,
            estimated_cost=0.003,
        )
        assert cost.id is not None
        assert cost.model == "gpt-4o"
        assert cost.estimated_cost == 0.003

    async def test_get_cost_records_filtered(self, session: AsyncSession) -> None:
        g1 = await create_game(session, game_uuid="cr-2")
        g2 = await create_game(session, game_uuid="cr-3")
        await create_cost_record(session, g1.id, "a1", "action", "gpt-4o")
        await create_cost_record(session, g1.id, "a1", "chat", "gpt-4o")
        await create_cost_record(session, g2.id, "a2", "action", "claude-3")
        all_costs = await get_cost_records(session)
        assert len(all_costs) == 3
        g1_costs = await get_cost_records(session, game_id=g1.id)
        assert len(g1_costs) == 2

    async def test_get_cost_summary_empty(self, session: AsyncSession) -> None:
        summary = await get_cost_summary(session)
        assert summary["total_cost"] == 0
        assert summary["call_count"] == 0

    async def test_get_cost_summary(self, session: AsyncSession) -> None:
        game = await create_game(session, game_uuid="cr-4")
        await create_cost_record(
            session, game.id, "a1", "action", "gpt-4o",
            input_tokens=500, output_tokens=100, estimated_cost=0.003,
        )
        await create_cost_record(
            session, game.id, "a1", "chat", "gpt-4o",
            input_tokens=300, output_tokens=50, estimated_cost=0.001,
        )
        summary = await get_cost_summary(session)
        assert summary["total_cost"] == 0.004
        assert summary["total_input_tokens"] == 800
        assert summary["total_output_tokens"] == 150
        assert summary["call_count"] == 2


# ─── Integration Test ─────────────────────────────────


class TestFullGameFlow:
    """Integration test creating a full game with hands, actions, chat, and costs."""

    async def test_complete_flow(self, session: AsyncSession) -> None:
        # Create game
        game = await create_game(session, game_uuid="flow-1", config={"chips": 1000})

        # Add players
        p0 = await create_game_player(session, game.id, 0, "Human", 1000)
        p1 = await create_game_player(session, game.id, 1, "Bot", 1000, agent_id="gpt-4o")

        # Start game
        await update_game_status(session, game.id, "in_progress")

        # Deal hand
        hand = await create_hand(session, game.id, 1, 0, 10, 20)

        # Record actions
        await create_hand_action(session, hand.id, 1, "call", amount=20, phase="preflop", sequence=1)
        await create_hand_action(session, hand.id, 0, "check", phase="preflop", sequence=2)
        await create_hand_action(session, hand.id, 0, "bet", amount=40, phase="flop", sequence=3)
        await create_hand_action(session, hand.id, 1, "fold", phase="flop", sequence=4)

        # Update hand result
        await update_hand(
            session, hand.id,
            community_cards_json='["Ah", "7c", "2d"]',
            winners_json='[0]',
            phase="flop",
        )

        # Chat
        await create_chat_message(session, game.id, 1, "Bot", "Well played!", hand_number=1)

        # Cost tracking
        await create_cost_record(
            session, game.id, "gpt-4o", "action", "gpt-4o",
            input_tokens=600, output_tokens=80, estimated_cost=0.0025,
        )

        # Finish game
        await update_game_player(session, p0.id, final_chips=1040, finish_position=1)
        await update_game_player(session, p1.id, final_chips=960, finish_position=2)
        await update_game_status(
            session, game.id, "finished",
            winner_seat=0, total_hands=1,
        )

        # Verify everything
        final_game = await get_game_by_uuid(session, "flow-1")
        assert final_game is not None
        assert final_game.status == "finished"
        assert final_game.winner_seat == 0

        players = await get_game_players(session, game.id)
        assert len(players) == 2
        assert players[0].finish_position == 1

        hands = await get_hands_for_game(session, game.id)
        assert len(hands) == 1

        actions = await get_actions_for_hand(session, hand.id)
        assert len(actions) == 4

        msgs = await get_chat_messages(session, game.id)
        assert len(msgs) == 1

        summary = await get_cost_summary(session)
        assert summary["call_count"] == 1
