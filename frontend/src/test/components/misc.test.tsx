/**
 * Tests for CostIndicator and TurnTimer components.
 */

import { render, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { CostIndicator } from "../../components/cost/CostIndicator";
import { TurnTimer } from "../../components/timer/TurnTimer";
import { useGameStore } from "../../stores/gameStore";
import { fetchCosts } from "../../services/api";

// ─── CostIndicator ──────────────────────────────────

vi.mock("../../services/api", () => ({
  fetchCosts: vi.fn(),
}));

const mockFetchCosts = vi.mocked(fetchCosts);

describe("CostIndicator", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockFetchCosts.mockResolvedValue({
      summary: { total_cost: 0, total_input_tokens: 0, total_output_tokens: 0, call_count: 0 },
      records: [],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("renders with initial zero cost", () => {
    const { container } = render(<CostIndicator />);
    expect(
      container.querySelector(".cost-indicator__amount"),
    ).toHaveTextContent("0.0000");
  });

  it("displays fetched cost", async () => {
    mockFetchCosts.mockResolvedValue({
      summary: { total_cost: 1.2345, total_input_tokens: 1000, total_output_tokens: 500, call_count: 5 },
      records: [],
    });

    vi.useRealTimers();
    const { container } = render(<CostIndicator />);

    await waitFor(() => {
      expect(
        container.querySelector(".cost-indicator__amount"),
      ).toHaveTextContent("1.2345");
    });
  });

  it("handles fetch error gracefully", async () => {
    mockFetchCosts.mockRejectedValue(new Error("Network error"));

    vi.useRealTimers();
    const { container } = render(<CostIndicator />);

    // Wait for the promise rejection to settle
    await waitFor(() => {
      expect(mockFetchCosts).toHaveBeenCalled();
    });

    // Should still render with 0 cost
    expect(
      container.querySelector(".cost-indicator__amount"),
    ).toHaveTextContent("0.0000");
  });
});

// ─── TurnTimer ──────────────────────────────────────

describe("TurnTimer", () => {
  beforeEach(() => {
    useGameStore.setState({ timer: null });
  });

  it("returns null when timer is not active", () => {
    const { container } = render(<TurnTimer />);
    expect(container.querySelector(".turn-timer")).toBeNull();
  });

  it("renders timer when active", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 30 },
    });

    const { container } = render(<TurnTimer />);
    expect(container.querySelector(".turn-timer")).toBeInTheDocument();
    expect(container.querySelector(".turn-timer__text")).toHaveTextContent(
      "30",
    );
  });

  it("applies urgent class when time is low", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 5 },
    });

    const { container } = render(<TurnTimer />);
    expect(container.querySelector(".turn-timer")).toHaveClass(
      "turn-timer--urgent",
    );
  });

  it("renders SVG elements", () => {
    useGameStore.setState({
      timer: { seat_index: 0, seconds_remaining: 45 },
    });

    const { container } = render(<TurnTimer />);
    expect(container.querySelector("svg")).toBeInTheDocument();
    expect(
      container.querySelector(".turn-timer__track"),
    ).toBeInTheDocument();
    expect(
      container.querySelector(".turn-timer__progress"),
    ).toBeInTheDocument();
  });
});
