"""Tests for game state persistence — save/restore round-trip."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.persistence import (
    restore_game_engine,
    save_game_result,
    save_hand,
    save_new_game,
)
from llm_holdem.db.repository import (
    get_actions_for_hand,
    get_game_by_uuid,
    get_game_players,
    get_hands_for_game,
    update_game_player,
    update_game_status,
)
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState


def _make_players(n: int = 4, chips: int = 1000) -> list[PlayerState]:
    """Create a list of test players."""
    return [
        PlayerState(
            seat_index=i,
            name=f"Player {i}",
            chips=chips,
            agent_id=f"agent-{i}" if i > 0 else None,
        )
        for i in range(n)
    ]


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


class TestSaveNewGame:
    """Tests for save_new_game."""

    async def test_save_creates_game_record(self, session: AsyncSession) -> None:
        players = _make_players(3)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)

        game = await get_game_by_uuid(session, game_engine.game_id)
        assert game is not None
        assert game.id == game_db_id
        assert game.status == "waiting"

    async def test_save_creates_player_records(self, session: AsyncSession) -> None:
        players = _make_players(4)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)

        db_players = await get_game_players(session, game_db_id)
        assert len(db_players) == 4
        assert db_players[0].name == "Player 0"
        assert db_players[0].agent_id is None  # Human player
        assert db_players[1].agent_id == "agent-1"

    async def test_save_with_config(self, session: AsyncSession) -> None:
        players = _make_players(2)
        game_engine = GameEngine(players, seed=42)
        config = {"starting_chips": 1000, "level": "fast"}
        game_db_id = await save_new_game(
            session, game_engine, mode="spectator", config=config,
        )

        game = await get_game_by_uuid(session, game_engine.game_id)
        assert game is not None
        assert game.mode == "spectator"
        assert "starting_chips" in game.config_json


class TestSaveHand:
    """Tests for save_hand."""

    async def test_save_hand_after_fold(self, session: AsyncSession) -> None:
        players = _make_players(2, chips=1000)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)
        await update_game_status(session, game_db_id, "in_progress")

        # Play a hand where player 1 folds
        game_engine.start_hand()
        game_engine.apply_action(game_engine.get_preflop_order()[0], "fold")
        game_engine.award_pot_to_last_player()

        hand_db_id = await save_hand(session, game_db_id, game_engine)

        hands = await get_hands_for_game(session, game_db_id)
        assert len(hands) == 1
        assert hands[0].hand_number == 1
        assert hands[0].id == hand_db_id

    async def test_save_hand_with_actions(self, session: AsyncSession) -> None:
        players = _make_players(2, chips=1000)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)
        await update_game_status(session, game_db_id, "in_progress")

        game_engine.start_hand()
        # Post blinds are already in actions, now add player actions
        preflop_order = game_engine.get_preflop_order()
        game_engine.apply_action(preflop_order[0], "call")
        game_engine.apply_action(preflop_order[1], "check")
        game_engine.advance_phase()  # to flop
        game_engine.apply_action(game_engine.get_postflop_order()[0], "fold")
        game_engine.award_pot_to_last_player()

        hand_db_id = await save_hand(session, game_db_id, game_engine)
        actions = await get_actions_for_hand(session, hand_db_id)

        # 2 blinds + 3 player actions = 5
        assert len(actions) >= 4  # At least blind posts + player actions

    async def test_save_hand_with_showdown(self, session: AsyncSession) -> None:
        players = _make_players(2, chips=1000)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)
        await update_game_status(session, game_db_id, "in_progress")

        game_engine.start_hand()
        preflop_order = game_engine.get_preflop_order()
        game_engine.apply_action(preflop_order[0], "call")
        game_engine.apply_action(preflop_order[1], "check")

        # Run through all phases
        for _ in range(3):  # flop, turn, river
            game_engine.advance_phase()
            postflop_order = game_engine.get_postflop_order()
            for seat in postflop_order:
                player = game_engine.players[seat]
                if not player.is_folded and not player.is_all_in:
                    game_engine.apply_action(seat, "check")

        game_engine.run_showdown()
        hand_db_id = await save_hand(session, game_db_id, game_engine)

        hands = await get_hands_for_game(session, game_db_id)
        assert len(hands) == 1
        assert hands[0].showdown_json is not None
        assert hands[0].community_cards_json is not None


class TestSaveGameResult:
    """Tests for save_game_result."""

    async def test_save_final_result(self, session: AsyncSession) -> None:
        players = _make_players(2, chips=1000)
        game_engine = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, game_engine)
        await update_game_status(session, game_db_id, "in_progress")

        # Simulate: player 1 loses all chips
        game_engine.players[1].chips = 0
        game_engine.players[1].is_eliminated = True

        await save_game_result(session, game_db_id, game_engine)

        game = await get_game_by_uuid(session, game_engine.game_id)
        assert game is not None
        assert game.status == "completed"
        assert game.winner_seat == 0

        db_players = await get_game_players(session, game_db_id)
        winner = next(p for p in db_players if p.seat_index == 0)
        assert winner.finish_position == 1


class TestRestoreGameEngine:
    """Tests for restore_game_engine."""

    async def test_restore_new_game(self, session: AsyncSession) -> None:
        """Restore a game that was just created (no hands played)."""
        players = _make_players(3, chips=500)
        original = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, original)
        await update_game_status(session, game_db_id, "in_progress")

        restored = await restore_game_engine(session, original.game_id)
        assert restored is not None
        assert restored.game_id == original.game_id
        assert len(restored.players) == 3
        assert all(p.chips == 500 for p in restored.players)

    async def test_restore_after_hand(self, session: AsyncSession) -> None:
        """Restore a game after one hand has been played."""
        players = _make_players(2, chips=1000)
        original = GameEngine(players, seed=42)
        game_db_id = await save_new_game(session, original)
        await update_game_status(session, game_db_id, "in_progress")

        # Play a hand
        original.start_hand()
        preflop_order = original.get_preflop_order()
        original.apply_action(preflop_order[0], "fold")
        original.award_pot_to_last_player()
        original.end_hand()

        # Save hand and update player chips
        await save_hand(session, game_db_id, original)
        db_players = await get_game_players(session, game_db_id)
        for db_p in db_players:
            engine_p = original.players[db_p.seat_index]
            await update_game_player(session, db_p.id, final_chips=engine_p.chips)

        # Restore
        restored = await restore_game_engine(session, original.game_id)
        assert restored is not None
        assert restored.hand_number == 1
        # Check chip counts match
        for rp, op in zip(restored.players, original.players, strict=False):
            assert rp.chips == op.chips

    async def test_restore_nonexistent(self, session: AsyncSession) -> None:
        result = await restore_game_engine(session, "does-not-exist")
        assert result is None

    async def test_save_restore_round_trip(self, session: AsyncSession) -> None:
        """Full round trip: create → play hand → save → restore → verify."""
        players = _make_players(4, chips=1000)
        original = GameEngine(players, seed=123)
        game_db_id = await save_new_game(session, original, config={"chips": 1000})
        await update_game_status(session, game_db_id, "in_progress")

        # Play a hand to completion
        original.start_hand()
        preflop_order = original.get_preflop_order()

        # All players call/check through
        for seat in preflop_order:
            player = original.players[seat]
            if not player.is_folded and not player.is_all_in:
                valid_actions = original.betting_manager.get_valid_actions(player)
                if "call" in valid_actions:
                    original.apply_action(seat, "call")
                else:
                    original.apply_action(seat, "check")

        # Advance through flop, turn, river with checks
        for _ in range(3):
            original.advance_phase()
            for seat in original.get_postflop_order():
                player = original.players[seat]
                if not player.is_folded and not player.is_all_in:
                    original.apply_action(seat, "check")

        original.run_showdown()
        original.end_hand()

        # Save hand + player chips
        await save_hand(session, game_db_id, original)
        db_players = await get_game_players(session, game_db_id)
        for db_p in db_players:
            engine_p = original.players[db_p.seat_index]
            await update_game_player(session, db_p.id, final_chips=engine_p.chips)

        # Restore and verify
        restored = await restore_game_engine(session, original.game_id)
        assert restored is not None
        assert restored.hand_number == 1
        assert len(restored.players) == 4
        assert restored.game_id == original.game_id

        # Chip totals should be preserved
        total_original = sum(p.chips for p in original.players)
        total_restored = sum(p.chips for p in restored.players)
        assert total_original == total_restored
