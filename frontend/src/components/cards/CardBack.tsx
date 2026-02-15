/**
 * CardBack — a face-down card.
 */

import "./Card.css";

export function CardBack(): React.ReactElement {
  return (
    <div className="card-back">
      <div className="card-back__pattern" />
    </div>
  );
}
