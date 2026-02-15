/**
 * AgentCard — displays an agent's profile summary in the roster browser.
 */

import type { AgentProfile } from "../../types/agents";
import "./AgentCard.css";

interface AgentCardProps {
  agent: AgentProfile;
  isSelected: boolean;
  onSelect: (agentId: string) => void;
}

export function AgentCard({
  agent,
  isSelected,
  onSelect,
}: AgentCardProps): React.ReactElement {
  return (
    <button
      className={`agent-card ${isSelected ? "agent-card--selected" : ""}`}
      onClick={() => onSelect(agent.id)}
      type="button"
    >
      <div className="agent-card__avatar">
        <img
          src={agent.avatar_url}
          alt={agent.name}
          className="agent-card__avatar-img"
          onError={(e) => {
            (e.target as HTMLImageElement).src = "/avatars/default.png";
          }}
        />
      </div>
      <div className="agent-card__info">
        <span className="agent-card__name">{agent.name}</span>
        <span className="agent-card__provider">{agent.provider}</span>
      </div>
    </button>
  );
}
