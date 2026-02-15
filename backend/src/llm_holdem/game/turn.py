"""Turn order management for poker betting rounds."""

import logging

from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


class TurnManager:
    """Manages turn order for betting rounds.

    Handles:
    - Pre-flop: action starts left of big blind
    - Post-flop: action starts left of dealer
    - Heads-up: dealer is small blind, acts first pre-flop, last post-flop
    - Skipping folded, all-in, and eliminated players
    - Dealer button rotation
    """

    def __init__(self, num_seats: int) -> None:
        """Initialize the turn manager.

        Args:
            num_seats: Total number of seats at the table.
        """
        self._num_seats = num_seats
        self._dealer_position: int = 0

    @property
    def dealer_position(self) -> int:
        """Current dealer button position (seat index)."""
        return self._dealer_position

    @dealer_position.setter
    def dealer_position(self, value: int) -> None:
        self._dealer_position = value

    def advance_dealer(self, players: list[PlayerState]) -> int:
        """Move the dealer button to the next active player.

        Args:
            players: Current list of players.

        Returns:
            The new dealer seat index.
        """
        active_seats = self._get_active_seats(players)
        if not active_seats:
            return self._dealer_position

        # Find next active seat after current dealer
        current = self._dealer_position
        for _ in range(self._num_seats):
            current = (current + 1) % self._num_seats
            if current in active_seats:
                self._dealer_position = current
                logger.debug("Dealer button moved to seat %d", current)
                return current

        return self._dealer_position

    def get_blind_positions(
        self, players: list[PlayerState]
    ) -> tuple[int, int]:
        """Determine small blind and big blind positions.

        Args:
            players: Current list of players.

        Returns:
            Tuple of (small_blind_seat, big_blind_seat).
        """
        active_seats = self._get_active_seats(players)

        if len(active_seats) == 2:
            # Heads-up: dealer is small blind
            sb_seat = self._dealer_position
            bb_seat = self._next_active_seat(sb_seat, active_seats)
            return sb_seat, bb_seat

        # 3+ players: SB is left of dealer, BB is left of SB
        sb_seat = self._next_active_seat(self._dealer_position, active_seats)
        bb_seat = self._next_active_seat(sb_seat, active_seats)
        return sb_seat, bb_seat

    def get_preflop_order(
        self,
        players: list[PlayerState],
        bb_seat: int,
    ) -> list[int]:
        """Get the turn order for pre-flop betting.

        Pre-flop action starts to the left of the big blind and
        continues clockwise, ending with the big blind.

        Args:
            players: Current list of players.
            bb_seat: Big blind seat index.

        Returns:
            List of seat indices in turn order.
        """
        active_seats = self._get_actionable_seats(players)
        if not active_seats:
            return []

        # Start left of BB
        order: list[int] = []
        current = bb_seat
        for _ in range(self._num_seats):
            current = (current + 1) % self._num_seats
            if current in active_seats:
                order.append(current)

        # BB acts last (if still actionable)
        if bb_seat in active_seats and bb_seat not in order:
            order.append(bb_seat)

        return order

    def get_postflop_order(
        self, players: list[PlayerState]
    ) -> list[int]:
        """Get the turn order for post-flop betting rounds.

        Post-flop action starts to the left of the dealer and
        continues clockwise.

        Args:
            players: Current list of players.

        Returns:
            List of seat indices in turn order.
        """
        active_seats = self._get_actionable_seats(players)
        if not active_seats:
            return []

        order: list[int] = []
        current = self._dealer_position
        for _ in range(self._num_seats):
            current = (current + 1) % self._num_seats
            if current in active_seats:
                order.append(current)

        return order

    def get_next_player(
        self,
        current_seat: int,
        players: list[PlayerState],
    ) -> int | None:
        """Get the next player who can act after the current one.

        Args:
            current_seat: The seat of the player who just acted.
            players: Current list of players.

        Returns:
            Next actionable seat index, or None if no one can act.
        """
        active_seats = self._get_actionable_seats(players)
        if not active_seats:
            return None

        current = current_seat
        for _ in range(self._num_seats):
            current = (current + 1) % self._num_seats
            if current in active_seats and current != current_seat:
                return current

        return None

    def _get_active_seats(self, players: list[PlayerState]) -> set[int]:
        """Get seat indices of non-eliminated players.

        Args:
            players: Current list of players.

        Returns:
            Set of active (non-eliminated) seat indices.
        """
        return {
            p.seat_index
            for p in players
            if not p.is_eliminated
        }

    def _get_actionable_seats(self, players: list[PlayerState]) -> set[int]:
        """Get seat indices of players who can still act.

        A player can act if they are not folded, not all-in, and not eliminated.

        Args:
            players: Current list of players.

        Returns:
            Set of actionable seat indices.
        """
        return {
            p.seat_index
            for p in players
            if not p.is_folded and not p.is_all_in and not p.is_eliminated
        }

    def _next_active_seat(self, from_seat: int, active_seats: set[int]) -> int:
        """Find the next active seat clockwise from a given seat.

        Args:
            from_seat: Starting seat index.
            active_seats: Set of active seat indices.

        Returns:
            The next active seat index.
        """
        current = from_seat
        for _ in range(self._num_seats):
            current = (current + 1) % self._num_seats
            if current in active_seats:
                return current
        return from_seat  # Fallback (shouldn't happen with valid input)

    def __repr__(self) -> str:
        return f"TurnManager(seats={self._num_seats}, dealer={self._dealer_position})"
