"""Tests for chat agent — with mocked LLM responses."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic_ai.usage import Usage

from llm_holdem.agents.chat_agent import (
    CHAT_COOLDOWN_SECONDS,
    get_chat_response,
    should_agent_speak,
    trigger_chat_responses,
)
from llm_holdem.agents.schemas import AgentProfile, ChatResponse
from llm_holdem.game.state import Card, GameState, PlayerState


def _make_profile(
    agent_id: str = "test-agent",
    name: str = "Test Agent",
    talk_style: str = "trash-talker",
) -> AgentProfile:
    """Create a test agent profile."""
    return AgentProfile(
        id=agent_id,
        name=name,
        avatar="test.png",
        backstory="A test agent.",
        model="openai:gpt-4o",
        provider="openai",
        play_style="aggressive",
        talk_style=talk_style,
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


# ─── should_agent_speak Tests ───────────────────────


class TestShouldAgentSpeak:
    """Tests for should_agent_speak."""

    def test_trash_talker_high_probability(self) -> None:
        """Trash-talkers should speak frequently (seeded random)."""
        profile = _make_profile(talk_style="trash-talker")
        # Run many times and check the proportion is in the ballpark
        spoke = sum(
            1
            for _ in range(1000)
            if should_agent_speak(profile, "showdown")
        )
        # Expected ~70% for trash-talker, accept wide range
        assert spoke > 500, f"Trash-talker spoke {spoke}/1000 times, expected >500"

    def test_silent_low_probability(self) -> None:
        """Silent players should speak rarely."""
        profile = _make_profile(talk_style="silent and observant")
        spoke = sum(
            1
            for _ in range(1000)
            if should_agent_speak(profile, "big_pot")
        )
        # Expected ~10% for silent, accept generous range
        assert spoke < 300, f"Silent agent spoke {spoke}/1000 times, expected <300"

    def test_cooldown_prevents_speaking(self) -> None:
        """Agent should not speak if they spoke recently."""
        profile = _make_profile()
        # last_spoke_at is very recent
        last_spoke_at = time.time() - 1.0  # 1 second ago
        spoke_count = sum(
            1
            for _ in range(100)
            if should_agent_speak(profile, "showdown", last_spoke_at)
        )
        assert spoke_count == 0

    def test_cooldown_expired(self) -> None:
        """Agent can speak again after cooldown expires."""
        profile = _make_profile(talk_style="trash-talker")
        # last_spoke_at is long ago
        last_spoke_at = time.time() - CHAT_COOLDOWN_SECONDS - 5.0
        spoke = sum(
            1
            for _ in range(1000)
            if should_agent_speak(profile, "showdown", last_spoke_at)
        )
        # Should speak at normal rate
        assert spoke > 400


# ─── get_chat_response Tests ────────────────────────


class TestGetChatResponse:
    """Tests for get_chat_response with mocked LLM."""

    async def test_returns_chat_message(self) -> None:
        """Successful chat response."""
        mock_result = MagicMock()
        mock_result.response = ChatResponse(message="Nice hand!")
        mock_result.usage = Usage(input_tokens=50, output_tokens=10, requests=1)

        with patch("llm_holdem.agents.chat_agent._create_chat_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            response, usage = await get_chat_response(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                trigger_event="showdown",
                event_description="Player showed a flush",
            )

            assert response.message == "Nice hand!"
            assert usage.input_tokens == 50

    async def test_returns_none_on_failure(self) -> None:
        """Returns None message on LLM failure."""
        with patch("llm_holdem.agents.chat_agent._create_chat_agent") as mock_create:
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(side_effect=Exception("LLM error"))
            mock_create.return_value = mock_agent

            response, usage = await get_chat_response(
                profile=_make_profile(),
                game_state=_make_game_state(),
                seat_index=1,
                trigger_event="showdown",
                event_description="Someone won",
            )

            assert response.message is None
            assert usage.input_tokens == 0


# ─── trigger_chat_responses Tests ────────────────────


class TestTriggerChatResponses:
    """Tests for trigger_chat_responses."""

    async def test_triggers_multiple_agents(self) -> None:
        """Multiple agents can respond concurrently."""
        profiles = [
            (_make_profile("agent-1", "Agent 1"), 1),
            (_make_profile("agent-2", "Agent 2"), 2),
        ]

        def make_mock_result(msg: str) -> MagicMock:
            result = MagicMock()
            result.response = ChatResponse(message=msg)
            result.usage = Usage(input_tokens=30, output_tokens=5, requests=1)
            return result

        with patch("llm_holdem.agents.chat_agent.get_chat_response") as mock_get:
            mock_get.side_effect = [
                (ChatResponse(message="Yo!"), Usage(input_tokens=30, output_tokens=5, requests=1)),
                (ChatResponse(message="Hey!"), Usage(input_tokens=35, output_tokens=6, requests=1)),
            ]

            with patch("llm_holdem.agents.chat_agent.should_agent_speak", return_value=True):
                results = await trigger_chat_responses(
                    profiles_and_seats=profiles,
                    game_state=_make_game_state(),
                    trigger_event="showdown",
                    event_description="Big hand",
                )

            assert len(results) == 2
            messages = [r[2] for r in results]  # (agent_id, seat, message, usage)
            assert "Yo!" in messages
            assert "Hey!" in messages

    async def test_respects_max_speakers(self) -> None:
        """Only max_speakers agents can respond per event."""
        profiles = [
            (_make_profile(f"agent-{i}", f"Agent {i}"), i)
            for i in range(6)
        ]

        with patch("llm_holdem.agents.chat_agent.get_chat_response") as mock_get:
            mock_get.return_value = (
                ChatResponse(message="Hi!"),
                Usage(input_tokens=20, output_tokens=5, requests=1),
            )
            with patch("llm_holdem.agents.chat_agent.should_agent_speak", return_value=True):
                results = await trigger_chat_responses(
                    profiles_and_seats=profiles,
                    game_state=_make_game_state(),
                    trigger_event="showdown",
                    event_description="Final hand",
                    max_speakers=2,
                )

            # At most 2 speakers
            assert len(results) <= 2

    async def test_filters_none_messages(self) -> None:
        """Results with None messages are filtered out."""
        profiles = [
            (_make_profile("agent-1", "Agent 1"), 1),
        ]

        with patch("llm_holdem.agents.chat_agent.get_chat_response") as mock_get:
            mock_get.return_value = (
                ChatResponse(message=None),
                Usage(input_tokens=20, output_tokens=5, requests=1),
            )
            with patch("llm_holdem.agents.chat_agent.should_agent_speak", return_value=True):
                results = await trigger_chat_responses(
                    profiles_and_seats=profiles,
                    game_state=_make_game_state(),
                    trigger_event="showdown",
                    event_description="Showdown",
                )

            assert len(results) == 0

    async def test_no_speakers_when_none_want_to_speak(self) -> None:
        """No results when all agents decline to speak."""
        profiles = [
            (_make_profile("agent-1", "Agent 1"), 1),
            (_make_profile("agent-2", "Agent 2"), 2),
        ]

        with patch("llm_holdem.agents.chat_agent.should_agent_speak", return_value=False):
            results = await trigger_chat_responses(
                profiles_and_seats=profiles,
                game_state=_make_game_state(),
                trigger_event="showdown",
                event_description="Nothing",
            )

            assert len(results) == 0
