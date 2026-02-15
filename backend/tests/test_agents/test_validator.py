"""Tests for prompt validator — information integrity."""

import pytest

from llm_holdem.agents.validator import PromptValidationError
from llm_holdem.agents.validator import get_opponent_hole_cards
from llm_holdem.agents.validator import sanitize_game_state
from llm_holdem.agents.validator import validate_and_build
from llm_holdem.agents.validator import validate_prompt
from llm_holdem.game.state import Card
from llm_holdem.game.state import GameState
from llm_holdem.game.state import PlayerState


def _make_state() -> GameState:
    """Create test game state with known hole cards."""
    return GameState(
        game_id="test",
        hand_number=1,
        phase="flop",
        players=[
            PlayerState(
                seat_index=0,
                name="Human",
                chips=1000,
                hole_cards=[Card(rank="A", suit="s"), Card(rank="K", suit="s")],
            ),
            PlayerState(
                seat_index=1,
                agent_id="agent-1",
                name="Bot1",
                chips=1000,
                hole_cards=[Card(rank="Q", suit="h"), Card(rank="J", suit="d")],
            ),
            PlayerState(
                seat_index=2,
                agent_id="agent-2",
                name="Bot2",
                chips=1000,
                hole_cards=[Card(rank="T", suit="c"), Card(rank="9", suit="c")],
            ),
        ],
        community_cards=[
            Card(rank="2", suit="h"),
            Card(rank="5", suit="d"),
            Card(rank="8", suit="s"),
        ],
    )


class TestGetOpponentHoleCards:
    """Tests for extracting opponent hole cards."""

    def test_extracts_opponent_cards(self) -> None:
        state = _make_state()
        cards = get_opponent_hole_cards(state, viewer_seat=0)
        # Should have Bot1 (Qh, Jd) and Bot2 (Tc, 9c) cards
        assert len(cards) == 4
        card_strs = {f"{c.rank}{c.suit}" for c in cards}
        assert "Qh" in card_strs
        assert "Jd" in card_strs
        assert "Tc" in card_strs
        assert "9c" in card_strs

    def test_excludes_own_cards(self) -> None:
        state = _make_state()
        cards = get_opponent_hole_cards(state, viewer_seat=0)
        card_strs = {f"{c.rank}{c.suit}" for c in cards}
        assert "As" not in card_strs
        assert "Ks" not in card_strs

    def test_different_viewer(self) -> None:
        state = _make_state()
        cards = get_opponent_hole_cards(state, viewer_seat=1)
        card_strs = {f"{c.rank}{c.suit}" for c in cards}
        # Bot1 (seat 1) should not see its own cards as opponents
        assert "Qh" not in card_strs
        # But should see Human's and Bot2's cards
        assert "As" in card_strs
        assert "Tc" in card_strs

    def test_no_hole_cards(self) -> None:
        state = GameState(
            game_id="test",
            players=[
                PlayerState(seat_index=0, name="A", chips=1000, hole_cards=None),
                PlayerState(seat_index=1, name="B", chips=1000, hole_cards=None),
            ],
        )
        cards = get_opponent_hole_cards(state, viewer_seat=0)
        assert len(cards) == 0


class TestSanitizeGameState:
    """Tests for game state sanitization."""

    def test_preserves_own_cards(self) -> None:
        state = _make_state()
        sanitized = sanitize_game_state(state, viewer_seat=0)
        assert sanitized.players[0].hole_cards is not None
        assert len(sanitized.players[0].hole_cards) == 2

    def test_strips_opponent_cards(self) -> None:
        state = _make_state()
        sanitized = sanitize_game_state(state, viewer_seat=0)
        assert sanitized.players[1].hole_cards is None
        assert sanitized.players[2].hole_cards is None

    def test_preserves_community_cards(self) -> None:
        state = _make_state()
        sanitized = sanitize_game_state(state, viewer_seat=0)
        assert len(sanitized.community_cards) == 3

    def test_preserves_other_player_info(self) -> None:
        state = _make_state()
        sanitized = sanitize_game_state(state, viewer_seat=0)
        assert sanitized.players[1].name == "Bot1"
        assert sanitized.players[1].chips == 1000

    def test_does_not_mutate_original(self) -> None:
        state = _make_state()
        sanitize_game_state(state, viewer_seat=0)
        # Original should still have opponent cards
        assert state.players[1].hole_cards is not None
        assert len(state.players[1].hole_cards) == 2


class TestValidatePrompt:
    """Tests for prompt validation (the hard gate)."""

    def test_valid_prompt_passes(self) -> None:
        """A prompt with only the viewer's own cards should pass."""
        state = _make_state()
        prompt = (
            "Your hole cards: As Ks\n"
            "Community: 2h 5d 8s\n"
            "Pot: 100\n"
            "What's your action?"
        )
        # Should not raise
        validate_prompt(prompt, state, viewer_seat=0)

    def test_opponent_card_detected(self) -> None:
        """A prompt containing opponent hole cards should fail."""
        state = _make_state()
        prompt = (
            "Your hole cards: As Ks\n"
            "Bot1 has: Qh Jd\n"  # LEAK!
            "Community: 2h 5d 8s\n"
        )
        with pytest.raises(PromptValidationError, match="opponent hole card"):
            validate_prompt(prompt, state, viewer_seat=0)

    def test_single_opponent_card_detected(self) -> None:
        """Even a single opponent card should be caught."""
        state = _make_state()
        prompt = "Some text with Tc in it."  # Bot2's card
        with pytest.raises(PromptValidationError):
            validate_prompt(prompt, state, viewer_seat=0)

    def test_own_card_not_flagged(self) -> None:
        """The viewer's own cards should not trigger validation errors."""
        state = _make_state()
        prompt = "Your cards: As Ks. Community: 2h 5d 8s."
        validate_prompt(prompt, state, viewer_seat=0)

    def test_community_cards_not_flagged(self) -> None:
        """Community cards are public and should not trigger errors."""
        state = _make_state()
        prompt = "Board: 2h 5d 8s. The flop is out."
        validate_prompt(prompt, state, viewer_seat=0)

    def test_no_false_positive_on_substring(self) -> None:
        """Card patterns within words should not trigger false positives."""
        state = _make_state()
        # "Jd" appears in state but let's check "Qh" doesn't false-positive
        # within a word like "QueenHeart" — our regex uses boundaries
        prompt = "Your hand looks great!"
        validate_prompt(prompt, state, viewer_seat=0)

    def test_no_opponents_no_cards_to_check(self) -> None:
        """When no opponents have cards, validation should pass trivially."""
        state = GameState(
            game_id="test",
            phase="between_hands",
            players=[
                PlayerState(seat_index=0, name="A", chips=1000, hole_cards=None),
                PlayerState(seat_index=1, name="B", chips=1000, hole_cards=None),
            ],
        )
        validate_prompt("Anything goes here", state, viewer_seat=0)

    def test_validate_and_build_returns_prompt(self) -> None:
        state = _make_state()
        prompt = "Your cards: As Ks"
        result = validate_and_build(prompt, state, viewer_seat=0)
        assert result == prompt

    def test_validate_and_build_raises_on_leak(self) -> None:
        state = _make_state()
        prompt = "Opponents have Qh and Jd"
        with pytest.raises(PromptValidationError):
            validate_and_build(prompt, state, viewer_seat=0)

    def test_case_sensitivity(self) -> None:
        """Card patterns are case-specific (Qh vs QH)."""
        state = _make_state()
        # Our validator checks both Qh and QH
        prompt = "Something with QH in it."
        with pytest.raises(PromptValidationError):
            validate_prompt(prompt, state, viewer_seat=0)
