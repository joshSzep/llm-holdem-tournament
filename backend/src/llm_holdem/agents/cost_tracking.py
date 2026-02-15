"""Cost tracking — estimates and records LLM API costs.

Captures token usage from Pydantic AI responses, estimates cost based
on model pricing, and persists records to the database.
"""

import logging
from datetime import UTC, datetime

from pydantic_ai.usage import Usage
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.db.models import CostRecord
from llm_holdem.db.repository import create_cost_record

logger = logging.getLogger(__name__)


# ─── Model Pricing Registry ─────────────────────────────────────
# Prices per 1M tokens (input, output) in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "openai:gpt-4o": (2.50, 10.00),
    "openai:gpt-4o-mini": (0.15, 0.60),
    "openai:gpt-4-turbo": (10.00, 30.00),
    "openai:gpt-4": (30.00, 60.00),
    "openai:gpt-3.5-turbo": (0.50, 1.50),
    # Anthropic
    "anthropic:claude-sonnet-4-20250514": (3.00, 15.00),
    "anthropic:claude-haiku-4-20250514": (0.80, 4.00),
    "anthropic:claude-opus-4-20250514": (15.00, 75.00),
    # Google
    "google:gemini-2.0-flash": (0.10, 0.40),
    "google:gemini-2.5-flash": (0.15, 0.60),
    "google:gemini-1.5-pro": (1.25, 5.00),
    # Groq (typically free or very cheap)
    "groq:llama-3.3-70b-versatile": (0.59, 0.79),
    "groq:llama-3.1-8b-instant": (0.05, 0.08),
    "groq:mixtral-8x7b-32768": (0.24, 0.24),
    # Mistral
    "mistral:mistral-large-latest": (2.00, 6.00),
    "mistral:mistral-small-latest": (0.20, 0.60),
    # Ollama (local, free)
    "ollama:llama3.2": (0.0, 0.0),
    "ollama:llama3.1": (0.0, 0.0),
    "ollama:mistral": (0.0, 0.0),
}

# Default pricing for unknown models
DEFAULT_PRICING = (1.00, 3.00)


def estimate_cost(model: str, usage: Usage) -> float:
    """Estimate the cost of an LLM call in USD.

    Args:
        model: The Pydantic AI model string.
        usage: Token usage from the Pydantic AI response.

    Returns:
        Estimated cost in USD.
    """
    input_price, output_price = MODEL_PRICING.get(model, DEFAULT_PRICING)

    input_cost = (usage.input_tokens / 1_000_000) * input_price
    output_cost = (usage.output_tokens / 1_000_000) * output_price

    return input_cost + output_cost


async def record_cost(
    session: AsyncSession,
    game_id: int,
    agent_id: str,
    call_type: str,
    model: str,
    usage: Usage,
) -> CostRecord:
    """Record an LLM API call cost to the database.

    Args:
        session: Database session.
        game_id: Database ID of the game.
        agent_id: The agent's identifier.
        call_type: Type of call ('action' or 'chat').
        model: The model string.
        usage: Token usage from Pydantic AI.

    Returns:
        The created CostRecord.
    """
    cost = estimate_cost(model, usage)

    record = CostRecord(
        game_id=game_id,
        agent_id=agent_id,
        call_type=call_type,
        model=model,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        estimated_cost=cost,
        timestamp=datetime.now(UTC).isoformat(),
    )

    created = await create_cost_record(session, record)

    logger.debug(
        "Cost recorded: agent=%s, type=%s, model=%s, "
        "tokens=%d/%d, cost=$%.6f",
        agent_id,
        call_type,
        model,
        usage.input_tokens,
        usage.output_tokens,
        cost,
    )

    return created
