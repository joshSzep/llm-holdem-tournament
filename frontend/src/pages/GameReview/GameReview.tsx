/**
 * GameReview page — hand-by-hand replay of a completed game.
 * Includes hand navigator, action stepper, player info with hole cards,
 * chat timeline, and omniscient view of all cards.
 */

import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./GameReview.css";
import { fetchHands, fetchHand, fetchGameDetail, fetchGameChat } from "../../services/api";
import type {
  HandSummary,
  HandDetail,
  GameDetail,
  GamePlayerSummary,
  ChatMessageRecord,
} from "../../types/api";
import { CommunityCards } from "../../components/table/CommunityCards";
import { Avatar } from "../../components/avatars/Avatar";
import type { Card } from "../../types/game";

interface ShowdownPlayerResult {
  player_index: number;
  hand_rank: number;
  hand_name: string;
  hand_description: string;
  hole_cards?: Card[];
}

const fadeVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.25 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export function GameReview(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const gameId = id ? Number(id) : null;

  const [hands, setHands] = useState<HandSummary[]>([]);
  const [currentHandIndex, setCurrentHandIndex] = useState(0);
  const [handDetail, setHandDetail] = useState<HandDetail | null>(null);
  const [actionIndex, setActionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [gameDetail, setGameDetail] = useState<GameDetail | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessageRecord[]>([]);

  // Load game detail, hand list, and chat
  useEffect(() => {
    if (gameId === null) return;
    setLoading(true);

    const loadAll = async (): Promise<void> => {
      try {
        const [h, detail, chat] = await Promise.all([
          fetchHands(gameId),
          fetchGameDetail(gameId),
          fetchGameChat(gameId),
        ]);
        setHands(h);
        setGameDetail(detail);
        setChatMessages(chat);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    void loadAll();
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

  // Build player lookup
  const playerMap: Record<number, GamePlayerSummary> = useMemo(() => {
    if (!gameDetail) return {};
    const map: Record<number, GamePlayerSummary> = {};
    for (const p of gameDetail.players) {
      map[p.seat_index] = p;
    }
    return map;
  }, [gameDetail]);

  // Parse community cards from JSON
  const communityCards: Card[] = useMemo(() => {
    if (!handDetail) return [];
    try {
      const parsed: unknown = JSON.parse(handDetail.community_cards_json);
      if (Array.isArray(parsed)) return parsed as Card[];
    } catch {
      // ignore
    }
    return [];
  }, [handDetail]);

  // Parse showdown for hole cards and hand results
  const showdownResults: ShowdownPlayerResult[] = useMemo(() => {
    if (!handDetail?.showdown_json) return [];
    try {
      const showdown = JSON.parse(handDetail.showdown_json) as {
        hand_results?: ShowdownPlayerResult[];
      };
      return showdown.hand_results ?? [];
    } catch {
      return [];
    }
  }, [handDetail]);

  // Parse winners
  const winners: number[] = useMemo(() => {
    if (!handDetail?.showdown_json) return [];
    try {
      const showdown = JSON.parse(handDetail.showdown_json) as {
        winners?: number[];
      };
      return showdown.winners ?? [];
    } catch {
      return [];
    }
  }, [handDetail]);

  // Chat messages for current hand
  const currentHandChat = useMemo(() => {
    const currentHand = hands[currentHandIndex];
    if (!currentHand) return [];
    return chatMessages.filter(
      (m) => m.hand_number === currentHand.hand_number,
    );
  }, [chatMessages, hands, currentHandIndex]);

  const getPlayerName = (seatIndex: number): string => {
    return playerMap[seatIndex]?.name ?? `Seat ${seatIndex}`;
  };

  const getPlayerAvatar = (seatIndex: number): string => {
    return playerMap[seatIndex]?.avatar_url ?? "/avatars/default.png";
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
        <button
          className="game-review__back-btn"
          onClick={() => navigate(`/game/${id}/results`)}
        >
          Results
        </button>
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
        <div className="game-review__main">
          {/* Community cards */}
          <AnimatePresence mode="wait">
            <motion.div
              className="game-review__board"
              key={currentHand?.hand_number}
              variants={fadeVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
            >
              <CommunityCards cards={communityCards} />
            </motion.div>
          </AnimatePresence>

          {/* Hand info */}
          {currentHand && (
            <div className="game-review__hand-info">
              <span>
                Dealer:{" "}
                <strong>{getPlayerName(currentHand.dealer_position)}</strong>
              </span>
              <span>
                Blinds:{" "}
                <strong>
                  {currentHand.small_blind}/{currentHand.big_blind}
                </strong>
              </span>
            </div>
          )}

          {/* Showdown results / Hole cards (omniscient view) */}
          {showdownResults.length > 0 && (
            <div className="game-review__showdown">
              <h3 className="game-review__sub-title">Showdown</h3>
              <div className="game-review__showdown-list">
                {showdownResults.map((result) => (
                  <div
                    key={result.player_index}
                    className={`game-review__showdown-item ${
                      winners.includes(result.player_index)
                        ? "game-review__showdown-item--winner"
                        : ""
                    }`}
                  >
                    <Avatar
                      src={getPlayerAvatar(result.player_index)}
                      name={getPlayerName(result.player_index)}
                      size="small"
                    />
                    <div className="game-review__showdown-info">
                      <span className="game-review__showdown-name">
                        {getPlayerName(result.player_index)}
                        {winners.includes(result.player_index) && " 🏆"}
                      </span>
                      <span className="game-review__showdown-hand">
                        {result.hand_name}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
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
                    <Avatar
                      src={getPlayerAvatar(action.seat_index)}
                      name={getPlayerName(action.seat_index)}
                      size="small"
                    />
                    <span className="game-review__action-player">
                      {getPlayerName(action.seat_index)}
                    </span>
                    <span className={`game-review__action-type game-review__action-type--${action.action_type}`}>
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

        {/* Chat sidebar */}
        {currentHandChat.length > 0 && (
          <aside className="game-review__chat">
            <h3 className="game-review__sub-title">Table Talk</h3>
            <div className="game-review__chat-list">
              {currentHandChat.map((msg, i) => (
                <div key={i} className="game-review__chat-msg">
                  <Avatar
                    src={getPlayerAvatar(msg.seat_index)}
                    name={msg.name}
                    size="small"
                  />
                  <div className="game-review__chat-bubble">
                    <span className="game-review__chat-name">{msg.name}</span>
                    <span className="game-review__chat-text">{msg.message}</span>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
