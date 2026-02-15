"""Tests for prompt builder."""

from llm_holdem.agents.prompt import (
    build_action_prompt,
    build_chat_prompt,
    format_action,
    format_card,
    format_cards,
    format_player_info,
    format_pot_info,
)
from llm_holdem.game.state import Action, Card, GameState, PlayerState, Pot


def _make_game_state() -> GameState:
    """Create a test game state."""
    return GameState(
        game_id="test-game",
        hand_number=3,
        phase="flop",
        small_blind=10,
        big_blind=20,
        players=[
            PlayerState(
                seat_index=0,
                name="Human",
                chips=900,
                hole_cards=[Card(rank="A", suit="s"), Card(rank="K", suit="s")],
                current_bet=20,
            ),
            PlayerState(
                seat_index=1,
                agent_id="tight-tony",
                name="Tight Tony",
                chips=1100,
                hole_cards=[Card(rank="Q", suit="h"), Card(rank="J", suit="h")],
                current_bet=20,
            ),
            PlayerState(
                seat_index=2,
                agent_id="bluff-betty",
                name="Bluff Betty",
                chips=1000,
                is_folded=True,
            ),
        ],
        community_cards=[
            Card(rank="T", suit="s"),
            Card(rank="9", suit="s"),
            Card(rank="2", suit="d"),
        ],
        pots=[Pot(amount=60, eligible_players=[0, 1])],
        current_bet=20,
        current_hand_actions=[
            Action(player_index=0, action_type="post_blind", amount=10),
            Action(player_index=1, action_type="post_blind", amount=20),
            Action(player_index=2, action_type="fold"),
            Action(player_index=0, action_type="call", amount=20),
        ],
    )


class TestFormatCard:
    """Tests for card formatting."""

    def test_ace_of_spades(self) -> None:
        assert format_card(Card(rank="A", suit="s")) == "As"

    def test_ten_of_hearts(self) -> None:
        assert format_card(Card(rank="T", suit="h")) == "Th"

    def test_format_cards_list(self) -> None:
        cards = [Card(rank="A", suit="s"), Card(rank="K", suit="h")]
        assert format_cards(cards) == "As Kh"

    def test_format_cards_empty(self) -> None:
        assert format_cards([]) == "none"


class TestFormatPlayerInfo:
    """Tests for player info formatting."""

    def test_active_player(self) -> None:
        player = PlayerState(seat_index=0, name="Alice", chips=1000, current_bet=50)
        result = format_player_info(player, viewer_seat=0, show_hole_cards=False)
        assert "Alice" in result
        assert "1000" in result
        assert "50" in result

    def test_folded_player(self) -> None:
        player = PlayerState(seat_index=1, name="Bob", chips=500, is_folded=True)
        result = format_player_info(player, viewer_seat=0)
        assert "FOLDED" in result

    def test_all_in_player(self) -> None:
        player = PlayerState(seat_index=2, name="Carol", chips=0, is_all_in=True)
        result = format_player_info(player, viewer_seat=0)
        assert "ALL-IN" in result

    def test_show_own_hole_cards(self) -> None:
        player = PlayerState(
            seat_index=0, name="Alice", chips=1000,
            hole_cards=[Card(rank="A", suit="s"), Card(rank="K", suit="s")],
        )
        result = format_player_info(player, viewer_seat=0, show_hole_cards=True)
        assert "As" in result
        assert "Ks" in result

    def test_hide_opponent_hole_cards(self) -> None:
        player = PlayerState(
            seat_index=1, name="Bot", chips=1000,
            hole_cards=[Card(rank="Q", suit="h"), Card(rank="J", suit="h")],
        )
        result = format_player_info(player, viewer_seat=0, show_hole_cards=True)
        assert "Qh" not in result
        assert "Jh" not in result

    def test_eliminated_player(self) -> None:
        player = PlayerState(seat_index=3, name="Elim", chips=0, is_eliminated=True)
        result = format_player_info(player, viewer_seat=0)
        assert "ELIMINATED" in result


class TestFormatAction:
    """Tests for action formatting."""

    def test_fold(self) -> None:
        assert "folds" in format_action(Action(player_index=0, action_type="fold"))

    def test_check(self) -> None:
        assert "checks" in format_action(Action(player_index=0, action_type="check"))

    def test_call(self) -> None:
        result = format_action(Action(player_index=0, action_type="call", amount=50))
        assert "calls" in result
        assert "50" in result

    def test_raise(self) -> None:
        result = format_action(Action(player_index=0, action_type="raise", amount=100))
        assert "raises to" in result
        assert "100" in result

    def test_post_blind(self) -> None:
        result = format_action(Action(player_index=0, action_type="post_blind", amount=10))
        assert "blind" in result
        assert "10" in result


class TestFormatPotInfo:
    """Tests for pot formatting."""

    def test_single_pot(self) -> None:
        state = GameState(pots=[Pot(amount=100, eligible_players=[0, 1])])
        result = format_pot_info(state)
        assert "Main pot" in result
        assert "100" in result

    def test_side_pots(self) -> None:
        state = GameState(pots=[
            Pot(amount=300, eligible_players=[0, 1, 2]),
            Pot(amount=200, eligible_players=[0, 1]),
        ])
        result = format_pot_info(state)
        assert "Main pot" in result
        assert "Side pot" in result

    def test_no_pots(self) -> None:
        state = GameState(pots=[])
        result = format_pot_info(state)
        assert "0" in result


class TestBuildActionPrompt:
    """Tests for full action prompt building."""

    def test_contains_game_info(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["fold", "check", "raise"],
        )
        assert "Hand #3" in prompt
        assert "flop" in prompt
        assert "10/20" in prompt  # blinds

    def test_contains_own_hole_cards(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["fold", "check"],
        )
        assert "As" in prompt
        assert "Ks" in prompt

    def test_does_not_contain_opponent_cards(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["fold", "check"],
        )
        # Opponent has Qh Jh — should not appear
        assert "Hole cards: Qh" not in prompt
        assert "Hole cards: Jh" not in prompt

    def test_contains_community_cards(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["fold", "check"],
        )
        assert "Ts" in prompt
        assert "9s" in prompt

    def test_contains_valid_actions(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["fold", "call", "raise"],
            min_raise_to=40,
            max_raise_to=900,
            call_amount=20,
        )
        assert "fold" in prompt
        assert "call" in prompt
        assert "raise" in prompt
        assert "40" in prompt  # min raise

    def test_contains_betting_history(self) -> None:
        state = _make_game_state()
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["check"],
        )
        assert "blind" in prompt.lower()

    def test_with_hand_history(self) -> None:
        state = _make_game_state()
        history = [
            {"hand_number": "1", "summary": "Tight Tony won 50 chips"},
            {"hand_number": "2", "summary": "Human won 100 chips"},
        ]
        prompt = build_action_prompt(
            game_state=state,
            seat_index=0,
            valid_actions=["check"],
            hand_history=history,
        )
        assert "Hand #1" in prompt
        assert "Hand #2" in prompt


class TestBuildChatPrompt:
    """Tests for chat prompt building."""

    def test_contains_event(self) -> None:
        state = _make_game_state()
        prompt = build_chat_prompt(
            game_state=state,
            seat_index=1,
            trigger_event="showdown",
            event_description="Tight Tony wins with a flush!",
        )
        assert "SHOWDOWN" in prompt
        assert "flush" in prompt

    def test_contains_recent_chat(self) -> None:
        state = _make_game_state()
        prompt = build_chat_prompt(
            game_state=state,
            seat_index=1,
            trigger_event="all_in",
            event_description="Player goes all-in",
            recent_chat=[
                {"name": "Human", "message": "Let's go!"},
                {"name": "Bluff Betty", "message": "Scared money don't make money!"},
            ],
        )
        assert "Let's go!" in prompt
        assert "Scared money" in prompt

    def test_contains_player_info(self) -> None:
        state = _make_game_state()
        prompt = build_chat_prompt(
            game_state=state,
            seat_index=1,
            trigger_event="big_pot",
            event_description="Big pot!",
        )
        assert "Human" in prompt
        assert "Tight Tony" in prompt
