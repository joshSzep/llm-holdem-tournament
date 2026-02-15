/**
 * SeatConfigurator — per-seat agent picker.
 */

import { useState } from "react";

import type { AgentProfile } from "../../types/agents";
import { AgentCard } from "./AgentCard";
import "./SeatConfigurator.css";

interface SeatConfiguratorProps {
  seatIndex: number;
  selectedAgentId: string | "random" | null;
  agents: AgentProfile[];
  disabled: boolean;
  onSelect: (agentId: string | "random" | null) => void;
}

export function SeatConfigurator({
  seatIndex,
  selectedAgentId,
  agents,
  disabled,
  onSelect,
}: SeatConfiguratorProps): React.ReactElement {
  const [isOpen, setIsOpen] = useState(false);

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);
  const displayName =
    selectedAgentId === "random"
      ? "Random"
      : selectedAgent?.name ?? "Empty Seat";

  return (
    <div className={`seat-configurator ${disabled ? "seat-configurator--disabled" : ""}`}>
      <div className="seat-configurator__header">
        <span className="seat-configurator__label">Seat {seatIndex + 1}</span>
        <button
          className="seat-configurator__toggle"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          type="button"
        >
          {displayName}
          <span className="seat-configurator__arrow">
            {isOpen ? "▲" : "▼"}
          </span>
        </button>
      </div>

      {isOpen && (
        <div className="seat-configurator__dropdown">
          <button
            className={`seat-configurator__option ${selectedAgentId === "random" ? "seat-configurator__option--selected" : ""}`}
            onClick={() => {
              onSelect("random");
              setIsOpen(false);
            }}
            type="button"
          >
            🎲 Random Agent
          </button>
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              isSelected={selectedAgentId === agent.id}
              onSelect={(id) => {
                onSelect(id);
                setIsOpen(false);
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
