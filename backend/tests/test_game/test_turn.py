"""Tests for turn order management."""

from llm_holdem.game.state import PlayerState
from llm_holdem.game.turn import TurnManager


def _make_players(
    num: int,
    folded: set[int] | None = None,
    all_in: set[int] | None = None,
    eliminated: set[int] | None = None,
) -> list[PlayerState]:
    """Create a list of test players.

    Args:
        num: Number of players to create.
        folded: Set of seat indices that are folded.
        all_in: Set of seat indices that are all-in.
        eliminated: Set of seat indices that are eliminated.
    """
    folded = folded or set()
    all_in = all_in or set()
    eliminated = eliminated or set()
    return [
        PlayerState(
            seat_index=i,
            name=f"Player {i}",
            chips=1000,
            is_folded=i in folded,
            is_all_in=i in all_in,
            is_eliminated=i in eliminated,
        )
        for i in range(num)
    ]


class TestDealerButton:
    """Tests for dealer button management."""

    def test_advance_dealer(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6)
        new_pos = tm.advance_dealer(players)
        assert new_pos == 1

    def test_advance_dealer_wraps_around(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 5
        players = _make_players(6)
        new_pos = tm.advance_dealer(players)
        assert new_pos == 0

    def test_advance_dealer_skips_eliminated(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, eliminated={1, 2})
        new_pos = tm.advance_dealer(players)
        assert new_pos == 3

    def test_advance_dealer_all_eliminated_stays(self) -> None:
        tm = TurnManager(3)
        tm.dealer_position = 0
        players = _make_players(3, eliminated={0, 1, 2})
        new_pos = tm.advance_dealer(players)
        assert new_pos == 0  # No movement possible


class TestBlindPositions:
    """Tests for blind position calculation."""

    def test_three_players(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, eliminated={3, 4, 5})
        sb, bb = tm.get_blind_positions(players)
        # Dealer=0, SB=1, BB=2
        assert sb == 1
        assert bb == 2

    def test_six_players(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 2
        players = _make_players(6)
        sb, bb = tm.get_blind_positions(players)
        # Dealer=2, SB=3, BB=4
        assert sb == 3
        assert bb == 4

    def test_heads_up_dealer_is_sb(self) -> None:
        """In heads-up, the dealer is the SB."""
        tm = TurnManager(6)
        tm.dealer_position = 1
        players = _make_players(6, eliminated={0, 2, 3, 4})
        # Active: seats 1 and 5
        sb, bb = tm.get_blind_positions(players)
        assert sb == 1  # Dealer is SB
        assert bb == 5  # Other player is BB

    def test_heads_up_wrapping(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 5
        players = _make_players(6, eliminated={1, 2, 3, 4})
        # Active: seats 0 and 5
        sb, bb = tm.get_blind_positions(players)
        assert sb == 5  # Dealer is SB
        assert bb == 0

    def test_skips_eliminated_for_blinds(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, eliminated={1, 3, 5})
        # Active: 0, 2, 4
        sb, bb = tm.get_blind_positions(players)
        assert sb == 2  # Next active after dealer
        assert bb == 4  # Next active after SB


class TestPreflopOrder:
    """Tests for pre-flop turn order."""

    def test_six_players_preflop(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6)
        # SB=1, BB=2
        order = tm.get_preflop_order(players, bb_seat=2)
        # Action goes: left of BB (3, 4, 5, 0, 1, 2)
        assert order == [3, 4, 5, 0, 1, 2]

    def test_three_players_preflop(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, eliminated={3, 4, 5})
        order = tm.get_preflop_order(players, bb_seat=2)
        # Active: 0, 1, 2. BB=2 acts last
        assert order == [0, 1, 2]

    def test_heads_up_preflop(self) -> None:
        """Heads-up pre-flop: SB (dealer) acts first."""
        tm = TurnManager(6)
        tm.dealer_position = 1
        players = _make_players(6, eliminated={0, 2, 3, 4})
        # Active: 1, 5. Dealer/SB=1, BB=5
        order = tm.get_preflop_order(players, bb_seat=5)
        # SB acts first pre-flop in heads-up
        assert order == [1, 5]

    def test_skips_folded(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, folded={3, 5})
        order = tm.get_preflop_order(players, bb_seat=2)
        assert 3 not in order
        assert 5 not in order

    def test_skips_all_in(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, all_in={4})
        order = tm.get_preflop_order(players, bb_seat=2)
        assert 4 not in order

    def test_empty_order_all_folded(self) -> None:
        tm = TurnManager(3)
        players = _make_players(3, folded={0, 1, 2})
        order = tm.get_preflop_order(players, bb_seat=2)
        assert order == []


class TestPostflopOrder:
    """Tests for post-flop turn order."""

    def test_six_players_postflop(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6)
        order = tm.get_postflop_order(players)
        # Post-flop starts left of dealer
        assert order == [1, 2, 3, 4, 5, 0]

    def test_postflop_skips_folded(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 0
        players = _make_players(6, folded={2, 4})
        order = tm.get_postflop_order(players)
        assert order == [1, 3, 5, 0]

    def test_heads_up_postflop(self) -> None:
        """Heads-up post-flop: BB (non-dealer) acts first."""
        tm = TurnManager(6)
        tm.dealer_position = 1
        players = _make_players(6, eliminated={0, 2, 3, 4})
        # Active: 1, 5. Post-flop: left of dealer first
        order = tm.get_postflop_order(players)
        assert order == [5, 1]  # BB first, dealer/SB last


class TestNextPlayer:
    """Tests for getting the next player."""

    def test_next_player_simple(self) -> None:
        tm = TurnManager(6)
        players = _make_players(6)
        nxt = tm.get_next_player(0, players)
        assert nxt == 1

    def test_next_player_wraps(self) -> None:
        tm = TurnManager(6)
        players = _make_players(6)
        nxt = tm.get_next_player(5, players)
        assert nxt == 0

    def test_next_player_skips_folded(self) -> None:
        tm = TurnManager(6)
        players = _make_players(6, folded={1, 2})
        nxt = tm.get_next_player(0, players)
        assert nxt == 3

    def test_next_player_no_one(self) -> None:
        tm = TurnManager(3)
        players = _make_players(3, folded={0, 1, 2})
        nxt = tm.get_next_player(0, players)
        assert nxt is None

    def test_repr(self) -> None:
        tm = TurnManager(6)
        tm.dealer_position = 3
        assert "seats=6" in repr(tm)
        assert "dealer=3" in repr(tm)
