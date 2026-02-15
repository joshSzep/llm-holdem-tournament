/**
 * CommunityCards — displays the 5-card community area in the center of the table.
 */

import type { Card as CardType } from "../../types/game";
import { Card } from "../cards/Card";

interface CommunityCardsProps {
  cards: CardType[];
}

export function CommunityCards({
  cards,
}: CommunityCardsProps): React.ReactElement {
  return (
    <div className="community-cards">
      {cards.map((card, i) => (
        <Card key={`${card.rank}${card.suit}-${i}`} card={card} />
      ))}
      {/* Empty placeholders for undealt cards */}
      {Array.from({ length: 5 - cards.length }).map((_, i) => (
        <div key={`empty-${i}`} className="community-cards__placeholder" />
      ))}
    </div>
  );
}
