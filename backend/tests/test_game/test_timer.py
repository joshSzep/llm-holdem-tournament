"""Tests for the turn timer."""

import asyncio

from llm_holdem.game.timer import TurnTimer, get_timeout_action


class TestGetTimeoutAction:
    """Tests for get_timeout_action."""

    def test_check_when_available(self) -> None:
        assert get_timeout_action(can_check=True) == "check"

    def test_fold_when_cannot_check(self) -> None:
        assert get_timeout_action(can_check=False) == "fold"


class TestTurnTimerInit:
    """Tests for TurnTimer initialization."""

    def test_default_timeout(self) -> None:
        timer = TurnTimer()
        assert timer.timeout_seconds == 30
        assert not timer.is_running
        assert timer.current_seat is None

    def test_custom_timeout(self) -> None:
        timer = TurnTimer(timeout_seconds=10)
        assert timer.timeout_seconds == 10


class TestTurnTimerCancel:
    """Tests for TurnTimer cancel."""

    def test_cancel_when_not_running(self) -> None:
        timer = TurnTimer()
        timer.cancel()  # Should not raise
        assert not timer.is_running

    async def test_cancel_stops_timer(self) -> None:
        timer = TurnTimer(timeout_seconds=10)
        timer.start(seat_index=0)
        assert timer.is_running
        assert timer.current_seat == 0
        timer.cancel()
        assert not timer.is_running
        assert timer.current_seat is None


class TestTurnTimerActionReceived:
    """Tests for action_received stopping the timer."""

    async def test_action_received_stops_timer(self) -> None:
        timer = TurnTimer(timeout_seconds=5)
        timer.start(seat_index=1)
        assert timer.is_running

        # Simulate action received quickly
        timer.action_received()
        # Give task a moment to process
        await asyncio.sleep(0.05)
        assert not timer.is_running


class TestTurnTimerTimeout:
    """Tests for timer timeout behavior."""

    async def test_timeout_fires_callback(self) -> None:
        timeout_seats: list[int] = []

        def on_timeout(seat: int) -> None:
            timeout_seats.append(seat)

        timer = TurnTimer(timeout_seconds=1, on_timeout=on_timeout)
        acted = await timer.wait_for_action(seat_index=2)

        assert not acted
        assert timeout_seats == [2]

    async def test_action_before_timeout(self) -> None:
        timeout_seats: list[int] = []

        def on_timeout(seat: int) -> None:
            timeout_seats.append(seat)

        timer = TurnTimer(timeout_seconds=5, on_timeout=on_timeout)

        # Send action shortly after start
        async def send_action() -> None:
            await asyncio.sleep(0.1)
            timer.action_received()

        asyncio.create_task(send_action())
        acted = await timer.wait_for_action(seat_index=0)

        assert acted
        assert timeout_seats == []  # Timeout callback not fired


class TestTurnTimerTick:
    """Tests for timer tick callbacks."""

    async def test_tick_fires_each_second(self) -> None:
        ticks: list[tuple[int, int]] = []

        def on_tick(seat: int, remaining: int) -> None:
            ticks.append((seat, remaining))

        timer = TurnTimer(timeout_seconds=2, on_tick=on_tick)
        await timer.wait_for_action(seat_index=3)

        # Should have received ticks for 2 and 1
        assert len(ticks) == 2
        assert ticks[0] == (3, 2)
        assert ticks[1] == (3, 1)

    async def test_tick_stops_on_action(self) -> None:
        ticks: list[tuple[int, int]] = []

        def on_tick(seat: int, remaining: int) -> None:
            ticks.append((seat, remaining))

        timer = TurnTimer(timeout_seconds=5, on_tick=on_tick)

        async def send_action() -> None:
            await asyncio.sleep(0.5)
            timer.action_received()

        asyncio.create_task(send_action())
        await timer.wait_for_action(seat_index=0)

        # Should have only 1 tick (for second 5), then action received
        assert len(ticks) <= 2  # At most 1-2 ticks before action


class TestTurnTimerAsync:
    """Tests for async callback support."""

    async def test_async_on_timeout(self) -> None:
        timeout_seats: list[int] = []

        async def on_timeout(seat: int) -> None:
            timeout_seats.append(seat)

        timer = TurnTimer(timeout_seconds=1, on_timeout=on_timeout)
        acted = await timer.wait_for_action(seat_index=1)

        assert not acted
        assert timeout_seats == [1]

    async def test_async_on_tick(self) -> None:
        ticks: list[tuple[int, int]] = []

        async def on_tick(seat: int, remaining: int) -> None:
            ticks.append((seat, remaining))

        timer = TurnTimer(timeout_seconds=1, on_tick=on_tick)
        await timer.wait_for_action(seat_index=0)

        assert len(ticks) == 1
        assert ticks[0] == (0, 1)


class TestTurnTimerRestart:
    """Tests for restarting the timer."""

    async def test_start_cancels_previous(self) -> None:
        timer = TurnTimer(timeout_seconds=10)
        timer.start(seat_index=0)
        assert timer.current_seat == 0

        timer.start(seat_index=1)
        assert timer.current_seat == 1
        assert timer.is_running

        timer.cancel()
