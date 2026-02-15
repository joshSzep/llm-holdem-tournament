"""Data access layer — CRUD operations for all database models."""

import json
import logging

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.models import ChatMessage, CostRecord, Game, GamePlayer, Hand, HandAction

logger = logging.getLogger(__name__)


# ─── Game CRUD ────────────────────────────────────────

async def create_game(
    session: AsyncSession,
    game_uuid: str,
    mode: str = "player",
    config: dict | None = None,
) -> Game:
    """Create a new game record.

    Args:
        session: Database session.
        game_uuid: Unique game identifier.
        mode: Game mode ("player" or "spectator").
        config: Optional game configuration dict.

    Returns:
        The created Game record.
    """
    game = Game(
        game_uuid=game_uuid,
        mode=mode,
        status="waiting",
        config_json=json.dumps(config or {}),
    )
    session.add(game)
    await session.commit()
    await session.refresh(game)
    logger.info("Created game %s (id=%s)", game_uuid, game.id)
    return game


async def get_game_by_uuid(session: AsyncSession, game_uuid: str) -> Game | None:
    """Get a game by its UUID.

    Args:
        session: Database session.
        game_uuid: The game UUID.

    Returns:
        The Game record, or None if not found.
    """
    result = await session.exec(select(Game).where(Game.game_uuid == game_uuid))
    return result.first()


async def get_game_by_id(session: AsyncSession, game_id: int) -> Game | None:
    """Get a game by its database ID.

    Args:
        session: Database session.
        game_id: The database ID.

    Returns:
        The Game record, or None if not found.
    """
    return await session.get(Game, game_id)


async def list_games(session: AsyncSession, status: str | None = None) -> list[Game]:
    """List all games, optionally filtered by status.

    Args:
        session: Database session.
        status: Optional status filter.

    Returns:
        List of Game records.
    """
    query = select(Game)
    if status:
        query = query.where(Game.status == status)
    query = query.order_by(Game.id.desc())  # type: ignore[union-attr]
    result = await session.exec(query)
    return list(result)


async def update_game_status(
    session: AsyncSession,
    game_id: int,
    status: str,
    winner_seat: int | None = None,
    total_hands: int | None = None,
    finished_at: str | None = None,
) -> Game | None:
    """Update a game's status and related fields.

    Args:
        session: Database session.
        game_id: The game database ID.
        status: New status.
        winner_seat: Optional winner seat index.
        total_hands: Optional total hands played.
        finished_at: Optional finish timestamp.

    Returns:
        The updated Game, or None if not found.
    """
    game = await session.get(Game, game_id)
    if game is None:
        return None
    game.status = status
    if winner_seat is not None:
        game.winner_seat = winner_seat
    if total_hands is not None:
        game.total_hands = total_hands
    if finished_at is not None:
        game.finished_at = finished_at
    session.add(game)
    await session.commit()
    await session.refresh(game)
    return game


# ─── GamePlayer CRUD ──────────────────────────────────

async def create_game_player(
    session: AsyncSession,
    game_id: int,
    seat_index: int,
    name: str,
    starting_chips: int = 1000,
    agent_id: str | None = None,
    avatar_url: str = "",
) -> GamePlayer:
    """Create a game player record.

    Args:
        session: Database session.
        game_id: The game's database ID.
        seat_index: Player's seat index.
        name: Player display name.
        starting_chips: Initial chip count.
        agent_id: Agent ID (None for human).
        avatar_url: Avatar URL.

    Returns:
        The created GamePlayer record.
    """
    player = GamePlayer(
        game_id=game_id,
        seat_index=seat_index,
        agent_id=agent_id,
        name=name,
        avatar_url=avatar_url,
        starting_chips=starting_chips,
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


async def get_game_players(session: AsyncSession, game_id: int) -> list[GamePlayer]:
    """Get all players for a game.

    Args:
        session: Database session.
        game_id: The game's database ID.

    Returns:
        List of GamePlayer records ordered by seat.
    """
    result = await session.exec(
        select(GamePlayer)
        .where(GamePlayer.game_id == game_id)
        .order_by(GamePlayer.seat_index)  # type: ignore[arg-type]
    )
    return list(result)


async def update_game_player(
    session: AsyncSession,
    player_id: int,
    final_chips: int | None = None,
    finish_position: int | None = None,
    elimination_hand: int | None = None,
) -> GamePlayer | None:
    """Update a game player's final state.

    Args:
        session: Database session.
        player_id: The player's database ID.
        final_chips: Final chip count.
        finish_position: Finishing position (1 = winner).
        elimination_hand: Hand number when eliminated.

    Returns:
        The updated GamePlayer, or None if not found.
    """
    player = await session.get(GamePlayer, player_id)
    if player is None:
        return None
    if final_chips is not None:
        player.final_chips = final_chips
    if finish_position is not None:
        player.finish_position = finish_position
    if elimination_hand is not None:
        player.elimination_hand = elimination_hand
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


# ─── Hand CRUD ────────────────────────────────────────

async def create_hand(
    session: AsyncSession,
    game_id: int,
    hand_number: int,
    dealer_position: int,
    small_blind: int,
    big_blind: int,
) -> Hand:
    """Create a hand record.

    Args:
        session: Database session.
        game_id: The game's database ID.
        hand_number: Hand sequence number.
        dealer_position: Dealer seat index.
        small_blind: Small blind amount.
        big_blind: Big blind amount.

    Returns:
        The created Hand record.
    """
    hand = Hand(
        game_id=game_id,
        hand_number=hand_number,
        dealer_position=dealer_position,
        small_blind=small_blind,
        big_blind=big_blind,
    )
    session.add(hand)
    await session.commit()
    await session.refresh(hand)
    return hand


async def update_hand(
    session: AsyncSession,
    hand_id: int,
    community_cards_json: str | None = None,
    pots_json: str | None = None,
    winners_json: str | None = None,
    showdown_json: str | None = None,
    phase: str | None = None,
) -> Hand | None:
    """Update a hand record with results.

    Args:
        session: Database session.
        hand_id: The hand's database ID.
        community_cards_json: JSON community cards.
        pots_json: JSON pots.
        winners_json: JSON winner seats.
        showdown_json: JSON showdown result.
        phase: Final phase.

    Returns:
        The updated Hand, or None if not found.
    """
    hand = await session.get(Hand, hand_id)
    if hand is None:
        return None
    if community_cards_json is not None:
        hand.community_cards_json = community_cards_json
    if pots_json is not None:
        hand.pots_json = pots_json
    if winners_json is not None:
        hand.winners_json = winners_json
    if showdown_json is not None:
        hand.showdown_json = showdown_json
    if phase is not None:
        hand.phase = phase
    session.add(hand)
    await session.commit()
    await session.refresh(hand)
    return hand


async def get_hands_for_game(session: AsyncSession, game_id: int) -> list[Hand]:
    """Get all hands for a game in order.

    Args:
        session: Database session.
        game_id: The game's database ID.

    Returns:
        List of Hand records ordered by hand number.
    """
    result = await session.exec(
        select(Hand)
        .where(Hand.game_id == game_id)
        .order_by(Hand.hand_number)  # type: ignore[arg-type]
    )
    return list(result)


async def get_hand_by_number(
    session: AsyncSession, game_id: int, hand_number: int
) -> Hand | None:
    """Get a specific hand by game and hand number.

    Args:
        session: Database session.
        game_id: The game's database ID.
        hand_number: The hand number.

    Returns:
        The Hand record, or None if not found.
    """
    result = await session.exec(
        select(Hand)
        .where(Hand.game_id == game_id)
        .where(Hand.hand_number == hand_number)
    )
    return result.first()


# ─── HandAction CRUD ──────────────────────────────────

async def create_hand_action(
    session: AsyncSession,
    hand_id: int,
    seat_index: int,
    action_type: str,
    amount: int | None = None,
    phase: str = "",
    sequence: int = 0,
) -> HandAction:
    """Create a hand action record.

    Args:
        session: Database session.
        hand_id: The hand's database ID.
        seat_index: Acting player's seat.
        action_type: Action type.
        amount: Optional bet/raise amount.
        phase: Game phase when action occurred.
        sequence: Action sequence number.

    Returns:
        The created HandAction record.
    """
    action = HandAction(
        hand_id=hand_id,
        seat_index=seat_index,
        action_type=action_type,
        amount=amount,
        phase=phase,
        sequence=sequence,
    )
    session.add(action)
    await session.commit()
    await session.refresh(action)
    return action


async def get_actions_for_hand(session: AsyncSession, hand_id: int) -> list[HandAction]:
    """Get all actions for a hand in order.

    Args:
        session: Database session.
        hand_id: The hand's database ID.

    Returns:
        List of HandAction records ordered by sequence.
    """
    result = await session.exec(
        select(HandAction)
        .where(HandAction.hand_id == hand_id)
        .order_by(HandAction.sequence)  # type: ignore[arg-type]
    )
    return list(result)


# ─── ChatMessage CRUD ─────────────────────────────────

async def create_chat_message(
    session: AsyncSession,
    game_id: int,
    seat_index: int,
    name: str,
    message: str,
    hand_number: int | None = None,
    trigger_event: str = "",
) -> ChatMessage:
    """Create a chat message record.

    Args:
        session: Database session.
        game_id: The game's database ID.
        seat_index: Sender's seat index.
        name: Sender display name.
        message: Message text.
        hand_number: Optional hand number.
        trigger_event: What triggered the message.

    Returns:
        The created ChatMessage record.
    """
    msg = ChatMessage(
        game_id=game_id,
        hand_number=hand_number,
        seat_index=seat_index,
        name=name,
        message=message,
        trigger_event=trigger_event,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_chat_messages(
    session: AsyncSession,
    game_id: int,
    limit: int = 50,
) -> list[ChatMessage]:
    """Get recent chat messages for a game.

    Args:
        session: Database session.
        game_id: The game's database ID.
        limit: Maximum messages to return.

    Returns:
        List of ChatMessage records, newest first.
    """
    result = await session.exec(
        select(ChatMessage)
        .where(ChatMessage.game_id == game_id)
        .order_by(ChatMessage.id.desc())  # type: ignore[union-attr]
        .limit(limit)
    )
    return list(reversed(list(result)))


# ─── CostRecord CRUD ──────────────────────────────────

async def create_cost_record(
    session: AsyncSession,
    game_id: int,
    agent_id: str,
    call_type: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    estimated_cost: float = 0.0,
) -> CostRecord:
    """Create a cost record for an LLM API call.

    Args:
        session: Database session.
        game_id: The game's database ID.
        agent_id: The agent that made the call.
        call_type: "action" or "chat".
        model: Model identifier.
        input_tokens: Input token count.
        output_tokens: Output token count.
        estimated_cost: Estimated cost in USD.

    Returns:
        The created CostRecord.
    """
    cost = CostRecord(
        game_id=game_id,
        agent_id=agent_id,
        call_type=call_type,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=estimated_cost,
    )
    session.add(cost)
    await session.commit()
    await session.refresh(cost)
    return cost


async def get_cost_records(
    session: AsyncSession,
    game_id: int | None = None,
) -> list[CostRecord]:
    """Get cost records, optionally filtered by game.

    Args:
        session: Database session.
        game_id: Optional game ID filter.

    Returns:
        List of CostRecord records.
    """
    query = select(CostRecord)
    if game_id is not None:
        query = query.where(CostRecord.game_id == game_id)
    query = query.order_by(CostRecord.id)  # type: ignore[union-attr]
    result = await session.exec(query)
    return list(result)


async def get_cost_summary(session: AsyncSession) -> dict:
    """Get summarized cost data across all games.

    Args:
        session: Database session.

    Returns:
        Dict with total_cost, total_input_tokens, total_output_tokens, call_count.
    """
    result = await session.exec(select(CostRecord))
    records = list(result)

    total_cost = sum(r.estimated_cost for r in records)
    total_input = sum(r.input_tokens for r in records)
    total_output = sum(r.output_tokens for r in records)

    return {
        "total_cost": round(total_cost, 6),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "call_count": len(records),
    }


async def get_game_stats(session: AsyncSession, game_id: int) -> dict:
    """Compute rich game statistics for the post-game summary.

    Args:
        session: Database session.
        game_id: The game's database ID.

    Returns:
        Dict with total_hands, biggest_pot, best_hand, most_aggressive,
        most_hands_won, biggest_bluff fields.
    """
    hands = await get_hands_for_game(session, game_id)
    players = await get_game_players(session, game_id)

    total_hands = len(hands)
    biggest_pot = 0
    biggest_pot_hand = 0
    best_hand_name = ""
    best_hand_rank = 9999
    best_hand_player = ""
    best_hand_number = 0

    # Per-player stats
    raise_counts: dict[int, int] = {}
    wins: dict[int, int] = {}

    player_names: dict[int, str] = {p.seat_index: p.name for p in players}

    for hand in hands:
        # Parse pots
        try:
            pots = json.loads(hand.pots_json) if hand.pots_json else []
            hand_total_pot = sum(p.get("amount", 0) for p in pots if isinstance(p, dict))
            if hand_total_pot > biggest_pot:
                biggest_pot = hand_total_pot
                biggest_pot_hand = hand.hand_number
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse winners
        try:
            winners = json.loads(hand.winners_json) if hand.winners_json else []
            for w in winners:
                if isinstance(w, int):
                    wins[w] = wins.get(w, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse showdown for best hand
        if hand.showdown_json:
            try:
                showdown = json.loads(hand.showdown_json)
                hand_results = showdown.get("hand_results", [])
                for hr in hand_results:
                    rank = hr.get("hand_rank", 9999)
                    if isinstance(rank, int) and rank < best_hand_rank:
                        best_hand_rank = rank
                        best_hand_name = hr.get("hand_name", "")
                        seat = hr.get("player_index", -1)
                        best_hand_player = player_names.get(seat, f"Seat {seat}")
                        best_hand_number = hand.hand_number
            except (json.JSONDecodeError, TypeError):
                pass

        # Count raises per player
        actions = await get_actions_for_hand(session, hand.id)
        for action in actions:
            if action.action_type == "raise":
                raise_counts[action.seat_index] = raise_counts.get(action.seat_index, 0) + 1

    # Find most aggressive player
    most_aggressive_name = ""
    most_raises = 0
    for seat, count in raise_counts.items():
        if count > most_raises:
            most_raises = count
            most_aggressive_name = player_names.get(seat, f"Seat {seat}")

    # Find player with most hands won
    most_wins_name = ""
    most_wins_count = 0
    for seat, count in wins.items():
        if count > most_wins_count:
            most_wins_count = count
            most_wins_name = player_names.get(seat, f"Seat {seat}")

    return {
        "total_hands": total_hands,
        "biggest_pot": biggest_pot,
        "biggest_pot_hand": biggest_pot_hand,
        "best_hand_name": best_hand_name if best_hand_rank < 9999 else "",
        "best_hand_player": best_hand_player if best_hand_rank < 9999 else "",
        "best_hand_number": best_hand_number if best_hand_rank < 9999 else 0,
        "most_aggressive_name": most_aggressive_name,
        "most_aggressive_raises": most_raises,
        "most_hands_won_name": most_wins_name,
        "most_hands_won_count": most_wins_count,
    }
