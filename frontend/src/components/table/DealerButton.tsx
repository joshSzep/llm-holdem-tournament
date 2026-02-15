/**
 * DealerButton — small circular dealer button indicator.
 */

interface DealerButtonProps {
  visible: boolean;
}

export function DealerButton({
  visible,
}: DealerButtonProps): React.ReactElement | null {
  if (!visible) return null;
  return <div className="dealer-button">D</div>;
}
