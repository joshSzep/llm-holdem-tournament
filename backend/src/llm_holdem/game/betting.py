"""Betting logic — action validation and application."""

import logging
from typing import Literal

from llm_holdem.game.state import Action
from llm_holdem.game.state import ActionType
from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


class InvalidActionError(Exception):
    """Raised when a player attempts an invalid action."""

    pass


class BettingManager:
    """Manages betting actions, validation, and round completion detection.

    Handles fold, check, call, raise/bet actions and tracks the state
    needed to determine when a betting round is complete.
    """

    def __init__(self) -> None:
        """Initialize the betting manager for a new betting round."""
        self._current_bet: int = 0
        self._min_raise: int = 0
        self._last_raiser: int | None = None
        self._actions_this_round: list[Action] = []
        self._players_acted: set[int] = set()

    @property
    def current_bet(self) -> int:
        """The current bet level that players must match."""
        return self._current_bet

    @property
    def min_raise(self) -> int:
        """The minimum raise amount."""
        return self._min_raise

    @property
    def last_raiser(self) -> int | None:
        """Seat index of the last player who raised, or None."""
        return self._last_raiser

    @property
    def actions_this_round(self) -> list[Action]:
        """Actions taken in the current betting round."""
        return list(self._actions_this_round)

    def new_round(self, big_blind: int = 0) -> None:
        """Reset for a new betting round.

        Args:
            big_blind: The big blind amount (used as initial bet for pre-flop).
        """
        self._current_bet = big_blind
        self._min_raise = big_blind
        self._last_raiser = None
        self._actions_this_round = []
        self._players_acted = set()

    def get_valid_actions(
        self,
        player: PlayerState,
    ) -> list[ActionType]:
        """Get the list of valid actions for a player.

        Args:
            player: The player state.

        Returns:
            List of valid action types.
        """
        if player.is_folded or player.is_all_in or player.is_eliminated:
            return []

        actions: list[ActionType] = ["fold"]

        amount_to_call = self._current_bet - player.current_bet
        if amount_to_call <= 0:
            actions.append("check")
        else:
            actions.append("call")

        # Can raise if they have enough chips beyond a call
        if player.chips > amount_to_call:
            actions.append("raise")

        return actions

    def get_call_amount(self, player: PlayerState) -> int:
        """Get the amount a player needs to call.

        Args:
            player: The player state.

        Returns:
            Amount needed to call (0 if they can check).
        """
        amount = self._current_bet - player.current_bet
        # Can't call more than you have (all-in)
        return min(max(0, amount), player.chips)

    def get_min_raise_to(self, player: PlayerState) -> int:
        """Get the minimum total bet after a raise.

        The minimum raise is the current bet plus the minimum raise increment.

        Args:
            player: The player state.

        Returns:
            Minimum total bet amount for a raise.
        """
        return self._current_bet + self._min_raise

    def get_max_raise_to(self, player: PlayerState) -> int:
        """Get the maximum total bet (all-in amount).

        Args:
            player: The player state.

        Returns:
            Maximum total bet amount (player goes all-in).
        """
        return player.current_bet + player.chips

    def validate_action(
        self,
        player: PlayerState,
        action_type: ActionType,
        amount: int | None = None,
    ) -> tuple[bool, str]:
        """Validate a player action.

        Args:
            player: The player state.
            action_type: The action type.
            amount: The bet/raise amount (required for raises).

        Returns:
            Tuple of (is_valid, error_message).
        """
        valid_actions = self.get_valid_actions(player)
        if not valid_actions:
            return False, "Player cannot act (folded, all-in, or eliminated)"

        if action_type not in valid_actions:
            return False, f"Invalid action '{action_type}'. Valid actions: {valid_actions}"

        if action_type == "raise":
            if amount is None:
                return False, "Raise requires an amount"

            min_raise_to = self.get_min_raise_to(player)
            max_raise_to = self.get_max_raise_to(player)

            # All-in for less than minimum raise is allowed
            if amount < min_raise_to and amount != max_raise_to:
                return False, (
                    f"Raise to {amount} is below minimum raise to {min_raise_to} "
                    f"(all-in for {max_raise_to} is also valid)"
                )

            if amount > max_raise_to:
                return False, f"Raise to {amount} exceeds max of {max_raise_to}"

        return True, ""

    def apply_action(
        self,
        player: PlayerState,
        action_type: ActionType,
        amount: int | None = None,
        timestamp: str = "",
    ) -> Action:
        """Apply a player action to the game state.

        Modifies the player state in place.

        Args:
            player: The player state (will be modified).
            action_type: The action type.
            amount: The raise-to amount (for raises).
            timestamp: Action timestamp.

        Returns:
            The Action record.

        Raises:
            InvalidActionError: If the action is not valid.
        """
        is_valid, error = self.validate_action(player, action_type, amount)
        if not is_valid:
            raise InvalidActionError(error)

        action_amount: int | None = None

        if action_type == "fold":
            player.is_folded = True
            action_amount = 0
            logger.debug("Player %d folds", player.seat_index)

        elif action_type == "check":
            action_amount = 0
            logger.debug("Player %d checks", player.seat_index)

        elif action_type == "call":
            call_amount = self.get_call_amount(player)
            player.chips -= call_amount
            player.current_bet += call_amount
            if player.chips == 0:
                player.is_all_in = True
                logger.debug(
                    "Player %d calls %d (all-in)", player.seat_index, call_amount
                )
            else:
                logger.debug("Player %d calls %d", player.seat_index, call_amount)
            action_amount = call_amount

        elif action_type == "raise":
            assert amount is not None  # Validated above
            raise_to = amount
            # How much additional chips are needed from this player
            additional = raise_to - player.current_bet
            player.chips -= additional
            player.current_bet = raise_to

            # Update minimum raise increment
            raise_increment = raise_to - self._current_bet
            if raise_increment > self._min_raise:
                self._min_raise = raise_increment

            self._current_bet = raise_to
            self._last_raiser = player.seat_index

            if player.chips == 0:
                player.is_all_in = True
                logger.debug(
                    "Player %d raises to %d (all-in)", player.seat_index, raise_to
                )
            else:
                logger.debug("Player %d raises to %d", player.seat_index, raise_to)

            action_amount = additional
            # Reset acted set since everyone needs to act again after a raise
            self._players_acted = set()

        player.has_acted = True
        self._players_acted.add(player.seat_index)

        action = Action(
            player_index=player.seat_index,
            action_type=action_type,
            amount=action_amount,
            timestamp=timestamp,
        )
        self._actions_this_round.append(action)
        return action

    def is_round_complete(self, players: list[PlayerState]) -> bool:
        """Check if the current betting round is complete.

        A betting round is complete when all active (non-folded, non-all-in)
        players have acted and all bets are equal.

        Args:
            players: All players in the hand.

        Returns:
            True if the betting round is complete.
        """
        active_players = [
            p for p in players
            if not p.is_folded and not p.is_all_in and not p.is_eliminated
        ]

        if len(active_players) <= 1:
            return True

        # All active players must have acted
        for p in active_players:
            if p.seat_index not in self._players_acted:
                return False

        # All active players must have matched the current bet
        for p in active_players:
            if p.current_bet != self._current_bet:
                return False

        return True

    def count_active_players(self, players: list[PlayerState]) -> int:
        """Count players who haven't folded or been eliminated.

        Args:
            players: All players in the hand.

        Returns:
            Number of active (not folded, not eliminated) players.
        """
        return sum(
            1
            for p in players
            if not p.is_folded and not p.is_eliminated
        )

    def count_actionable_players(self, players: list[PlayerState]) -> int:
        """Count players who can still act (not folded, not all-in, not eliminated).

        Args:
            players: All players in the hand.

        Returns:
            Number of actionable players.
        """
        return sum(
            1
            for p in players
            if not p.is_folded and not p.is_all_in and not p.is_eliminated
        )

    def is_hand_over(self, players: list[PlayerState]) -> bool:
        """Check if the hand is over (only one active player remains).

        Args:
            players: All players in the hand.

        Returns:
            True if only one player hasn't folded.
        """
        return self.count_active_players(players) <= 1

    def should_skip_to_showdown(self, players: list[PlayerState]) -> bool:
        """Check if remaining rounds should be skipped straight to showdown.

        This happens when all remaining players are all-in (or only one
        can still act).

        Args:
            players: All players in the hand.

        Returns:
            True if no more betting can occur.
        """
        return self.count_actionable_players(players) <= 1 and self.count_active_players(players) > 1
