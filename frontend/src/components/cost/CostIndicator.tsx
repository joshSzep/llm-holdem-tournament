/**
 * CostIndicator — shows running API cost for the current game session.
 */

import { useState, useEffect } from "react";
import { fetchCosts } from "../../services/api";

export function CostIndicator(): React.ReactElement {
  const [totalCost, setTotalCost] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = async (): Promise<void> => {
      try {
        const data = await fetchCosts();
        if (!cancelled) setTotalCost(data.summary.total_cost);
      } catch {
        // silently fail — cost is non-critical
      }
    };
    void load();
    const interval = setInterval(() => void load(), 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="cost-indicator" title="Estimated API cost this game">
      <span className="cost-indicator__icon">$</span>
      <span className="cost-indicator__amount">
        {totalCost.toFixed(4)}
      </span>
    </div>
  );
}
