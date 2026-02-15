/**
 * GameTable page — the main game view.
 * Wires together PokerTable, ActionButtons, ChatPanel,
 * TurnTimer, CostIndicator, and the WebSocket connection.
 */

import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import "./GameTable.css";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useGameActions } from "../../hooks/useGameActions";
import {
  useGameStore,
  selectHumanPlayer,
  selectIsHumanTurn,
} from "../../stores/gameStore";
import { PokerTable } from "../../components/table/PokerTable";
import { ActionButtons } from "../../components/controls/ActionButtons";
import { ChatPanel } from "../../components/chat/ChatPanel";
import { TurnTimer } from "../../components/timer/TurnTimer";
import { CostIndicator } from "../../components/cost/CostIndicator";
import { LoadingSpinner } from "../../components/transitions/LoadingSpinner";

export function GameTable(): React.ReactElement {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const gameId = id ? Number(id) : null;

  const { send } = useWebSocket(gameId);
  const { fold, check, call, raise, sendChat } = useGameActions(send);

  const gameState = useGameStore((s) => s.gameState);
  const isConnected = useGameStore((s) => s.isConnected);
  const gameOver = useGameStore((s) => s.gameOver);
  const timer = useGameStore((s) => s.timer);
  const isPaused = useGameStore((s) => s.isPaused);
  const pauseReason = useGameStore((s) => s.pauseReason);
  const error = useGameStore((s) => s.error);

  const humanPlayer = gameState ? selectHumanPlayer(gameState) : null;
  const isHumanTurn = gameState ? selectIsHumanTurn(gameState) : false;
  const isPlayerMode = gameState?.mode === "player";

  // Determine action availability
  const canCheck =
    isHumanTurn &&
    humanPlayer !== null &&
    gameState !== null &&
    humanPlayer.current_bet >= gameState.current_bet;
  const canCall =
    isHumanTurn &&
    humanPlayer !== null &&
    gameState !== null &&
    humanPlayer.current_bet < gameState.current_bet;
  const callAmount =
    canCall && humanPlayer && gameState
      ? gameState.current_bet - humanPlayer.current_bet
      : 0;
  const canRaise = isHumanTurn && humanPlayer !== null && !humanPlayer.is_all_in;
  const minRaise = gameState ? gameState.big_blind : 0;
  const maxRaise = humanPlayer ? humanPlayer.chips : 0;
  const potSize = gameState
    ? gameState.pots.reduce((sum, p) => sum + p.amount, 0)
    : 0;

  // Navigate to results when game ends
  if (gameOver && gameId) {
    // Slight delay to let the user see the final state
    setTimeout(() => {
      navigate(`/game/${gameId}/results`);
    }, 3000);
  }

  // Loading state
  if (!gameState) {
    return (
      <div className="game-table game-table--loading">
        <LoadingSpinner
          message={!isConnected ? "Connecting…" : "Waiting for game state…"}
          size="large"
        />
      </div>
    );
  }

  return (
    <div className="game-table">
      {/* Reconnection overlay */}
      <AnimatePresence>
        {!isConnected && gameState && (
          <motion.div
            className="game-table__reconnect-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <LoadingSpinner message="Reconnecting…" size="medium" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header bar */}
      <header className="game-table__header">
        <div className="game-table__info">
          <span className="game-table__hand">
            Hand #{gameState.hand_number}
          </span>
          <span className="game-table__blinds">
            Blinds: {gameState.small_blind}/{gameState.big_blind}
          </span>
          <span className="game-table__phase">
            {gameState.phase.replace("_", " ")}
          </span>
        </div>
        <div className="game-table__header-right">
          <TurnTimer />
          <CostIndicator />
        </div>
      </header>

      {/* Error / Pause overlays */}
      {error && (
        <div className="game-table__overlay game-table__overlay--error">
          {error}
        </div>
      )}
      {isPaused && (
        <div className="game-table__overlay game-table__overlay--paused">
          Game Paused{pauseReason ? `: ${pauseReason}` : ""}
        </div>
      )}

      {/* Main content: table + sidebar */}
      <div className="game-table__content">
        <div className="game-table__table-area">
          <PokerTable
            players={gameState.players}
            communityCards={gameState.community_cards}
            pots={gameState.pots}
            currentPlayerIndex={gameState.current_player_index}
            humanSeatIndex={humanPlayer?.seat_index ?? null}
            timerSeatIndex={timer?.seat_index ?? null}
            timerSeconds={timer?.seconds_remaining ?? null}
            showdownResult={gameState.showdown_result}
            recentActions={gameState.current_hand_actions}
            phase={gameState.phase}
          />

          {/* Action buttons — only in player mode, on human's turn */}
          {isPlayerMode && isHumanTurn && (
            <div className="game-table__actions">
              <ActionButtons
                canCheck={canCheck}
                canCall={canCall}
                canRaise={canRaise}
                callAmount={callAmount}
                minRaise={minRaise}
                maxRaise={maxRaise}
                potSize={potSize}
                bigBlind={gameState.big_blind}
                onFold={fold}
                onCheck={check}
                onCall={call}
                onRaise={raise}
              />
            </div>
          )}
        </div>

        {/* Chat sidebar */}
        <aside className="game-table__sidebar">
          <ChatPanel showInput={isPlayerMode} onSendChat={sendChat} />
        </aside>
      </div>
    </div>
  );
}
