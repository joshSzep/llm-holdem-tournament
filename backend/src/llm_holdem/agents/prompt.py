"""Prompt builder — constructs structured game context for LLM agents.

Builds the user-message content that accompanies the system prompt for both
action and chat agents. Handles formatting of cards, stacks, pots, betting
history, hand history, and recent chat.
"""

import logging

from llm_holdem.game.state import Action
from llm_holdem.game.state import Card
from llm_holdem.game.state import GameState
from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


def format_card(card: Card) -> str:
    """Format a card for display in a prompt.

    Args:
        card: A Card object.

    Returns:
        A human-readable string like 'As' for Ace of spades.
    """
    return f"{card.rank}{card.suit}"


def format_cards(cards: list[Card]) -> str:
    """Format a list of cards.

    Args:
        cards: List of Card objects.

    Returns:
        Space-separated card strings, or 'none' if empty.
    """
    if not cards:
        return "none"
    return " ".join(format_card(c) for c in cards)


def format_player_info(
    player: PlayerState,
    viewer_seat: int,
    show_hole_cards: bool = False,
) -> str:
    """Format a single player's visible information.

    Args:
        player: The player's state.
        viewer_seat: The seat index of the agent viewing this info.
        show_hole_cards: Whether to reveal hole cards (only for the viewer's own hand).

    Returns:
        A formatted string describing the player.
    """
    parts: list[str] = []
    parts.append(f"Seat {player.seat_index}: {player.name}")
    parts.append(f"Chips: {player.chips}")

    if player.is_eliminated:
        parts.append("(ELIMINATED)")
    elif player.is_folded:
        parts.append("(FOLDED)")
    elif player.is_all_in:
        parts.append("(ALL-IN)")

    if player.current_bet > 0:
        parts.append(f"Current bet: {player.current_bet}")

    if player.is_dealer:
        parts.append("(DEALER)")

    # Only show hole cards for the viewer's own seat
    if show_hole_cards and player.seat_index == viewer_seat and player.hole_cards:
        parts.append(f"Hole cards: {format_cards(player.hole_cards)}")

    return " | ".join(parts)


def format_action(action: Action) -> str:
    """Format a single action for display.

    Args:
        action: The action.

    Returns:
        A human-readable action string.
    """
    if action.action_type == "post_blind":
        return f"Seat {action.player_index} posts blind {action.amount}"
    elif action.action_type == "fold":
        return f"Seat {action.player_index} folds"
    elif action.action_type == "check":
        return f"Seat {action.player_index} checks"
    elif action.action_type == "call":
        return f"Seat {action.player_index} calls {action.amount}"
    elif action.action_type == "raise":
        return f"Seat {action.player_index} raises to {action.amount}"
    return f"Seat {action.player_index} {action.action_type} {action.amount or ''}"


def format_betting_history(actions: list[Action]) -> str:
    """Format the betting history for the current hand.

    Args:
        actions: List of actions in the current hand.

    Returns:
        Newline-separated action descriptions.
    """
    if not actions:
        return "No actions yet."
    return "\n".join(format_action(a) for a in actions)


def format_pot_info(game_state: GameState) -> str:
    """Format pot information.

    Args:
        game_state: The current game state.

    Returns:
        A string describing the pot(s).
    """
    if not game_state.pots:
        return "Pot: 0"

    parts: list[str] = []
    for i, pot in enumerate(game_state.pots):
        label = "Main pot" if i == 0 else f"Side pot {i}"
        parts.append(f"{label}: {pot.amount}")
    return "\n".join(parts)


def build_action_prompt(
    game_state: GameState,
    seat_index: int,
    valid_actions: list[str],
    min_raise_to: int | None = None,
    max_raise_to: int | None = None,
    call_amount: int | None = None,
    hand_history: list[dict[str, str]] | None = None,
) -> str:
    """Build the user-message content for an action decision.

    Args:
        game_state: The current game state.
        seat_index: The seat of the agent making the decision.
        valid_actions: List of valid action types.
        min_raise_to: Minimum raise-to amount (if raise is valid).
        max_raise_to: Maximum raise-to amount (if raise is valid).
        call_amount: Amount to call (if call is valid).
        hand_history: Optional list of previous hand summaries.

    Returns:
        A formatted prompt string.
    """
    sections: list[str] = []

    # Game info
    sections.append(f"=== GAME STATE (Hand #{game_state.hand_number}) ===")
    sections.append(f"Phase: {game_state.phase}")
    sections.append(f"Blinds: {game_state.small_blind}/{game_state.big_blind}")
    sections.append(f"Your seat: {seat_index}")
    sections.append("")

    # Players
    sections.append("=== PLAYERS ===")
    for player in game_state.players:
        if not player.is_eliminated:
            show_cards = player.seat_index == seat_index
            sections.append(format_player_info(player, seat_index, show_hole_cards=show_cards))
    sections.append("")

    # Community cards
    sections.append("=== COMMUNITY CARDS ===")
    sections.append(format_cards(game_state.community_cards))
    sections.append("")

    # Pots
    sections.append("=== POT ===")
    sections.append(format_pot_info(game_state))
    sections.append("")

    # Betting history
    sections.append("=== BETTING HISTORY (this hand) ===")
    sections.append(format_betting_history(game_state.current_hand_actions))
    sections.append("")

    # Valid actions
    sections.append("=== YOUR VALID ACTIONS ===")
    action_parts: list[str] = []
    for action in valid_actions:
        if action == "call" and call_amount is not None:
            action_parts.append(f"call (costs {call_amount})")
        elif action == "raise" and min_raise_to is not None:
            max_str = f", max {max_raise_to}" if max_raise_to is not None else ""
            action_parts.append(f"raise (min raise-to: {min_raise_to}{max_str})")
        else:
            action_parts.append(action)
    sections.append(", ".join(action_parts))
    sections.append("")

    # Hand history (previous hands, if available)
    if hand_history:
        sections.append("=== RECENT HAND HISTORY ===")
        for entry in hand_history:
            sections.append(f"Hand #{entry.get('hand_number', '?')}: {entry.get('summary', '')}")
        sections.append("")

    sections.append("What is your action?")

    return "\n".join(sections)


def build_chat_prompt(
    game_state: GameState,
    seat_index: int,
    trigger_event: str,
    event_description: str,
    recent_chat: list[dict[str, str]] | None = None,
) -> str:
    """Build the user-message content for a chat/table-talk response.

    Args:
        game_state: The current game state.
        seat_index: The seat of the agent generating chat.
        trigger_event: The event type that triggered chat (e.g., 'showdown', 'all_in').
        event_description: Human-readable description of what happened.
        recent_chat: Optional list of recent chat messages.

    Returns:
        A formatted prompt string.
    """
    sections: list[str] = []

    sections.append(f"=== TABLE SITUATION (Hand #{game_state.hand_number}) ===")
    sections.append(f"Phase: {game_state.phase}")
    sections.append(f"Community cards: {format_cards(game_state.community_cards)}")
    sections.append(format_pot_info(game_state))
    sections.append("")

    # Player summary
    sections.append("=== PLAYERS ===")
    for player in game_state.players:
        if not player.is_eliminated:
            sections.append(format_player_info(player, seat_index))
    sections.append("")

    # Event
    sections.append(f"=== EVENT: {trigger_event.upper()} ===")
    sections.append(event_description)
    sections.append("")

    # Recent chat
    if recent_chat:
        sections.append("=== RECENT TABLE TALK ===")
        for msg in recent_chat[-10:]:  # Last 10 messages
            sections.append(f"{msg.get('name', 'Unknown')}: {msg.get('message', '')}")
        sections.append("")

    sections.append(
        "React to this event in character. "
        "Keep it short (1-2 sentences). "
        "Set message to null if you don't want to say anything."
    )

    return "\n".join(sections)
