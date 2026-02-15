"""Tests for card and deck operations."""

from llm_holdem.game.dealer import Deck
from llm_holdem.game.state import RANKS, SUITS, Card


class TestCard:
    """Tests for the Card model."""

    def test_card_creation(self) -> None:
        card = Card(rank="A", suit="s")
        assert card.rank == "A"
        assert card.suit == "s"

    def test_card_str(self) -> None:
        card = Card(rank="K", suit="h")
        assert str(card) == "Kh"

    def test_card_display_name(self) -> None:
        card = Card(rank="A", suit="s")
        assert card.display_name == "Ace of Spades"

    def test_card_display_name_ten(self) -> None:
        card = Card(rank="T", suit="d")
        assert card.display_name == "Ten of Diamonds"

    def test_card_equality(self) -> None:
        card1 = Card(rank="A", suit="s")
        card2 = Card(rank="A", suit="s")
        assert card1 == card2

    def test_card_inequality(self) -> None:
        card1 = Card(rank="A", suit="s")
        card2 = Card(rank="K", suit="s")
        assert card1 != card2

    def test_card_inequality_different_suit(self) -> None:
        card1 = Card(rank="A", suit="s")
        card2 = Card(rank="A", suit="h")
        assert card1 != card2

    def test_card_hash(self) -> None:
        card1 = Card(rank="A", suit="s")
        card2 = Card(rank="A", suit="s")
        assert hash(card1) == hash(card2)

    def test_card_hashable_in_set(self) -> None:
        cards = {Card(rank="A", suit="s"), Card(rank="A", suit="s"), Card(rank="K", suit="h")}
        assert len(cards) == 2

    def test_card_repr(self) -> None:
        card = Card(rank="Q", suit="c")
        assert repr(card) == "Card(rank='Q', suit='c')"

    def test_card_not_equal_to_non_card(self) -> None:
        card = Card(rank="A", suit="s")
        assert card != "As"
        assert card != 42


class TestDeck:
    """Tests for the Deck class."""

    def test_new_deck_has_52_cards(self) -> None:
        deck = Deck()
        assert deck.remaining == 52
        assert len(deck) == 52

    def test_new_deck_has_no_dealt(self) -> None:
        deck = Deck()
        assert deck.dealt_count == 0

    def test_deck_contains_all_52_unique_cards(self) -> None:
        deck = Deck()
        all_cards = list(deck.cards)
        assert len(all_cards) == 52
        # Check for uniqueness
        card_set = set(all_cards)
        assert len(card_set) == 52

    def test_deck_contains_all_ranks_and_suits(self) -> None:
        deck = Deck()
        all_cards = list(deck.cards)
        for rank in RANKS:
            for suit in SUITS:
                assert Card(rank=rank, suit=suit) in all_cards

    def test_deal_one_card(self) -> None:
        deck = Deck()
        card = deck.deal_one()
        assert isinstance(card, Card)
        assert deck.remaining == 51
        assert deck.dealt_count == 1

    def test_deal_multiple_cards(self) -> None:
        deck = Deck()
        cards = deck.deal(5)
        assert len(cards) == 5
        assert deck.remaining == 47

    def test_deal_returns_unique_cards(self) -> None:
        deck = Deck()
        deck.shuffle()
        cards = deck.deal(52)
        assert len(set(cards)) == 52

    def test_deal_zero_raises(self) -> None:
        deck = Deck()
        import pytest

        with pytest.raises(ValueError, match="Cannot deal 0 cards"):
            deck.deal(0)

    def test_deal_negative_raises(self) -> None:
        deck = Deck()
        import pytest

        with pytest.raises(ValueError, match="Cannot deal -1 cards"):
            deck.deal(-1)

    def test_deal_too_many_raises(self) -> None:
        deck = Deck()
        import pytest

        with pytest.raises(ValueError, match="only 52 remaining"):
            deck.deal(53)

    def test_deal_exhausts_deck(self) -> None:
        deck = Deck()
        import pytest

        deck.deal(52)
        with pytest.raises(ValueError, match="only 0 remaining"):
            deck.deal_one()

    def test_shuffle_changes_order(self) -> None:
        deck1 = Deck(seed=42)
        deck2 = Deck(seed=42)

        # Before shuffle, decks should be in same order
        assert list(deck1.cards) == list(deck2.cards)

        # After shuffle with same seed, they should still match
        deck1.shuffle()
        deck2.shuffle()
        assert list(deck1.cards) == list(deck2.cards)

        # But shuffled deck should differ from unshuffled
        deck3 = Deck()
        assert list(deck1.cards) != list(deck3.cards)

    def test_shuffle_with_seed_is_reproducible(self) -> None:
        deck1 = Deck(seed=123)
        deck1.shuffle()
        cards1 = deck1.deal(52)

        deck2 = Deck(seed=123)
        deck2.shuffle()
        cards2 = deck2.deal(52)

        assert cards1 == cards2

    def test_shuffle_without_seed_is_random(self) -> None:
        # Two decks shuffled without seed should almost certainly differ
        deck1 = Deck()
        deck1.shuffle()
        order1 = [str(c) for c in deck1.cards]

        deck2 = Deck()
        deck2.shuffle()
        order2 = [str(c) for c in deck2.cards]

        # Statistically near-impossible to be equal
        assert order1 != order2

    def test_reset(self) -> None:
        deck = Deck()
        deck.shuffle()
        deck.deal(10)
        assert deck.remaining == 42

        deck.reset()
        assert deck.remaining == 52
        assert deck.dealt_count == 0

    def test_burn(self) -> None:
        deck = Deck()
        burned = deck.burn()
        assert isinstance(burned, Card)
        assert deck.remaining == 51

    def test_deal_to_players(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        hands = deck.deal_to_players(6)
        assert len(hands) == 6
        for hand in hands:
            assert len(hand) == 2
        assert deck.remaining == 40

    def test_deal_to_players_round_robin(self) -> None:
        """Cards are dealt round-robin: one to each player, then repeat."""
        deck = Deck(seed=42)
        deck.shuffle()

        # Deal to 3 players
        hands = deck.deal_to_players(3)

        # Reconstruct the deal order: player0-card1, p1-c1, p2-c1, p0-c2, p1-c2, p2-c2
        deck2 = Deck(seed=42)
        deck2.shuffle()
        all_dealt = deck2.deal(6)

        assert hands[0][0] == all_dealt[0]
        assert hands[1][0] == all_dealt[1]
        assert hands[2][0] == all_dealt[2]
        assert hands[0][1] == all_dealt[3]
        assert hands[1][1] == all_dealt[4]
        assert hands[2][1] == all_dealt[5]

    def test_deal_to_players_too_many_raises(self) -> None:
        deck = Deck()
        import pytest

        with pytest.raises(ValueError, match="Cannot deal"):
            deck.deal_to_players(27)  # 27 * 2 = 54 > 52

    def test_deal_community_flop(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        deck.deal(12)  # Deal to 6 players
        flop = deck.deal_community(3)
        assert len(flop) == 3
        # 52 - 12 (hole) - 1 (burn) - 3 (flop) = 36
        assert deck.remaining == 36

    def test_deal_community_without_burn(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        cards = deck.deal_community(3, burn=False)
        assert len(cards) == 3
        assert deck.remaining == 49  # No burn

    def test_deal_community_turn(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        deck.deal(12)  # Hole cards
        deck.deal_community(3)  # Flop (burn + 3)
        turn = deck.deal_community(1)  # Turn (burn + 1)
        assert len(turn) == 1
        # 52 - 12 - 1 - 3 - 1 - 1 = 34
        assert deck.remaining == 34

    def test_deal_community_river(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        deck.deal(12)  # Hole cards
        deck.deal_community(3)  # Flop
        deck.deal_community(1)  # Turn
        river = deck.deal_community(1)  # River
        assert len(river) == 1
        # 52 - 12 - 1 - 3 - 1 - 1 - 1 - 1 = 32
        assert deck.remaining == 32

    def test_full_hand_deal_sequence(self) -> None:
        """Simulate a full hand deal for 6 players."""
        deck = Deck(seed=42)
        deck.shuffle()

        # Deal hole cards
        hands = deck.deal_to_players(6)
        assert deck.remaining == 40

        # Flop
        flop = deck.deal_community(3)
        assert len(flop) == 3
        assert deck.remaining == 36

        # Turn
        turn = deck.deal_community(1)
        assert len(turn) == 1
        assert deck.remaining == 34

        # River
        river = deck.deal_community(1)
        assert len(river) == 1
        assert deck.remaining == 32

        # All dealt cards should be unique
        all_cards = []
        for hand in hands:
            all_cards.extend(hand)
        all_cards.extend(flop)
        all_cards.extend(turn)
        all_cards.extend(river)
        # Don't forget the 3 burn cards
        assert len(set(all_cards)) == len(all_cards)

    def test_peek(self) -> None:
        deck = Deck(seed=42)
        deck.shuffle()
        peeked = deck.peek(3)
        assert len(peeked) == 3
        assert deck.remaining == 52  # Peek doesn't remove cards

        # Dealing should give the same cards
        dealt = deck.deal(3)
        assert dealt == peeked

    def test_peek_too_many_raises(self) -> None:
        deck = Deck()
        deck.deal(50)
        import pytest

        with pytest.raises(ValueError, match="Cannot peek"):
            deck.peek(3)

    def test_repr(self) -> None:
        deck = Deck()
        assert repr(deck) == "Deck(remaining=52, dealt=0)"
        deck.deal(5)
        assert repr(deck) == "Deck(remaining=47, dealt=5)"

    def test_shuffle_only_shuffles_remaining(self) -> None:
        """Shuffling after dealing should only shuffle remaining cards."""
        deck = Deck(seed=42)
        deck.shuffle()
        dealt = deck.deal(10)

        # Shuffle remaining cards
        deck.shuffle()

        # Previously dealt cards should still be at the front
        assert list(deck.cards[:10]) == dealt
