"""Turn timer — 30-second countdown for human player turns."""

import asyncio
import logging
from typing import Callable
from typing import Literal

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30


class TurnTimer:
    """Manages a countdown timer for a player's turn.

    When the timer expires, an auto-action (check or fold) is applied.
    The timer can broadcast tick updates via a callback.
    """

    def __init__(
        self,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        on_tick: Callable[[int, int], None] | None = None,
        on_timeout: Callable[[int], None] | None = None,
    ) -> None:
        """Initialize the turn timer.

        Args:
            timeout_seconds: Duration of the timer in seconds.
            on_tick: Optional async/sync callback(seat_index, seconds_remaining).
            on_timeout: Optional async/sync callback(seat_index) when timer expires.
        """
        self._timeout_seconds = timeout_seconds
        self._on_tick = on_tick
        self._on_timeout = on_timeout
        self._task: asyncio.Task | None = None
        self._current_seat: int | None = None
        self._is_running = False
        self._action_received = asyncio.Event()

    @property
    def is_running(self) -> bool:
        """Whether the timer is currently counting down."""
        return self._is_running

    @property
    def current_seat(self) -> int | None:
        """The seat index whose turn is being timed."""
        return self._current_seat

    @property
    def timeout_seconds(self) -> int:
        """The timeout duration in seconds."""
        return self._timeout_seconds

    def start(self, seat_index: int) -> None:
        """Start the timer for a player's turn.

        If a timer is already running, it is cancelled first.

        Args:
            seat_index: The seat index of the player.
        """
        self.cancel()
        self._current_seat = seat_index
        self._is_running = True
        self._action_received.clear()
        self._task = asyncio.create_task(self._run_timer(seat_index))
        logger.debug("Timer started for seat %d (%ds)", seat_index, self._timeout_seconds)

    def cancel(self) -> None:
        """Cancel the current timer if running."""
        if self._task and not self._task.done():
            self._task.cancel()
        self._is_running = False
        self._current_seat = None
        self._task = None

    def action_received(self) -> None:
        """Signal that the player has taken an action, stopping the timer."""
        self._action_received.set()
        self._is_running = False
        logger.debug("Timer stopped — action received from seat %s", self._current_seat)

    async def wait_for_action(self, seat_index: int) -> bool:
        """Start timer and wait for either action or timeout.

        Args:
            seat_index: The seat index to time.

        Returns:
            True if player acted in time, False if timeout.
        """
        self.start(seat_index)
        try:
            if self._task:
                await self._task
        except asyncio.CancelledError:
            pass

        return self._action_received.is_set()

    async def _run_timer(self, seat_index: int) -> None:
        """Internal timer loop with per-second ticks.

        Args:
            seat_index: The seat being timed.
        """
        try:
            for remaining in range(self._timeout_seconds, 0, -1):
                if self._action_received.is_set():
                    return

                # Fire tick callback
                if self._on_tick is not None:
                    result = self._on_tick(seat_index, remaining)
                    if asyncio.iscoroutine(result):
                        await result

                try:
                    await asyncio.wait_for(
                        self._wait_for_action_event(),
                        timeout=1.0,
                    )
                    # Action received during this second
                    return
                except asyncio.TimeoutError:
                    continue

            # Timer expired — player didn't act in time
            if not self._action_received.is_set():
                logger.info("Timer expired for seat %d", seat_index)
                self._is_running = False
                if self._on_timeout is not None:
                    result = self._on_timeout(seat_index)
                    if asyncio.iscoroutine(result):
                        await result

        except asyncio.CancelledError:
            logger.debug("Timer cancelled for seat %d", seat_index)
            raise

    async def _wait_for_action_event(self) -> None:
        """Wait for the action_received event."""
        await self._action_received.wait()


def get_timeout_action(can_check: bool) -> Literal["check", "fold"]:
    """Determine what action to take on timeout.

    Args:
        can_check: Whether check is a valid action.

    Returns:
        "check" if possible, otherwise "fold".
    """
    return "check" if can_check else "fold"
