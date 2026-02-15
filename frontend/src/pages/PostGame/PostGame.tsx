/**
 * PostGame page — shown after a game ends.
 * Displays final standings, stats, and action buttons.
 */

import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import "./PostGame.css";
import { useGameStore } from "../../stores/gameStore";
import { fetchGameDetail } from "../../services/api";
import type { GameDetail } from "../../types/api";

export function PostGame(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const gameOver = useGameStore((s) => s.gameOver);
  const reset = useGameStore((s) => s.reset);

  const [gameDetail, setGameDetail] = useState<GameDetail | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchGameDetail(Number(id))
      .then(setGameDetail)
      .catch(() => {
        /* ignore */
      });
  }, [id]);

  const standings = gameOver?.final_standings ?? [];

  const handleBackToLobby = (): void => {
    reset();
    navigate("/");
  };

  const handleReview = (): void => {
    navigate(`/game/${id}/review`);
  };

  return (
    <div className="post-game">
      <div className="post-game__card">
        <h1 className="post-game__title">Game Over</h1>

        {gameOver && (
          <div className="post-game__winner">
            <span className="post-game__winner-icon">🏆</span>
            <span className="post-game__winner-name">
              {gameOver.winner_name}
            </span>
            <span className="post-game__winner-label">wins!</span>
          </div>
        )}

        {/* Final Standings */}
        {standings.length > 0 && (
          <div className="post-game__standings">
            <h2 className="post-game__section-title">Final Standings</h2>
            <table className="post-game__table">
              <thead>
                <tr>
                  <th>Place</th>
                  <th>Player</th>
                  <th>Chips</th>
                  <th>Position</th>
                </tr>
              </thead>
              <tbody>
                {standings.map((s, i) => (
                  <tr
                    key={s.seat_index}
                    className={
                      i === 0 ? "post-game__row--winner" : ""
                    }
                  >
                    <td>#{i + 1}</td>
                    <td>{s.name}</td>
                    <td className="post-game__chips">
                      {s.final_chips.toLocaleString()}
                    </td>
                    <td>
                      {s.finish_position === 1
                        ? "Winner"
                        : `#${s.finish_position}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Game Stats */}
        {gameDetail && (
          <div className="post-game__stats">
            <h2 className="post-game__section-title">Game Stats</h2>
            <div className="post-game__stats-grid">
              <div className="post-game__stat">
                <span className="post-game__stat-value">
                  {gameDetail.total_hands}
                </span>
                <span className="post-game__stat-label">
                  Hands Played
                </span>
              </div>
              <div className="post-game__stat">
                <span className="post-game__stat-value">
                  {gameDetail.players.length}
                </span>
                <span className="post-game__stat-label">Players</span>
              </div>
              <div className="post-game__stat">
                <span className="post-game__stat-value">
                  {gameDetail.status}
                </span>
                <span className="post-game__stat-label">Status</span>
              </div>
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
            className="post-game__btn post-game__btn--secondary"
            onClick={handleReview}
          >
            Review Hands
          </button>
        </div>
      </div>
    </div>
  );
}
