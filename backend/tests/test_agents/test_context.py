"""Tests for context window manager."""

from llm_holdem.agents.context import DEFAULT_CONTEXT_WINDOW
from llm_holdem.agents.context import estimate_tokens
from llm_holdem.agents.context import fits_in_context
from llm_holdem.agents.context import get_available_input_tokens
from llm_holdem.agents.context import get_context_window
from llm_holdem.agents.context import truncate_hand_history


class TestGetContextWindow:
    """Tests for context window registry."""

    def test_known_model(self) -> None:
        assert get_context_window("openai:gpt-4o") == 128_000

    def test_anthropic_model(self) -> None:
        assert get_context_window("anthropic:claude-sonnet-4-20250514") == 200_000

    def test_unknown_model_uses_default(self) -> None:
        assert get_context_window("unknown:model") == DEFAULT_CONTEXT_WINDOW

    def test_available_tokens_reserves_output(self) -> None:
        available = get_available_input_tokens("openai:gpt-4o")
        window = get_context_window("openai:gpt-4o")
        assert available < window
        assert available == window - 1_000


class TestEstimateTokens:
    """Tests for token estimation."""

    def test_empty_string(self) -> None:
        assert estimate_tokens("") == 1  # Minimum 1

    def test_short_string(self) -> None:
        tokens = estimate_tokens("Hello world")
        assert tokens >= 1

    def test_longer_string(self) -> None:
        text = "a" * 400  # 400 chars ≈ 100 tokens
        tokens = estimate_tokens(text)
        assert tokens == 100

    def test_proportional(self) -> None:
        short = estimate_tokens("Hello")
        long = estimate_tokens("Hello " * 100)
        assert long > short


class TestFitsInContext:
    """Tests for context limit checking."""

    def test_short_prompt_fits(self) -> None:
        assert fits_in_context(
            system_prompt="You are a poker player.",
            user_prompt="What's your action?",
            model="openai:gpt-4o",
        )

    def test_massive_prompt_does_not_fit(self) -> None:
        # Create a prompt way larger than any context window
        huge = "x" * (200_000 * 4 + 1)  # 200k tokens
        assert not fits_in_context(
            system_prompt=huge,
            user_prompt="action?",
            model="openai:gpt-4",  # Only 8k window
        )

    def test_near_limit(self) -> None:
        # gpt-4 has 8192 tokens, minus 1000 for output = 7192
        # At 4 chars/token, that's ~28768 chars
        system = "a" * 20000  # ~5000 tokens
        user = "b" * 8000  # ~2000 tokens
        # Total ~7000 < 7192 → should fit
        assert fits_in_context(system, user, "openai:gpt-4")


class TestTruncateHandHistory:
    """Tests for hand history truncation."""

    def test_no_truncation_needed(self) -> None:
        history = [
            {"hand_number": "1", "summary": "Player A won 50 chips"},
            {"hand_number": "2", "summary": "Player B won 100 chips"},
        ]
        result = truncate_hand_history(
            system_prompt="System prompt",
            current_hand_prompt="Current hand info",
            hand_history=history,
            model="openai:gpt-4o",  # 128k context
        )
        assert len(result) == 2

    def test_truncation_removes_oldest(self) -> None:
        # Create many entries that would exceed a small context window
        history = [
            {"hand_number": str(i), "summary": "x" * 1000}
            for i in range(100)
        ]
        result = truncate_hand_history(
            system_prompt="s" * 10000,
            current_hand_prompt="c" * 10000,
            hand_history=history,
            model="openai:gpt-4",  # Only 8k context
        )
        # Should have truncated some entries
        assert len(result) < len(history)

    def test_preserved_entries_are_most_recent(self) -> None:
        history = [
            {"hand_number": str(i), "summary": f"Hand {i} summary"}
            for i in range(50)
        ]
        result = truncate_hand_history(
            system_prompt="sys",
            current_hand_prompt="cur",
            hand_history=history,
            model="openai:gpt-4",  # 8k context
        )
        if result:
            # Last entry should be the most recent
            assert result[-1]["hand_number"] == "49"

    def test_empty_history(self) -> None:
        result = truncate_hand_history(
            system_prompt="sys",
            current_hand_prompt="cur",
            hand_history=[],
            model="openai:gpt-4o",
        )
        assert result == []

    def test_fixed_content_exceeds_window(self) -> None:
        """When just system + current prompt exceed the window, return empty."""
        result = truncate_hand_history(
            system_prompt="x" * 100000,
            current_hand_prompt="y" * 100000,
            hand_history=[{"hand_number": "1", "summary": "test"}],
            model="openai:gpt-4",  # 8k context
        )
        assert result == []
