"""Tests for agent profiles and schemas."""

import pytest

from llm_holdem.agents.profiles import ALL_AGENT_PROFILES
from llm_holdem.agents.profiles import AGENT_PROFILES_BY_ID
from llm_holdem.agents.schemas import AgentProfile
from llm_holdem.agents.schemas import ChatResponse
from llm_holdem.agents.schemas import PokerAction


# ─── PokerAction Tests ────────────────────────────────


class TestPokerAction:
    """Tests for PokerAction model."""

    def test_fold_action(self) -> None:
        action = PokerAction(action="fold", reasoning="Bad hand")
        assert action.action == "fold"
        assert action.amount is None
        assert action.reasoning == "Bad hand"

    def test_check_action(self) -> None:
        action = PokerAction(action="check")
        assert action.action == "check"
        assert action.reasoning == ""

    def test_call_action(self) -> None:
        action = PokerAction(action="call", reasoning="Pot odds")
        assert action.action == "call"

    def test_raise_with_amount(self) -> None:
        action = PokerAction(action="raise", amount=200, reasoning="Bluffing")
        assert action.action == "raise"
        assert action.amount == 200

    def test_raise_without_amount(self) -> None:
        action = PokerAction(action="raise")
        assert action.amount is None

    def test_serialization_roundtrip(self) -> None:
        action = PokerAction(action="raise", amount=500, reasoning="Strong hand")
        data = action.model_dump()
        restored = PokerAction.model_validate(data)
        assert restored == action

    def test_invalid_action_type(self) -> None:
        with pytest.raises(Exception):
            PokerAction(action="bet")  # type: ignore[arg-type]


# ─── ChatResponse Tests ──────────────────────────────


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_with_message(self) -> None:
        resp = ChatResponse(message="Nice bluff!")
        assert resp.message == "Nice bluff!"

    def test_none_message(self) -> None:
        resp = ChatResponse(message=None)
        assert resp.message is None

    def test_default_is_none(self) -> None:
        resp = ChatResponse()
        assert resp.message is None


# ─── AgentProfile Tests ──────────────────────────────


class TestAgentProfile:
    """Tests for AgentProfile model."""

    def test_complete_profile(self) -> None:
        profile = AgentProfile(
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
        assert profile.id == "test-agent"
        assert profile.provider == "openai"

    def test_serialization(self) -> None:
        profile = AgentProfile(
            id="x", name="X", avatar="x.png", backstory="X",
            model="openai:gpt-4o", provider="openai",
            play_style="tight", talk_style="silent",
            risk_tolerance="cautious", bluffing_tendency="rare",
            action_system_prompt="act", chat_system_prompt="chat",
        )
        data = profile.model_dump()
        restored = AgentProfile.model_validate(data)
        assert restored.id == profile.id


# ─── Profile Collection Tests ────────────────────────


class TestProfileCollection:
    """Tests for the 30+ agent profile definitions."""

    def test_at_least_30_profiles(self) -> None:
        assert len(ALL_AGENT_PROFILES) >= 30

    def test_all_unique_ids(self) -> None:
        ids = [p.id for p in ALL_AGENT_PROFILES]
        assert len(ids) == len(set(ids)), "Duplicate agent IDs found"

    def test_all_unique_names(self) -> None:
        names = [p.name for p in ALL_AGENT_PROFILES]
        assert len(names) == len(set(names)), "Duplicate agent names found"

    def test_all_have_required_fields(self) -> None:
        for profile in ALL_AGENT_PROFILES:
            assert profile.id, f"Profile missing id"
            assert profile.name, f"Profile {profile.id} missing name"
            assert profile.avatar, f"Profile {profile.id} missing avatar"
            assert profile.backstory, f"Profile {profile.id} missing backstory"
            assert profile.model, f"Profile {profile.id} missing model"
            assert profile.provider, f"Profile {profile.id} missing provider"
            assert profile.action_system_prompt, f"Profile {profile.id} missing action prompt"
            assert profile.chat_system_prompt, f"Profile {profile.id} missing chat prompt"

    def test_model_format(self) -> None:
        """All models should have provider:model format."""
        for profile in ALL_AGENT_PROFILES:
            assert ":" in profile.model, (
                f"Profile {profile.id} model '{profile.model}' missing provider prefix"
            )

    def test_provider_matches_model_prefix(self) -> None:
        """Provider field should match the model string prefix."""
        for profile in ALL_AGENT_PROFILES:
            model_provider = profile.model.split(":")[0]
            assert model_provider == profile.provider, (
                f"Profile {profile.id}: provider '{profile.provider}' "
                f"doesn't match model prefix '{model_provider}'"
            )

    def test_lookup_dict_matches(self) -> None:
        assert len(AGENT_PROFILES_BY_ID) == len(ALL_AGENT_PROFILES)
        for profile in ALL_AGENT_PROFILES:
            assert AGENT_PROFILES_BY_ID[profile.id] is profile

    def test_multiple_providers_represented(self) -> None:
        providers = {p.provider for p in ALL_AGENT_PROFILES}
        assert len(providers) >= 5, f"Expected 5+ providers, got {providers}"

    def test_action_prompt_contains_personality(self) -> None:
        """Action prompts should reference the agent's traits."""
        for profile in ALL_AGENT_PROFILES:
            assert profile.name in profile.action_system_prompt
            assert profile.play_style in profile.action_system_prompt

    def test_chat_prompt_contains_personality(self) -> None:
        """Chat prompts should reference the agent's traits."""
        for profile in ALL_AGENT_PROFILES:
            assert profile.name in profile.chat_system_prompt
            assert profile.talk_style in profile.chat_system_prompt
