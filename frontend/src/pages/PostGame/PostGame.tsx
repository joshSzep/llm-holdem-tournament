/**
 * PostGame page — shown after a game ends.
 * Displays final standings with avatars, rich game statistics,
 * and action buttons for rematch, review, and back-to-lobby.
 */

import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import "./PostGame.css";
import { useGameStore } from "../../stores/gameStore";
import { fetchGameDetail, fetchGameStats, createGame } from "../../services/api";
import type { GameDetail, GameStatsResponse } from "../../types/api";
import { Avatar } from "../../components/avatars/Avatar";

const cardVariants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.5, ease: "easeOut" as const },
  },
};

const rowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: 0.1 + i * 0.08, duration: 0.3, ease: "easeOut" as const },
  }),
};

const statVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: (i: number) => ({
    opacity: 1,
    scale: 1,
    transition: { delay: 0.3 + i * 0.1, duration: 0.4, ease: "easeOut" as const },
  }),
};

function getMedalEmoji(position: number): string {
  if (position === 1) return "🥇";
  if (position === 2) return "🥈";
  if (position === 3) return "🥉";
  return "";
}

export function PostGame(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const gameOver = useGameStore((s) => s.gameOver);
  const reset = useGameStore((s) => s.reset);

  const [gameDetail, setGameDetail] = useState<GameDetail | null>(null);
  const [gameStats, setGameStats] = useState<GameStatsResponse | null>(null);
  const [isRematchLoading, setIsRematchLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    const gameId = Number(id);
    fetchGameDetail(gameId)
      .then(setGameDetail)
      .catch(() => { /* ignore */ });
    fetchGameStats(gameId)
      .then(setGameStats)
      .catch(() => { /* ignore */ });
  }, [id]);

  const standings = gameOver?.final_standings ?? [];

  const handleBackToLobby = (): void => {
    reset();
    navigate("/");
  };

  const handleReview = (): void => {
    navigate(`/game/${id}/review`);
  };

  const handleRematch = useCallback(async () => {
    if (!gameDetail || isRematchLoading) return;
    setIsRematchLoading(true);
    try {
      const agentIds = gameDetail.players
        .filter((p) => !p.is_human && p.agent_id)
        .map((p) => p.agent_id as string);
      const startingChips = gameDetail.players[0]?.starting_chips ?? 1000;
      const response = await createGame({
        mode: gameDetail.mode as "player" | "spectator",
        agent_ids: agentIds,
        starting_chips: startingChips,
        num_players: gameDetail.players.length,
      });
      reset();
      navigate(`/game/${response.game_id}`);
    } catch {
      setIsRematchLoading(false);
    }
  }, [gameDetail, isRematchLoading, reset, navigate]);

  // Build avatar lookup from game detail
  const avatarMap: Record<number, string> = {};
  if (gameDetail) {
    for (const p of gameDetail.players) {
      avatarMap[p.seat_index] = p.avatar_url;
    }
  }

  // Build rich stats items
  const statItems: Array<{ value: string; label: string }> = [];
  if (gameStats) {
    statItems.push({
      value: String(gameStats.total_hands),
      label: "Hands Played",
    });
    if (gameStats.biggest_pot > 0) {
      statItems.push({
        value: gameStats.biggest_pot.toLocaleString(),
        label: `Biggest Pot (Hand #${gameStats.biggest_pot_hand})`,
      });
    }
    if (gameStats.best_hand_name) {
      statItems.push({
        value: gameStats.best_hand_name,
        label: `Best Hand — ${gameStats.best_hand_player}`,
      });
    }
    if (gameStats.most_aggressive_name) {
      statItems.push({
        value: `${gameStats.most_aggressive_raises} raises`,
        label: `Most Aggressive — ${gameStats.most_aggressive_name}`,
      });
    }
    if (gameStats.most_hands_won_name) {
      statItems.push({
        value: `${gameStats.most_hands_won_count} wins`,
        label: `Most Hands Won — ${gameStats.most_hands_won_name}`,
      });
    }
    if (gameDetail) {
      statItems.push({
        value: String(gameDetail.players.length),
        label: "Players",
      });
    }
  } else if (gameDetail) {
    statItems.push(
      { value: String(gameDetail.total_hands ?? 0), label: "Hands Played" },
      { value: String(gameDetail.players.length), label: "Players" },
    );
  }

  return (
    <div className="post-game">
      <motion.div
        className="post-game__card"
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <h1 className="post-game__title">Game Over</h1>

        {gameOver && (
          <motion.div
            className="post-game__winner"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5, type: "spring" as const, stiffness: 200 }}
          >
            <span className="post-game__winner-icon">🏆</span>
            <span className="post-game__winner-name">
              {gameOver.winner_name}
            </span>
            <span className="post-game__winner-label">wins!</span>
          </motion.div>
        )}

        {/* Final Standings */}
        {standings.length > 0 && (
          <div className="post-game__standings">
            <h2 className="post-game__section-title">Final Standings</h2>
            <table className="post-game__table">
              <thead>
                <tr>
                  <th>Place</th>
                  <th></th>
                  <th>Player</th>
                  <th>Chips</th>
                </tr>
              </thead>
              <tbody>
                {standings.map((s, i) => (
                  <motion.tr
                    key={s.seat_index}
                    className={
                      i === 0 ? "post-game__row--winner" : ""
                    }
                    custom={i}
                    variants={rowVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    <td>
                      {getMedalEmoji(i + 1)} #{i + 1}
                    </td>
                    <td className="post-game__avatar-cell">
                      <Avatar
                        src={avatarMap[s.seat_index] ?? "/avatars/default.png"}
                        name={s.name}
                        state="default"
                        size="small"
                      />
                    </td>
                    <td>{s.name}</td>
                    <td className="post-game__chips">
                      {s.final_chips.toLocaleString()}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Game Stats */}
        {statItems.length > 0 && (
          <div className="post-game__stats">
            <h2 className="post-game__section-title">Game Stats</h2>
            <div className="post-game__stats-grid">
              {statItems.map((item, i) => (
                <motion.div
                  className="post-game__stat"
                  key={item.label}
                  custom={i}
                  variants={statVariants}
                  initial="hidden"
                  animate="visible"
                >
                  <span className="post-game__stat-value">
                    {item.value}
                  </span>
                  <span className="post-game__stat-label">
                    {item.label}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="post-game__actions">
          <button
            className="post-game__btn post-game__btn--primary"
            onClick={handleBackToLobby}
          >
            Back to Lobby
          </button>
          <button
            className="post-game__btn post-game__btn--accent"
            onClick={() => void handleRematch()}
            disabled={!gameDetail || isRematchLoading}
          >
            {isRematchLoading ? "Starting…" : "Rematch"}
          </button>
          <button
            className="post-game__btn post-game__btn--secondary"
            onClick={handleReview}
          >
            Review Hands
          </button>
        </div>
      </motion.div>
    </div>
  );
}
