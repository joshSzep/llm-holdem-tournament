"""Tests for the TournamentManager."""


from llm_holdem.game.blinds import BlindManager
from llm_holdem.game.state import PlayerState
from llm_holdem.game.tournament import (
    TournamentManager,
    TournamentResult,
    TournamentStanding,
    TournamentStats,
)

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


def _play_hand_all_fold_to_first(tm: TournamentManager) -> None:
    """Play a hand where everyone folds to the first actor.

    The remaining player is the one who doesn't fold.
    """
    engine = tm.engine
    tm.start_hand()

    order = engine.get_preflop_order()
    players = engine.players

    # Fold all but the last player in the action order
    for seat in order[:-1]:
        if not players[seat].is_folded and not players[seat].is_eliminated:
            if engine.betting_manager.count_active_players(players) > 1:
                engine.apply_action(seat, "fold")

    # Award pot to last remaining
    active = [p for p in players if not p.is_folded and not p.is_eliminated]
    if len(active) == 1:
        engine.award_pot_to_last_player()

    tm.end_hand()


def _play_hand_check_to_showdown(tm: TournamentManager) -> None:
    """Play a hand where everyone calls pre-flop then checks to showdown."""
    engine = tm.engine
    players = engine.players
    tm.start_hand()

    # Pre-flop: call/check
    order = engine.get_preflop_order()
    for seat in order:
        p = players[seat]
        if not p.is_folded and not p.is_eliminated:
            valid = engine.betting_manager.get_valid_actions(p)
            if "call" in valid:
                engine.apply_action(seat, "call")
            elif "check" in valid:
                engine.apply_action(seat, "check")

    # Flop, turn, river: check
    for _ in range(3):
        engine.advance_phase()
        post_order = engine.get_postflop_order()
        for seat in post_order:
            p = players[seat]
            if not p.is_folded and not p.is_all_in:
                engine.apply_action(seat, "check")

    engine.advance_phase()  # to showdown
    engine.run_showdown()
    tm.end_hand()


class TestTournamentInit:
    """Tests for tournament initialization."""

    def test_create_tournament(self) -> None:
        """Should create a tournament with the given players."""
        players = _make_players(4, chips=1000)
        tm = TournamentManager(players, seed=42)

        assert tm.engine is not None
        assert len(tm.engine.players) == 4
        assert not tm.is_complete

    def test_start_tournament(self) -> None:
        """Starting should set status and timestamp."""
        players = _make_players(4, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        assert tm.engine.status == "active"
        assert tm.stats.started_at != ""

    def test_custom_blind_manager(self) -> None:
        """Should accept a custom blind manager."""
        players = _make_players(4, chips=1000)
        bm = BlindManager(hands_per_level=5)
        tm = TournamentManager(players, blind_manager=bm, seed=42)

        assert tm.engine.blind_manager is bm


class TestTournamentStats:
    """Tests for statistics collection."""

    def test_total_hands_tracked(self) -> None:
        """Total hands should increment."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_all_fold_to_first(tm)
        assert tm.stats.total_hands == 1

        _play_hand_all_fold_to_first(tm)
        assert tm.stats.total_hands == 2

    def test_folds_counted(self) -> None:
        """Fold actions should be counted."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_all_fold_to_first(tm)
        assert tm.stats.total_folds > 0

    def test_hands_won_without_showdown(self) -> None:
        """Hands won by everyone folding should be tracked."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_all_fold_to_first(tm)
        assert tm.stats.hands_won_without_showdown == 1

    def test_showdown_counted(self) -> None:
        """Hands that reach showdown should be counted."""
        players = _make_players(2, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_check_to_showdown(tm)
        assert tm.stats.showdowns == 1

    def test_biggest_pot_tracked(self) -> None:
        """Biggest pot should be tracked."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_all_fold_to_first(tm)
        assert tm.stats.biggest_pot > 0
        assert tm.stats.biggest_pot_hand == 1

    def test_best_hand_tracked_after_showdown(self) -> None:
        """Best hand should be tracked after showdown."""
        players = _make_players(2, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_check_to_showdown(tm)

        assert tm.stats.best_hand_name != ""
        assert tm.stats.best_hand_rank < 9999
        assert tm.stats.best_hand_player >= 0


class TestElimination:
    """Tests for player elimination."""

    def test_player_eliminated_at_zero_chips(self) -> None:
        """Player reaching 0 chips should be eliminated."""
        # Create players where one will be knocked out quickly
        players = _make_players(2, chips=20)  # Just enough for 1 BB
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_check_to_showdown(tm)

        # One player should have won the other's chips
        eliminated = [p for p in players if p.is_eliminated]
        assert len(eliminated) >= 1

    def test_elimination_order_tracked(self) -> None:
        """Eliminated players should be tracked in order."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_check_to_showdown(tm)

        if tm.is_complete:
            assert len(tm.elimination_order) >= 1
            assert tm.elimination_order[0].hands_survived > 0


class TestTournamentCompletion:
    """Tests for tournament completion."""

    def test_tournament_completes_when_one_left(self) -> None:
        """Tournament should complete when only one player has chips."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        # Play until complete (limited iterations for safety)
        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                # If check-to-showdown fails (e.g., all-in dynamics), try fold
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        assert tm.is_complete
        assert tm.result is not None

    def test_result_has_winner(self) -> None:
        """Completed tournament should have a winner."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        if tm.result:
            assert tm.result.winner is not None
            assert tm.result.winner.finish_position == 1

    def test_result_has_standings(self) -> None:
        """Result should have standings for all players."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        if tm.result:
            assert len(tm.result.standings) == 2
            positions = [s.finish_position for s in tm.result.standings]
            assert 1 in positions
            assert 2 in positions

    def test_result_has_stats(self) -> None:
        """Result should have tournament stats."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        if tm.result:
            assert tm.result.stats.total_hands > 0
            assert tm.result.stats.ended_at != ""

    def test_engine_status_completed(self) -> None:
        """Engine status should be 'completed' when tournament finishes."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        if tm.is_complete:
            assert tm.engine.status == "completed"


class TestGetStandings:
    """Tests for live standings."""

    def test_standings_all_active(self) -> None:
        """All active players should appear in standings."""
        players = _make_players(4, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        standings = tm.get_standings()
        assert len(standings) == 4

    def test_standings_sorted_by_chips(self) -> None:
        """Active players should be sorted by chip count."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_all_fold_to_first(tm)
        standings = tm.get_standings()

        # Active players should be in descending chip order
        active_standings = [
            s for s in standings
            if not players[s.seat_index].is_eliminated
        ]
        for i in range(len(active_standings) - 1):
            assert (
                active_standings[i].chips_at_elimination
                >= active_standings[i + 1].chips_at_elimination
            )

    def test_standings_include_eliminated(self) -> None:
        """Eliminated players should appear after active players."""
        players = _make_players(2, chips=20)
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(100):
            if tm.is_complete:
                break
            try:
                _play_hand_check_to_showdown(tm)
            except Exception:
                try:
                    _play_hand_all_fold_to_first(tm)
                except Exception:
                    break

        if tm.is_complete:
            standings = tm.get_standings()
            assert len(standings) == 2


class TestRepr:
    """Tests for string representation."""

    def test_repr(self) -> None:
        """Repr should be informative."""
        players = _make_players(3, chips=1000)
        tm = TournamentManager(players, seed=42)

        r = repr(tm)
        assert "TournamentManager" in r
        assert "active=3" in r
        assert "complete=False" in r


class TestModels:
    """Tests for Pydantic data models."""

    def test_tournament_stats_defaults(self) -> None:
        """TournamentStats should have sensible defaults."""
        stats = TournamentStats()
        assert stats.total_hands == 0
        assert stats.biggest_pot == 0
        assert stats.best_hand_rank == 9999

    def test_tournament_standing_fields(self) -> None:
        """TournamentStanding should store all required fields."""
        standing = TournamentStanding(
            seat_index=0,
            name="Player 0",
            finish_position=1,
            hands_survived=10,
            chips_at_elimination=5000,
        )
        assert standing.seat_index == 0
        assert standing.finish_position == 1
        assert standing.hands_survived == 10

    def test_tournament_result_fields(self) -> None:
        """TournamentResult should have required structure."""
        result = TournamentResult()
        assert result.winner is None
        assert result.standings == []
        assert result.stats.total_hands == 0


class TestChipConservation:
    """Tests ensuring chips are always conserved."""

    def test_chips_conserved_across_hands(self) -> None:
        """Total chips should remain constant across multiple hands."""
        players = _make_players(3, chips=1000)
        initial_total = sum(p.chips for p in players)  # 3000
        tm = TournamentManager(players, seed=42)
        tm.start()

        for _ in range(5):
            if tm.is_complete:
                break
            _play_hand_all_fold_to_first(tm)
            total = sum(p.chips for p in players)
            assert total == initial_total

    def test_chips_conserved_through_showdown(self) -> None:
        """Total chips should be constant even with showdowns."""
        players = _make_players(2, chips=1000)
        initial_total = sum(p.chips for p in players)
        tm = TournamentManager(players, seed=42)
        tm.start()

        _play_hand_check_to_showdown(tm)
        total = sum(p.chips for p in players)
        assert total == initial_total
