"""Action agent — Pydantic AI agent for poker game decisions.

Uses Pydantic AI structured output to get a PokerAction from the LLM.
Includes retry logic for invalid actions and error handling with fallbacks.
"""

import asyncio
import logging
from typing import Literal

from pydantic_ai import Agent
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.usage import Usage

from llm_holdem.agents.context import fits_in_context, truncate_hand_history
from llm_holdem.agents.prompt import build_action_prompt
from llm_holdem.agents.schemas import AgentProfile, PokerAction
from llm_holdem.agents.validator import PromptValidationError, sanitize_game_state, validate_prompt
from llm_holdem.game.state import GameState

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 2
BACKOFF_BASE = 1.0  # seconds


def _create_action_agent(profile: AgentProfile) -> Agent[None, PokerAction]:
    """Create a Pydantic AI agent configured for poker action decisions.

    Args:
        profile: The agent's profile with model and system prompt.

    Returns:
        A configured Pydantic AI Agent.
    """
    return Agent(
        model=profile.model,
        output_type=PokerAction,
        system_prompt=profile.action_system_prompt,
        retries=MAX_RETRIES,
        name=f"action-{profile.id}",
        defer_model_check=True,
    )


def _validate_action(
    action: PokerAction,
    valid_actions: list[str],
    min_raise_to: int | None,
    max_raise_to: int | None,
) -> str | None:
    """Validate a poker action against the game rules.

    Args:
        action: The action returned by the LLM.
        valid_actions: List of valid action types.
        min_raise_to: Minimum raise-to amount.
        max_raise_to: Maximum raise-to amount.

    Returns:
        Error message if invalid, None if valid.
    """
    if action.action not in valid_actions:
        return (
            f"'{action.action}' is not valid. "
            f"Valid actions: {', '.join(valid_actions)}"
        )

    if action.action == "raise":
        if action.amount is None:
            return "Raise requires an amount."
        if min_raise_to is not None and action.amount < min_raise_to:
            return (
                f"Raise amount {action.amount} is below minimum {min_raise_to}."
            )
        if max_raise_to is not None and action.amount > max_raise_to:
            return (
                f"Raise amount {action.amount} exceeds maximum {max_raise_to}."
            )

    return None


async def get_ai_action(
    profile: AgentProfile,
    game_state: GameState,
    seat_index: int,
    valid_actions: list[str],
    min_raise_to: int | None = None,
    max_raise_to: int | None = None,
    call_amount: int | None = None,
    hand_history: list[dict[str, str]] | None = None,
    recent_chat: list[dict[str, str]] | None = None,
) -> tuple[PokerAction, Usage]:
    """Get an AI agent's poker action using Pydantic AI.

    This is the main entry point for AI decisions. It:
    1. Sanitizes the game state (removes opponent hole cards)
    2. Builds the prompt with context window management
    3. Validates the prompt (hard gate)
    4. Calls the LLM via Pydantic AI
    5. Validates the returned action
    6. Retries on invalid actions with error explanation
    7. Falls back to check/fold on all failures

    Args:
        profile: The agent's profile.
        game_state: The full game state.
        seat_index: The agent's seat.
        valid_actions: Valid action types for this turn.
        min_raise_to: Minimum raise-to amount.
        max_raise_to: Maximum raise-to amount.
        call_amount: Amount to call.
        hand_history: Previous hand summaries for context.
        recent_chat: Recent chat messages for context.

    Returns:
        Tuple of (PokerAction, Usage) with the decision and token usage.
    """
    # Sanitize game state
    sanitized_state = sanitize_game_state(game_state, seat_index)

    # Context window management
    truncated_history = hand_history
    if hand_history:
        truncated_history = truncate_hand_history(
            system_prompt=profile.action_system_prompt,
            current_hand_prompt="",  # Will be estimated
            hand_history=hand_history,
            model=profile.model,
        )

    # Build prompt
    prompt = build_action_prompt(
        game_state=sanitized_state,
        seat_index=seat_index,
        valid_actions=valid_actions,
        min_raise_to=min_raise_to,
        max_raise_to=max_raise_to,
        call_amount=call_amount,
        hand_history=truncated_history,
    )

    # Validate prompt (HARD GATE)
    try:
        validate_prompt(prompt, game_state, seat_index)
    except PromptValidationError as e:
        logger.error(
            "Prompt validation failed for agent %s at seat %d: %s",
            profile.id,
            seat_index,
            e,
        )
        # Fallback: check if possible, otherwise fold
        fallback_action = "check" if "check" in valid_actions else "fold"
        return (
            PokerAction(
                action=fallback_action,
                reasoning=f"Prompt validation error: {e}",
            ),
            Usage(),
        )

    # Verify context fits
    if not fits_in_context(profile.action_system_prompt, prompt, profile.model):
        logger.warning(
            "Prompt exceeds context window for agent %s (model: %s)",
            profile.id,
            profile.model,
        )

    # Create agent and attempt LLM call
    agent = _create_action_agent(profile)
    total_usage = Usage()

    for attempt in range(MAX_RETRIES + 1):
        try:
            result = await agent.run(prompt)
            action = result.response
            usage = result.usage

            # Accumulate usage
            total_usage.input_tokens += usage.input_tokens
            total_usage.output_tokens += usage.output_tokens
            total_usage.requests += usage.requests

            # Validate the action
            error = _validate_action(action, valid_actions, min_raise_to, max_raise_to)
            if error is None:
                logger.info(
                    "Agent %s (seat %d) chooses: %s %s — %s",
                    profile.id,
                    seat_index,
                    action.action,
                    action.amount or "",
                    action.reasoning[:80] if action.reasoning else "",
                )
                return action, total_usage

            # Invalid action — retry with error
            logger.warning(
                "Agent %s returned invalid action (attempt %d): %s",
                profile.id,
                attempt + 1,
                error,
            )
            if attempt < MAX_RETRIES:
                prompt = (
                    f"{prompt}\n\n"
                    f"ERROR: Your previous action was invalid: {error}\n"
                    f"Please try again with a valid action."
                )

        except UnexpectedModelBehavior as e:
            logger.warning(
                "Agent %s LLM unexpected behavior (attempt %d): %s",
                profile.id,
                attempt + 1,
                e,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))

        except Exception as e:
            logger.error(
                "Agent %s LLM error (attempt %d): %s",
                profile.id,
                attempt + 1,
                e,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))

    # All retries exhausted — fallback
    fallback_action: Literal["check", "fold"] = "check" if "check" in valid_actions else "fold"
    logger.warning(
        "Agent %s exhausted retries, falling back to %s",
        profile.id,
        fallback_action,
    )
    return (
        PokerAction(
            action=fallback_action,
            reasoning="All LLM attempts failed, falling back to safe action.",
        ),
        total_usage,
    )
