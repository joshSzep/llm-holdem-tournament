"""Tests for betting logic."""

import pytest

from llm_holdem.game.betting import BettingManager, InvalidActionError
from llm_holdem.game.state import PlayerState


def _player(
    seat: int,
    chips: int = 1000,
    current_bet: int = 0,
    is_folded: bool = False,
    is_all_in: bool = False,
    is_eliminated: bool = False,
) -> PlayerState:
    """Create a test player."""
    return PlayerState(
        seat_index=seat,
        name=f"Player {seat}",
        chips=chips,
        current_bet=current_bet,
        is_folded=is_folded,
        is_all_in=is_all_in,
        is_eliminated=is_eliminated,
    )


class TestValidActions:
    """Tests for get_valid_actions."""

    def test_can_check_when_no_bet(self) -> None:
        bm = BettingManager()
        bm.new_round(0)
        p = _player(0)
        actions = bm.get_valid_actions(p)
        assert "check" in actions
        assert "call" not in actions

    def test_can_call_when_bet_exists(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0)
        actions = bm.get_valid_actions(p)
        assert "call" in actions
        assert "check" not in actions

    def test_can_check_when_bet_matched(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, current_bet=20)
        actions = bm.get_valid_actions(p)
        assert "check" in actions

    def test_can_always_fold(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0)
        actions = bm.get_valid_actions(p)
        assert "fold" in actions

    def test_can_raise_with_enough_chips(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        actions = bm.get_valid_actions(p)
        assert "raise" in actions

    def test_cannot_raise_when_exact_call(self) -> None:
        """Player has exactly enough to call but not raise."""
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=20)
        actions = bm.get_valid_actions(p)
        assert "raise" not in actions
        assert "call" in actions

    def test_no_actions_for_folded_player(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, is_folded=True)
        assert bm.get_valid_actions(p) == []

    def test_no_actions_for_all_in_player(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, is_all_in=True)
        assert bm.get_valid_actions(p) == []

    def test_no_actions_for_eliminated_player(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, is_eliminated=True)
        assert bm.get_valid_actions(p) == []


class TestCallAmount:
    """Tests for call amount calculation."""

    def test_full_call(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        assert bm.get_call_amount(p) == 20

    def test_partial_call_when_already_bet(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000, current_bet=10)
        assert bm.get_call_amount(p) == 10

    def test_all_in_call(self) -> None:
        """Player can't afford full call, goes all-in."""
        bm = BettingManager()
        bm.new_round(100)
        p = _player(0, chips=30)
        assert bm.get_call_amount(p) == 30

    def test_zero_call_when_bet_matched(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, current_bet=20)
        assert bm.get_call_amount(p) == 0


class TestRaiseAmounts:
    """Tests for raise amount calculations."""

    def test_min_raise(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        assert bm.get_min_raise_to(p) == 40  # Current 20 + min raise 20

    def test_max_raise(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=500)
        assert bm.get_max_raise_to(p) == 500  # All-in


class TestApplyAction:
    """Tests for applying actions."""

    def test_fold(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0)
        action = bm.apply_action(p, "fold")
        assert p.is_folded
        assert action.action_type == "fold"
        assert action.player_index == 0

    def test_check(self) -> None:
        bm = BettingManager()
        bm.new_round(0)
        p = _player(0)
        action = bm.apply_action(p, "check")
        assert not p.is_folded
        assert action.action_type == "check"
        assert p.chips == 1000  # No change

    def test_call(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        action = bm.apply_action(p, "call")
        assert p.chips == 980
        assert p.current_bet == 20
        assert action.amount == 20

    def test_call_all_in(self) -> None:
        bm = BettingManager()
        bm.new_round(100)
        p = _player(0, chips=30)
        action = bm.apply_action(p, "call")
        assert p.chips == 0
        assert p.is_all_in
        assert action.amount == 30

    def test_raise(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        action = bm.apply_action(p, "raise", amount=60)
        assert p.chips == 940
        assert p.current_bet == 60
        assert bm.current_bet == 60
        assert bm.last_raiser == 0

    def test_raise_all_in(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=50)
        action = bm.apply_action(p, "raise", amount=50)
        assert p.chips == 0
        assert p.is_all_in
        assert p.current_bet == 50

    def test_raise_updates_min_raise(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        bm.apply_action(p, "raise", amount=80)
        # Raise from 20 to 80 = increment of 60
        assert bm.min_raise == 60
        # Next min raise to = 80 + 60 = 140
        assert bm.get_min_raise_to(_player(1, chips=1000)) == 140

    def test_invalid_action_raises(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        with pytest.raises(InvalidActionError, match="Invalid action 'check'"):
            bm.apply_action(p, "check")

    def test_raise_without_amount_raises(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        with pytest.raises(InvalidActionError, match="Raise requires an amount"):
            bm.apply_action(p, "raise")

    def test_raise_below_minimum_raises(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        with pytest.raises(InvalidActionError, match="below minimum"):
            bm.apply_action(p, "raise", amount=30)

    def test_raise_above_max_raises(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=100)
        with pytest.raises(InvalidActionError, match="exceeds max"):
            bm.apply_action(p, "raise", amount=200)

    def test_all_in_below_min_raise_is_valid(self) -> None:
        """Player can go all-in even if amount is below min raise."""
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=30)
        action = bm.apply_action(p, "raise", amount=30)
        assert p.is_all_in
        assert p.current_bet == 30

    def test_actions_recorded(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p = _player(0, chips=1000)
        bm.apply_action(p, "call")
        assert len(bm.actions_this_round) == 1
        assert bm.actions_this_round[0].action_type == "call"

    def test_raise_resets_acted_set(self) -> None:
        """After a raise, all other players need to act again."""
        bm = BettingManager()
        bm.new_round(20)

        p0 = _player(0, chips=1000)
        p1 = _player(1, chips=1000)
        p2 = _player(2, chips=1000)

        bm.apply_action(p0, "call")
        bm.apply_action(p1, "raise", amount=60)
        # p0 needs to act again
        assert not bm.is_round_complete([p0, p1, p2])


class TestRoundCompletion:
    """Tests for betting round completion detection."""

    def test_not_complete_initially(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        players = [_player(0), _player(1), _player(2)]
        assert not bm.is_round_complete(players)

    def test_complete_when_all_check(self) -> None:
        bm = BettingManager()
        bm.new_round(0)
        p0 = _player(0)
        p1 = _player(1)
        p2 = _player(2)

        bm.apply_action(p0, "check")
        bm.apply_action(p1, "check")
        bm.apply_action(p2, "check")

        assert bm.is_round_complete([p0, p1, p2])

    def test_complete_when_all_call(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p0 = _player(0, current_bet=20)  # BB
        p1 = _player(1)
        p2 = _player(2)

        bm.apply_action(p1, "call")
        bm.apply_action(p2, "call")
        bm.apply_action(p0, "check")

        assert bm.is_round_complete([p0, p1, p2])

    def test_not_complete_after_raise(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p0 = _player(0, chips=1000)
        p1 = _player(1, chips=1000)

        bm.apply_action(p0, "raise", amount=60)
        assert not bm.is_round_complete([p0, p1])

    def test_complete_after_fold_to_one(self) -> None:
        bm = BettingManager()
        bm.new_round(20)
        p0 = _player(0)
        p1 = _player(1)
        p2 = _player(2)

        bm.apply_action(p0, "fold")
        bm.apply_action(p1, "fold")

        assert bm.is_round_complete([p0, p1, p2])

    def test_complete_when_only_all_in_and_one_active(self) -> None:
        bm = BettingManager()
        bm.new_round(0)
        p0 = _player(0, is_all_in=True)
        p1 = _player(1)

        bm.apply_action(p1, "check")

        assert bm.is_round_complete([p0, p1])


class TestHandOver:
    """Tests for hand-over detection."""

    def test_not_over_with_multiple_active(self) -> None:
        bm = BettingManager()
        players = [_player(0), _player(1)]
        assert not bm.is_hand_over(players)

    def test_over_when_one_remains(self) -> None:
        bm = BettingManager()
        players = [_player(0, is_folded=True), _player(1)]
        assert bm.is_hand_over(players)

    def test_over_when_all_fold_except_one(self) -> None:
        bm = BettingManager()
        players = [
            _player(0, is_folded=True),
            _player(1, is_folded=True),
            _player(2),
        ]
        assert bm.is_hand_over(players)


class TestSkipToShowdown:
    """Tests for skip-to-showdown detection."""

    def test_no_skip_with_multiple_actionable(self) -> None:
        bm = BettingManager()
        players = [_player(0), _player(1)]
        assert not bm.should_skip_to_showdown(players)

    def test_skip_when_all_but_one_all_in(self) -> None:
        bm = BettingManager()
        players = [
            _player(0, is_all_in=True),
            _player(1, is_all_in=True),
            _player(2),
        ]
        assert bm.should_skip_to_showdown(players)

    def test_skip_when_all_all_in(self) -> None:
        bm = BettingManager()
        players = [
            _player(0, is_all_in=True),
            _player(1, is_all_in=True),
        ]
        assert bm.should_skip_to_showdown(players)

    def test_no_skip_when_only_one_active(self) -> None:
        """Only one not-folded player — hand is over, don't skip to showdown."""
        bm = BettingManager()
        players = [_player(0, is_folded=True), _player(1)]
        assert not bm.should_skip_to_showdown(players)
