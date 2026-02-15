/**
 * REST API client service.
 * All API calls go through this module — never use fetch() directly elsewhere.
 */

import type { AgentListResponse } from "../types/agents";
import type {
  CostListResponse,
  CreateGameRequest,
  CreateGameResponse,
  GameDetail,
  GameSummary,
  HandDetail,
  HandSummary,
  ProvidersResponse,
} from "../types/api";

const API_BASE = "/api";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new ApiError(response.status, text);
  }

  return response.json() as Promise<T>;
}

// ─── Agent Endpoints ─────────────────────────────────

export async function fetchAgents(): Promise<AgentListResponse> {
  return request<AgentListResponse>("/agents");
}

export async function fetchAgent(
  agentId: string,
): Promise<AgentListResponse["agents"][0]> {
  return request<AgentListResponse["agents"][0]>(`/agents/${agentId}`);
}

// ─── Game Endpoints ──────────────────────────────────

export async function fetchGames(
  status?: string,
): Promise<GameSummary[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<GameSummary[]>(`/games${query}`);
}

export async function fetchGameDetail(
  gameId: number,
): Promise<GameDetail> {
  return request<GameDetail>(`/games/${gameId}`);
}

export async function createGame(
  req: CreateGameRequest,
): Promise<CreateGameResponse> {
  return request<CreateGameResponse>("/games", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ─── Hand Endpoints ──────────────────────────────────

export async function fetchHands(
  gameId: number,
): Promise<HandSummary[]> {
  return request<HandSummary[]>(`/games/${gameId}/hands`);
}

export async function fetchHand(
  gameId: number,
  handNumber: number,
): Promise<HandDetail> {
  return request<HandDetail>(`/games/${gameId}/hands/${handNumber}`);
}

// ─── Config Endpoints ────────────────────────────────

export async function fetchProviders(): Promise<ProvidersResponse> {
  return request<ProvidersResponse>("/config/providers");
}

// ─── Cost Endpoints ──────────────────────────────────

export async function fetchCosts(): Promise<CostListResponse> {
  return request<CostListResponse>("/costs");
}

export { ApiError };
