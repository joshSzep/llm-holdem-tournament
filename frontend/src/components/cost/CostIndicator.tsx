/**
 * CostIndicator — shows running API cost for the current game session.
 */

import { useState, useEffect, useCallback } from "react";
import { fetchCosts } from "../../services/api";

export function CostIndicator(): React.ReactElement {
  const [totalCost, setTotalCost] = useState(0);

  const loadCost = useCallback(async () => {
    try {
      const data = await fetchCosts();
      setTotalCost(data.summary.total_cost);
    } catch {
      // silently fail — cost is non-critical
    }
  }, []);

  useEffect(() => {
    loadCost();
    const interval = setInterval(loadCost, 15000); // refresh every 15s
    return () => clearInterval(interval);
  }, [loadCost]);

  return (
    <div className="cost-indicator" title="Estimated API cost this game">
      <span className="cost-indicator__icon">$</span>
      <span className="cost-indicator__amount">
        {totalCost.toFixed(4)}
      </span>
    </div>
  );
}
