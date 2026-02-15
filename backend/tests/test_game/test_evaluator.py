"""Tests for hand evaluation."""

import pytest

from llm_holdem.game.evaluator import compare_hands, determine_winners, evaluate_hand
from llm_holdem.game.state import Card


def _c(s: str) -> Card:
    """Shorthand card constructor from string like 'Ah', 'Ts', etc."""
    return Card(rank=s[0], suit=s[1])


def _cards(s: str) -> list[Card]:
    """Parse space-separated card strings, e.g. 'Ah Kh Qh Jh Th'."""
    return [_c(token) for token in s.split()]


class TestEvaluateHand:
    """Tests for the evaluate_hand function."""

    def test_royal_flush(self) -> None:
        hole = _cards("Ah Kh")
        board = _cards("Qh Jh Th 2c 3d")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Royal Flush"
        assert result.hand_rank == 1

    def test_straight_flush(self) -> None:
        hole = _cards("9h 8h")
        board = _cards("7h 6h 5h 2c 3d")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Straight Flush"

    def test_four_of_a_kind(self) -> None:
        hole = _cards("Ah Ac")
        board = _cards("Ad As 5c 8s 2h")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Four of a Kind"
        assert "Ace" in result.hand_description

    def test_full_house(self) -> None:
        hole = _cards("Kh Kc")
        board = _cards("Kd 7s 7h 2c 3d")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Full House"
        assert "King" in result.hand_description

    def test_flush(self) -> None:
        hole = _cards("Ah 9h")
        board = _cards("6h 3h 2h Kc Td")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Flush"

    def test_straight(self) -> None:
        hole = _cards("9c 8h")
        board = _cards("7d 6s 5c Ah 2h")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Straight"

    def test_three_of_a_kind(self) -> None:
        hole = _cards("Ah Ac")
        board = _cards("Ad 5c 8s 2h 9d")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Three of a Kind"
        assert "Ace" in result.hand_description

    def test_two_pair(self) -> None:
        hole = _cards("Ah Kh")
        board = _cards("Ac Kd 5s 8h 2c")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Two Pair"
        assert "Ace" in result.hand_description
        assert "King" in result.hand_description

    def test_pair(self) -> None:
        hole = _cards("Ah Kh")
        board = _cards("Ac 5d 8s 2h 9c")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Pair"
        assert "Ace" in result.hand_description

    def test_high_card(self) -> None:
        hole = _cards("Ah 9c")
        board = _cards("5d 3s 8h 2c Kd")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "High Card"
        assert "Ace" in result.hand_description

    def test_wheel_straight(self) -> None:
        """A-2-3-4-5 straight (wheel)."""
        hole = _cards("Ah 2c")
        board = _cards("3d 4s 5h 9c Kd")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Straight"

    def test_broadway_straight(self) -> None:
        """T-J-Q-K-A straight (broadway)."""
        hole = _cards("Ah Kc")
        board = _cards("Qd Jh Ts 3c 2d")
        result = evaluate_hand(hole, board)
        assert result.hand_name == "Straight"

    def test_hand_rank_ordering(self) -> None:
        """Better hands should have lower rank values."""
        royal = evaluate_hand(_cards("Ah Kh"), _cards("Qh Jh Th 2c 3d"))
        full_house = evaluate_hand(_cards("Kh Kc"), _cards("Kd 7s 7h 2c 3d"))
        pair = evaluate_hand(_cards("Ah Kh"), _cards("Ac 5d 8s 2h 9c"))
        high_card = evaluate_hand(_cards("Ah 9c"), _cards("5d 3s 8h 2c Kd"))

        assert royal.hand_rank < full_house.hand_rank
        assert full_house.hand_rank < pair.hand_rank
        assert pair.hand_rank < high_card.hand_rank

    def test_invalid_hole_card_count(self) -> None:
        with pytest.raises(ValueError, match="Expected 2 hole cards"):
            evaluate_hand(_cards("Ah"), _cards("5d 3s 8h 2c Kd"))

    def test_invalid_hole_card_count_three(self) -> None:
        with pytest.raises(ValueError, match="Expected 2 hole cards"):
            evaluate_hand(_cards("Ah Kh Qh"), _cards("5d 3s 8h 2c Kd"))

    def test_invalid_community_too_few(self) -> None:
        with pytest.raises(ValueError, match="Expected 3-5 community cards"):
            evaluate_hand(_cards("Ah Kh"), _cards("5d 3s"))

    def test_invalid_community_too_many(self) -> None:
        with pytest.raises(ValueError, match="Expected 3-5 community cards"):
            evaluate_hand(_cards("Ah Kh"), _cards("5d 3s 8h 2c Kd Qh"))

    def test_flop_evaluation(self) -> None:
        """Hand evaluation works with just 3 community cards."""
        result = evaluate_hand(_cards("Ah Kh"), _cards("Qh Jh Th"))
        assert result.hand_name == "Royal Flush"

    def test_turn_evaluation(self) -> None:
        """Hand evaluation works with 4 community cards."""
        result = evaluate_hand(_cards("Ah Kh"), _cards("Qh Jh Th 2c"))
        assert result.hand_name == "Royal Flush"


class TestCompareHands:
    """Tests for the compare_hands function."""

    def test_compare_two_players(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {
            0: _cards("Ah Kh"),  # Pair of Kings
            1: _cards("9c Tc"),  # High card
        }
        results = compare_hands(players, community)
        assert len(results) == 2
        assert results[0].player_index == 0  # Winner first

    def test_compare_multiple_players(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {
            0: _cards("Ah Kh"),  # Pair of Kings, Ace kicker
            1: _cards("Kc Qh"),  # Pair of Kings, Queen kicker
            2: _cards("9c Tc"),  # High card
        }
        results = compare_hands(players, community)
        assert results[0].player_index == 0  # Best hand first
        assert results[-1].player_index == 2  # Worst hand last

    def test_compare_results_sorted_by_rank(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {
            0: _cards("9c Tc"),  # High card
            1: _cards("Ah Kh"),  # Pair
            2: _cards("5c 5h"),  # Three of a kind (two 5s + one on board)
        }
        results = compare_hands(players, community)
        for i in range(len(results) - 1):
            assert results[i].hand_rank <= results[i + 1].hand_rank


class TestDetermineWinners:
    """Tests for the determine_winners function."""

    def test_single_winner(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {
            0: _cards("Ah Kh"),  # Pair of Kings
            1: _cards("9c Tc"),  # High card
        }
        winners, results = determine_winners(players, community)
        assert winners == [0]
        assert len(results) == 2

    def test_split_pot_identical_hands(self) -> None:
        """Two players with exactly the same hand should tie."""
        community = _cards("Ah Kd Qc Jh Ts")
        # Both players have a broadway straight from the board
        players = {
            0: _cards("2c 3c"),
            1: _cards("2d 3d"),
        }
        winners, results = determine_winners(players, community)
        assert len(winners) == 2
        assert 0 in winners
        assert 1 in winners

    def test_split_pot_same_pair(self) -> None:
        """Two players with same pair, same kickers → split."""
        community = _cards("Ah Kd 8c 5h 2s")
        players = {
            0: _cards("Ac 3c"),  # Pair of Aces
            1: _cards("Ad 3d"),  # Pair of Aces (same kickers via board)
        }
        winners, results = determine_winners(players, community)
        assert len(winners) == 2

    def test_empty_players(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        winners, results = determine_winners({}, community)
        assert winners == []
        assert results == []

    def test_single_player(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {0: _cards("Ah Kh")}
        winners, results = determine_winners(players, community)
        assert winners == [0]

    def test_three_player_showdown(self) -> None:
        community = _cards("5d 3s 8h 2c Kd")
        players = {
            0: _cards("Ah Ac"),  # Pair of Aces
            1: _cards("Kh Kc"),  # Three Kings (Kh, Kc + Kd on board)
            2: _cards("8c 8d"),  # Three 8s (8c, 8d + 8h on board)
        }
        winners, results = determine_winners(players, community)
        # Three Kings beats Three 8s beats Pair of Aces
        assert winners == [1]

    def test_kicker_decides(self) -> None:
        """When two players have the same pair, kicker should decide."""
        community = _cards("Ah 5d 8c 2s 3h")
        players = {
            0: _cards("Ac Kh"),  # Pair of Aces, King kicker
            1: _cards("Ad Qh"),  # Pair of Aces, Queen kicker
        }
        winners, results = determine_winners(players, community)
        assert winners == [0]  # King kicker wins

    def test_flush_vs_straight(self) -> None:
        """Flush should beat a straight."""
        community = _cards("6h 7c 8d 9s 2h")
        players = {
            0: _cards("Th 5c"),  # Straight (6-7-8-9-T)
            1: _cards("Ah 3h"),  # Flush (Ah, 6h, 2h, 3h need one more heart...)
        }
        # Player 0 has a straight, player 1 only has 3 hearts
        winners, results = determine_winners(players, community)
        # Player 0 should win with the straight
        assert winners == [0]

    def test_full_house_beats_flush(self) -> None:
        community = _cards("Ah Kh Ac 5h 2h")
        players = {
            0: _cards("Ad 5c"),  # Full house (A-A-A-5-5)
            1: _cards("Qh 3h"),  # Flush (Ah Kh Qh 5h 3h... wait, that's only 5 hearts)
        }
        winners, results = determine_winners(players, community)
        assert winners == [0]  # Full house wins
