"""FastAPI application entry point."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel.ext.asyncio.session import AsyncSession

from llm_holdem.api.messages import ChatMessageIn, PauseGameMessage, PlayerActionMessage
from llm_holdem.api.websocket_handler import connection_manager, parse_client_message
from llm_holdem.config import get_settings
from llm_holdem.db.database import close_db, get_engine, init_db
from llm_holdem.db.repository import get_game_by_id, get_game_players
from llm_holdem.game.coordinator import GameCoordinator
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState
from llm_holdem.logging_config import setup_logging

logger = logging.getLogger(__name__)

# Active game coordinators keyed by game_id (URL string)
_active_games: dict[str, tuple[GameCoordinator, asyncio.Task]] = {}


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
    engine = await get_engine(settings.database_url)
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

    Connects the client, starts or reconnects to the GameCoordinator,
    and routes incoming messages (actions, pause, chat) to the coordinator.

    Args:
        websocket: The WebSocket connection.
        game_id: The game identifier (database integer ID as string).
    """
    # Lazy import to avoid circular dependency with routes.py
    from llm_holdem.api.routes import get_agent_registry

    await connection_manager.connect(game_id, websocket)

    coordinator: GameCoordinator | None = None
    game_task: asyncio.Task | None = None

    try:
        # Check for existing active coordinator (reconnection)
        if game_id in _active_games:
            existing_coordinator, existing_task = _active_games[game_id]
            if not existing_task.done():
                coordinator = existing_coordinator
                game_task = existing_task
                await coordinator._broadcast_state()
                logger.info("Reconnected to active game %s", game_id)
            else:
                del _active_games[game_id]

        if coordinator is None:
            # Validate game_id is a valid integer
            try:
                game_id_int = int(game_id)
            except ValueError:
                await connection_manager.send_error(
                    game_id, "Invalid game ID", code="INVALID_GAME_ID"
                )
                return

            # Start a new game
            settings = get_settings()
            db_engine = await get_engine(settings.database_url)

            async with AsyncSession(db_engine, expire_on_commit=False) as session:
                game = await get_game_by_id(session, game_id_int)
                if game is None:
                    await connection_manager.send_error(
                        game_id, "Game not found", code="GAME_NOT_FOUND"
                    )
                    return

                if game.status == "completed":
                    await connection_manager.send_error(
                        game_id,
                        "Game already completed",
                        code="GAME_COMPLETED",
                    )
                    return

                db_players = await get_game_players(session, game.id)
                game_db_id = game.id
                game_mode = game.mode

            # Build PlayerState list from DB records
            player_states = [
                PlayerState(
                    seat_index=p.seat_index,
                    agent_id=p.agent_id,
                    name=p.name,
                    avatar_url=p.avatar_url,
                    chips=p.starting_chips,
                )
                for p in db_players
            ]

            # Create engine — use game_id string as the engine ID so
            # ConnectionManager routing matches the WebSocket key.
            game_engine = GameEngine(players=player_states)
            game_engine.game_id = game_id

            # Create coordinator
            registry = get_agent_registry()
            coordinator = GameCoordinator(
                engine=game_engine,
                game_db_id=game_db_id,
                connection_manager=connection_manager,
                agent_registry=registry,
                use_llm=True,
                ai_delay=1.0,
            )

            # Run game in a background task with its own DB session
            async def _run_game_task(
                coord: GameCoordinator, gid: str, db_eng: object
            ) -> None:
                game_session = AsyncSession(db_eng, expire_on_commit=False)
                try:
                    await coord.run_game(game_session)
                except asyncio.CancelledError:
                    logger.info("Game %s task cancelled", gid)
                except Exception:
                    logger.exception("Game %s task error", gid)
                finally:
                    await game_session.close()
                    _active_games.pop(gid, None)

            game_task = asyncio.create_task(
                _run_game_task(coordinator, game_id, db_engine)
            )
            _active_games[game_id] = (coordinator, game_task)
            logger.info(
                "Started game %s (mode=%s, players=%d)",
                game_id,
                game_mode,
                len(player_states),
            )

        # ── Message loop ──────────────────────────────────
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

            if isinstance(message, PlayerActionMessage):
                coordinator.receive_player_action(message)
            elif isinstance(message, PauseGameMessage):
                if coordinator.is_paused:
                    coordinator.resume()
                else:
                    coordinator.pause()
            elif isinstance(message, ChatMessageIn):
                logger.debug(
                    "Chat from human in game %s: %s", game_id, message.message
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected from game %s", game_id)
    except Exception:
        logger.exception("WebSocket error for game %s", game_id)
    finally:
        # Only disconnect if our websocket is still the registered one
        # (avoids removing a newer reconnected session)
        current_ws = connection_manager.connections.get(game_id)
        if current_ws is websocket:
            connection_manager.disconnect(game_id)

