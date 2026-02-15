/**
 * RaiseSlider — slider + input for selecting raise amount.
 */

import { useState, useCallback, useEffect } from "react";

interface RaiseSliderProps {
  minRaise: number;
  maxRaise: number;
  currentAmount: number;
  onAmountChange: (amount: number) => void;
}

export function RaiseSlider({
  minRaise,
  maxRaise,
  currentAmount,
  onAmountChange,
}: RaiseSliderProps): React.ReactElement {
  const [inputValue, setInputValue] = useState(String(currentAmount));

  useEffect(() => {
    setInputValue(String(currentAmount));
  }, [currentAmount]);

  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = Number(e.target.value);
      onAmountChange(val);
    },
    [onAmountChange],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInputValue(e.target.value);
    },
    [],
  );

  const handleInputBlur = useCallback(() => {
    let val = Number(inputValue);
    if (isNaN(val) || val < minRaise) val = minRaise;
    if (val > maxRaise) val = maxRaise;
    onAmountChange(val);
    setInputValue(String(val));
  }, [inputValue, minRaise, maxRaise, onAmountChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        (e.target as HTMLInputElement).blur();
      }
    },
    [],
  );

  const percentage =
    maxRaise > minRaise
      ? ((currentAmount - minRaise) / (maxRaise - minRaise)) * 100
      : 0;

  return (
    <div className="raise-slider">
      <input
        type="range"
        className="raise-slider__range"
        min={minRaise}
        max={maxRaise}
        step={1}
        value={currentAmount}
        onChange={handleSliderChange}
        style={{
          background: `linear-gradient(to right, var(--color-accent) ${percentage}%, var(--color-bg-tertiary) ${percentage}%)`,
        }}
      />
      <input
        type="text"
        className="raise-slider__input"
        value={inputValue}
        onChange={handleInputChange}
        onBlur={handleInputBlur}
        onKeyDown={handleKeyDown}
        aria-label="Raise amount"
      />
    </div>
  );
}
