"""Tests for pot management."""

from llm_holdem.game.pot import PotManager


class TestPotManagerBasics:
    """Basic pot operations."""

    def test_initial_state(self) -> None:
        pm = PotManager()
        assert pm.total == 0
        assert len(pm.pots) == 1
        assert pm.main_pot.amount == 0

    def test_add_bet(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        assert pm.total == 100
        assert 0 in pm.main_pot.eligible_players

    def test_add_multiple_bets(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        pm.add_bet(2, 100)
        assert pm.total == 300

    def test_add_zero_bet(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 0)
        assert pm.total == 0

    def test_player_contributions(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 50)
        pm.add_bet(0, 50)
        pm.add_bet(1, 100)
        assert pm.player_contributions == {0: 100, 1: 100}

    def test_reset(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 200)
        pm.reset()
        assert pm.total == 0
        assert len(pm.pots) == 1
        assert pm.player_contributions == {}

    def test_repr(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        assert "total=100" in repr(pm)

    def test_side_pots_empty(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        assert pm.side_pots == []


class TestPotDistribution:
    """Pot distribution scenarios."""

    def test_single_winner(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        winnings = pm.distribute_simple([0])
        assert winnings == {0: 200}

    def test_split_pot_even(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        winnings = pm.distribute_simple([0, 1])
        assert winnings == {0: 100, 1: 100}

    def test_split_pot_odd_chip(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 50)
        pm.add_bet(1, 51)
        # Total = 101, split between 2 = 50 each + 1 extra to first
        winnings = pm.distribute_simple([0, 1])
        assert winnings[0] == 51  # Gets the odd chip
        assert winnings[1] == 50
        assert sum(winnings.values()) == 101

    def test_three_way_split_with_remainder(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        pm.add_bet(2, 100)
        # 300 / 3 = 100 each, no remainder
        winnings = pm.distribute_simple([0, 1, 2])
        assert winnings == {0: 100, 1: 100, 2: 100}

    def test_three_way_split_uneven(self) -> None:
        pm = PotManager()
        pm.add_bet(0, 34)
        pm.add_bet(1, 33)
        pm.add_bet(2, 33)
        # Total = 100, 3 winners = 33 each + 1 extra to first
        winnings = pm.distribute_simple([0, 1, 2])
        assert sum(winnings.values()) == 100


class TestSidePots:
    """Side pot calculations for all-in scenarios."""

    def test_simple_all_in(self) -> None:
        """Player 0 all-in for 50, Player 1 bets 100."""
        pm = PotManager()
        pm.add_bet(0, 50)
        pm.add_bet(1, 100)

        pm.calculate_side_pots(
            all_in_amounts={0: 50},
            active_players=[0, 1],
        )

        assert len(pm.pots) == 2
        # Main pot: 50 from each = 100
        assert pm.pots[0].amount == 100
        assert sorted(pm.pots[0].eligible_players) == [0, 1]
        # Side pot: 50 extra from player 1
        assert pm.pots[1].amount == 50
        assert pm.pots[1].eligible_players == [1]

    def test_multiple_all_ins(self) -> None:
        """Three players all-in for different amounts."""
        pm = PotManager()
        pm.add_bet(0, 100)  # Short stack
        pm.add_bet(1, 300)  # Medium stack
        pm.add_bet(2, 500)  # Big stack

        pm.calculate_side_pots(
            all_in_amounts={0: 100, 1: 300},
            active_players=[0, 1, 2],
        )

        assert len(pm.pots) == 3
        # Pot 1: 100 from each = 300
        assert pm.pots[0].amount == 300
        assert sorted(pm.pots[0].eligible_players) == [0, 1, 2]
        # Pot 2: 200 from players 1 and 2 = 400
        assert pm.pots[1].amount == 400
        assert sorted(pm.pots[1].eligible_players) == [1, 2]
        # Pot 3: 200 from player 2 only
        assert pm.pots[2].amount == 200
        assert pm.pots[2].eligible_players == [2]

    def test_no_all_ins(self) -> None:
        """Without all-ins, should remain a single pot."""
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        pm.add_bet(2, 100)

        pm.calculate_side_pots(
            all_in_amounts={},
            active_players=[0, 1, 2],
        )

        assert len(pm.pots) == 1
        assert pm.pots[0].amount == 300
        assert sorted(pm.pots[0].eligible_players) == [0, 1, 2]

    def test_side_pot_with_fold(self) -> None:
        """Player 2 folds; player 0 all-in; player 1 calls."""
        pm = PotManager()
        pm.add_bet(0, 50)
        pm.add_bet(1, 100)
        pm.add_bet(2, 20)  # Folded after posting blind

        pm.calculate_side_pots(
            all_in_amounts={0: 50},
            active_players=[0, 1],  # 2 is not active (folded)
        )

        # Main pot: 50 from each active + folded player's 20
        # Side pot: 50 extra from player 1
        assert len(pm.pots) == 2
        total = sum(p.amount for p in pm.pots)
        assert total == 170

    def test_side_pot_distribution(self) -> None:
        """Distribute side pots with different winners per pot."""
        pm = PotManager()
        pm.add_bet(0, 50)
        pm.add_bet(1, 100)

        pm.calculate_side_pots(
            all_in_amounts={0: 50},
            active_players=[0, 1],
        )

        # Player 0 wins main pot, player 1 wins side pot
        winnings = pm.distribute([[0], [1]])
        assert winnings[0] == 100  # Main pot
        assert winnings[1] == 50  # Side pot

    def test_side_pot_distribution_short_stack_wins(self) -> None:
        """Short-stack player wins: gets main pot, side pot goes to next best."""
        pm = PotManager()
        pm.add_bet(0, 100)  # All-in
        pm.add_bet(1, 300)
        pm.add_bet(2, 300)

        pm.calculate_side_pots(
            all_in_amounts={0: 100},
            active_players=[0, 1, 2],
        )

        # Player 0 has best hand, wins main pot
        # Player 2 has second best, wins side pot
        winnings = pm.distribute([[0], [2]])
        assert winnings[0] == 300  # Main pot (100 × 3)
        assert winnings[2] == 400  # Side pot (200 × 2)

    def test_same_all_in_amount(self) -> None:
        """Two players all-in for the same amount, third player calls more."""
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 100)
        pm.add_bet(2, 200)

        pm.calculate_side_pots(
            all_in_amounts={0: 100, 1: 100},
            active_players=[0, 1, 2],
        )

        assert len(pm.pots) == 2
        # Main pot: 100 from each = 300
        assert pm.pots[0].amount == 300
        # Side pot: 100 extra from player 2
        assert pm.pots[1].amount == 100
        assert pm.pots[1].eligible_players == [2]

    def test_total_preserved_after_side_pot_calc(self) -> None:
        """Total pot amount should be preserved after side pot calculation."""
        pm = PotManager()
        pm.add_bet(0, 100)
        pm.add_bet(1, 200)
        pm.add_bet(2, 300)
        total_before = pm.total

        pm.calculate_side_pots(
            all_in_amounts={0: 100, 1: 200},
            active_players=[0, 1, 2],
        )

        assert pm.total == total_before
