/**
 * HoleCards — displays the two hole cards for a player.
 * Shows face-up cards if visible, face-down otherwise.
 */

import type { Card as CardType } from "../../types/game";
import { Card } from "./Card";
import { CardBack } from "./CardBack";
import "./Card.css";

interface HoleCardsProps {
  cards: CardType[] | null;
  small?: boolean;
}

export function HoleCards({
  cards,
  small = false,
}: HoleCardsProps): React.ReactElement {
  return (
    <div className={`hole-cards ${small ? "hole-cards--small" : ""}`}>
      {cards && cards.length >= 2 ? (
        <>
          <Card card={cards[0]!} />
          <Card card={cards[1]!} />
        </>
      ) : (
        <>
          <CardBack />
          <CardBack />
        </>
      )}
    </div>
  );
}
