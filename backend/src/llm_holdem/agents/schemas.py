"""Agent-related Pydantic models — profiles, actions, and chat responses."""

from typing import Literal

from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    """A complete AI agent profile with personality and prompt configuration.

    Each agent has a unique identity, model assignment, personality traits,
    and pre-built system prompts for both action decisions and table talk.
    """

    id: str = Field(description="Unique agent identifier")
    name: str = Field(description="Display name")
    avatar: str = Field(description="Avatar filename in /avatars/")
    backstory: str = Field(description="Flavor text / bio shown in lobby")
    model: str = Field(description="Pydantic AI model string, e.g. 'openai:gpt-4o'")
    provider: str = Field(description="Provider key, e.g. 'openai', 'anthropic'")

    # Personality dimensions
    play_style: str = Field(description="e.g. 'aggressive', 'tight', 'loose', 'mathematical'")
    talk_style: str = Field(description="e.g. 'trash-talker', 'silent', 'friendly', 'sarcastic'")
    risk_tolerance: str = Field(description="e.g. 'reckless', 'calculated', 'cautious'")
    bluffing_tendency: str = Field(description="e.g. 'frequent', 'honest', 'deceptive'")

    # System prompts
    action_system_prompt: str = Field(description="System prompt for action decisions")
    chat_system_prompt: str = Field(description="System prompt for table talk")


class PokerAction(BaseModel):
    """Structured output from the Action Agent — a poker decision.

    The action agent returns this on every turn. The reasoning field is
    for debugging/logging only and is never shown to other players.
    """

    action: Literal["fold", "check", "call", "raise"] = Field(
        description="The chosen poker action"
    )
    amount: int | None = Field(
        default=None,
        description="Raise amount (total raise-to). Required only for 'raise'.",
    )
    reasoning: str = Field(
        default="",
        description="Internal reasoning (not shown to players, useful for debugging)",
    )


class ChatResponse(BaseModel):
    """Structured output from the Chat Agent — table talk or silence.

    If the agent chooses not to speak, message will be None.
    """

    message: str | None = Field(
        default=None,
        description="The chat message, or None if the agent chooses not to speak",
    )
