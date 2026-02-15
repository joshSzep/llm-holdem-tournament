/**
 * Tests for lobby components: GameModeSelector, AgentCard, SeatConfigurator.
 */

import { render, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { GameModeSelector } from "../../components/lobby/GameModeSelector";
import { AgentCard } from "../../components/lobby/AgentCard";
import { SeatConfigurator } from "../../components/lobby/SeatConfigurator";
import type { AgentProfile } from "../../types/agents";

// ─── GameModeSelector ────────────────────────────────

describe("GameModeSelector", () => {
  it("renders play and spectate buttons", () => {
    const { container } = render(
      <GameModeSelector mode="player" onModeChange={vi.fn()} />,
    );
    const buttons = container.querySelectorAll(".game-mode-selector__button");
    expect(buttons).toHaveLength(2);
  });

  it("highlights selected mode", () => {
    const { container } = render(
      <GameModeSelector mode="player" onModeChange={vi.fn()} />,
    );
    const activeBtn = container.querySelector(
      ".game-mode-selector__button--active",
    );
    expect(activeBtn).toHaveTextContent("Play");
  });

  it("highlights spectator when selected", () => {
    const { container } = render(
      <GameModeSelector mode="spectator" onModeChange={vi.fn()} />,
    );
    const activeBtn = container.querySelector(
      ".game-mode-selector__button--active",
    );
    expect(activeBtn).toHaveTextContent("Spectate");
  });

  it("calls onModeChange when mode clicked", () => {
    const onModeChange = vi.fn();
    const { container } = render(
      <GameModeSelector mode="player" onModeChange={onModeChange} />,
    );
    const buttons = container.querySelectorAll(".game-mode-selector__button");
    fireEvent.click(buttons[1]!); // Click "Spectate"
    expect(onModeChange).toHaveBeenCalledWith("spectator");
  });
});

// ─── AgentCard ───────────────────────────────────────

describe("AgentCard", () => {
  const agent: AgentProfile = {
    id: "bot1",
    name: "Test Bot",
    avatar_url: "/avatars/bot1.png",
    provider: "openai",
    model: "gpt-4",
    backstory: "A test bot",
  };

  it("renders agent name", () => {
    const { container } = render(
      <AgentCard agent={agent} isSelected={false} onSelect={vi.fn()} />,
    );
    expect(container.querySelector(".agent-card__name")).toHaveTextContent(
      "Test Bot",
    );
  });

  it("renders agent avatar", () => {
    const { container } = render(
      <AgentCard agent={agent} isSelected={false} onSelect={vi.fn()} />,
    );
    const img = container.querySelector("img");
    expect(img).toHaveAttribute("src", "/avatars/bot1.png");
  });

  it("renders provider info", () => {
    const { container } = render(
      <AgentCard agent={agent} isSelected={false} onSelect={vi.fn()} />,
    );
    expect(
      container.querySelector(".agent-card__provider"),
    ).toHaveTextContent("openai");
  });

  it("applies selected class when isSelected", () => {
    const { container } = render(
      <AgentCard agent={agent} isSelected onSelect={vi.fn()} />,
    );
    expect(container.querySelector(".agent-card")).toHaveClass(
      "agent-card--selected",
    );
  });

  it("calls onSelect with agent id when clicked", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <AgentCard agent={agent} isSelected={false} onSelect={onSelect} />,
    );
    fireEvent.click(container.querySelector(".agent-card")!);
    expect(onSelect).toHaveBeenCalledWith("bot1");
  });
});

// ─── SeatConfigurator ────────────────────────────────

describe("SeatConfigurator", () => {
  const agents: AgentProfile[] = [
    {
      id: "bot1",
      name: "Bot One",
      avatar_url: "/a.png",
      provider: "openai",
      model: "gpt-4",
      backstory: "",
    },
    {
      id: "bot2",
      name: "Bot Two",
      avatar_url: "/b.png",
      provider: "anthropic",
      model: "claude",
      backstory: "",
    },
  ];

  it("renders seat label", () => {
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="random"
        disabled={false}
        onSelect={vi.fn()}
      />,
    );
    expect(
      container.querySelector(".seat-configurator__label"),
    ).toHaveTextContent("Seat 1");
  });

  it("shows display name for random", () => {
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="random"
        disabled={false}
        onSelect={vi.fn()}
      />,
    );
    expect(
      container.querySelector(".seat-configurator__toggle"),
    ).toHaveTextContent("Random");
  });

  it("shows agent name when selected", () => {
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="bot1"
        disabled={false}
        onSelect={vi.fn()}
      />,
    );
    expect(
      container.querySelector(".seat-configurator__toggle"),
    ).toHaveTextContent("Bot One");
  });

  it("opens dropdown when toggle clicked", () => {
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="random"
        disabled={false}
        onSelect={vi.fn()}
      />,
    );
    fireEvent.click(container.querySelector(".seat-configurator__toggle")!);
    expect(
      container.querySelector(".seat-configurator__dropdown"),
    ).toBeInTheDocument();
  });

  it("calls onSelect when agent chosen", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="random"
        disabled={false}
        onSelect={onSelect}
      />,
    );
    // Open dropdown
    fireEvent.click(container.querySelector(".seat-configurator__toggle")!);
    // Click an agent card
    const agentCards = container.querySelectorAll(".agent-card");
    fireEvent.click(agentCards[0]!);
    expect(onSelect).toHaveBeenCalledWith("bot1");
  });

  it("is disabled when disabled prop is true", () => {
    const { container } = render(
      <SeatConfigurator
        seatIndex={0}
        agents={agents}
        selectedAgentId="random"
        disabled
        onSelect={vi.fn()}
      />,
    );
    expect(
      container.querySelector(".seat-configurator__toggle"),
    ).toBeDisabled();
  });
});
