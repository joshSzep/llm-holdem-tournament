"""Tests for action agent — with mocked LLM responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai.usage import Usage

from llm_holdem.agents.action_agent import _validate_action, get_ai_action
from llm_holdem.agents.schemas import AgentProfile, PokerAction
from llm_holdem.game.state import Card, GameState, PlayerState


def _make_profile() -> AgentProfile:
    """Create a test agent profile."""
    return AgentProfile(
        id="test-agent",
        name="Test Agent",
        avatar="test.png",
        backstory="A test agent.",
        model="openai:gpt-4o",
        provider="openai",
        play_style="aggressive",
        talk_style="trash-talker",
        risk_tolerance="reckless",
        bluffing_tendency="frequent",
        action_system_prompt="You are a poker player.",
        chat_system_prompt="You talk trash.",
    )


def _make_game_state() -> GameState:
    """Create a test game state."""
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
                agent_id="test-agent",
                name="Test Agent",
                chips=1000,
                hole_cards=[Card(rank="Q", suit="h"), Card(rank="J", suit="h")],
            ),
        ],
        community_cards=[
            Card(rank="T", suit="s"),
            Card(rank="9", suit="s"),
            Card(rank="2", suit="d"),
        ],
    )


# ─── Action Validation Tests ─────────────────────────


class TestValidateAction:
    """Tests for _validate_action."""

    def test_valid_fold(self) -> None:
        action = PokerAction(action="fold")
        assert _validate_action(action, ["fold", "check", "raise"], None, None) is None

    def test_valid_check(self) -> None:
        action = PokerAction(action="check")
        assert _validate_action(action, ["fold", "check"], None, None) is None

    def test_valid_call(self) -> None:
        action = PokerAction(action="call")
        assert _validate_action(action, ["fold", "call", "raise"], None, None) is None

    def test_valid_raise(self) -> None:
        action = PokerAction(action="raise", amount=100)
        assert _validate_action(action, ["fold", "call", "raise"], 40, 1000) is None

    def test_invalid_action_type(self) -> None:
        action = PokerAction(action="check")
        error = _validate_action(action, ["fold", "call"], None, None)
        assert error is not None
        assert "not valid" in error

    def test_raise_without_amount(self) -> None:
        action = PokerAction(action="raise")
        error = _validate_action(action, ["fold", "raise"], 40, 1000)
        assert error is not None
        assert "amount" in error.lower()

    def test_raise_below_minimum(self) -> None:
        action = PokerAction(action="raise", amount=20)
        error = _validate_action(action, ["fold", "raise"], 40, 1000)
        assert error is not None
        assert "below minimum" in error

    def test_raise_above_maximum(self) -> None:
        action = PokerAction(action="raise", amount=2000)
        error = _validate_action(action, ["fold", "raise"], 40, 1000)
        assert error is not None
        assert "exceeds maximum" in error


# ─── Mocked LLM Tests ────────────────────────────────


class TestGetAiAction:
    """Tests for get_ai_action with mocked LLM."""

    @pytest.fixture
    def mock_agent_result(self) -> MagicMock:
        """Create a mock Pydantic AI result."""
        result = MagicMock()
        result.response = PokerAction(action="call", reasoning="Good pot odds")
        result.usage = MagicMock(return_value=Usage(input_tokens=100, output_tokens=20, requests=1))
        return result

    async def test_successful_action(self, mock_agent_result: MagicMock) -> None:
        """Agent returns a valid action on first try."""
        with patch("llm_holdem.agents.action_agent._create_action_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value=mock_agent_result)
            mock_create.return_value = mock_agent

            action, usage = await get_ai_action(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                valid_actions=["fold", "call", "raise"],
                call_amount=20,
            )

            assert action.action == "call"
            assert usage.input_tokens == 100
            assert usage.output_tokens == 20

    async def test_fallback_on_validation_error(self) -> None:
        """If prompt validation fails, falls back to check/fold."""
        state = _make_game_state()
        # Make seat 1's hole cards appear in the prompt by corrupting the builder
        # Actually, this is hard to trigger from outside; let's just patch validate_prompt
        with patch(
            "llm_holdem.agents.action_agent.validate_prompt",
            side_effect=Exception("Validation failed"),
        ):
            from llm_holdem.agents.validator import PromptValidationError

            with patch(
                "llm_holdem.agents.action_agent.validate_prompt",
                side_effect=PromptValidationError("leak detected"),
            ):
                action, usage = await get_ai_action(
                    profile=_make_profile(),
                    game_state=state,
                    seat_index=1,
                    valid_actions=["fold", "check", "raise"],
                )

                assert action.action == "check"  # Falls back to check
                assert "validation" in action.reasoning.lower()

    async def test_fallback_on_all_retries_exhausted(self) -> None:
        """When all LLM retries fail, falls back to safe action."""
        with patch("llm_holdem.agents.action_agent._create_action_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=Exception("LLM down"))
            mock_create.return_value = mock_agent

            action, usage = await get_ai_action(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                valid_actions=["fold", "call"],
            )

            # Should fall back to fold (no "check" in valid actions)
            assert action.action == "fold"
            assert "failed" in action.reasoning.lower()

    async def test_fallback_to_check_when_available(self) -> None:
        """Fallback prefers check over fold."""
        with patch("llm_holdem.agents.action_agent._create_action_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=Exception("LLM down"))
            mock_create.return_value = mock_agent

            action, _ = await get_ai_action(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                valid_actions=["fold", "check", "raise"],
            )

            assert action.action == "check"

    async def test_retry_on_invalid_action(self) -> None:
        """Agent retries when LLM returns an invalid action."""
        invalid_result = MagicMock()
        invalid_result.response = PokerAction(action="raise", amount=5)  # Below min
        invalid_result.usage = MagicMock(return_value=Usage(input_tokens=50, output_tokens=10, requests=1))

        valid_result = MagicMock()
        valid_result.response = PokerAction(action="call", reasoning="OK fine")
        valid_result.usage = MagicMock(return_value=Usage(input_tokens=80, output_tokens=15, requests=1))

        with patch("llm_holdem.agents.action_agent._create_action_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=[invalid_result, valid_result])
            mock_create.return_value = mock_agent

            action, usage = await get_ai_action(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                valid_actions=["fold", "call", "raise"],
                min_raise_to=40,
                max_raise_to=1000,
            )

            assert action.action == "call"
            # Usage should be accumulated
            assert usage.input_tokens == 130  # 50 + 80
            assert usage.output_tokens == 25  # 10 + 15

    async def test_prompt_does_not_contain_opponent_cards(self) -> None:
        """The prompt sent to the LLM should not contain opponent hole cards."""
        captured_prompt = None

        async def capture_run(prompt: str, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            result = MagicMock()
            result.response = PokerAction(action="check")
            result.usage = MagicMock(return_value=Usage(input_tokens=10, output_tokens=5, requests=1))
            return result

        with patch("llm_holdem.agents.action_agent._create_action_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = capture_run
            mock_create.return_value = mock_agent

            await get_ai_action(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                valid_actions=["fold", "check"],
            )

            assert captured_prompt is not None
            # Seat 0's cards (As, Ks) should NOT appear
            assert "Hole cards: As" not in captured_prompt
            assert "Hole cards: Ks" not in captured_prompt
