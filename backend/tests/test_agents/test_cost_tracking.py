"""Tests for cost tracking module."""

import pytest
from pydantic_ai.usage import Usage

from llm_holdem.agents.cost_tracking import MODEL_PRICING
from llm_holdem.agents.cost_tracking import estimate_cost


class TestModelPricing:
    """Tests for the pricing registry."""

    def test_has_openai_models(self) -> None:
        assert "gpt-4o" in MODEL_PRICING or "openai:gpt-4o" in MODEL_PRICING

    def test_has_anthropic_models(self) -> None:
        found = any("claude" in k for k in MODEL_PRICING)
        assert found

    def test_pricing_has_positive_values(self) -> None:
        for model, prices in MODEL_PRICING.items():
            input_price, output_price = prices
            assert input_price >= 0, f"{model} has negative input price"
            assert output_price >= 0, f"{model} has negative output price"


class TestEstimateCost:
    """Tests for estimate_cost."""

    def test_known_model(self) -> None:
        usage = Usage(input_tokens=1_000_000, output_tokens=1_000_000, requests=1)
        cost = estimate_cost("gpt-4o", usage)
        assert cost > 0.0

    def test_zero_tokens(self) -> None:
        usage = Usage(input_tokens=0, output_tokens=0, requests=0)
        cost = estimate_cost("gpt-4o", usage)
        assert cost == 0.0

    def test_unknown_model_uses_default_pricing(self) -> None:
        usage = Usage(input_tokens=1000, output_tokens=1000, requests=1)
        cost = estimate_cost("unknown-model-xyz", usage)
        # Default pricing is non-zero (1.00/3.00 per 1M tokens)
        assert cost > 0.0

    def test_none_tokens_handled(self) -> None:
        usage = Usage(requests=1)  # tokens default to None
        cost = estimate_cost("gpt-4o", usage)
        assert cost == 0.0
