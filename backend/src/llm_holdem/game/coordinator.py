"""Game coordinator — ties together engine, WebSocket, DB, and timer.

This is the main game loop orchestrator. For AI turns, it uses Pydantic AI
agents via the action agent module. For human turns, it waits for WebSocket
messages with a 30-second timer. Also triggers reactive chat after key events.
"""

import asyncio
import logging
import random
from typing import Literal

from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.agents.action_agent import get_ai_action
from llm_holdem.agents.chat_agent import trigger_chat_responses
from llm_holdem.agents.cost_tracking import record_cost
from llm_holdem.agents.registry import AgentRegistry
from llm_holdem.agents.schemas import AgentProfile
from llm_holdem.api.messages import ChatMessageOut
from llm_holdem.api.messages import GameOverMessage
from llm_holdem.api.messages import GamePausedMessage
from llm_holdem.api.messages import GameResumedMessage
from llm_holdem.api.messages import PlayerActionMessage
from llm_holdem.api.messages import TimerUpdateMessage
from llm_holdem.api.websocket_handler import ConnectionManager
from llm_holdem.db.persistence import save_game_result
from llm_holdem.db.persistence import save_hand
from llm_holdem.db.persistence import save_new_game
from llm_holdem.db.repository import create_chat_message
from llm_holdem.db.repository import update_game_player
from llm_holdem.db.repository import update_game_status
from llm_holdem.db.repository import get_game_players
from llm_holdem.db.models import ChatMessage
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState
from llm_holdem.game.timer import TurnTimer
from llm_holdem.game.timer import get_timeout_action

logger = logging.getLogger(__name__)


class GameCoordinator:
    """Coordinates game flow between engine, WebSocket, database, and timer.

    Attributes:
        engine: The game engine instance.
        game_db_id: The database ID of the game.
        connection_manager: WebSocket connection manager.
        is_paused: Whether the game is currently paused.
    """

    def __init__(
        self,
        engine: GameEngine,
        game_db_id: int,
        connection_manager: ConnectionManager,
        session_factory: object | None = None,
        timer_seconds: int = 30,
        ai_delay: float = 0.5,
        agent_registry: AgentRegistry | None = None,
        use_llm: bool = True,
    ) -> None:
        """Initialize the game coordinator.

        Args:
            engine: The game engine.
            game_db_id: Database ID of the game.
            connection_manager: WebSocket connection manager.
            session_factory: Async callable returning an AsyncSession.
            timer_seconds: Timeout for human turns.
            ai_delay: Delay in seconds for AI "thinking" (0 for tests).
            agent_registry: Registry for looking up agent profiles.
            use_llm: If False, use random fallback instead of LLM calls.
        """
        self.engine = engine
        self.game_db_id = game_db_id
        self.connection_manager = connection_manager
        self._session_factory = session_factory
        self._timer_seconds = timer_seconds
        self._ai_delay = ai_delay
        self._agent_registry = agent_registry
        self._use_llm = use_llm
        self._timer = TurnTimer(timeout_seconds=timer_seconds)
        self._pending_action: asyncio.Future[PlayerActionMessage | None] | None = None
        self.is_paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._last_spoke_times: dict[str, float] = {}
        self._recent_chat: list[dict[str, str]] = []

    async def _broadcast_state(self) -> None:
        """Broadcast current game state to the connected client."""
        state = self.engine.get_state()
        await self.connection_manager.broadcast_game_state(
            self.engine.game_id, state
        )

    async def _send_timer_update(self, seat_index: int, seconds: int) -> None:
        """Send a timer update to the client.

        Args:
            seat_index: Whose turn it is.
            seconds: Seconds remaining.
        """
        msg = TimerUpdateMessage(seat_index=seat_index, seconds_remaining=seconds)
        await self.connection_manager.send_message(self.engine.game_id, msg)

    def pause(self) -> None:
        """Pause the game."""
        if not self.is_paused:
            self.is_paused = True
            self._pause_event.clear()
            logger.info("Game %s paused", self.engine.game_id)

    def resume(self) -> None:
        """Resume the game."""
        if self.is_paused:
            self.is_paused = False
            self._pause_event.set()
            logger.info("Game %s resumed", self.engine.game_id)

    async def _wait_if_paused(self) -> None:
        """Block until the game is unpaused."""
        if self.is_paused:
            await self.connection_manager.send_message(
                self.engine.game_id,
                GamePausedMessage(reason="Game paused"),
            )
            await self._pause_event.wait()
            await self.connection_manager.send_message(
                self.engine.game_id,
                GameResumedMessage(),
            )

    def receive_player_action(self, action: PlayerActionMessage) -> None:
        """Receive a player action from the WebSocket handler.

        Args:
            action: The player's action message.
        """
        if self._pending_action and not self._pending_action.done():
            self._pending_action.set_result(action)
            self._timer.action_received()

    def _get_agent_profile(self, agent_id: str) -> AgentProfile | None:
        """Look up an agent profile from the registry.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            The agent profile, or None if not found.
        """
        if self._agent_registry:
            return self._agent_registry.get_profile(agent_id)
        return None

    async def _get_ai_action_random(
        self, seat_index: int
    ) -> tuple[Literal["fold", "check", "call", "raise"], int | None]:
        """Get an AI action using random strategy (fallback).

        Args:
            seat_index: The AI player's seat.

        Returns:
            Tuple of (action_type, amount).
        """
        player = self.engine.players[seat_index]
        valid_actions = self.engine.betting_manager.get_valid_actions(player)

        action_type = random.choice(valid_actions)

        amount = None
        if action_type == "raise":
            min_raise = self.engine.betting_manager.get_min_raise_to(player)
            max_raise = player.chips + player.current_bet
            if min_raise <= max_raise:
                amount = random.randint(min_raise, min(max_raise, min_raise * 3))
            else:
                action_type = "call" if "call" in valid_actions else "check"

        if self._ai_delay > 0:
            await asyncio.sleep(self._ai_delay)
        return action_type, amount

    async def _get_ai_action(
        self, seat_index: int, session: AsyncSession
    ) -> tuple[Literal["fold", "check", "call", "raise"], int | None]:
        """Get an AI action, using LLM if available or random fallback.

        Args:
            seat_index: The AI player's seat.
            session: Database session for cost tracking.

        Returns:
            Tuple of (action_type, amount).
        """
        player = self.engine.players[seat_index]

        # Check if we should use LLM
        if not self._use_llm or not player.agent_id:
            return await self._get_ai_action_random(seat_index)

        profile = self._get_agent_profile(player.agent_id)
        if not profile:
            logger.warning(
                "No profile found for agent %s, using random", player.agent_id
            )
            return await self._get_ai_action_random(seat_index)

        # Get valid actions info
        valid_actions = self.engine.betting_manager.get_valid_actions(player)
        min_raise_to = None
        max_raise_to = None
        call_amount = None

        if "raise" in valid_actions:
            min_raise_to = self.engine.betting_manager.get_min_raise_to(player)
            max_raise_to = player.chips + player.current_bet
        if "call" in valid_actions:
            call_amount = self.engine.betting_manager.current_bet - player.current_bet

        # Get game state for prompt
        game_state = self.engine.get_state()

        try:
            poker_action, usage = await get_ai_action(
                profile=profile,
                game_state=game_state,
                seat_index=seat_index,
                valid_actions=valid_actions,
                min_raise_to=min_raise_to,
                max_raise_to=max_raise_to,
                call_amount=call_amount,
            )

            # Record cost
            if usage.input_tokens > 0 or usage.output_tokens > 0:
                await record_cost(
                    session=session,
                    game_id=self.game_db_id,
                    agent_id=player.agent_id,
                    call_type="action",
                    model=profile.model,
                    usage=usage,
                )

            if self._ai_delay > 0:
                await asyncio.sleep(self._ai_delay)

            return poker_action.action, poker_action.amount

        except Exception as e:
            logger.error(
                "LLM action failed for agent %s: %s, falling back to random",
                player.agent_id,
                e,
            )
            return await self._get_ai_action_random(seat_index)

    async def _get_human_action(
        self, seat_index: int
    ) -> tuple[Literal["fold", "check", "call", "raise"], int | None]:
        """Wait for a human player action via WebSocket.

        Args:
            seat_index: The human player's seat.

        Returns:
            Tuple of (action_type, amount).
        """
        loop = asyncio.get_event_loop()
        self._pending_action = loop.create_future()

        # Set up timer with tick broadcast
        async def on_tick(seat: int, remaining: int) -> None:
            await self._send_timer_update(seat, remaining)

        def on_timeout(seat: int) -> None:
            if self._pending_action and not self._pending_action.done():
                self._pending_action.set_result(None)

        self._timer = TurnTimer(
            timeout_seconds=self._timer_seconds,
            on_tick=on_tick,
            on_timeout=on_timeout,
        )
        self._timer.start(seat_index)

        try:
            action_msg = await self._pending_action
        except asyncio.CancelledError:
            action_msg = None
        finally:
            self._timer.cancel()
            self._pending_action = None

        if action_msg is None:
            # Timeout — auto check/fold
            player = self.engine.players[seat_index]
            valid = self.engine.betting_manager.get_valid_actions(player)
            can_check = "check" in valid
            auto_action = get_timeout_action(can_check)
            logger.info(
                "Human timed out at seat %d, auto-%s", seat_index, auto_action
            )
            return auto_action, None

        return action_msg.action_type, action_msg.amount

    async def run_game(self, session: AsyncSession) -> None:
        """Run the full game loop.

        Args:
            session: Database session for persistence.
        """
        self.engine.status = "active"
        await update_game_status(session, self.game_db_id, "in_progress")
        await self._broadcast_state()

        while not self.engine.is_tournament_over():
            await self._wait_if_paused()
            await self._run_hand(session)

        # Game over
        await save_game_result(session, self.game_db_id, self.engine)

        winner = self.engine.get_winner()
        if winner:
            await self.connection_manager.send_message(
                self.engine.game_id,
                GameOverMessage(
                    winner_seat=winner.seat_index,
                    winner_name=winner.name,
                ),
            )

        await self._broadcast_state()
        logger.info("Game %s completed", self.engine.game_id)

    async def _run_hand(self, session: AsyncSession) -> None:
        """Run a single hand to completion.

        Args:
            session: Database session for persistence.
        """
        self.engine.start_hand()
        await self._broadcast_state()

        # Pre-flop betting
        await self._run_betting_round(session, is_preflop=True)

        if self._hand_is_over():
            await self._finish_hand(session)
            return

        # Flop, Turn, River
        for phase_name in ("flop", "turn", "river"):
            self.engine.advance_phase()
            await self._broadcast_state()

            await self._run_betting_round(session, is_preflop=False)

            if self._hand_is_over():
                await self._finish_hand(session)
                return

        # Showdown
        self.engine.run_showdown()
        await self._broadcast_state()

        # Trigger showdown chat
        await self._trigger_chat(
            session, "showdown",
            "Showdown! Players reveal their cards.",
        )

        await self._finish_hand(session)

    async def _run_betting_round(
        self, session: AsyncSession, is_preflop: bool
    ) -> None:
        """Run a single betting round.

        Args:
            session: Database session.
            is_preflop: Whether this is the pre-flop round.
        """
        if is_preflop:
            order = self.engine.get_preflop_order()
        else:
            order = self.engine.get_postflop_order()

        for seat in order:
            await self._wait_if_paused()

            player = self.engine.players[seat]
            if player.is_folded or player.is_eliminated or player.is_all_in:
                continue

            # Check if only one active player remains
            active = [
                p for p in self.engine.players
                if not p.is_folded and not p.is_eliminated
            ]
            if len(active) <= 1:
                return

            # Get action
            if player.agent_id is not None:
                action_type, amount = await self._get_ai_action(seat, session)
            else:
                action_type, amount = await self._get_human_action(seat)

            # Apply action
            try:
                self.engine.apply_action(seat, action_type, amount)
            except Exception as e:
                logger.error("Invalid action from seat %d: %s", seat, e)
                # Auto-fold on invalid action
                self.engine.apply_action(seat, "fold")

            await self._broadcast_state()

            # Trigger chat for all-in events
            if action_type == "raise" and player.is_all_in:
                await self._trigger_chat(
                    session, "all_in",
                    f"{player.name} goes ALL-IN!",
                )

    def _hand_is_over(self) -> bool:
        """Check if the hand is over (only one non-folded player).

        Returns:
            True if only one player remains.
        """
        active = [
            p for p in self.engine.players
            if not p.is_folded and not p.is_eliminated
        ]
        return len(active) <= 1

    async def _finish_hand(self, session: AsyncSession) -> None:
        """Finish the current hand — award pot, save, end hand.

        Args:
            session: Database session.
        """
        if self._hand_is_over():
            self.engine.award_pot_to_last_player()

        await save_hand(session, self.game_db_id, self.engine)
        self.engine.end_hand()

        # Update player chips in DB
        db_players = await get_game_players(session, self.game_db_id)
        for db_p in db_players:
            engine_p = self.engine.players[db_p.seat_index]
            await update_game_player(
                session, db_p.id, final_chips=engine_p.chips,
            )

        await self._broadcast_state()

    async def _trigger_chat(
        self,
        session: AsyncSession,
        trigger_event: str,
        event_description: str,
    ) -> None:
        """Trigger reactive chat from AI agents.

        Args:
            session: Database session.
            trigger_event: The event type (e.g., 'showdown', 'all_in').
            event_description: Human-readable description.
        """
        if not self._use_llm or not self._agent_registry:
            return

        game_state = self.engine.get_state()

        # Gather eligible AI agents
        profiles_and_seats: list[tuple[AgentProfile, int]] = []
        for player in self.engine.players:
            if (
                player.agent_id
                and not player.is_eliminated
            ):
                profile = self._get_agent_profile(player.agent_id)
                if profile:
                    profiles_and_seats.append((profile, player.seat_index))

        if not profiles_and_seats:
            return

        try:
            messages = await trigger_chat_responses(
                profiles_and_seats=profiles_and_seats,
                game_state=game_state,
                trigger_event=trigger_event,
                event_description=event_description,
                recent_chat=self._recent_chat,
                last_spoke_times=self._last_spoke_times,
            )

            for agent_id, seat, message, usage in messages:
                # Broadcast chat message
                player = self.engine.players[seat]
                chat_msg = ChatMessageOut(
                    seat_index=seat,
                    name=player.name,
                    message=message,
                )
                await self.connection_manager.send_message(
                    self.engine.game_id, chat_msg
                )

                # Update recent chat
                self._recent_chat.append({
                    "name": player.name,
                    "message": message,
                })
                if len(self._recent_chat) > 20:
                    self._recent_chat = self._recent_chat[-20:]

                # Persist chat message
                db_msg = ChatMessage(
                    game_id=self.game_db_id,
                    hand_number=self.engine.hand_number,
                    seat_index=seat,
                    name=player.name,
                    message=message,
                    trigger_event=trigger_event,
                )
                await create_chat_message(session, db_msg)

                # Record cost
                if usage.input_tokens > 0 or usage.output_tokens > 0:
                    profile = self._get_agent_profile(agent_id)
                    if profile:
                        await record_cost(
                            session=session,
                            game_id=self.game_db_id,
                            agent_id=agent_id,
                            call_type="chat",
                            model=profile.model,
                            usage=usage,
                        )

        except Exception as e:
            logger.error("Chat trigger failed: %s", e)
