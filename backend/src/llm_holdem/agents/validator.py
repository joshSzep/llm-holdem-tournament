"""Prompt validator — ensures information integrity before every LLM call.

This is a HARD GATE: every prompt must pass validation before being sent
to any LLM. The validator ensures that no opponent hole cards or other
hidden information leaks into the prompt.
"""

import logging
import re

from llm_holdem.game.state import Card
from llm_holdem.game.state import GameState
from llm_holdem.game.state import PlayerState

logger = logging.getLogger(__name__)


class PromptValidationError(Exception):
    """Raised when a prompt contains information that should be hidden."""

    pass


def get_opponent_hole_cards(
    game_state: GameState,
    viewer_seat: int,
) -> list[Card]:
    """Extract all opponent hole cards from the game state.

    Args:
        game_state: The full game state.
        viewer_seat: The seat of the agent who should NOT see opponents' cards.

    Returns:
        List of all opponent hole cards.
    """
    opponent_cards: list[Card] = []
    for player in game_state.players:
        if player.seat_index != viewer_seat and player.hole_cards:
            opponent_cards.extend(player.hole_cards)
    return opponent_cards


def sanitize_game_state(
    game_state: GameState,
    viewer_seat: int,
) -> GameState:
    """Create a sanitized copy of the game state for a specific viewer.

    Strips opponent hole cards so only the viewer's own cards are visible.

    Args:
        game_state: The full game state with all information.
        viewer_seat: The seat of the agent viewing this state.

    Returns:
        A new GameState with opponent hole cards removed.
    """
    sanitized_players: list[PlayerState] = []
    for player in game_state.players:
        if player.seat_index == viewer_seat:
            # Viewer sees their own cards
            sanitized_players.append(player.model_copy())
        else:
            # Strip opponent hole cards
            sanitized = player.model_copy()
            sanitized.hole_cards = None
            sanitized_players.append(sanitized)

    return game_state.model_copy(update={"players": sanitized_players})


def _card_to_patterns(card: Card) -> list[str]:
    """Generate string patterns that could represent a card in a prompt.

    Args:
        card: The card to generate patterns for.

    Returns:
        List of possible string representations.
    """
    return [
        f"{card.rank}{card.suit}",
        f"{card.rank}{card.suit.upper()}",
    ]


def validate_prompt(
    prompt_text: str,
    game_state: GameState,
    viewer_seat: int,
) -> None:
    """Validate that a prompt does not contain hidden information.

    This is the HARD GATE. If validation fails, a PromptValidationError is
    raised and the prompt MUST NOT be sent to the LLM.

    Checks:
    1. No opponent hole cards appear in the prompt text.
    2. Only public information + the viewer's own cards are present.

    Args:
        prompt_text: The complete prompt text to validate.
        game_state: The full game state (for extracting opponent cards).
        viewer_seat: The seat of the agent whose perspective this is.

    Raises:
        PromptValidationError: If hidden information is found in the prompt.
    """
    opponent_cards = get_opponent_hole_cards(game_state, viewer_seat)

    if not opponent_cards:
        # No opponents have hole cards (e.g., between hands), nothing to leak
        logger.debug("Prompt validation passed (no opponent cards to check)")
        return

    # Check for each opponent card in the prompt
    for card in opponent_cards:
        patterns = _card_to_patterns(card)
        for pattern in patterns:
            # Use word-boundary-like matching to avoid false positives
            # e.g., "Ah" in "Ah" but not in "Yeah"
            # We look for the pattern surrounded by non-alphanumeric chars or string boundaries
            regex = r"(?<![a-zA-Z0-9])" + re.escape(pattern) + r"(?![a-zA-Z0-9])"
            if re.search(regex, prompt_text):
                raise PromptValidationError(
                    f"Prompt contains opponent hole card: {pattern} "
                    f"(viewer seat: {viewer_seat})"
                )

    logger.debug("Prompt validation passed for seat %d", viewer_seat)


def validate_and_build(
    prompt_text: str,
    game_state: GameState,
    viewer_seat: int,
) -> str:
    """Validate a prompt and return it if valid.

    Convenience function that acts as the mandatory gate.

    Args:
        prompt_text: The prompt text to validate.
        game_state: The full game state.
        viewer_seat: The viewer's seat.

    Returns:
        The validated prompt text.

    Raises:
        PromptValidationError: If validation fails.
    """
    validate_prompt(prompt_text, game_state, viewer_seat)
    return prompt_text
