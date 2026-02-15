"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.api.websocket_handler import connection_manager, parse_client_message
from llm_holdem.config import get_settings
from llm_holdem.db.database import close_db, get_engine, init_db
from llm_holdem.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan handler for startup and shutdown."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, logfire_token=settings.logfire_token)
    logger.info("LLM Hold'Em Tournament starting up")
    logger.info("Available providers: %s", settings.available_providers())

    # Initialize database
    await init_db(settings.database_url)
    logger.info("Database initialized")

    yield

    # Shutdown
    await close_db()
    logger.info("LLM Hold'Em Tournament shutting down")


app = FastAPI(
    title="LLM Hold'Em Tournament",
    description="Texas Hold'Em poker with LLM-powered opponents",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that provides an async database session.

    Yields:
        An AsyncSession with expire_on_commit=False.
    """
    settings = get_settings()
    engine = get_engine(settings.database_url)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/config/providers")
async def get_providers() -> dict[str, list[str]]:
    """Return list of available LLM providers."""
    settings = get_settings()
    return {"providers": settings.available_providers()}


# Register API routes
from llm_holdem.api.routes import router as api_router  # noqa: E402

app.include_router(api_router)


@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str) -> None:
    """WebSocket endpoint for real-time game communication.

    Enforces single session per game. Receives client messages and
    forwards them to the game coordinator (when available).

    Args:
        websocket: The WebSocket connection.
        game_id: The game identifier.
    """
    await connection_manager.connect(game_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = parse_client_message(data)
            if message is None:
                await connection_manager.send_error(
                    game_id,
                    "Invalid message format",
                    code="INVALID_MESSAGE",
                )
                continue

            # For now, acknowledge receipt. The game coordinator
            # (Phase 2.8) will handle actual game logic.
            logger.debug("Received message for game %s: %s", game_id, message.type)

    except WebSocketDisconnect:
        connection_manager.disconnect(game_id)
        logger.info("Client disconnected from game %s", game_id)
    except Exception as e:
        logger.error("WebSocket error for game %s: %s", game_id, e)
        connection_manager.disconnect(game_id)

