"""Pot management — main pot, side pots, and distribution."""

import logging

from llm_holdem.game.state import Pot

logger = logging.getLogger(__name__)


class PotManager:
    """Manages the pot(s) for a hand, including side pot creation and distribution.

    Side pots are created when players go all-in for different amounts.
    """

    def __init__(self) -> None:
        """Initialize with an empty main pot."""
        self._pots: list[Pot] = [Pot(amount=0, eligible_players=[])]
        self._player_contributions: dict[int, int] = {}

    @property
    def pots(self) -> list[Pot]:
        """Current pots (main + side pots)."""
        return self._pots

    @property
    def total(self) -> int:
        """Total amount across all pots."""
        return sum(p.amount for p in self._pots)

    @property
    def main_pot(self) -> Pot:
        """The main pot."""
        return self._pots[0]

    @property
    def side_pots(self) -> list[Pot]:
        """All side pots (excluding main pot)."""
        return self._pots[1:]

    @property
    def player_contributions(self) -> dict[int, int]:
        """Total amount each player has contributed across all pots."""
        return dict(self._player_contributions)

    def add_bet(self, seat_index: int, amount: int) -> None:
        """Add a bet from a player.

        Args:
            seat_index: The player's seat index.
            amount: The amount to add.
        """
        if amount <= 0:
            return

        self._player_contributions[seat_index] = (
            self._player_contributions.get(seat_index, 0) + amount
        )

        # Add to the main pot, side pots are calculated separately
        self._pots[0].amount += amount
        if seat_index not in self._pots[0].eligible_players:
            self._pots[0].eligible_players.append(seat_index)

        logger.debug(
            "Player %d added %d to pot (total: %d)", seat_index, amount, self.total
        )

    def calculate_side_pots(
        self,
        all_in_amounts: dict[int, int],
        active_players: list[int],
    ) -> None:
        """Recalculate pots from scratch based on contributions and all-ins.

        This is called when a betting round ends and side pots need to be created.

        Args:
            all_in_amounts: Mapping of seat index to total all-in amount for
                players who went all-in this hand.
            active_players: Seat indices of all players still in the hand
                (not folded, not eliminated).
        """
        if not all_in_amounts:
            # No all-ins, keep single pot with active players as eligible
            self._pots = [
                Pot(amount=self.total, eligible_players=sorted(active_players))
            ]
            return

        contributions = dict(self._player_contributions)
        if not contributions:
            return

        # Get unique contribution levels from all-in players, sorted ascending
        all_in_levels = sorted(set(all_in_amounts.values()))

        # Build pots by slicing at each all-in level
        pots: list[Pot] = []
        prev_level = 0

        for level in all_in_levels:
            pot_amount = 0
            eligible: list[int] = []

            for player, total_contrib in contributions.items():
                if player not in active_players:
                    continue
                # Each player contributes up to (level - prev_level) to this pot
                player_contrib = min(total_contrib - prev_level, level - prev_level)
                if player_contrib > 0:
                    pot_amount += player_contrib
                    eligible.append(player)

            if pot_amount > 0:
                pots.append(Pot(amount=pot_amount, eligible_players=sorted(eligible)))

            prev_level = level

        # Remaining pot for players who contributed more than the highest all-in
        max_all_in = max(all_in_levels) if all_in_levels else 0
        remaining_amount = 0
        remaining_eligible: list[int] = []

        for player, total_contrib in contributions.items():
            if player not in active_players:
                continue
            excess = total_contrib - max_all_in
            if excess > 0:
                remaining_amount += excess
                remaining_eligible.append(player)

        if remaining_amount > 0:
            pots.append(
                Pot(amount=remaining_amount, eligible_players=sorted(remaining_eligible))
            )

        # Add contributions from folded players to the main (first) pot
        folded_total = sum(
            contrib
            for player, contrib in contributions.items()
            if player not in active_players
        )
        if folded_total > 0 and pots:
            # Distribute folded contributions across pots proportionally
            # Simplified: add to first pot they were eligible for
            pots[0].amount += folded_total

        self._pots = pots if pots else [Pot(amount=0, eligible_players=[])]

        logger.info(
            "Side pots calculated: %d pot(s), total %d",
            len(self._pots),
            self.total,
        )

    def distribute(
        self,
        winners_per_pot: list[list[int]],
    ) -> dict[int, int]:
        """Distribute pot(s) to winners.

        Args:
            winners_per_pot: For each pot, the list of winner seat indices.
                If multiple winners for a pot, it's split evenly.

        Returns:
            Mapping of seat index to total winnings.
        """
        winnings: dict[int, int] = {}

        for i, pot in enumerate(self._pots):
            if i >= len(winners_per_pot):
                logger.warning("No winners specified for pot %d", i)
                continue

            pot_winners = winners_per_pot[i]
            if not pot_winners:
                logger.warning("Empty winner list for pot %d", i)
                continue

            share = pot.amount // len(pot_winners)
            remainder = pot.amount % len(pot_winners)

            for j, winner in enumerate(pot_winners):
                # Give the odd chip(s) to the first winner(s)
                extra = 1 if j < remainder else 0
                total = share + extra
                winnings[winner] = winnings.get(winner, 0) + total

            logger.info(
                "Pot %d (%d chips): distributed to %s",
                i,
                pot.amount,
                pot_winners,
            )

        return winnings

    def distribute_simple(self, winners: list[int]) -> dict[int, int]:
        """Distribute all pots to the same winner(s).

        Convenience method when there's no need for per-pot winner tracking
        (e.g., everyone folds to one player).

        Args:
            winners: List of winner seat indices.

        Returns:
            Mapping of seat index to total winnings.
        """
        return self.distribute([winners] * len(self._pots))

    def reset(self) -> None:
        """Reset for a new hand."""
        self._pots = [Pot(amount=0, eligible_players=[])]
        self._player_contributions.clear()

    def __repr__(self) -> str:
        return f"PotManager(pots={len(self._pots)}, total={self.total})"
