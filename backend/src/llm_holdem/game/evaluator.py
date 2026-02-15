"""Hand evaluation wrapper around the treys library."""

import logging

from treys import Card as TreysCard
from treys import Evaluator as TreysEvaluator

from llm_holdem.game.state import Card
from llm_holdem.game.state import HandResult
from llm_holdem.game.state import RANK_NAMES

logger = logging.getLogger(__name__)

# Singleton evaluator instance (stateless, thread-safe)
_evaluator = TreysEvaluator()

# Map our rank notation to treys notation (they're the same except we confirm)
_RANK_TO_TREYS: dict[str, str] = {
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "T": "T",
    "J": "J",
    "Q": "Q",
    "K": "K",
    "A": "A",
}

_SUIT_TO_TREYS: dict[str, str] = {
    "h": "h",
    "d": "d",
    "c": "c",
    "s": "s",
}

# Rank class constants from treys (0 = Royal Flush, 9 = High Card)
HAND_RANK_NAMES: dict[int, str] = {
    0: "Royal Flush",
    1: "Straight Flush",
    2: "Four of a Kind",
    3: "Full House",
    4: "Flush",
    5: "Straight",
    6: "Three of a Kind",
    7: "Two Pair",
    8: "Pair",
    9: "High Card",
}


def card_to_treys(card: Card) -> int:
    """Convert our Card model to a treys integer representation.

    Args:
        card: Our Card model.

    Returns:
        Treys integer card representation.
    """
    treys_str = f"{_RANK_TO_TREYS[card.rank]}{_SUIT_TO_TREYS[card.suit]}"
    return TreysCard.new(treys_str)


def cards_to_treys(cards: list[Card]) -> list[int]:
    """Convert a list of our Card models to treys integers.

    Args:
        cards: List of our Card models.

    Returns:
        List of treys integer card representations.
    """
    return [card_to_treys(c) for c in cards]


def evaluate_hand(hole_cards: list[Card], community_cards: list[Card]) -> HandResult:
    """Evaluate a poker hand.

    Args:
        hole_cards: The player's two hole cards.
        community_cards: The community cards (3-5 cards).

    Returns:
        HandResult with rank, name, and description.

    Raises:
        ValueError: If card counts are invalid.
    """
    if len(hole_cards) != 2:
        raise ValueError(f"Expected 2 hole cards, got {len(hole_cards)}")
    if not (3 <= len(community_cards) <= 5):
        raise ValueError(
            f"Expected 3-5 community cards, got {len(community_cards)}"
        )

    treys_hole = cards_to_treys(hole_cards)
    treys_board = cards_to_treys(community_cards)

    score = _evaluator.evaluate(treys_board, treys_hole)
    rank_class = _evaluator.get_rank_class(score)
    class_name = _evaluator.class_to_string(rank_class)

    # Build a descriptive hand name
    description = _build_hand_description(hole_cards, community_cards, class_name, rank_class)

    return HandResult(
        player_index=-1,  # Caller should set this
        hand_rank=score,
        hand_name=class_name,
        hand_description=description,
    )


def compare_hands(
    players_hole_cards: dict[int, list[Card]],
    community_cards: list[Card],
) -> list[HandResult]:
    """Evaluate and rank multiple players' hands.

    Args:
        players_hole_cards: Mapping of player seat index to their hole cards.
        community_cards: The community cards (3-5 cards).

    Returns:
        List of HandResult sorted by rank (best first, lowest score = best).
    """
    results: list[HandResult] = []

    for seat_index, hole_cards in players_hole_cards.items():
        result = evaluate_hand(hole_cards, community_cards)
        result.player_index = seat_index
        results.append(result)

    # Sort by hand_rank ascending (lower score = better hand in treys)
    results.sort(key=lambda r: r.hand_rank)
    return results


def determine_winners(
    players_hole_cards: dict[int, list[Card]],
    community_cards: list[Card],
) -> tuple[list[int], list[HandResult]]:
    """Determine the winner(s) of a hand.

    Args:
        players_hole_cards: Mapping of player seat index to their hole cards.
        community_cards: The community cards (3-5 cards).

    Returns:
        Tuple of (winner seat indices, all hand results sorted best-first).
        Multiple winners indicates a split pot.
    """
    if not players_hole_cards:
        return [], []

    results = compare_hands(players_hole_cards, community_cards)
    if not results:
        return [], []

    # Winners are all players with the same (best) rank
    best_rank = results[0].hand_rank
    winners = [r.player_index for r in results if r.hand_rank == best_rank]

    logger.info(
        "Hand evaluation: winner(s) %s with %s (rank %d)",
        winners,
        results[0].hand_name,
        best_rank,
    )

    return winners, results


def _build_hand_description(
    hole_cards: list[Card],
    community_cards: list[Card],
    class_name: str,
    rank_class: int,
) -> str:
    """Build a human-readable description of the hand.

    Args:
        hole_cards: Player's hole cards.
        community_cards: Community cards.
        class_name: The hand class name from treys.
        rank_class: The integer rank class.

    Returns:
        Descriptive string like "Full House, Kings full of Sevens".
    """
    all_cards = hole_cards + community_cards
    ranks = [c.rank for c in all_cards]
    rank_counts: dict[str, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1

    # Sort by count descending, then by rank value descending
    rank_order = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
    sorted_ranks = sorted(
        rank_counts.keys(),
        key=lambda r: (-rank_counts[r], rank_order.index(r)),
    )

    if rank_class == 3:  # Full House
        trips = [r for r in sorted_ranks if rank_counts[r] >= 3]
        pairs = [r for r in sorted_ranks if rank_counts[r] >= 2 and r != trips[0]]
        if trips and pairs:
            return f"{class_name}, {RANK_NAMES[trips[0]]}s full of {RANK_NAMES[pairs[0]]}s"
    elif rank_class == 2:  # Four of a Kind
        quads = [r for r in sorted_ranks if rank_counts[r] >= 4]
        if quads:
            return f"{class_name}, {RANK_NAMES[quads[0]]}s"
    elif rank_class == 6:  # Three of a Kind
        trips = [r for r in sorted_ranks if rank_counts[r] >= 3]
        if trips:
            return f"{class_name}, {RANK_NAMES[trips[0]]}s"
    elif rank_class == 7:  # Two Pair
        pairs = [r for r in sorted_ranks if rank_counts[r] >= 2]
        if len(pairs) >= 2:
            return f"{class_name}, {RANK_NAMES[pairs[0]]}s and {RANK_NAMES[pairs[1]]}s"
    elif rank_class == 8:  # Pair
        pairs = [r for r in sorted_ranks if rank_counts[r] >= 2]
        if pairs:
            return f"{class_name}, {RANK_NAMES[pairs[0]]}s"
    elif rank_class == 9:  # High Card
        # Find highest card
        best = min(sorted_ranks, key=lambda r: rank_order.index(r))
        return f"{class_name}, {RANK_NAMES[best]}"

    return class_name
