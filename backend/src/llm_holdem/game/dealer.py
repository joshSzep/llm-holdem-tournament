"""Deck and card dealing operations."""

import logging
import random
from collections.abc import Sequence

from llm_holdem.game.state import RANKS, SUITS, Card

logger = logging.getLogger(__name__)


class Deck:
    """A standard 52-card deck with shuffle and deal operations.

    The deck is created in order and must be shuffled before dealing.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize a new deck.

        Args:
            seed: Optional random seed for reproducible shuffling (tests).
        """
        self._cards: list[Card] = []
        self._dealt_count: int = 0
        self._rng = random.Random(seed)
        self.reset()

    def reset(self) -> None:
        """Reset the deck to a full 52-card ordered state."""
        self._cards = [Card(rank=rank, suit=suit) for suit in SUITS for rank in RANKS]
        self._dealt_count = 0

    def shuffle(self) -> None:
        """Shuffle the remaining cards in the deck."""
        remaining = self._cards[self._dealt_count :]
        self._rng.shuffle(remaining)
        self._cards[self._dealt_count :] = remaining
        logger.debug("Deck shuffled, %d cards remaining", self.remaining)

    @property
    def remaining(self) -> int:
        """Number of cards remaining in the deck."""
        return len(self._cards) - self._dealt_count

    @property
    def dealt_count(self) -> int:
        """Number of cards already dealt."""
        return self._dealt_count

    def deal(self, count: int = 1) -> list[Card]:
        """Deal cards from the top of the deck.

        Args:
            count: Number of cards to deal.

        Returns:
            List of dealt cards.

        Raises:
            ValueError: If not enough cards remain.
        """
        if count < 1:
            raise ValueError(f"Cannot deal {count} cards (must be >= 1)")
        if count > self.remaining:
            raise ValueError(
                f"Cannot deal {count} cards, only {self.remaining} remaining"
            )

        cards = self._cards[self._dealt_count : self._dealt_count + count]
        self._dealt_count += count
        logger.debug("Dealt %d card(s), %d remaining", count, self.remaining)
        return cards

    def deal_one(self) -> Card:
        """Deal a single card from the top of the deck.

        Returns:
            The dealt card.

        Raises:
            ValueError: If no cards remain.
        """
        return self.deal(1)[0]

    def burn(self) -> Card:
        """Burn (discard) one card from the top of the deck.

        Returns:
            The burned card.
        """
        logger.debug("Burning a card")
        return self.deal_one()

    def deal_to_players(
        self, num_players: int, cards_per_player: int = 2
    ) -> list[list[Card]]:
        """Deal hole cards to players in round-robin order.

        Cards are dealt one at a time to each player in sequence,
        mimicking real poker dealing.

        Args:
            num_players: Number of players to deal to.
            cards_per_player: Cards to deal to each player (default 2).

        Returns:
            List of lists, where each inner list is a player's hole cards.

        Raises:
            ValueError: If not enough cards for all players.
        """
        total_needed = num_players * cards_per_player
        if total_needed > self.remaining:
            raise ValueError(
                f"Cannot deal {total_needed} cards to {num_players} players, "
                f"only {self.remaining} remaining"
            )

        hands: list[list[Card]] = [[] for _ in range(num_players)]
        for _round in range(cards_per_player):
            for player_idx in range(num_players):
                hands[player_idx].append(self.deal_one())

        logger.debug(
            "Dealt %d cards each to %d players", cards_per_player, num_players
        )
        return hands

    def deal_community(self, count: int, burn: bool = True) -> list[Card]:
        """Deal community cards (with optional burn).

        Args:
            count: Number of community cards to deal.
            burn: Whether to burn a card first (default True per poker rules).

        Returns:
            List of community cards.
        """
        if burn:
            self.burn()
        return self.deal(count)

    def peek(self, count: int = 1) -> list[Card]:
        """Look at the top cards without removing them.

        Args:
            count: Number of cards to peek at.

        Returns:
            List of cards at the top of the deck.
        """
        if count > self.remaining:
            raise ValueError(
                f"Cannot peek at {count} cards, only {self.remaining} remaining"
            )
        return self._cards[self._dealt_count : self._dealt_count + count]

    @property
    def cards(self) -> Sequence[Card]:
        """All cards in the deck (dealt and undealt), read-only."""
        return self._cards

    def __len__(self) -> int:
        return self.remaining

    def __repr__(self) -> str:
        return f"Deck(remaining={self.remaining}, dealt={self.dealt_count})"
