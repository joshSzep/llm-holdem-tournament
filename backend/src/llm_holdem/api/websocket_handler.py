"""WebSocket handler for real-time game communication."""

import logging
from typing import Any

from fastapi import WebSocket
from pydantic import ValidationError

from llm_holdem.api.messages import (
    ChatMessageIn,
    ClientMessage,
    ErrorMessage,
    GameStateMessage,
    PauseGameMessage,
    PlayerActionMessage,
    ServerMessage,
)
from llm_holdem.game.state import GameState

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with single-session enforcement.

    Only one active connection per game is allowed. When a new connection
    arrives for a game that already has one, the old connection is closed.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        self._connections: dict[str, WebSocket] = {}

    @property
    def connections(self) -> dict[str, WebSocket]:
        """All active connections keyed by game_id."""
        return dict(self._connections)

    async def connect(self, game_id: str, websocket: WebSocket) -> None:
        """Accept a WebSocket connection for a game.

        If a connection already exists for this game, close the old one.

        Args:
            game_id: The game identifier.
            websocket: The WebSocket connection.
        """
        # Enforce single session per game
        if game_id in self._connections:
            old_ws = self._connections[game_id]
            logger.info("Closing existing connection for game %s", game_id)
            try:
                await old_ws.close(code=1000, reason="New connection established")
            except Exception:
                pass  # Old connection might already be closed

        await websocket.accept()
        self._connections[game_id] = websocket
        logger.info("WebSocket connected for game %s", game_id)

    def disconnect(self, game_id: str) -> None:
        """Remove a connection for a game.

        Args:
            game_id: The game identifier.
        """
        if game_id in self._connections:
            del self._connections[game_id]
            logger.info("WebSocket disconnected for game %s", game_id)

    def is_connected(self, game_id: str) -> bool:
        """Check if a game has an active connection.

        Args:
            game_id: The game identifier.

        Returns:
            True if connected.
        """
        return game_id in self._connections

    async def send_message(self, game_id: str, message: ServerMessage) -> None:
        """Send a server message to the connected client.

        Args:
            game_id: The game identifier.
            message: The message to send.
        """
        ws = self._connections.get(game_id)
        if ws is None:
            logger.warning("No connection for game %s, message dropped", game_id)
            return

        try:
            await ws.send_json(message.model_dump())
        except Exception as e:
            logger.error("Failed to send message to game %s: %s", game_id, e)
            self.disconnect(game_id)

    async def broadcast_game_state(self, game_id: str, state: GameState) -> None:
        """Broadcast the full game state to the connected client.

        Args:
            game_id: The game identifier.
            state: The complete game state.
        """
        msg = GameStateMessage(state=state)
        await self.send_message(game_id, msg)

    async def send_error(self, game_id: str, message: str, code: str = "") -> None:
        """Send an error message to the client.

        Args:
            game_id: The game identifier.
            message: Error description.
            code: Optional error code.
        """
        await self.send_message(game_id, ErrorMessage(message=message, code=code))


def parse_client_message(data: dict[str, Any]) -> ClientMessage | None:
    """Parse and validate a client message from raw JSON data.

    Args:
        data: Raw JSON dict from WebSocket.

    Returns:
        Parsed ClientMessage, or None if invalid.
    """
    msg_type = data.get("type")

    try:
        if msg_type == "player_action":
            return PlayerActionMessage(**data)
        elif msg_type == "chat_message":
            return ChatMessageIn(**data)
        elif msg_type == "pause_game":
            return PauseGameMessage(**data)
        else:
            logger.warning("Unknown client message type: %s", msg_type)
            return None
    except ValidationError as e:
        logger.warning("Invalid client message: %s", e)
        return None


# Singleton connection manager
connection_manager = ConnectionManager()
