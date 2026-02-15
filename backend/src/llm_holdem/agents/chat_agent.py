"""Chat agent — Pydantic AI agent for reactive table talk.

Triggered after key game events (all-in, showdown, elimination, big pot,
human chat). Each agent gets a chance to speak based on personality and
randomness. Chat is separate from action decisions.
"""

import asyncio
import logging
import random
import time

from pydantic_ai import Agent
from pydantic_ai.usage import Usage

from llm_holdem.agents.context import fits_in_context
from llm_holdem.agents.prompt import build_chat_prompt
from llm_holdem.agents.schemas import AgentProfile
from llm_holdem.agents.schemas import ChatResponse
from llm_holdem.agents.validator import sanitize_game_state
from llm_holdem.agents.validator import validate_prompt
from llm_holdem.game.state import GameState

logger = logging.getLogger(__name__)

# ─── Chat Trigger Events ──────────────────────────────────────────

CHAT_TRIGGER_EVENTS = [
    "all_in",
    "showdown",
    "elimination",
    "big_pot",
    "human_chat",
    "big_bluff",
    "bad_beat",
    "hand_start",
]

# Probability that a given agent speaks for a given event type
# Keyed by talk_style keywords → base probability
SPEAK_PROBABILITIES: dict[str, float] = {
    "trash-talker": 0.7,
    "friendly": 0.5,
    "sarcastic": 0.5,
    "dramatic": 0.6,
    "philosophical": 0.4,
    "silent": 0.1,
    "quiet": 0.15,
    "sparse": 0.2,
    "excitable": 0.6,
    "chatty": 0.7,
}

# Default probability if no talk-style keyword matches
DEFAULT_SPEAK_PROBABILITY = 0.35

# Minimum seconds between chat messages from the same agent
CHAT_COOLDOWN_SECONDS = 10.0


def _get_speak_probability(profile: AgentProfile) -> float:
    """Determine how likely this agent is to speak.

    Args:
        profile: The agent profile.

    Returns:
        Probability (0-1) that this agent speaks.
    """
    talk_style_lower = profile.talk_style.lower()
    for keyword, prob in SPEAK_PROBABILITIES.items():
        if keyword in talk_style_lower:
            return prob
    return DEFAULT_SPEAK_PROBABILITY


def should_agent_speak(
    profile: AgentProfile,
    trigger_event: str,
    last_spoke_at: float | None = None,
) -> bool:
    """Determine if an agent should speak for a given event.

    Uses personality traits and randomness to decide. Always allows speech
    for direct human chat responses (higher probability).

    Args:
        profile: The agent profile.
        trigger_event: The event type that occurred.
        last_spoke_at: Unix timestamp when agent last spoke, or None.

    Returns:
        True if the agent should generate a chat response.
    """
    # Enforce cooldown
    if last_spoke_at is not None:
        elapsed = time.time() - last_spoke_at
        if elapsed < CHAT_COOLDOWN_SECONDS:
            return False

    base_prob = _get_speak_probability(profile)

    # Boost probability for certain events
    if trigger_event == "human_chat":
        base_prob = min(base_prob * 1.5, 0.9)
    elif trigger_event in ("showdown", "elimination"):
        base_prob = min(base_prob * 1.3, 0.85)
    elif trigger_event == "hand_start":
        base_prob *= 0.3  # Rarely speak at hand start

    return random.random() < base_prob


def _create_chat_agent(profile: AgentProfile) -> Agent[None, ChatResponse]:
    """Create a Pydantic AI agent configured for chat responses.

    Args:
        profile: The agent's profile with model and chat system prompt.

    Returns:
        A configured Pydantic AI Agent.
    """
    return Agent(
        model=profile.model,
        output_type=ChatResponse,
        system_prompt=profile.chat_system_prompt,
        retries=1,
        name=f"chat-{profile.id}",
        defer_model_check=True,
    )


async def get_chat_response(
    profile: AgentProfile,
    game_state: GameState,
    seat_index: int,
    trigger_event: str,
    event_description: str,
    recent_chat: list[dict[str, str]] | None = None,
) -> tuple[ChatResponse, Usage]:
    """Get a chat response from an AI agent.

    Args:
        profile: The agent profile.
        game_state: The current game state.
        seat_index: The agent's seat.
        trigger_event: The event that triggered chat.
        event_description: Human-readable description of the event.
        recent_chat: Recent chat messages for context.

    Returns:
        Tuple of (ChatResponse, Usage).
    """
    # Sanitize game state
    sanitized_state = sanitize_game_state(game_state, seat_index)

    # Build prompt
    prompt = build_chat_prompt(
        game_state=sanitized_state,
        seat_index=seat_index,
        trigger_event=trigger_event,
        event_description=event_description,
        recent_chat=recent_chat,
    )

    # Validate prompt
    try:
        validate_prompt(prompt, game_state, seat_index)
    except Exception as e:
        logger.error("Chat prompt validation failed for %s: %s", profile.id, e)
        return ChatResponse(message=None), Usage()

    # Check context fits
    if not fits_in_context(profile.chat_system_prompt, prompt, profile.model):
        logger.warning("Chat prompt exceeds context for %s", profile.id)

    # Call LLM
    agent = _create_chat_agent(profile)
    try:
        result = await agent.run(prompt)
        response = result.response
        usage = result.usage

        if response.message:
            logger.info(
                "Agent %s says: %s",
                profile.id,
                response.message[:80],
            )
        return response, Usage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            requests=usage.requests,
        )

    except Exception as e:
        logger.error("Chat agent %s failed: %s", profile.id, e)
        return ChatResponse(message=None), Usage()


async def trigger_chat_responses(
    profiles_and_seats: list[tuple[AgentProfile, int]],
    game_state: GameState,
    trigger_event: str,
    event_description: str,
    recent_chat: list[dict[str, str]] | None = None,
    last_spoke_times: dict[str, float] | None = None,
    max_speakers: int = 3,
) -> list[tuple[str, int, str, Usage]]:
    """Trigger chat responses from multiple agents for an event.

    Selects which agents should speak based on personality and randomness,
    then queries them concurrently. Limits the number of speakers to
    prevent chat spam.

    Args:
        profiles_and_seats: List of (profile, seat_index) for eligible agents.
        game_state: Current game state.
        trigger_event: The event type.
        event_description: Description of the event.
        recent_chat: Recent chat messages.
        last_spoke_times: Dict of agent_id -> last spoke timestamp.
        max_speakers: Maximum number of agents that can speak per event.

    Returns:
        List of (agent_id, seat_index, message, usage) for agents that spoke.
    """
    if last_spoke_times is None:
        last_spoke_times = {}

    # Determine which agents should speak
    speakers: list[tuple[AgentProfile, int]] = []
    for profile, seat in profiles_and_seats:
        last_spoke = last_spoke_times.get(profile.id)
        if should_agent_speak(profile, trigger_event, last_spoke):
            speakers.append((profile, seat))
            if len(speakers) >= max_speakers:
                break

    if not speakers:
        return []

    # Query speakers concurrently
    tasks = [
        get_chat_response(
            profile=profile,
            game_state=game_state,
            seat_index=seat,
            trigger_event=trigger_event,
            event_description=event_description,
            recent_chat=recent_chat,
        )
        for profile, seat in speakers
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect successful responses
    messages: list[tuple[str, int, str, Usage]] = []
    for i, result in enumerate(results):
        profile, seat = speakers[i]
        if isinstance(result, Exception):
            logger.error("Chat response failed for %s: %s", profile.id, result)
            continue
        response, usage = result
        if response.message:
            messages.append((profile.id, seat, response.message, usage))
            last_spoke_times[profile.id] = time.time()

    return messages
