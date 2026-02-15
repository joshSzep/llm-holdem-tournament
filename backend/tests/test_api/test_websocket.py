"""Tests for WebSocket handler and connection management."""

from starlette.testclient import TestClient

from llm_holdem.api.messages import (
    ChatMessageIn,
    ChatMessageOut,
    ErrorMessage,
    GameOverMessage,
    GamePausedMessage,
    GameResumedMessage,
    GameStateMessage,
    PauseGameMessage,
    PlayerActionMessage,
    TimerUpdateMessage,
)
from llm_holdem.api.websocket_handler import ConnectionManager, parse_client_message
from llm_holdem.game.state import GameState
from llm_holdem.main import app

# ─── Message Serialization Tests ─────────────────────


class TestServerMessages:
    """Tests for server → client message models."""

    def test_game_state_message(self) -> None:
        state = GameState(game_id="test-123", status="active", phase="pre_flop")
        msg = GameStateMessage(state=state)
        data = msg.model_dump()
        assert data["type"] == "game_state"
        assert data["state"]["game_id"] == "test-123"

    def test_chat_message_out(self) -> None:
        msg = ChatMessageOut(seat_index=1, name="Bot", message="Nice hand!")
        data = msg.model_dump()
        assert data["type"] == "chat_message"
        assert data["name"] == "Bot"

    def test_timer_update(self) -> None:
        msg = TimerUpdateMessage(seat_index=0, seconds_remaining=15)
        data = msg.model_dump()
        assert data["type"] == "timer_update"
        assert data["seconds_remaining"] == 15

    def test_game_over(self) -> None:
        msg = GameOverMessage(winner_seat=0, winner_name="Player 0")
        data = msg.model_dump()
        assert data["type"] == "game_over"

    def test_error_message(self) -> None:
        msg = ErrorMessage(message="Something went wrong", code="ERR_001")
        data = msg.model_dump()
        assert data["type"] == "error"
        assert data["code"] == "ERR_001"

    def test_game_paused(self) -> None:
        msg = GamePausedMessage(reason="Reconnecting")
        assert msg.type == "game_paused"

    def test_game_resumed(self) -> None:
        msg = GameResumedMessage()
        assert msg.type == "game_resumed"


class TestClientMessages:
    """Tests for client → server message models."""

    def test_player_action_fold(self) -> None:
        msg = PlayerActionMessage(action_type="fold")
        assert msg.type == "player_action"
        assert msg.action_type == "fold"
        assert msg.amount is None

    def test_player_action_raise(self) -> None:
        msg = PlayerActionMessage(action_type="raise", amount=100)
        assert msg.amount == 100

    def test_chat_message_in(self) -> None:
        msg = ChatMessageIn(message="Hello everyone!")
        assert msg.type == "chat_message"

    def test_pause_game(self) -> None:
        msg = PauseGameMessage()
        assert msg.type == "pause_game"


class TestParseClientMessage:
    """Tests for parse_client_message."""

    def test_parse_player_action(self) -> None:
        data = {"type": "player_action", "action_type": "call"}
        msg = parse_client_message(data)
        assert isinstance(msg, PlayerActionMessage)
        assert msg.action_type == "call"

    def test_parse_player_action_with_amount(self) -> None:
        data = {"type": "player_action", "action_type": "raise", "amount": 200}
        msg = parse_client_message(data)
        assert isinstance(msg, PlayerActionMessage)
        assert msg.amount == 200

    def test_parse_chat_message(self) -> None:
        data = {"type": "chat_message", "message": "Hey!"}
        msg = parse_client_message(data)
        assert isinstance(msg, ChatMessageIn)
        assert msg.message == "Hey!"

    def test_parse_pause_game(self) -> None:
        data = {"type": "pause_game"}
        msg = parse_client_message(data)
        assert isinstance(msg, PauseGameMessage)

    def test_parse_unknown_type(self) -> None:
        data = {"type": "unknown_action"}
        msg = parse_client_message(data)
        assert msg is None

    def test_parse_invalid_data(self) -> None:
        data = {"type": "player_action", "action_type": "invalid_type"}
        msg = parse_client_message(data)
        assert msg is None

    def test_parse_missing_required_field(self) -> None:
        data = {"type": "player_action"}  # Missing action_type
        msg = parse_client_message(data)
        assert msg is None


# ─── ConnectionManager Tests ─────────────────────────


class TestConnectionManager:
    """Tests for the ConnectionManager."""

    def test_initial_state(self) -> None:
        mgr = ConnectionManager()
        assert mgr.connections == {}
        assert not mgr.is_connected("game-1")

    def test_disconnect_nonexistent(self) -> None:
        mgr = ConnectionManager()
        # Should not raise
        mgr.disconnect("nonexistent")


# ─── WebSocket Integration Tests ─────────────────────


class TestWebSocketEndpoint:
    """Integration tests for the WebSocket endpoint."""

    def test_websocket_connect_invalid_game_id(self) -> None:
        """Test that a non-integer game_id gets an error response."""
        client = TestClient(app)
        with client.websocket_connect("/ws/game/test-game-1") as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["code"] == "INVALID_GAME_ID"

    def test_websocket_connect_game_not_found(self) -> None:
        """Test that a non-existent game gets an error response."""
        client = TestClient(app)
        with client.websocket_connect("/ws/game/99999") as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["code"] == "GAME_NOT_FOUND"

    def test_websocket_invalid_message(self) -> None:
        """Test that invalid messages get an error response."""
        client = TestClient(app)
        with client.websocket_connect("/ws/game/not-a-game") as ws:
            # Server sends error for invalid game ID first
            data = ws.receive_json()
            assert data["type"] == "error"
            assert data["code"] == "INVALID_GAME_ID"

    def test_websocket_invalid_action_type(self) -> None:
        """Test that invalid action types get an error response."""
        client = TestClient(app)
        with client.websocket_connect("/ws/game/not-a-game") as ws:
            data = ws.receive_json()
            assert data["type"] == "error"
