/**
 * GameModeSelector — Toggle between "Play" and "Spectate" modes.
 */

import "./Lobby.css";

interface GameModeSelectorProps {
  mode: "player" | "spectator";
  onModeChange: (mode: "player" | "spectator") => void;
}

export function GameModeSelector({
  mode,
  onModeChange,
}: GameModeSelectorProps): React.ReactElement {
  return (
    <div className="game-mode-selector">
      <button
        className={`game-mode-selector__button ${mode === "player" ? "game-mode-selector__button--active" : ""}`}
        onClick={() => onModeChange("player")}
      >
        Play
      </button>
      <button
        className={`game-mode-selector__button ${mode === "spectator" ? "game-mode-selector__button--active" : ""}`}
        onClick={() => onModeChange("spectator")}
      >
        Spectate
      </button>
    </div>
  );
}
