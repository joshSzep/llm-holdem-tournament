"""Agent registry — loads profiles and filters by available providers."""

import logging

from llm_holdem.agents.profiles import ALL_AGENT_PROFILES
from llm_holdem.agents.profiles import AGENT_PROFILES_BY_ID
from llm_holdem.agents.schemas import AgentProfile
from llm_holdem.config import Settings
from llm_holdem.config import get_settings

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry of available AI agents, filtered by configured API keys.

    Loads all 30+ agent profiles and exposes only those whose LLM provider
    has a configured API key (or is locally available like Ollama).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the registry.

        Args:
            settings: Application settings. Uses default if not provided.
        """
        self._settings = settings or get_settings()
        self._all_profiles = list(ALL_AGENT_PROFILES)
        self._available_providers: set[str] = set()
        self._available_profiles: list[AgentProfile] = []
        self._refresh()

    def _refresh(self) -> None:
        """Refresh available providers and filter profiles."""
        self._available_providers = set(self._settings.available_providers())
        self._available_profiles = [
            p for p in self._all_profiles
            if p.provider in self._available_providers
        ]
        logger.info(
            "Agent registry: %d/%d agents available (providers: %s)",
            len(self._available_profiles),
            len(self._all_profiles),
            ", ".join(sorted(self._available_providers)) or "none",
        )

    @property
    def available_providers(self) -> set[str]:
        """Set of providers with configured API keys."""
        return set(self._available_providers)

    @property
    def all_profiles(self) -> list[AgentProfile]:
        """All agent profiles, regardless of provider availability."""
        return list(self._all_profiles)

    @property
    def available_profiles(self) -> list[AgentProfile]:
        """Agent profiles filtered to only available providers."""
        return list(self._available_profiles)

    def get_profile(self, agent_id: str) -> AgentProfile | None:
        """Get a specific agent profile by ID.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            The agent profile, or None if not found.
        """
        return AGENT_PROFILES_BY_ID.get(agent_id)

    def get_available_profile(self, agent_id: str) -> AgentProfile | None:
        """Get a profile by ID, but only if its provider is available.

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            The agent profile if available, or None.
        """
        profile = self.get_profile(agent_id)
        if profile and profile.provider in self._available_providers:
            return profile
        return None

    def get_profiles_by_provider(self, provider: str) -> list[AgentProfile]:
        """Get all available profiles for a specific provider.

        Args:
            provider: The provider key (e.g., 'openai', 'anthropic').

        Returns:
            List of available profiles for that provider.
        """
        return [
            p for p in self._available_profiles
            if p.provider == provider
        ]

    def is_agent_available(self, agent_id: str) -> bool:
        """Check if an agent is available (provider key configured).

        Args:
            agent_id: The agent's unique identifier.

        Returns:
            True if the agent's provider is configured.
        """
        profile = self.get_profile(agent_id)
        return profile is not None and profile.provider in self._available_providers
