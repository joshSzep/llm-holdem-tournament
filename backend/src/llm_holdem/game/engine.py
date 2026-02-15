"""Core game engine — orchestrates a complete poker hand."""

import logging
import uuid
from typing import Literal

from llm_holdem.game.betting import BettingManager
from llm_holdem.game.blinds import BlindManager
from llm_holdem.game.dealer import Deck
from llm_holdem.game.evaluator import determine_winners
from llm_holdem.game.pot import PotManager
from llm_holdem.game.state import (
    Action,
    Card,
    GamePhase,
    GameState,
    GameStatus,
    PlayerState,
    ShowdownResult,
)
from llm_holdem.game.turn import TurnManager

logger = logging.getLogger(__name__)


class GameEngine:
    """Orchestrates a complete poker hand.

    This is the core game loop coordinator. It manages the sequence of
    dealing, betting rounds, and showdown for a single hand, and provides
    methods to run a complete hand or step through it action-by-action.

    The engine uses composition — it delegates to specialized managers
    for each aspect of the game.
    """

    def __init__(
        self,
        players: list[PlayerState],
        blind_manager: BlindManager | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the game engine.

        Args:
            players: List of player states for all seats.
            blind_manager: Optional blind manager (creates default if None).
            seed: Optional random seed for deck shuffling.
        """
        self._players = players
        self._num_seats = len(players)
        self._blind_manager = blind_manager or BlindManager()
        self._turn_manager = TurnManager(self._num_seats)
        self._betting_manager = BettingManager()
        self._pot_manager = PotManager()
        self._deck = Deck(seed=seed)

        self._game_id = str(uuid.uuid4())
        self._hand_number = 0
        self._phase: GamePhase = "between_hands"
        self._community_cards: list[Card] = []
        self._all_hand_actions: list[Action] = []
        self._showdown_result: ShowdownResult | None = None
        self._status: GameStatus = "active"

        # Track all-in amounts for side pot calculation
        self._all_in_amounts: dict[int, int] = {}

    @property
    def game_id(self) -> str:
        """The unique game ID."""
        return self._game_id

    @game_id.setter
    def game_id(self, value: str) -> None:
        self._game_id = value

    @property
    def players(self) -> list[PlayerState]:
        """All players."""
        return self._players

    @property
    def phase(self) -> GamePhase:
        """Current game phase."""
        return self._phase

    @property
    def hand_number(self) -> int:
        """Current hand number."""
        return self._hand_number

    @property
    def community_cards(self) -> list[Card]:
        """Current community cards."""
        return list(self._community_cards)

    @property
    def pot_manager(self) -> PotManager:
        """The pot manager."""
        return self._pot_manager

    @property
    def betting_manager(self) -> BettingManager:
        """The betting manager."""
        return self._betting_manager

    @property
    def blind_manager(self) -> BlindManager:
        """The blind manager."""
        return self._blind_manager

    @property
    def turn_manager(self) -> TurnManager:
        """The turn manager."""
        return self._turn_manager

    @property
    def status(self) -> GameStatus:
        """Current game status."""
        return self._status

    @status.setter
    def status(self, value: GameStatus) -> None:
        self._status = value

    def get_state(self) -> GameState:
        """Build and return the current complete game state.

        Returns:
            Full GameState snapshot.
        """
        return GameState(
            game_id=self._game_id,
            status=self._status,
            players=list(self._players),
            dealer_position=self._turn_manager.dealer_position,
            small_blind=self._blind_manager.small_blind,
            big_blind=self._blind_manager.big_blind,
            hand_number=self._hand_number,
            community_cards=list(self._community_cards),
            pots=list(self._pot_manager.pots),
            current_bet=self._betting_manager.current_bet,
            current_player_index=None,
            phase=self._phase,
            current_hand_actions=list(self._all_hand_actions),
            showdown_result=self._showdown_result,
            total_hands_played=self._hand_number,
            eliminated_players=[
                p.seat_index for p in self._players if p.is_eliminated
            ],
        )

    # ─── Hand Lifecycle ───────────────────────────────────

    def start_hand(self) -> None:
        """Start a new hand: advance dealer, post blinds, deal hole cards.

        Resets per-hand state and prepares for pre-flop betting.
        """
        self._hand_number += 1
        self._phase = "pre_flop"
        self._community_cards = []
        self._all_hand_actions = []
        self._showdown_result = None
        self._all_in_amounts = {}

        # Reset player hand state
        for p in self._players:
            if not p.is_eliminated:
                p.is_folded = False
                p.is_all_in = False
                p.current_bet = 0
                p.hole_cards = None
                p.has_acted = False

        # Reset managers
        self._pot_manager.reset()
        self._deck.reset()
        self._deck.shuffle()

        # Advance dealer
        self._turn_manager.advance_dealer(self._players)

        # Post blinds
        self._post_blinds()

        # Deal hole cards
        self._deal_hole_cards()

        # Start pre-flop betting
        self._betting_manager.new_round(self._blind_manager.big_blind)

        logger.info(
            "Hand %d started. Dealer: seat %d. Blinds: %d/%d",
            self._hand_number,
            self._turn_manager.dealer_position,
            self._blind_manager.small_blind,
            self._blind_manager.big_blind,
        )

    def _post_blinds(self) -> None:
        """Post small and big blinds."""
        sb_seat, bb_seat = self._turn_manager.get_blind_positions(self._players)
        sb_player = self._players[sb_seat]
        bb_player = self._players[bb_seat]

        postings = self._blind_manager.get_blind_posting(
            sb_seat=sb_seat,
            bb_seat=bb_seat,
            sb_stack=sb_player.chips,
            bb_stack=bb_player.chips,
        )

        for seat, amount, label in postings:
            player = self._players[seat]
            player.chips -= amount
            player.current_bet = amount
            self._pot_manager.add_bet(seat, amount)

            if player.chips == 0:
                player.is_all_in = True
                self._all_in_amounts[seat] = amount

            action = Action(
                player_index=seat,
                action_type="post_blind",
                amount=amount,
            )
            self._all_hand_actions.append(action)

            logger.debug(
                "Player %d posts %s (%d chips)", seat, label, amount
            )

    def _deal_hole_cards(self) -> None:
        """Deal 2 hole cards to each active player."""
        active_players = [
            p for p in self._players if not p.is_eliminated
        ]

        if not active_players:
            return

        # Deal in seat order starting from left of dealer
        hands = self._deck.deal_to_players(len(active_players))
        for i, player in enumerate(active_players):
            player.hole_cards = hands[i]

    def get_preflop_order(self) -> list[int]:
        """Get the turn order for pre-flop betting.

        Returns:
            List of seat indices in turn order.
        """
        _, bb_seat = self._turn_manager.get_blind_positions(self._players)
        return self._turn_manager.get_preflop_order(self._players, bb_seat)

    def get_postflop_order(self) -> list[int]:
        """Get the turn order for post-flop betting.

        Returns:
            List of seat indices in turn order.
        """
        return self._turn_manager.get_postflop_order(self._players)

    def apply_action(
        self,
        seat_index: int,
        action_type: Literal["fold", "check", "call", "raise"],
        amount: int | None = None,
        timestamp: str = "",
    ) -> Action:
        """Apply a player action.

        Args:
            seat_index: The seat index of the player acting.
            action_type: The action type.
            amount: Optional raise-to amount.
            timestamp: Action timestamp.

        Returns:
            The applied Action.
        """
        player = self._players[seat_index]
        action = self._betting_manager.apply_action(
            player, action_type, amount, timestamp
        )

        # Track all-in for side pot calculation
        if player.is_all_in and seat_index not in self._all_in_amounts:
            self._all_in_amounts[seat_index] = player.current_bet

        # Add to pot
        if action.amount and action.amount > 0:
            self._pot_manager.add_bet(seat_index, action.amount)

        self._all_hand_actions.append(action)
        return action

    # ─── Phase Transitions ────────────────────────────────

    def advance_phase(self) -> GamePhase:
        """Advance to the next game phase.

        Deals community cards for flop/turn/river, or triggers showdown.

        Returns:
            The new phase.
        """
        # Reset player bets for the new round
        for p in self._players:
            p.current_bet = 0
            p.has_acted = False

        # Calculate side pots at end of round
        active_seats = [
            p.seat_index
            for p in self._players
            if not p.is_folded and not p.is_eliminated
        ]
        if self._all_in_amounts:
            self._pot_manager.calculate_side_pots(
                self._all_in_amounts, active_seats
            )

        if self._phase == "pre_flop":
            self._phase = "flop"
            self._community_cards.extend(self._deck.deal_community(3))
        elif self._phase == "flop":
            self._phase = "turn"
            self._community_cards.extend(self._deck.deal_community(1))
        elif self._phase == "turn":
            self._phase = "river"
            self._community_cards.extend(self._deck.deal_community(1))
        elif self._phase == "river":
            self._phase = "showdown"
        else:
            logger.warning("Cannot advance from phase: %s", self._phase)

        # Start new betting round
        if self._phase in ("flop", "turn", "river"):
            self._betting_manager.new_round(0)

        logger.info("Phase advanced to: %s", self._phase)
        return self._phase

    def run_showdown(self) -> ShowdownResult:
        """Run the showdown and determine winner(s).

        Returns:
            ShowdownResult with winners and hand evaluations.
        """
        self._phase = "showdown"

        # Recalculate side pots one final time
        active_seats = [
            p.seat_index
            for p in self._players
            if not p.is_folded and not p.is_eliminated
        ]
        if self._all_in_amounts:
            self._pot_manager.calculate_side_pots(
                self._all_in_amounts, active_seats
            )

        # Gather hole cards from non-folded players
        players_hands: dict[int, list[Card]] = {}
        for p in self._players:
            if not p.is_folded and not p.is_eliminated and p.hole_cards:
                players_hands[p.seat_index] = p.hole_cards

        if not players_hands:
            logger.warning("No players with hole cards at showdown")
            return ShowdownResult(winners=[])

        # Determine winners
        winners, hand_results = determine_winners(
            players_hands, self._community_cards
        )

        # Distribute pots
        # For each pot, find winners among eligible players
        pot_distributions: list[dict[str, int | list[int]]] = []
        winners_per_pot: list[list[int]] = []

        for pot in self._pot_manager.pots:
            # Find the best hand among eligible players
            eligible_results = [
                r for r in hand_results
                if r.player_index in pot.eligible_players
            ]
            if eligible_results:
                best_rank = eligible_results[0].hand_rank
                pot_winners = [
                    r.player_index
                    for r in eligible_results
                    if r.hand_rank == best_rank
                ]
            else:
                pot_winners = winners[:1] if winners else []

            winners_per_pot.append(pot_winners)
            pot_distributions.append({
                "pot_amount": pot.amount,
                "winners": pot_winners,
            })

        winnings = self._pot_manager.distribute(winners_per_pot)

        # Apply winnings to player stacks
        for seat, amount in winnings.items():
            self._players[seat].chips += amount

        self._showdown_result = ShowdownResult(
            winners=winners,
            hand_results=hand_results,
            pot_distributions=pot_distributions,
        )

        logger.info(
            "Showdown complete. Winner(s): %s. Winnings: %s",
            winners,
            winnings,
        )

        return self._showdown_result

    def award_pot_to_last_player(self) -> int:
        """Award the pot to the last remaining (non-folded) player.

        Called when all other players have folded.

        Returns:
            Seat index of the winner.
        """
        active = [
            p for p in self._players
            if not p.is_folded and not p.is_eliminated
        ]
        if len(active) != 1:
            raise ValueError(
                f"Expected exactly 1 active player, found {len(active)}"
            )

        winner = active[0]
        winnings = self._pot_manager.distribute_simple([winner.seat_index])
        for seat, amount in winnings.items():
            self._players[seat].chips += amount

        self._phase = "between_hands"

        logger.info(
            "All others folded. Player %d wins %d chips",
            winner.seat_index,
            winnings.get(winner.seat_index, 0),
        )

        return winner.seat_index

    def end_hand(self) -> None:
        """Finalize a hand — check for eliminations and advance blinds."""
        self._phase = "between_hands"

        # Check for eliminations
        for p in self._players:
            if p.chips == 0 and not p.is_eliminated:
                p.is_eliminated = True
                logger.info(
                    "Player %d (%s) eliminated on hand %d",
                    p.seat_index,
                    p.name,
                    self._hand_number,
                )

        # Advance blind level
        blind_increased = self._blind_manager.advance_hand()
        if blind_increased:
            logger.info(
                "Blinds now %d/%d",
                self._blind_manager.small_blind,
                self._blind_manager.big_blind,
            )

    def active_player_count(self) -> int:
        """Count non-eliminated players.

        Returns:
            Number of players still in the tournament.
        """
        return sum(1 for p in self._players if not p.is_eliminated)

    def is_tournament_over(self) -> bool:
        """Check if the tournament is over (1 or fewer players remaining).

        Returns:
            True if the tournament is complete.
        """
        return self.active_player_count() <= 1

    def get_winner(self) -> PlayerState | None:
        """Get the tournament winner.

        Returns:
            The winning player, or None if tournament isn't over.
        """
        active = [p for p in self._players if not p.is_eliminated]
        if len(active) == 1:
            return active[0]
        return None

    def __repr__(self) -> str:
        return (
            f"GameEngine(hand={self._hand_number}, phase={self._phase}, "
            f"players={self.active_player_count()})"
        )
