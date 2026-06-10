import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { SequenceRiskResponse } from "../../lib/types";
import { formatCompactNumber, formatMonthsAsYears, formatPercent } from "../../lib/format";
import InfoLink from "../InfoLink";

interface Props {
  result: SequenceRiskResponse;
  onOpenInfo: (topic: string) => void;
}

const MAX_SAMPLED_PATHS = 40;

/** Red (poor early returns) -> green (strong early returns). */
function colorForRank(t: number): string {
  const hue = Math.round(t * 120);
  return `hsl(${hue}, 70%, 45%)`;
}

export default function SequenceRiskChart({ result, onOpenInfo }: Props) {
  const { paths, months, sensitivity } = result;

  const scatterSuccess = paths
    .filter((p) => p.success)
    .map((p) => ({ early_return: p.early_return, ending_balance: p.ending_balance }));
  const scatterFailure = paths
    .filter((p) => !p.success)
    .map((p) => ({ early_return: p.early_return, ending_balance: p.ending_balance }));

  // Rank paths by early_return to assign a red->green color scale.
  const rankByIndex = new Map<number, number>();
  const sortedIdx = paths.map((_, i) => i).sort((a, b) => paths[a].early_return - paths[b].early_return);
  sortedIdx.forEach((origIdx, rank) => {
    rankByIndex.set(origIdx, paths.length > 1 ? rank / (paths.length - 1) : 0.5);
  });

  // Sample evenly spaced paths (by chronological start order) for the path chart.
  const step = Math.max(1, Math.floor(paths.length / MAX_SAMPLED_PATHS));
  const sampledIndices: number[] = [];
  for (let i = 0; i < paths.length; i += step) sampledIndices.push(i);

  const pathData = months.map((month, mi) => {
    const row: Record<string, number> = { month };
    for (const idx of sampledIndices) {
      row[`path_${idx}`] = paths[idx].balances[mi];
    }
    return row;
  });

  return (
    <div className="chart-container">
      <h3 className="chart-title">
        Sequence-of-returns risk
        <InfoLink topic="sequence-risk" label="sequence-of-returns risk" onOpen={onOpenInfo} />
      </h3>

      <div className="sequence-charts">
        <div>
          <h4 className="chart-subtitle">Balance paths, colored by early-period return</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={pathData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" tickFormatter={formatMonthsAsYears} stroke="#6b7280" />
              <YAxis tickFormatter={formatCompactNumber} stroke="#6b7280" width={64} />
              <Tooltip
                labelFormatter={(month) => `Year ${(Number(month) / 12).toFixed(1)}`}
                formatter={(value) => [formatCompactNumber(Number(value)), "Balance"]}
              />
              {sampledIndices.map((idx) => (
                <Line
                  key={idx}
                  dataKey={`path_${idx}`}
                  stroke={colorForRank(rankByIndex.get(idx) ?? 0.5)}
                  strokeWidth={1}
                  dot={false}
                  isAnimationActive={false}
                  legendType="none"
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <p className="chart-meta">
            <span style={{ color: colorForRank(0) }}>■</span> weak early returns &nbsp;
            <span style={{ color: colorForRank(1) }}>■</span> strong early returns &nbsp;
            ({sampledIndices.length} of {paths.length} retirement-start windows shown)
          </p>
        </div>

        <div>
          <h4 className="chart-subtitle">Early-period return vs. ending balance</h4>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="early_return"
                name="Early-period annualized return"
                tickFormatter={(v) => formatPercent(v, 0)}
                type="number"
                stroke="#6b7280"
              />
              <YAxis
                dataKey="ending_balance"
                name="Ending balance"
                tickFormatter={formatCompactNumber}
                type="number"
                stroke="#6b7280"
                width={64}
              />
              <ZAxis range={[20, 20]} />
              <Tooltip
                formatter={(value, name) => {
                  const num = Number(value);
                  const isEarly = String(name) === "early_return";
                  return [isEarly ? formatPercent(num, 1) : formatCompactNumber(num), isEarly ? "Early-period return" : "Ending balance"];
                }}
                cursor={{ strokeDasharray: "3 3" }}
              />
              <Legend />
              <Scatter name="Success" data={scatterSuccess} fill="#16a34a" />
              <Scatter name="Failure (depleted)" data={scatterFailure} fill="#dc2626" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="sensitivity-summary">
        <div>
          <span className="stat-label">Corr(early return, ending balance)</span>
          <span className="stat-value">{sensitivity.early_return_corr_with_ending_balance.toFixed(2)}</span>
        </div>
        <div>
          <span className="stat-label">Corr(late return, ending balance)</span>
          <span className="stat-value">{sensitivity.late_return_corr_with_ending_balance.toFixed(2)}</span>
        </div>
        <div>
          <span className="stat-label">Mean early return | success</span>
          <span className="stat-value">{formatPercent(sensitivity.early_return_mean_success, 1)}</span>
        </div>
        <div>
          <span className="stat-label">Mean early return | failure</span>
          <span className="stat-value">
            {sensitivity.early_return_mean_failure === null ? "n/a" : formatPercent(sensitivity.early_return_mean_failure, 1)}
          </span>
        </div>
      </div>
      <p className="chart-meta">
        {result.period_years}-year early/late windows · success rate {formatPercent(result.success_rate, 1)} across{" "}
        {paths.length} retirement-start dates
      </p>
    </div>
  );
}
