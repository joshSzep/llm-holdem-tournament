/**
 * ActionButtons — the main player action controls.
 * Shows Fold, Check/Call, and Raise with slider and presets.
 * Only visible when it's the human player's turn.
 */

import { useState, useCallback } from "react";
import "./ActionButtons.css";
import { RaiseSlider } from "./RaiseSlider";
import { PresetButtons } from "./PresetButtons";

interface ActionButtonsProps {
  canCheck: boolean;
  canCall: boolean;
  canRaise: boolean;
  callAmount: number;
  minRaise: number;
  maxRaise: number;
  potSize: number;
  bigBlind: number;
  onFold: () => void;
  onCheck: () => void;
  onCall: () => void;
  onRaise: (amount: number) => void;
}

export function ActionButtons({
  canCheck,
  canCall,
  canRaise,
  callAmount,
  minRaise,
  maxRaise,
  potSize,
  bigBlind,
  onFold,
  onCheck,
  onCall,
  onRaise,
}: ActionButtonsProps): React.ReactElement {
  const [raiseAmount, setRaiseAmount] = useState(minRaise);

  const handleRaise = useCallback(() => {
    onRaise(raiseAmount);
  }, [raiseAmount, onRaise]);

  const handlePresetSelect = useCallback((amount: number) => {
    setRaiseAmount(amount);
  }, []);

  return (
    <div className="action-buttons">
      <div className="action-buttons__main">
        <button
          className="action-buttons__btn action-buttons__btn--fold"
          onClick={onFold}
        >
          Fold
        </button>

        {canCheck && (
          <button
            className="action-buttons__btn action-buttons__btn--check"
            onClick={onCheck}
          >
            Check
          </button>
        )}

        {canCall && (
          <button
            className="action-buttons__btn action-buttons__btn--call"
            onClick={onCall}
          >
            Call {callAmount.toLocaleString()}
          </button>
        )}

        {canRaise && (
          <button
            className="action-buttons__btn action-buttons__btn--raise"
            onClick={handleRaise}
          >
            Raise {raiseAmount.toLocaleString()}
          </button>
        )}
      </div>

      {canRaise && (
        <div className="action-buttons__raise-controls">
          <PresetButtons
            minRaise={minRaise}
            maxRaise={maxRaise}
            potSize={potSize}
            bigBlind={bigBlind}
            onSelect={handlePresetSelect}
          />
          <RaiseSlider
            minRaise={minRaise}
            maxRaise={maxRaise}
            currentAmount={raiseAmount}
            onAmountChange={setRaiseAmount}
          />
        </div>
      )}
    </div>
  );
}
