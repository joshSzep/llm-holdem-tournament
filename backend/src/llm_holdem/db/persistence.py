"""Game state persistence — save/restore game state to/from the database."""

import json
import logging
from datetime import UTC, datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.repository import (
    create_game,
    create_game_player,
    create_hand,
    create_hand_action,
    get_game_by_uuid,
    get_game_players,
    get_hands_for_game,
    update_game_player,
    update_game_status,
    update_hand,
)
from llm_holdem.game.blinds import BlindManager
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


async def save_new_game(
    session: AsyncSession,
    engine: GameEngine,
    mode: str = "player",
    config: dict | None = None,
) -> int:
    """Persist a newly created game and its players to the database.

    Args:
        session: Database session.
        engine: The game engine with initial state.
        mode: Game mode ("player" or "spectator").
        config: Optional game configuration dict.

    Returns:
        The database ID of the created game.
    """
    game = await create_game(
        session,
        game_uuid=engine.game_id,
        mode=mode,
        config=config,
    )

    for player in engine.players:
        await create_game_player(
            session,
            game_id=game.id,
            seat_index=player.seat_index,
            name=player.name,
            starting_chips=player.chips,
            agent_id=player.agent_id,
            avatar_url=player.avatar_url,
        )

    logger.info("Saved new game %s (db_id=%d) with %d players",
                engine.game_id, game.id, len(engine.players))
    return game.id


async def save_hand(
    session: AsyncSession,
    game_db_id: int,
    engine: GameEngine,
) -> int:
    """Persist the current hand's data after it completes.

    Args:
        session: Database session.
        game_db_id: The database ID of the game.
        engine: The game engine with completed hand state.

    Returns:
        The database ID of the created hand record.
    """
    state = engine.get_state()

    # Create hand record
    hand = await create_hand(
        session,
        game_id=game_db_id,
        hand_number=engine.hand_number,
        dealer_position=state.dealer_position,
        small_blind=state.small_blind,
        big_blind=state.big_blind,
    )

    # Save actions
    for seq, action in enumerate(state.current_hand_actions):
        await create_hand_action(
            session,
            hand_id=hand.id,
            seat_index=action.player_index,
            action_type=action.action_type,
            amount=action.amount,
            phase="",
            sequence=seq,
        )

    # Update hand with results
    community_json = json.dumps([str(c) for c in state.community_cards])
    pots_json = json.dumps([
        {"amount": p.amount, "eligible": p.eligible_players}
        for p in state.pots
    ])

    winners_json = "[]"
    showdown_json = None
    if state.showdown_result:
        winners_json = json.dumps(state.showdown_result.winners)
        showdown_json = state.showdown_result.model_dump_json()

    await update_hand(
        session,
        hand.id,
        community_cards_json=community_json,
        pots_json=pots_json,
        winners_json=winners_json,
        showdown_json=showdown_json,
        phase=state.phase,
    )

    logger.info("Saved hand %d for game db_id=%d", engine.hand_number, game_db_id)
    return hand.id


async def save_game_result(
    session: AsyncSession,
    game_db_id: int,
    engine: GameEngine,
) -> None:
    """Persist the final game result.

    Args:
        session: Database session.
        game_db_id: The database ID of the game.
        engine: The game engine after the tournament ends.
    """
    winner = engine.get_winner()
    winner_seat = winner.seat_index if winner else None

    await update_game_status(
        session,
        game_id=game_db_id,
        status="completed",
        winner_seat=winner_seat,
        total_hands=engine.hand_number,
        finished_at=datetime.now(UTC).isoformat(),
    )

    # Update all player final states
    db_players = await get_game_players(session, game_db_id)
    for db_player in db_players:
        engine_player = next(
            (p for p in engine.players if p.seat_index == db_player.seat_index),
            None,
        )
        if engine_player:
            finish_position = None
            elimination_hand = None
            if engine_player.is_eliminated:
                finish_position = len(engine.players)  # Simplified — real impl sets via elimination order
            elif winner and engine_player.seat_index == winner.seat_index:
                finish_position = 1

            await update_game_player(
                session,
                db_player.id,
                final_chips=engine_player.chips,
                finish_position=finish_position,
                elimination_hand=elimination_hand,
            )

    logger.info("Saved game result for db_id=%d, winner seat=%s",
                game_db_id, winner_seat)


async def restore_game_engine(
    session: AsyncSession,
    game_uuid: str,
) -> GameEngine | None:
    """Restore a game engine from the database.

    Reconstructs the GameEngine with all player states, blind levels,
    and dealer position from the most recent hand.

    Args:
        session: Database session.
        game_uuid: The game UUID to restore.

    Returns:
        A reconstructed GameEngine, or None if game not found.
    """
    game = await get_game_by_uuid(session, game_uuid)
    if game is None:
        return None

    db_players = await get_game_players(session, game.id)
    if not db_players:
        return None

    # Reconstruct player states
    players: list[PlayerState] = []
    for db_p in db_players:
        chips = db_p.final_chips if db_p.final_chips is not None else db_p.starting_chips
        is_eliminated = chips == 0 and db_p.elimination_hand is not None

        players.append(PlayerState(
            seat_index=db_p.seat_index,
            agent_id=db_p.agent_id,
            name=db_p.name,
            avatar_url=db_p.avatar_url,
            chips=chips,
            is_eliminated=is_eliminated,
        ))

    # Reconstruct blind level from hand history
    hands = await get_hands_for_game(session, game.id)
    blind_manager = BlindManager()

    hand_number = 0
    dealer_position = 0
    if hands:
        last_hand = hands[-1]
        hand_number = last_hand.hand_number
        dealer_position = last_hand.dealer_position

        # Advance blind manager to match the recorded blind level
        while blind_manager.big_blind < last_hand.big_blind:
            # Force advance to the right level
            blind_manager._current_level += 1
            if blind_manager._current_level >= len(blind_manager._schedule):
                break

    # Create engine with restored state
    engine = GameEngine(players, blind_manager=blind_manager)
    engine.game_id = game_uuid
    engine._hand_number = hand_number
    engine._phase = "between_hands"
    engine._status = "active" if game.status == "in_progress" else game.status

    # Set dealer position
    engine.turn_manager._dealer_position = dealer_position

    logger.info("Restored game %s at hand %d with %d players",
                game_uuid, hand_number, len(players))
    return engine
