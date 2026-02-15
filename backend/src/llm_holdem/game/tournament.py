"""Tournament manager — orchestrates multi-hand tournament play."""

import logging
from datetime import datetime
from datetime import timezone

from pydantic import BaseModel
from pydantic import Field

from llm_holdem.game.blinds import BlindManager
from llm_holdem.game.engine import GameEngine
from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


class TournamentStats(BaseModel):
    """Statistics collected during a tournament."""

    total_hands: int = 0
    biggest_pot: int = 0
    biggest_pot_hand: int = 0
    best_hand_name: str = ""
    best_hand_rank: int = 9999  # Lower is better in treys
    best_hand_player: int = -1
    best_hand_hand_number: int = 0
    total_folds: int = 0
    total_raises: int = 0
    total_all_ins: int = 0
    showdowns: int = 0
    hands_won_without_showdown: int = 0
    started_at: str = ""
    ended_at: str = ""


class TournamentStanding(BaseModel):
    """A player's final standing in the tournament."""

    seat_index: int
    name: str = ""
    agent_id: str | None = None
    finish_position: int  # 1 = winner
    hands_survived: int = 0
    chips_at_elimination: int = 0


class TournamentResult(BaseModel):
    """Complete result of a finished tournament."""

    winner: TournamentStanding | None = None
    standings: list[TournamentStanding] = Field(default_factory=list)
    stats: TournamentStats = Field(default_factory=TournamentStats)


class TournamentManager:
    """Manages a multi-hand poker tournament.

    Orchestrates the game engine across multiple hands, tracks
    eliminations, standings, and statistics until one player remains.
    """

    def __init__(
        self,
        players: list[PlayerState],
        blind_manager: BlindManager | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the tournament.

        Args:
            players: List of player states for all seats.
            blind_manager: Optional blind manager (creates default if None).
            seed: Optional random seed for reproducibility.
        """
        self._engine = GameEngine(
            players=players,
            blind_manager=blind_manager,
            seed=seed,
        )
        self._stats = TournamentStats()
        self._elimination_order: list[TournamentStanding] = []
        self._result: TournamentResult | None = None

    @property
    def engine(self) -> GameEngine:
        """The underlying game engine."""
        return self._engine

    @property
    def stats(self) -> TournamentStats:
        """Current tournament statistics."""
        return self._stats

    @property
    def elimination_order(self) -> list[TournamentStanding]:
        """Players eliminated, in order of elimination."""
        return list(self._elimination_order)

    @property
    def result(self) -> TournamentResult | None:
        """Final tournament result, or None if still in progress."""
        return self._result

    @property
    def is_complete(self) -> bool:
        """Whether the tournament is finished."""
        return self._engine.is_tournament_over()

    def start(self) -> None:
        """Start the tournament."""
        self._stats.started_at = datetime.now(timezone.utc).isoformat()
        self._engine.status = "active"
        logger.info(
            "Tournament started with %d players",
            self._engine.active_player_count(),
        )

    def start_hand(self) -> None:
        """Start a new hand in the tournament."""
        self._engine.start_hand()

    def end_hand(self) -> None:
        """End the current hand, check eliminations, and update stats.

        This should be called after either:
        - run_showdown() completes, or
        - award_pot_to_last_player() completes (everyone folded)
        """
        # Collect stats before end_hand modifies state
        self._update_hand_stats()

        # Check for new eliminations BEFORE calling engine.end_hand()
        newly_eliminated = self._check_eliminations()

        # Finalize the hand in the engine (marks eliminated, advances blinds)
        self._engine.end_hand()

        self._stats.total_hands = self._engine.hand_number

        # Record standings for newly eliminated players
        for seat in newly_eliminated:
            player = self._engine.players[seat]
            standing = TournamentStanding(
                seat_index=seat,
                name=player.name,
                agent_id=player.agent_id,
                finish_position=0,  # Will be set when tournament finishes
                hands_survived=self._engine.hand_number,
                chips_at_elimination=0,
            )
            self._elimination_order.append(standing)
            logger.info(
                "Player %d (%s) eliminated on hand %d",
                seat,
                player.name,
                self._engine.hand_number,
            )

        # Check if tournament is over
        if self._engine.is_tournament_over():
            self._finalize()

    def _check_eliminations(self) -> list[int]:
        """Identify players who will be eliminated (0 chips).

        Returns:
            List of seat indices of newly eliminated players.
        """
        newly_eliminated: list[int] = []
        for p in self._engine.players:
            if p.chips == 0 and not p.is_eliminated:
                newly_eliminated.append(p.seat_index)
        return newly_eliminated

    def _update_hand_stats(self) -> None:
        """Update tournament statistics from the current hand."""
        # Biggest pot
        pot_total = self._engine.pot_manager.total
        if pot_total > self._stats.biggest_pot:
            self._stats.biggest_pot = pot_total
            self._stats.biggest_pot_hand = self._engine.hand_number

        # Count action types
        for action in self._engine._all_hand_actions:
            if action.action_type == "fold":
                self._stats.total_folds += 1
            elif action.action_type == "raise":
                self._stats.total_raises += 1

        # Count all-ins
        for p in self._engine.players:
            if p.is_all_in:
                self._stats.total_all_ins += 1

        # Showdown stats
        if self._engine._showdown_result is not None:
            self._stats.showdowns += 1
            # Check for best hand
            for hr in self._engine._showdown_result.hand_results:
                if hr.hand_rank < self._stats.best_hand_rank:
                    self._stats.best_hand_rank = hr.hand_rank
                    self._stats.best_hand_name = hr.hand_name
                    self._stats.best_hand_player = hr.player_index
                    self._stats.best_hand_hand_number = self._engine.hand_number
        else:
            self._stats.hands_won_without_showdown += 1

    def _finalize(self) -> None:
        """Finalize the tournament — compute standings and result."""
        self._stats.ended_at = datetime.now(timezone.utc).isoformat()
        self._engine.status = "completed"

        # The winner is the last player standing
        winner_player = self._engine.get_winner()

        # Assign finish positions
        # Elimination order is first-out to last-out
        total_players = len(self._engine.players)

        # Standings: eliminated players in reverse order (last eliminated = 2nd place)
        standings: list[TournamentStanding] = []

        if winner_player:
            winner_standing = TournamentStanding(
                seat_index=winner_player.seat_index,
                name=winner_player.name,
                agent_id=winner_player.agent_id,
                finish_position=1,
                hands_survived=self._engine.hand_number,
                chips_at_elimination=winner_player.chips,
            )
            standings.append(winner_standing)

        # Reverse elimination order for finish positions
        for i, standing in enumerate(reversed(self._elimination_order)):
            standing.finish_position = 2 + i
            standings.append(standing)

        self._result = TournamentResult(
            winner=winner_standing if winner_player else None,
            standings=standings,
            stats=self._stats,
        )

        logger.info(
            "Tournament complete! Winner: %s. Hands played: %d",
            winner_player.name if winner_player else "None",
            self._stats.total_hands,
        )

    def get_standings(self) -> list[TournamentStanding]:
        """Get current standings (active players + eliminated).

        Active players are ranked by chip count, then eliminated
        players in reverse elimination order.

        Returns:
            List of standings, sorted by position.
        """
        standings: list[TournamentStanding] = []
        active = [
            p for p in self._engine.players if not p.is_eliminated
        ]
        # Sort active players by chips descending
        active.sort(key=lambda p: p.chips, reverse=True)

        for i, p in enumerate(active):
            standings.append(
                TournamentStanding(
                    seat_index=p.seat_index,
                    name=p.name,
                    agent_id=p.agent_id,
                    finish_position=i + 1,
                    hands_survived=self._engine.hand_number,
                    chips_at_elimination=p.chips,
                )
            )

        # Append eliminated players in reverse order
        for i, standing in enumerate(reversed(self._elimination_order)):
            standing.finish_position = len(active) + i + 1
            standings.append(standing)

        return standings

    def __repr__(self) -> str:
        return (
            f"TournamentManager(hand={self._engine.hand_number}, "
            f"active={self._engine.active_player_count()}, "
            f"complete={self.is_complete})"
        )
