"""Context window manager — ensures prompts fit within model token limits.

Maintains a registry of model context window sizes and provides token
estimation. When a prompt exceeds the model's limit, oldest hand history
entries are truncated first, preserving the current hand and recent context.
"""

import logging

logger = logging.getLogger(__name__)


# ─── Model Context Window Registry ──────────────────────────────────

# Maximum context window sizes (in tokens) for known models.
# These are input limits; output tokens come out of the same budget
# for some models, but we budget conservatively by reserving ~1000
# tokens for the output.
MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    # OpenAI
    "openai:gpt-4o": 128_000,
    "openai:gpt-4o-mini": 128_000,
    "openai:gpt-4-turbo": 128_000,
    "openai:gpt-4": 8_192,
    "openai:gpt-3.5-turbo": 16_385,
    # Anthropic
    "anthropic:claude-sonnet-4-20250514": 200_000,
    "anthropic:claude-haiku-4-20250514": 200_000,
    "anthropic:claude-opus-4-20250514": 200_000,
    # Google
    "google:gemini-2.0-flash": 1_048_576,
    "google:gemini-2.5-flash": 1_048_576,
    "google:gemini-1.5-pro": 2_097_152,
    # Groq
    "groq:llama-3.3-70b-versatile": 128_000,
    "groq:llama-3.1-8b-instant": 128_000,
    "groq:mixtral-8x7b-32768": 32_768,
    # Mistral
    "mistral:mistral-large-latest": 128_000,
    "mistral:mistral-small-latest": 128_000,
    # Ollama (defaults for common local models)
    "ollama:llama3.2": 128_000,
    "ollama:llama3.1": 128_000,
    "ollama:mistral": 32_000,
}

# Default context window for unknown models
DEFAULT_CONTEXT_WINDOW = 32_000

# Tokens reserved for output generation
OUTPUT_RESERVE_TOKENS = 1_000

# Approximate chars per token (conservative estimate for English text)
CHARS_PER_TOKEN = 4


def get_context_window(model: str) -> int:
    """Get the context window size for a model.

    Args:
        model: The Pydantic AI model string (e.g., 'openai:gpt-4o').

    Returns:
        The context window size in tokens.
    """
    window = MODEL_CONTEXT_WINDOWS.get(model, DEFAULT_CONTEXT_WINDOW)
    return window


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.

    Uses a simple character-based heuristic. For production accuracy,
    a proper tokenizer should be used, but this is sufficient for
    our context window management since we leave ample margin.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    return max(1, len(text) // CHARS_PER_TOKEN)


def get_available_input_tokens(model: str) -> int:
    """Get the number of tokens available for input, after reserving output space.

    Args:
        model: The Pydantic AI model string.

    Returns:
        Available input tokens.
    """
    return get_context_window(model) - OUTPUT_RESERVE_TOKENS


def truncate_hand_history(
    system_prompt: str,
    current_hand_prompt: str,
    hand_history: list[dict[str, str]],
    model: str,
    recent_chat: str = "",
) -> list[dict[str, str]]:
    """Truncate hand history to fit within context window.

    Preserves the system prompt, current hand context, and recent chat.
    Removes oldest hand history entries first until the total fits.

    Args:
        system_prompt: The full system prompt text.
        current_hand_prompt: The current hand's prompt content.
        hand_history: List of hand history entries to potentially truncate.
        model: The model string for determining context limits.
        recent_chat: Recent chat text to preserve.

    Returns:
        Truncated hand history (may be shorter than input).
    """
    available = get_available_input_tokens(model)

    # Calculate fixed token costs
    fixed_tokens = (
        estimate_tokens(system_prompt)
        + estimate_tokens(current_hand_prompt)
        + estimate_tokens(recent_chat)
    )

    remaining = available - fixed_tokens
    if remaining <= 0:
        logger.warning(
            "Fixed prompt content (%d tokens) exceeds context window (%d tokens) for model %s",
            fixed_tokens,
            available,
            model,
        )
        return []

    # Try including hand history from most recent to oldest
    # This preserves the most relevant context
    result: list[dict[str, str]] = []
    total_tokens = 0

    for entry in reversed(hand_history):
        summary = entry.get("summary", "")
        entry_tokens = estimate_tokens(f"Hand #{entry.get('hand_number', '?')}: {summary}")
        if total_tokens + entry_tokens <= remaining:
            result.insert(0, entry)
            total_tokens += entry_tokens
        else:
            truncated_count = len(hand_history) - len(result)
            logger.info(
                "Truncated %d oldest hand history entries for model %s "
                "(used %d/%d available tokens for history)",
                truncated_count,
                model,
                total_tokens,
                remaining,
            )
            break

    return result


def fits_in_context(
    system_prompt: str,
    user_prompt: str,
    model: str,
) -> bool:
    """Check if a complete prompt fits within the model's context window.

    Args:
        system_prompt: The system prompt text.
        user_prompt: The user message text.
        model: The model string.

    Returns:
        True if the combined prompt fits within available tokens.
    """
    total = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    available = get_available_input_tokens(model)
    return total <= available
