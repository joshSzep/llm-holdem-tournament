"""Tests for agent registry."""


from llm_holdem.agents.profiles import ALL_AGENT_PROFILES
from llm_holdem.agents.registry import AgentRegistry
from llm_holdem.config import Settings


def _make_settings(**overrides: str) -> Settings:
    """Create a Settings instance with specific API keys."""
    defaults = {
        "openai_api_key": "",
        "anthropic_api_key": "",
        "google_api_key": "",
        "groq_api_key": "",
        "mistral_api_key": "",
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_no_keys_only_ollama(self) -> None:
        """With no API keys, only Ollama agents should be available."""
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        assert "ollama" in registry.available_providers
        for p in registry.available_profiles:
            assert p.provider == "ollama"

    def test_openai_key_enables_openai_agents(self) -> None:
        settings = _make_settings(openai_api_key="sk-test")
        registry = AgentRegistry(settings=settings)
        assert "openai" in registry.available_providers
        openai_agents = registry.get_profiles_by_provider("openai")
        assert len(openai_agents) > 0
        for a in openai_agents:
            assert a.provider == "openai"

    def test_multiple_keys(self) -> None:
        settings = _make_settings(
            openai_api_key="sk-test",
            anthropic_api_key="sk-ant-test",
        )
        registry = AgentRegistry(settings=settings)
        assert "openai" in registry.available_providers
        assert "anthropic" in registry.available_providers
        # All profiles are openai, so available count equals openai count
        assert len(registry.available_profiles) == len(
            registry.get_profiles_by_provider("openai")
        )

    def test_all_keys_all_agents(self) -> None:
        settings = _make_settings(
            openai_api_key="sk-test",
            anthropic_api_key="sk-ant-test",
            google_api_key="test-google",
            groq_api_key="gsk-test",
            mistral_api_key="test-mistral",
        )
        registry = AgentRegistry(settings=settings)
        assert len(registry.available_profiles) == len(ALL_AGENT_PROFILES)

    def test_get_profile_by_id(self) -> None:
        settings = _make_settings(openai_api_key="sk-test")
        registry = AgentRegistry(settings=settings)
        profile = registry.get_profile("tight-tony")
        assert profile is not None
        assert profile.name == "Tight Tony"

    def test_get_profile_nonexistent(self) -> None:
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        assert registry.get_profile("nonexistent") is None

    def test_get_available_profile(self) -> None:
        settings = _make_settings(openai_api_key="sk-test")
        registry = AgentRegistry(settings=settings)
        # OpenAI agent should be available
        profile = registry.get_available_profile("tight-tony")
        assert profile is not None
        # All agents are openai, so bluff-betty is also available with openai key
        profile = registry.get_available_profile("bluff-betty")
        assert profile is not None

    def test_get_available_profile_no_key(self) -> None:
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        # Without openai key, no agents are available
        profile = registry.get_available_profile("tight-tony")
        assert profile is None

    def test_is_agent_available(self) -> None:
        settings = _make_settings(openai_api_key="sk-test")
        registry = AgentRegistry(settings=settings)
        assert registry.is_agent_available("tight-tony") is True
        assert registry.is_agent_available("bluff-betty") is True
        assert registry.is_agent_available("nonexistent") is False

    def test_is_agent_available_no_key(self) -> None:
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        assert registry.is_agent_available("tight-tony") is False

    def test_all_profiles_returns_all(self) -> None:
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        assert len(registry.all_profiles) == len(ALL_AGENT_PROFILES)

    def test_get_profiles_by_provider_empty(self) -> None:
        settings = _make_settings()
        registry = AgentRegistry(settings=settings)
        assert registry.get_profiles_by_provider("openai") == []
