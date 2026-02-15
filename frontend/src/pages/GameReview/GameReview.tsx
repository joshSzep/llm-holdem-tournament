/**
 * GameReview page — hand-by-hand replay of a completed game.
 * Includes hand navigator, action stepper, and read-only chat.
 */

import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import "./GameReview.css";
import { fetchHands, fetchHand } from "../../services/api";
import type { HandSummary, HandDetail } from "../../types/api";
import { CommunityCards } from "../../components/table/CommunityCards";
import type { Card } from "../../types/game";

export function GameReview(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const gameId = id ? Number(id) : null;

  const [hands, setHands] = useState<HandSummary[]>([]);
  const [currentHandIndex, setCurrentHandIndex] = useState(0);
  const [handDetail, setHandDetail] = useState<HandDetail | null>(null);
  const [actionIndex, setActionIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  // Load hand list
  useEffect(() => {
    if (gameId === null) return;
    setLoading(true);
    fetchHands(gameId)
      .then((h) => {
        setHands(h);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [gameId]);

  // Load hand detail when hand selection changes
  useEffect(() => {
    if (gameId === null || hands.length === 0) return;
    const hand = hands[currentHandIndex];
    if (!hand) return;
    fetchHand(gameId, hand.hand_number)
      .then((d) => {
        setHandDetail(d);
        setActionIndex(0);
      })
      .catch(() => {
        /* ignore */
      });
  }, [gameId, hands, currentHandIndex]);

  const handlePrevHand = useCallback(() => {
    setCurrentHandIndex((i) => Math.max(0, i - 1));
  }, []);

  const handleNextHand = useCallback(() => {
    setCurrentHandIndex((i) => Math.min(hands.length - 1, i + 1));
  }, [hands.length]);

  const handlePrevAction = useCallback(() => {
    setActionIndex((i) => Math.max(0, i - 1));
  }, []);

  const handleNextAction = useCallback(() => {
    if (!handDetail) return;
    setActionIndex((i) =>
      Math.min(handDetail.actions.length - 1, i + 1),
    );
  }, [handDetail]);

  const totalActions = handDetail?.actions.length ?? 0;

  // Parse community cards from JSON
  const parseCommunityCards = (): Card[] => {
    if (!handDetail) return [];
    try {
      const parsed: unknown = JSON.parse(handDetail.community_cards_json);
      if (Array.isArray(parsed)) return parsed as Card[];
    } catch {
      // ignore parse errors
    }
    return [];
  };

  if (loading) {
    return (
      <div className="game-review game-review--loading">
        <div className="game-review__status">Loading hands…</div>
      </div>
    );
  }

  if (hands.length === 0) {
    return (
      <div className="game-review game-review--empty">
        <div className="game-review__status">No hands to review</div>
        <button
          className="game-review__back-btn"
          onClick={() => navigate("/")}
        >
          Back to Lobby
        </button>
      </div>
    );
  }

  const currentHand = hands[currentHandIndex];

  return (
    <div className="game-review">
      {/* Header */}
      <header className="game-review__header">
        <button
          className="game-review__back-btn"
          onClick={() => navigate("/")}
        >
          ← Lobby
        </button>
        <h1 className="game-review__title">
          Game #{gameId} Review
        </h1>
      </header>

      {/* Hand navigator */}
      <div className="game-review__navigator">
        <button
          className="game-review__nav-btn"
          onClick={handlePrevHand}
          disabled={currentHandIndex === 0}
        >
          ← Prev Hand
        </button>
        <span className="game-review__hand-label">
          Hand {currentHand?.hand_number ?? "?"} of {hands.length}
        </span>
        <button
          className="game-review__nav-btn"
          onClick={handleNextHand}
          disabled={currentHandIndex >= hands.length - 1}
        >
          Next Hand →
        </button>
      </div>

      {/* Main content */}
      <div className="game-review__content">
        {/* Community cards */}
        <div className="game-review__board">
          <CommunityCards cards={parseCommunityCards()} />
        </div>

        {/* Hand info */}
        {currentHand && (
          <div className="game-review__hand-info">
            <span>
              Dealer:{" "}
              <strong>Seat {currentHand.dealer_position}</strong>
            </span>
            <span>
              Blinds:{" "}
              <strong>
                {currentHand.small_blind}/{currentHand.big_blind}
              </strong>
            </span>
          </div>
        )}

        {/* Action stepper */}
        {handDetail && totalActions > 0 && (
          <div className="game-review__actions">
            <div className="game-review__action-nav">
              <button
                className="game-review__nav-btn"
                onClick={handlePrevAction}
                disabled={actionIndex === 0}
              >
                ← Prev
              </button>
              <span className="game-review__action-label">
                Action {actionIndex + 1} of {totalActions}
              </span>
              <button
                className="game-review__nav-btn"
                onClick={handleNextAction}
                disabled={actionIndex >= totalActions - 1}
              >
                Next →
              </button>
            </div>

            {/* Action list */}
            <div className="game-review__action-list">
              {handDetail.actions.map((action, i) => (
                <div
                  key={i}
                  className={`game-review__action-item ${
                    i === actionIndex
                      ? "game-review__action-item--active"
                      : ""
                  } ${i < actionIndex ? "game-review__action-item--past" : ""}`}
                >
                  <span className="game-review__action-seat">
                    Seat {action.seat_index}
                  </span>
                  <span className="game-review__action-type">
                    {action.action_type}
                  </span>
                  {action.amount !== null && action.amount > 0 && (
                    <span className="game-review__action-amount">
                      {action.amount.toLocaleString()}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
