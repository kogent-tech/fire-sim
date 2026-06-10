import type { SimulationResponse } from "../lib/types";
import { formatCompactNumber, formatPercent } from "../lib/format";

interface Props {
  result: SimulationResponse;
}

const STRATEGY_LABELS: Record<string, string> = {
  fixed: "Fixed (inflation-adjusted)",
  guyton_klinger: "Guyton-Klinger guardrails",
  constant_percentage: "Constant % of portfolio",
};

export default function SummaryStats({ result }: Props) {
  const ending = result.ending_balance_percentiles;

  return (
    <div className="summary-stats">
      <div className="stat-card">
        <span className="stat-label">Success rate</span>
        <span className="stat-value stat-value-large">{formatPercent(result.success_rate, 1)}</span>
        <span className="stat-sub">
          {result.n_paths.toLocaleString()} {result.method === "historical" ? "historical windows" : "simulated paths"}
        </span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Withdrawal strategy</span>
        <span className="stat-value">{STRATEGY_LABELS[result.withdrawal_strategy] ?? result.withdrawal_strategy}</span>
        <span className="stat-sub">
          {formatPercent(result.withdrawal_rate, 2)} initial · {result.horizon_years}-year horizon ·{" "}
          {Math.round(result.stock_alloc * 100)}% stocks
        </span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Median ending balance</span>
        <span className="stat-value stat-value-large">{formatCompactNumber(ending["50"] ?? NaN)}</span>
        <span className="stat-sub">
          starting from {formatCompactNumber(result.starting_balance)}
        </span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Ending balance range</span>
        <span className="stat-value">
          {formatCompactNumber(ending[Object.keys(ending).sort((a, b) => Number(a) - Number(b))[0]])} –{" "}
          {formatCompactNumber(ending[Object.keys(ending).sort((a, b) => Number(b) - Number(a))[0]])}
        </span>
        <span className="stat-sub">p{Object.keys(ending).sort((a, b) => Number(a) - Number(b)).join(" / p")}</span>
      </div>
    </div>
  );
}
