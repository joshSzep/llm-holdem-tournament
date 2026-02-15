/**
 * PresetButtons — quick bet sizing presets (Min, 2×, 3×, Pot, All-In).
 */

interface PresetButtonsProps {
  minRaise: number;
  maxRaise: number;
  potSize: number;
  bigBlind: number;
  onSelect: (amount: number) => void;
}

interface Preset {
  label: string;
  getAmount: (props: PresetButtonsProps) => number;
}

const PRESETS: Preset[] = [
  { label: "Min", getAmount: (p) => p.minRaise },
  { label: "2×", getAmount: (p) => Math.min(p.bigBlind * 2, p.maxRaise) },
  { label: "3×", getAmount: (p) => Math.min(p.bigBlind * 3, p.maxRaise) },
  { label: "Pot", getAmount: (p) => Math.min(p.potSize, p.maxRaise) },
  { label: "All-In", getAmount: (p) => p.maxRaise },
];

export function PresetButtons(props: PresetButtonsProps): React.ReactElement {
  const { minRaise, maxRaise, onSelect } = props;

  return (
    <div className="preset-buttons">
      {PRESETS.map((preset) => {
        const amount = preset.getAmount(props);
        const clamped = Math.max(minRaise, Math.min(amount, maxRaise));
        return (
          <button
            key={preset.label}
            className="preset-buttons__btn"
            onClick={() => onSelect(clamped)}
            disabled={minRaise > maxRaise}
          >
            {preset.label}
          </button>
        );
      })}
    </div>
  );
}
