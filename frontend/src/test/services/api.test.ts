/**
 * Tests for REST API service.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import {
  fetchAgents,
  fetchAgent,
  fetchGames,
  fetchGameDetail,
  createGame,
  fetchHands,
  fetchCosts,
  fetchProviders,
  ApiError,
} from "../../services/api";

describe("API service", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  function mockFetchResponse(data: unknown, status = 200): void {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(data),
    });
  }

  function mockFetchError(status: number, message: string): void {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ok: false,
      status,
      text: () => Promise.resolve(message),
    });
  }

  it("fetchAgents calls correct endpoint", async () => {
    const agents = [{ id: "bot1", name: "Bot" }];
    mockFetchResponse(agents);
    const result = await fetchAgents();
    expect(result).toEqual(agents);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/agents",
      expect.objectContaining({
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      }),
    );
  });

  it("fetchAgent calls correct endpoint with id", async () => {
    const agent = { id: "bot1", name: "Bot" };
    mockFetchResponse(agent);
    const result = await fetchAgent("bot1");
    expect(result).toEqual(agent);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/agents/bot1",
      expect.any(Object),
    );
  });

  it("fetchGames calls correct endpoint", async () => {
    mockFetchResponse([]);
    await fetchGames();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/games",
      expect.any(Object),
    );
  });

  it("fetchGameDetail calls correct endpoint", async () => {
    mockFetchResponse({ id: 1, status: "active" });
    await fetchGameDetail(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/games/1",
      expect.any(Object),
    );
  });

  it("createGame sends POST with body", async () => {
    mockFetchResponse({ game_uuid: "abc", game_id: 1 });
    const body = {
      mode: "player" as const,
      agent_ids: ["bot1"],
      starting_chips: 1000,
      num_players: 2,
    };
    await createGame(body);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/games",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(body),
      }),
    );
  });

  it("fetchHands calls correct endpoint", async () => {
    mockFetchResponse([]);
    await fetchHands(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/games/1/hands",
      expect.any(Object),
    );
  });

  it("fetchCosts calls correct endpoint", async () => {
    mockFetchResponse({ summary: {}, records: [] });
    await fetchCosts();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/costs",
      expect.any(Object),
    );
  });

  it("fetchProviders calls correct endpoint", async () => {
    mockFetchResponse({ providers: ["openai"] });
    await fetchProviders();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/config/providers",
      expect.any(Object),
    );
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetchError(404, "Not found");
    await expect(fetchAgent("missing")).rejects.toThrow(ApiError);
  });

  it("ApiError has status and data", async () => {
    mockFetchError(400, "Bad request");
    try {
      await fetchAgent("bad");
      expect.fail("should throw");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(400);
    }
  });
});
