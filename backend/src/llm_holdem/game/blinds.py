"""Blind structure and escalation management."""

import logging

logger = logging.getLogger(__name__)

# Default blind levels: (small_blind, big_blind)
# Blinds double every 10 hands per the product requirements
DEFAULT_BLIND_LEVELS: list[tuple[int, int]] = [
    (10, 20),
    (20, 40),
    (40, 80),
    (75, 150),
    (150, 300),
    (300, 600),
    (500, 1000),
    (1000, 2000),
]

# Number of hands before blinds increase
DEFAULT_HANDS_PER_LEVEL: int = 10


class BlindManager:
    """Manages the blind structure and escalation for a tournament.

    Blinds increase every N hands (default 10) according to a predefined
    schedule.
    """

    def __init__(
        self,
        levels: list[tuple[int, int]] | None = None,
        hands_per_level: int = DEFAULT_HANDS_PER_LEVEL,
    ) -> None:
        """Initialize the blind manager.

        Args:
            levels: List of (small_blind, big_blind) tuples. Uses default if None.
            hands_per_level: Number of hands at each level before escalation.
        """
        self._levels = levels or list(DEFAULT_BLIND_LEVELS)
        self._hands_per_level = hands_per_level
        self._current_level: int = 0
        self._hands_at_current_level: int = 0

    @property
    def small_blind(self) -> int:
        """Current small blind amount."""
        return self._levels[self._current_level][0]

    @property
    def big_blind(self) -> int:
        """Current big blind amount."""
        return self._levels[self._current_level][1]

    @property
    def current_level(self) -> int:
        """Current blind level index (0-based)."""
        return self._current_level

    @property
    def hands_at_current_level(self) -> int:
        """Number of hands played at the current level."""
        return self._hands_at_current_level

    @property
    def hands_per_level(self) -> int:
        """Number of hands per blind level."""
        return self._hands_per_level

    @property
    def hands_until_increase(self) -> int:
        """Hands remaining before the next blind increase."""
        if self._current_level >= len(self._levels) - 1:
            return -1  # Already at max level
        return self._hands_per_level - self._hands_at_current_level

    @property
    def is_max_level(self) -> bool:
        """Whether we're at the maximum blind level."""
        return self._current_level >= len(self._levels) - 1

    @property
    def next_level(self) -> tuple[int, int] | None:
        """The next blind level, or None if at max."""
        if self.is_max_level:
            return None
        return self._levels[self._current_level + 1]

    @property
    def all_levels(self) -> list[tuple[int, int]]:
        """All blind levels."""
        return list(self._levels)

    def advance_hand(self) -> bool:
        """Notify the manager that a hand has been completed.

        Should be called after each hand is finished.

        Returns:
            True if the blinds increased as a result of this hand.
        """
        self._hands_at_current_level += 1
        increased = False

        if (
            self._hands_at_current_level >= self._hands_per_level
            and not self.is_max_level
        ):
            self._current_level += 1
            self._hands_at_current_level = 0
            increased = True
            logger.info(
                "Blinds increased to %d/%d (level %d)",
                self.small_blind,
                self.big_blind,
                self._current_level,
            )

        return increased

    def get_blind_posting(
        self,
        sb_seat: int,
        bb_seat: int,
        sb_stack: int,
        bb_stack: int,
    ) -> list[tuple[int, int, str]]:
        """Calculate the blind amounts each player should post.

        Handles short stacks that can't afford the full blind.

        Args:
            sb_seat: Small blind player's seat index.
            bb_seat: Big blind player's seat index.
            sb_stack: Small blind player's chip count.
            bb_stack: Big blind player's chip count.

        Returns:
            List of (seat_index, amount, label) tuples.
        """
        postings: list[tuple[int, int, str]] = []

        # Small blind
        sb_amount = min(self.small_blind, sb_stack)
        if sb_amount > 0:
            postings.append((sb_seat, sb_amount, "small_blind"))

        # Big blind
        bb_amount = min(self.big_blind, bb_stack)
        if bb_amount > 0:
            postings.append((bb_seat, bb_amount, "big_blind"))

        return postings

    def __repr__(self) -> str:
        return (
            f"BlindManager(level={self._current_level}, "
            f"blinds={self.small_blind}/{self.big_blind}, "
            f"hands_at_level={self._hands_at_current_level})"
        )
