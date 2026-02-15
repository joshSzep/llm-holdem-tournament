/**
 * Agent profile types — mirrors backend agent schemas.
 */

export interface AgentProfile {
  id: string;
  name: string;
  avatar_url: string;
  provider: string;
  model: string;
  backstory: string;
}

export interface AgentListResponse {
  agents: AgentProfile[];
}
