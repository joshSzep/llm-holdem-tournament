"""Integration tests for the GameEngine."""

import pytest

from llm_holdem.game.blinds import BlindManager
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import Card, PlayerState

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _make_players(
    num: int, chips: int = 1000, start_seat: int = 0
) -> list[PlayerState]:
    """Create a list of test players."""
    return [
        PlayerState(
            seat_index=start_seat + i,
            name=f"Player {start_seat + i}",
            chips=chips,
        )
        for i in range(num)
    ]


def _make_card(rank: str, suit: str) -> Card:
    """Convenience card constructor."""
    return Card(rank=rank, suit=suit)  # type: ignore[arg-type]


class TestHandLifecycle:
    """Tests for the full hand lifecycle: start, bet, advance, showdown."""

    def test_start_hand_initializes_state(self) -> None:
        """Starting a hand should set phase, deal cards, and post blinds."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        assert engine.phase == "pre_flop"
        assert engine.hand_number == 1
        # All players should have hole cards
        for p in players:
            assert p.hole_cards is not None
            assert len(p.hole_cards) == 2
        # Blinds should be posted (default 10/20)
        total_blind_chips = sum(p.current_bet for p in players)
        assert total_blind_chips == 30  # 10 + 20

    def test_start_hand_resets_between_hands(self) -> None:
        """Starting a new hand should reset per-hand state."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        # Play a full hand first
        engine.start_hand()
        engine.apply_action(players[0].seat_index, "fold")
        engine.apply_action(players[1].seat_index, "fold")
        engine.award_pot_to_last_player()
        engine.end_hand()

        # Start another hand
        engine.start_hand()

        assert engine.phase == "pre_flop"
        assert engine.hand_number == 2
        assert engine.community_cards == []
        for p in players:
            if not p.is_eliminated:
                assert not p.is_folded
                assert p.hole_cards is not None

    def test_multiple_hands_advance_dealer(self) -> None:
        """Dealer position should advance each hand."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        positions: list[int] = []
        for _ in range(3):
            engine.start_hand()
            positions.append(engine.turn_manager.dealer_position)
            # Quick fold-down to end the hand
            for p in players:
                if not p.is_folded and not p.is_eliminated:
                    if engine.betting_manager.count_active_players(players) > 1:
                        engine.apply_action(p.seat_index, "fold")
                    else:
                        break
            engine.award_pot_to_last_player()
            engine.end_hand()

        # Each hand should have a different dealer position
        assert len(set(positions)) > 1

    def test_hand_number_increments(self) -> None:
        """Hand number should increment each hand."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)

        for expected in range(1, 4):
            engine.start_hand()
            assert engine.hand_number == expected
            engine.apply_action(players[0].seat_index, "fold")
            engine.award_pot_to_last_player()
            engine.end_hand()


class TestBlindPosting:
    """Tests for blind posting mechanics."""

    def test_blinds_deducted_from_stacks(self) -> None:
        """Blind posting should deduct chips from player stacks."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # One player pays SB (10), one pays BB (20), one pays nothing
        chip_totals = sorted([p.chips for p in players])
        assert 980 in chip_totals  # BB posted
        assert 990 in chip_totals  # SB posted
        assert 1000 in chip_totals  # Dealer, no blind

    def test_blinds_added_to_pot(self) -> None:
        """Blind chips should be in the pot."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        assert engine.pot_manager.total == 30

    def test_short_stack_all_in_blind(self) -> None:
        """Player with less than the blind should go all-in."""
        players = _make_players(3, chips=1000)
        # Make one player very short-stacked
        players[1].chips = 5  # Less than SB of 10
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # The short-stacked player should be all-in
        short_player = players[1]
        if short_player.current_bet > 0 and short_player.chips == 0:
            assert short_player.is_all_in


class TestPhaseTransitions:
    """Tests for advancing through game phases."""

    def test_preflop_to_flop(self) -> None:
        """Advancing from pre-flop should deal 3 community cards."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        new_phase = engine.advance_phase()

        assert new_phase == "flop"
        assert len(engine.community_cards) == 3

    def test_flop_to_turn(self) -> None:
        """Advancing from flop should deal 1 more community card (4 total)."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        engine.advance_phase()  # flop
        new_phase = engine.advance_phase()  # turn

        assert new_phase == "turn"
        assert len(engine.community_cards) == 4

    def test_turn_to_river(self) -> None:
        """Advancing from turn should deal 1 more (5 total)."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        engine.advance_phase()  # flop
        engine.advance_phase()  # turn
        new_phase = engine.advance_phase()  # river

        assert new_phase == "river"
        assert len(engine.community_cards) == 5

    def test_river_to_showdown(self) -> None:
        """Advancing from river should go to showdown."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        engine.advance_phase()  # flop
        engine.advance_phase()  # turn
        engine.advance_phase()  # river
        new_phase = engine.advance_phase()  # showdown

        assert new_phase == "showdown"
        assert len(engine.community_cards) == 5

    def test_community_cards_unique(self) -> None:
        """All community cards should be unique."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        engine.advance_phase()  # flop
        engine.advance_phase()  # turn
        engine.advance_phase()  # river

        cards = engine.community_cards
        card_strs = [str(c) for c in cards]
        assert len(card_strs) == len(set(card_strs))


class TestApplyAction:
    """Tests for applying player actions through the engine."""

    def test_fold_action(self) -> None:
        """Folding should mark the player as folded."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Find a player who can act
        order = engine.get_preflop_order()
        acting_seat = order[0]

        action = engine.apply_action(acting_seat, "fold")
        assert action.action_type == "fold"
        assert players[acting_seat].is_folded

    def test_call_action(self) -> None:
        """Calling should match the current bet."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        order = engine.get_preflop_order()
        acting_seat = order[0]
        player = players[acting_seat]

        # The player should be able to call
        engine.apply_action(acting_seat, "call")
        assert player.current_bet == engine.betting_manager.current_bet

    def test_raise_action(self) -> None:
        """Raising should increase the current bet."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        order = engine.get_preflop_order()
        acting_seat = order[0]

        initial_bet = engine.betting_manager.current_bet
        engine.apply_action(acting_seat, "raise", amount=80)
        assert engine.betting_manager.current_bet > initial_bet

    def test_check_post_flop(self) -> None:
        """Checking should be valid post-flop when no bets are placed."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        # Both players call to move past pre-flop
        order = engine.get_preflop_order()
        for seat in order:
            if not players[seat].is_folded:
                valid = engine.betting_manager.get_valid_actions(players[seat])
                if "call" in valid:
                    engine.apply_action(seat, "call")
                elif "check" in valid:
                    engine.apply_action(seat, "check")

        engine.advance_phase()  # Move to flop

        # Post-flop, first player should be able to check
        post_order = engine.get_postflop_order()
        if post_order:
            seat = post_order[0]
            valid = engine.betting_manager.get_valid_actions(players[seat])
            assert "check" in valid

    def test_actions_recorded(self) -> None:
        """All actions should be recorded in the hand actions list."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        # Blind actions are already recorded
        blind_action_count = len(engine._all_hand_actions)
        assert blind_action_count > 0  # At least SB and BB

        # Apply a fold
        order = engine.get_preflop_order()
        engine.apply_action(order[0], "fold")

        assert len(engine._all_hand_actions) == blind_action_count + 1


class TestAllFoldHand:
    """Tests for hands where everyone folds to one player."""

    def test_everyone_folds_awards_pot(self) -> None:
        """When all but one player folds, the remaining player wins the pot."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        order = engine.get_preflop_order()
        # Fold all but the last in order
        for seat in order[:-1]:
            engine.apply_action(seat, "fold")

        # Also fold any remaining non-folded players except the last
        active = [
            p for p in players
            if not p.is_folded and not p.is_eliminated
        ]
        while len(active) > 1:
            engine.apply_action(active[0].seat_index, "fold")
            active = [
                p for p in players
                if not p.is_folded and not p.is_eliminated
            ]

        pot_total = engine.pot_manager.total
        winner_seat = engine.award_pot_to_last_player()
        assert players[winner_seat].chips == 1000 - players[winner_seat].current_bet + pot_total

    def test_fold_all_except_bb_preflop(self) -> None:
        """If everyone folds pre-flop, BB wins the pot."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Fold all pre-flop players except the ones we need
        order = engine.get_preflop_order()
        _, bb_seat = engine.turn_manager.get_blind_positions(players)

        for seat in order:
            if seat != bb_seat:
                if not players[seat].is_folded:
                    engine.apply_action(seat, "fold")

        # BB should be last standing
        active = [
            p for p in players if not p.is_folded and not p.is_eliminated
        ]
        assert len(active) == 1

        winner_seat = engine.award_pot_to_last_player()
        assert winner_seat == bb_seat


class TestShowdown:
    """Tests for showdown evaluation and pot distribution."""

    def test_showdown_determines_winner(self) -> None:
        """Showdown should correctly determine and award the winner."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Both players just call/check through all streets
        for _ in range(4):  # pre-flop, flop, turn, river
            active = [
                p for p in players
                if not p.is_folded and not p.is_eliminated
            ]
            for p in active:
                valid = engine.betting_manager.get_valid_actions(p)
                if "check" in valid:
                    engine.apply_action(p.seat_index, "check")
                elif "call" in valid:
                    engine.apply_action(p.seat_index, "call")

            if engine.phase != "showdown":
                if engine.betting_manager.is_round_complete(players):
                    engine.advance_phase()

        # Run showdown if we've gotten to river/showdown
        if engine.phase in ("river", "showdown"):
            if engine.phase == "river":
                engine.advance_phase()  # to showdown
            result = engine.run_showdown()

            assert len(result.winners) >= 1
            # Total chips should be conserved
            total = sum(p.chips for p in players)
            assert total == 2000

    def test_showdown_preserves_total_chips(self) -> None:
        """Total chips must be conserved after showdown."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Everyone calls pre-flop
        order = engine.get_preflop_order()
        for seat in order:
            if not players[seat].is_folded:
                valid = engine.betting_manager.get_valid_actions(players[seat])
                if "call" in valid:
                    engine.apply_action(seat, "call")
                elif "check" in valid:
                    engine.apply_action(seat, "check")

        # Advance through all phases
        for _ in range(3):  # flop, turn, river
            engine.advance_phase()
            post_order = engine.get_postflop_order()
            for seat in post_order:
                if not players[seat].is_folded:
                    engine.apply_action(seat, "check")

        engine.advance_phase()  # to showdown
        engine.run_showdown()
        engine.end_hand()

        total = sum(p.chips for p in players)
        assert total == 3000

    def test_showdown_result_has_hand_results(self) -> None:
        """Showdown result should include hand evaluations."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Call through to showdown
        order = engine.get_preflop_order()
        for seat in order:
            valid = engine.betting_manager.get_valid_actions(players[seat])
            if "call" in valid:
                engine.apply_action(seat, "call")
            elif "check" in valid:
                engine.apply_action(seat, "check")

        for _ in range(3):
            engine.advance_phase()
            post_order = engine.get_postflop_order()
            for seat in post_order:
                if not players[seat].is_folded:
                    engine.apply_action(seat, "check")

        engine.advance_phase()  # to showdown
        result = engine.run_showdown()

        assert result.hand_results is not None
        assert len(result.hand_results) == 2
        for hr in result.hand_results:
            assert hr.hand_name  # Should have human-readable name


class TestEndHand:
    """Tests for hand finalization."""

    def test_eliminated_players_marked(self) -> None:
        """Players with 0 chips should be eliminated."""
        players = _make_players(2, chips=20)  # Very low chips
        engine = GameEngine(players, seed=42)

        engine.start_hand()

        # Both go all-in (BB is 20, so short stacks)
        order = engine.get_preflop_order()
        for seat in order:
            valid = engine.betting_manager.get_valid_actions(players[seat])
            if "call" in valid:
                engine.apply_action(seat, "call")
            elif "check" in valid:
                engine.apply_action(seat, "check")

        # Advance to showdown
        for _ in range(3):
            engine.advance_phase()

        engine.advance_phase()  # to showdown
        engine.run_showdown()
        engine.end_hand()

        # At least one player should have 0 chips and be eliminated
        eliminated = [p for p in players if p.is_eliminated]
        assert len(eliminated) >= 1

    def test_blind_level_advances(self) -> None:
        """Blinds should increase after enough hands."""
        players = _make_players(2, chips=10000)
        blind_manager = BlindManager(hands_per_level=2)
        engine = GameEngine(players, blind_manager=blind_manager, seed=42)

        initial_bb = engine.blind_manager.big_blind

        # Play 2 quick hands
        for _ in range(2):
            engine.start_hand()
            engine.apply_action(players[0].seat_index, "fold")
            engine.award_pot_to_last_player()
            engine.end_hand()

        # After 2 hands with hands_per_level=2, blinds should advance
        assert engine.blind_manager.big_blind > initial_bb


class TestGetState:
    """Tests for the game state snapshot."""

    def test_state_includes_all_fields(self) -> None:
        """get_state should return a complete GameState."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        engine.start_hand()
        state = engine.get_state()

        assert state.game_id == engine.game_id
        assert state.phase == "pre_flop"
        assert state.hand_number == 1
        assert len(state.players) == 3
        assert state.small_blind == 10
        assert state.big_blind == 20
        assert state.status == "active"

    def test_state_updates_after_actions(self) -> None:
        """Game state should reflect applied actions."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        order = engine.get_preflop_order()
        engine.apply_action(order[0], "fold")

        state = engine.get_state()
        # The folded player should be marked in the state
        folded_in_state = state.players[order[0]]
        assert folded_in_state.is_folded

    def test_state_reflects_community_cards(self) -> None:
        """Community cards should appear in state after dealing."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        # Call pre-flop
        order = engine.get_preflop_order()
        for seat in order:
            valid = engine.betting_manager.get_valid_actions(players[seat])
            if "call" in valid:
                engine.apply_action(seat, "call")
            elif "check" in valid:
                engine.apply_action(seat, "check")

        engine.advance_phase()  # flop
        state = engine.get_state()

        assert state.phase == "flop"
        assert len(state.community_cards) == 3


class TestTournamentCompletion:
    """Tests for tournament-level queries."""

    def test_active_player_count(self) -> None:
        """active_player_count should exclude eliminated players."""
        players = _make_players(4, chips=1000)
        engine = GameEngine(players, seed=42)

        assert engine.active_player_count() == 4

        players[0].is_eliminated = True
        assert engine.active_player_count() == 3

        players[1].is_eliminated = True
        assert engine.active_player_count() == 2

    def test_is_tournament_over(self) -> None:
        """Tournament should be over when 1 player remains."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        assert not engine.is_tournament_over()

        players[0].is_eliminated = True
        assert not engine.is_tournament_over()

        players[1].is_eliminated = True
        assert engine.is_tournament_over()

    def test_get_winner(self) -> None:
        """get_winner returns the last standing player."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        assert engine.get_winner() is None

        players[0].is_eliminated = True
        players[1].is_eliminated = True

        winner = engine.get_winner()
        assert winner is not None
        assert winner.seat_index == 2

    def test_get_winner_returns_none_if_not_over(self) -> None:
        """get_winner should return None if multiple players remain."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        assert engine.get_winner() is None


class TestCompleteHand:
    """Integration tests simulating complete hands."""

    def test_complete_hand_check_through(self) -> None:
        """Simulate a complete hand where everyone checks through."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        total_before = sum(p.chips for p in players)

        engine.start_hand()

        # Pre-flop: everyone calls/checks
        order = engine.get_preflop_order()
        for seat in order:
            if not players[seat].is_folded:
                valid = engine.betting_manager.get_valid_actions(players[seat])
                if "call" in valid:
                    engine.apply_action(seat, "call")
                elif "check" in valid:
                    engine.apply_action(seat, "check")

        # Advance through flop, turn, river with checks
        for _ in range(3):
            engine.advance_phase()
            post_order = engine.get_postflop_order()
            for seat in post_order:
                if not players[seat].is_folded and not players[seat].is_all_in:
                    engine.apply_action(seat, "check")

        # Advance to showdown
        engine.advance_phase()  # to showdown
        result = engine.run_showdown()
        engine.end_hand()

        # Chips conserved
        total_after = sum(p.chips for p in players)
        assert total_after == total_before

        # Someone won
        assert len(result.winners) >= 1

    def test_complete_hand_with_raise_and_folds(self) -> None:
        """Simulate a hand with raises and folds."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        total_before = sum(p.chips for p in players)

        engine.start_hand()

        # Pre-flop: first player raises, others fold
        order = engine.get_preflop_order()
        engine.apply_action(order[0], "raise", amount=60)

        # Remaining players fold
        for seat in order[1:]:
            if not players[seat].is_folded:
                engine.apply_action(seat, "fold")

        # BB might still act - check if hand is over
        active = [
            p for p in players if not p.is_folded and not p.is_eliminated
        ]
        if len(active) == 1:
            winner_seat = engine.award_pot_to_last_player()
            engine.end_hand()
        else:
            # If BB is still active from the blind, they need to act too
            for p in active:
                if not p.has_acted:
                    engine.apply_action(p.seat_index, "fold")
            active = [
                p for p in players if not p.is_folded and not p.is_eliminated
            ]
            if len(active) == 1:
                winner_seat = engine.award_pot_to_last_player()
                engine.end_hand()

        total_after = sum(p.chips for p in players)
        assert total_after == total_before

    def test_heads_up_complete_hand(self) -> None:
        """Simulate a complete heads-up hand to showdown."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players, seed=42)
        total_before = sum(p.chips for p in players)

        engine.start_hand()

        # Pre-flop: call
        order = engine.get_preflop_order()
        for seat in order:
            valid = engine.betting_manager.get_valid_actions(players[seat])
            if "call" in valid:
                engine.apply_action(seat, "call")
            elif "check" in valid:
                engine.apply_action(seat, "check")

        # Post-flop: check through
        for _ in range(3):
            engine.advance_phase()
            post_order = engine.get_postflop_order()
            for seat in post_order:
                if not players[seat].is_folded and not players[seat].is_all_in:
                    engine.apply_action(seat, "check")

        engine.advance_phase()  # to showdown
        result = engine.run_showdown()
        engine.end_hand()

        total_after = sum(p.chips for p in players)
        assert total_after == total_before
        assert len(result.winners) >= 1

    def test_six_player_hand(self) -> None:
        """Simulate a 6-player hand to showdown."""
        players = _make_players(6, chips=1000)
        engine = GameEngine(players, seed=42)
        total_before = sum(p.chips for p in players)

        engine.start_hand()

        # Pre-flop: some fold, some call
        order = engine.get_preflop_order()
        for i, seat in enumerate(order):
            if not players[seat].is_folded:
                if i < 2:  # First 2 fold
                    engine.apply_action(seat, "fold")
                else:
                    valid = engine.betting_manager.get_valid_actions(players[seat])
                    if "call" in valid:
                        engine.apply_action(seat, "call")
                    elif "check" in valid:
                        engine.apply_action(seat, "check")

        # Check through remaining streets
        for _ in range(3):
            engine.advance_phase()
            post_order = engine.get_postflop_order()
            for seat in post_order:
                p = players[seat]
                if not p.is_folded and not p.is_all_in:
                    engine.apply_action(seat, "check")

        engine.advance_phase()
        result = engine.run_showdown()
        engine.end_hand()

        total_after = sum(p.chips for p in players)
        assert total_after == total_before
        assert len(result.winners) >= 1


class TestEdgeCases:
    """Edge case tests."""

    def test_award_pot_with_no_active_raises_error(self) -> None:
        """award_pot_to_last_player should raise if multiple are active."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)
        engine.start_hand()

        with pytest.raises(ValueError, match="Expected exactly 1"):
            engine.award_pot_to_last_player()

    def test_engine_repr(self) -> None:
        """Engine repr should be informative."""
        players = _make_players(3, chips=1000)
        engine = GameEngine(players, seed=42)

        r = repr(engine)
        assert "GameEngine" in r
        assert "hand=0" in r
        assert "players=3" in r

    def test_game_id_unique(self) -> None:
        """Each engine instance should have a unique game_id."""
        players = _make_players(2, chips=1000)
        engine1 = GameEngine(players, seed=42)
        engine2 = GameEngine(players, seed=42)

        assert engine1.game_id != engine2.game_id

    def test_seed_reproducibility(self) -> None:
        """Same seed should produce same hole cards."""
        players1 = _make_players(2, chips=1000)
        engine1 = GameEngine(players1, seed=12345)
        engine1.start_hand()

        players2 = _make_players(2, chips=1000)
        engine2 = GameEngine(players2, seed=12345)
        engine2.start_hand()

        for p1, p2 in zip(players1, players2):
            assert p1.hole_cards == p2.hole_cards

    def test_eliminated_players_skipped_in_dealing(self) -> None:
        """Eliminated players should not receive cards."""
        players = _make_players(4, chips=1000)
        players[1].is_eliminated = True
        players[1].chips = 0

        engine = GameEngine(players, seed=42)
        engine.start_hand()

        assert players[1].hole_cards is None
        for i, p in enumerate(players):
            if i != 1:
                assert p.hole_cards is not None

    def test_status_getter_setter(self) -> None:
        """Status should be gettable and settable."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players)

        assert engine.status == "active"
        engine.status = "completed"
        assert engine.status == "completed"

    def test_game_id_setter(self) -> None:
        """game_id should be settable."""
        players = _make_players(2, chips=1000)
        engine = GameEngine(players)

        engine.game_id = "test-game-123"
        assert engine.game_id == "test-game-123"
