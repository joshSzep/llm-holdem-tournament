/**
 * Lobby page — main landing page with game setup, in-progress games, and history.
 */

import { useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useLobbyStore, selectInProgressGames, selectCompletedGames } from "../../stores/lobbyStore";
import { createGame } from "../../services/api";
import { GameModeSelector } from "../../components/lobby/GameModeSelector";
import { SeatConfigurator } from "../../components/lobby/SeatConfigurator";
import "./Lobby.css";

export function Lobby(): React.ReactElement {
  const navigate = useNavigate();
  const {
    agents,
    games,
    selectedMode,
    seats,
    startingChips,
    isLoadingAgents,
    setSelectedMode,
    setSeatAgent,
    setSeatCount,
    setStartingChips,
    loadAgents,
    loadGames,
  } = useLobbyStore();

  const inProgressGames = selectInProgressGames(games);
  const completedGames = selectCompletedGames(games);

  useEffect(() => {
    void loadAgents();
    void loadGames();
  }, [loadAgents, loadGames]);

  // Seat 0 is reserved for the human in "player" mode
  const aiSeatStart = selectedMode === "player" ? 1 : 0;
  const totalSeats = seats.length + (selectedMode === "player" ? 1 : 0);

  const handleStartGame = useCallback(async () => {
    // Collect agent IDs from seat config
    const agentIds: string[] = [];
    for (const seat of seats) {
      if (seat.agentId === "random") {
        // Pick a random available agent
        if (agents.length > 0) {
          const randomAgent = agents[Math.floor(Math.random() * agents.length)];
          if (randomAgent) agentIds.push(randomAgent.id);
        }
      } else if (seat.agentId) {
        agentIds.push(seat.agentId);
      }
    }

    if (agentIds.length === 0) return;

    try {
      const response = await createGame({
        mode: selectedMode,
        agent_ids: agentIds,
        starting_chips: startingChips,
        num_players: totalSeats,
      });
      navigate(`/game/${response.game_id}`);
    } catch {
      // Error handling — could set an error state
    }
  }, [seats, agents, selectedMode, startingChips, totalSeats, navigate]);

  return (
    <div className="lobby">
      <header className="lobby__header">
        <h1 className="lobby__title">LLM Hold&apos;Em Tournament</h1>
        <p className="lobby__subtitle">
          Texas Hold&apos;Em with AI Opponents
        </p>
      </header>

      <div className="lobby__content">
        {/* ─── New Game Section ─── */}
        <section className="lobby__section">
          <h2 className="lobby__section-title">New Game</h2>

          <GameModeSelector
            mode={selectedMode}
            onModeChange={setSelectedMode}
          />

          <div className="lobby__config">
            <div className="lobby__config-row">
              <label className="lobby__label" htmlFor="seat-count">
                Players
              </label>
              <select
                id="seat-count"
                className="lobby__select"
                value={seats.length + (selectedMode === "player" ? 1 : 0)}
                onChange={(e) => {
                  const total = Number(e.target.value);
                  const aiSeats =
                    selectedMode === "player" ? total - 1 : total;
                  setSeatCount(aiSeats);
                }}
              >
                {[2, 3, 4, 5, 6].map((n) => (
                  <option key={n} value={n}>
                    {n} players
                  </option>
                ))}
              </select>
            </div>

            <div className="lobby__config-row">
              <label className="lobby__label" htmlFor="starting-chips">
                Starting Chips
              </label>
              <select
                id="starting-chips"
                className="lobby__select"
                value={startingChips}
                onChange={(e) => setStartingChips(Number(e.target.value))}
              >
                {[500, 1000, 2000, 5000].map((n) => (
                  <option key={n} value={n}>
                    {n.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedMode === "player" && (
            <div className="lobby__your-seat">
              <span className="lobby__your-seat-label">Seat 1</span>
              <span className="lobby__your-seat-name">You</span>
            </div>
          )}

          <div className="lobby__seats">
            {seats.map((seat, index) => (
              <SeatConfigurator
                key={index}
                seatIndex={aiSeatStart + index}
                selectedAgentId={seat.agentId}
                agents={agents}
                disabled={isLoadingAgents}
                onSelect={(agentId) => setSeatAgent(index, agentId)}
              />
            ))}
          </div>

          <button
            className="lobby__start-button"
            onClick={() => void handleStartGame()}
            disabled={agents.length === 0}
          >
            Start Game
          </button>
        </section>

        {/* ─── In-Progress Games ─── */}
        {inProgressGames.length > 0 && (
          <section className="lobby__section">
            <h2 className="lobby__section-title">In Progress</h2>
            <div className="lobby__game-list">
              {inProgressGames.map((game) => (
                <div key={game.id} className="lobby__game-card">
                  <div className="lobby__game-info">
                    <span className="lobby__game-mode">{game.mode}</span>
                    <span className="lobby__game-players">
                      {game.player_count} players
                    </span>
                    <span className="lobby__game-hands">
                      {game.total_hands ?? 0} hands
                    </span>
                  </div>
                  <button
                    className="lobby__resume-button"
                    onClick={() => navigate(`/game/${game.id}`)}
                  >
                    Resume
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ─── Game History ─── */}
        {completedGames.length > 0 && (
          <section className="lobby__section">
            <h2 className="lobby__section-title">History</h2>
            <div className="lobby__game-list">
              {completedGames.map((game) => (
                <div key={game.id} className="lobby__game-card">
                  <div className="lobby__game-info">
                    <span className="lobby__game-mode">{game.mode}</span>
                    <span className="lobby__game-players">
                      {game.player_count} players
                    </span>
                    <span className="lobby__game-hands">
                      {game.total_hands ?? 0} hands
                    </span>
                  </div>
                  <button
                    className="lobby__review-button"
                    onClick={() => navigate(`/game/${game.id}/review`)}
                  >
                    Review
                  </button>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
