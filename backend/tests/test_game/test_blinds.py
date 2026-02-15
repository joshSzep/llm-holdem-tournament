"""Tests for blind management."""

from llm_holdem.game.blinds import DEFAULT_BLIND_LEVELS, BlindManager


class TestBlindManagerBasics:
    """Basic blind operations."""

    def test_initial_state(self) -> None:
        bm = BlindManager()
        assert bm.small_blind == 10
        assert bm.big_blind == 20
        assert bm.current_level == 0
        assert bm.hands_at_current_level == 0

    def test_custom_levels(self) -> None:
        bm = BlindManager(levels=[(25, 50), (50, 100)])
        assert bm.small_blind == 25
        assert bm.big_blind == 50

    def test_custom_hands_per_level(self) -> None:
        bm = BlindManager(hands_per_level=5)
        assert bm.hands_per_level == 5

    def test_hands_until_increase(self) -> None:
        bm = BlindManager()
        assert bm.hands_until_increase == 10

    def test_is_not_max_level_initially(self) -> None:
        bm = BlindManager()
        assert not bm.is_max_level

    def test_next_level(self) -> None:
        bm = BlindManager()
        assert bm.next_level == (20, 40)

    def test_all_levels(self) -> None:
        bm = BlindManager()
        assert bm.all_levels == list(DEFAULT_BLIND_LEVELS)

    def test_repr(self) -> None:
        bm = BlindManager()
        assert "10/20" in repr(bm)
        assert "level=0" in repr(bm)


class TestBlindEscalation:
    """Blind escalation tests."""

    def test_no_increase_before_threshold(self) -> None:
        bm = BlindManager()
        for _ in range(9):
            increased = bm.advance_hand()
            assert not increased
        assert bm.small_blind == 10
        assert bm.big_blind == 20

    def test_increase_at_threshold(self) -> None:
        bm = BlindManager()
        for _ in range(9):
            bm.advance_hand()
        increased = bm.advance_hand()
        assert increased
        assert bm.small_blind == 20
        assert bm.big_blind == 40
        assert bm.current_level == 1
        assert bm.hands_at_current_level == 0

    def test_full_escalation_schedule(self) -> None:
        bm = BlindManager()
        for level_idx, (expected_sb, expected_bb) in enumerate(DEFAULT_BLIND_LEVELS):
            assert bm.small_blind == expected_sb
            assert bm.big_blind == expected_bb
            assert bm.current_level == level_idx
            for _ in range(10):
                bm.advance_hand()

    def test_stays_at_max_level(self) -> None:
        bm = BlindManager()
        # Advance through all levels
        for _ in range(len(DEFAULT_BLIND_LEVELS) * 10 + 20):
            bm.advance_hand()
        assert bm.is_max_level
        assert bm.small_blind == 1000
        assert bm.big_blind == 2000

    def test_max_level_next_is_none(self) -> None:
        bm = BlindManager(levels=[(10, 20)])
        assert bm.is_max_level
        assert bm.next_level is None

    def test_hands_until_increase_at_max(self) -> None:
        bm = BlindManager(levels=[(10, 20)])
        assert bm.hands_until_increase == -1

    def test_custom_hands_per_level_escalation(self) -> None:
        bm = BlindManager(hands_per_level=3)
        for _ in range(3):
            bm.advance_hand()
        assert bm.current_level == 1
        assert bm.small_blind == 20
        assert bm.big_blind == 40

    def test_hands_until_decrease_as_hands_played(self) -> None:
        bm = BlindManager()
        assert bm.hands_until_increase == 10
        bm.advance_hand()
        assert bm.hands_until_increase == 9
        for _ in range(4):
            bm.advance_hand()
        assert bm.hands_until_increase == 5


class TestBlindPosting:
    """Blind posting calculation."""

    def test_normal_posting(self) -> None:
        bm = BlindManager()
        postings = bm.get_blind_posting(
            sb_seat=0, bb_seat=1, sb_stack=1000, bb_stack=1000
        )
        assert len(postings) == 2
        assert postings[0] == (0, 10, "small_blind")
        assert postings[1] == (1, 20, "big_blind")

    def test_short_stack_sb(self) -> None:
        """Small blind player can't afford full SB."""
        bm = BlindManager()
        postings = bm.get_blind_posting(
            sb_seat=0, bb_seat=1, sb_stack=5, bb_stack=1000
        )
        assert postings[0] == (0, 5, "small_blind")
        assert postings[1] == (1, 20, "big_blind")

    def test_short_stack_bb(self) -> None:
        """Big blind player can't afford full BB."""
        bm = BlindManager()
        postings = bm.get_blind_posting(
            sb_seat=0, bb_seat=1, sb_stack=1000, bb_stack=15
        )
        assert postings[0] == (0, 10, "small_blind")
        assert postings[1] == (1, 15, "big_blind")

    def test_both_short_stacks(self) -> None:
        bm = BlindManager()
        postings = bm.get_blind_posting(
            sb_seat=0, bb_seat=1, sb_stack=3, bb_stack=8
        )
        assert postings[0] == (0, 3, "small_blind")
        assert postings[1] == (1, 8, "big_blind")

    def test_zero_stack_sb(self) -> None:
        """Player with 0 chips posts nothing."""
        bm = BlindManager()
        postings = bm.get_blind_posting(
            sb_seat=0, bb_seat=1, sb_stack=0, bb_stack=1000
        )
        assert len(postings) == 1  # Only BB
        assert postings[0] == (1, 20, "big_blind")

    def test_higher_blind_level_posting(self) -> None:
        bm = BlindManager()
        for _ in range(10):
            bm.advance_hand()
        # Now at level 1: 20/40
        postings = bm.get_blind_posting(
            sb_seat=3, bb_seat=4, sb_stack=500, bb_stack=500
        )
        assert postings[0] == (3, 20, "small_blind")
        assert postings[1] == (4, 40, "big_blind")
