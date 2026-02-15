"""Tests for REST API endpoints."""

import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.main import app
from llm_holdem.main import get_session


@pytest.fixture
async def engine():
    """Create an in-memory async engine with tables."""
    eng = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def override_session(engine):
    """Override the FastAPI session dependency for testing."""

    async def _get_test_session():
        async with AsyncSession(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = _get_test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_session):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ─── Health Check ─────────────────────────────────────


class TestHealthCheck:
    """Tests for health check endpoint."""

    async def test_health_check(self, client: AsyncClient) -> None:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ─── Providers ────────────────────────────────────────


class TestProviders:
    """Tests for provider configuration endpoint."""

    async def test_get_providers(self, client: AsyncClient) -> None:
        resp = await client.get("/api/config/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
        # Ollama is always included
        assert "ollama" in data["providers"]


# ─── Agents ───────────────────────────────────────────


class TestAgents:
    """Tests for agent endpoints."""

    async def test_list_agents(self, client: AsyncClient) -> None:
        resp = await client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        # Without API keys, only ollama agents are available (5)
        assert len(data["agents"]) >= 5

    async def test_get_agent_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/agents/hometown-henry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Hometown Henry"

    async def test_get_agent_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/agents/nonexistent")
        assert resp.status_code == 404


# ─── Games ────────────────────────────────────────────


class TestGames:
    """Tests for game endpoints."""

    async def test_create_game(self, client: AsyncClient) -> None:
        resp = await client.post("/api/games", json={
            "mode": "player",
            "agent_ids": ["hometown-henry", "rookie-rachel"],
            "starting_chips": 1000,
            "num_players": 3,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "game_uuid" in data
        assert "game_id" in data

    async def test_create_spectator_game(self, client: AsyncClient) -> None:
        resp = await client.post("/api/games", json={
            "mode": "spectator",
            "agent_ids": ["hometown-henry", "rookie-rachel"],
            "starting_chips": 500,
            "num_players": 2,
        })
        assert resp.status_code == 201

    async def test_list_games_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/games")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_games_with_data(self, client: AsyncClient) -> None:
        # Create a game first
        await client.post("/api/games", json={
            "mode": "player",
            "agent_ids": ["hometown-henry"],
            "starting_chips": 1000,
            "num_players": 2,
        })
        resp = await client.get("/api/games")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "waiting"
        assert data[0]["player_count"] == 2

    async def test_get_game_detail(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/games", json={
            "mode": "player",
            "agent_ids": ["hometown-henry"],
            "starting_chips": 1000,
            "num_players": 2,
        })
        game_id = create_resp.json()["game_id"]

        resp = await client.get(f"/api/games/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_uuid"] == create_resp.json()["game_uuid"]
        assert len(data["players"]) == 2
        # First player should be human
        human = next(p for p in data["players"] if p["seat_index"] == 0)
        assert human["is_human"] is True
        assert human["name"] == "You"

    async def test_get_game_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/games/9999")
        assert resp.status_code == 404


# ─── Hands ────────────────────────────────────────────


class TestHands:
    """Tests for hand history endpoints."""

    async def test_get_hands_empty(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/games", json={
            "mode": "player",
            "agent_ids": ["hometown-henry"],
            "starting_chips": 1000,
            "num_players": 2,
        })
        game_id = create_resp.json()["game_id"]

        resp = await client.get(f"/api/games/{game_id}/hands")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_hands_game_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/games/9999/hands")
        assert resp.status_code == 404

    async def test_get_hand_not_found(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/games", json={
            "mode": "player",
            "agent_ids": ["hometown-henry"],
            "starting_chips": 1000,
            "num_players": 2,
        })
        game_id = create_resp.json()["game_id"]

        resp = await client.get(f"/api/games/{game_id}/hands/1")
        assert resp.status_code == 404


# ─── Costs ────────────────────────────────────────────


class TestCosts:
    """Tests for cost tracking endpoints."""

    async def test_get_costs_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/costs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_cost"] == 0
        assert data["summary"]["call_count"] == 0
        assert data["records"] == []
