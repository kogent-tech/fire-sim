import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CompareResponse } from "../../lib/types";
import { formatCompactNumber, formatMonthsAsYears, formatPercent } from "../../lib/format";

interface Props {
  compare: CompareResponse;
}

const METHOD_META: Record<string, { label: string; color: string }> = {
  historical: { label: "Historical", color: "#1d4ed8" },
  montecarlo: { label: "Monte Carlo", color: "#16a34a" },
  cape_adjusted: { label: "CAPE-adjusted", color: "#d97706" },
};

export default function MethodComparisonChart({ compare }: Props) {
  const methods = Object.keys(compare.results).filter((m) => m in METHOD_META);
  const reference = compare.results[methods[0]];
  if (!reference) return null;

  const months = reference.balance_percentiles.months;
  const data = months.map((month, i) => {
    const row: Record<string, number> = { month };
    for (const method of methods) {
      const series = compare.results[method].balance_percentiles.series["50"];
      if (series) row[method] = series[i];
    }
    return row;
  });

  return (
    <div className="chart-container">
      <h3 className="chart-title">Method comparison (median balance)</h3>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="month" tickFormatter={formatMonthsAsYears} stroke="#6b7280" />
          <YAxis tickFormatter={formatCompactNumber} stroke="#6b7280" width={64} />
          <Tooltip
            labelFormatter={(month) => `Year ${(Number(month) / 12).toFixed(1)}`}
            formatter={(value, name) => [formatCompactNumber(Number(value)), METHOD_META[String(name)]?.label ?? String(name)]}
          />
          <Legend formatter={(name) => METHOD_META[name as string]?.label ?? name} />
          {methods.map((method) => (
            <Line
              key={method}
              dataKey={method}
              stroke={METHOD_META[method].color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <div className="comparison-table">
        <table>
          <thead>
            <tr>
              <th>Method</th>
              <th>Success rate</th>
              <th>Median ending balance</th>
              <th>Withdrawal rate</th>
            </tr>
          </thead>
          <tbody>
            {methods.map((method) => {
              const r = compare.results[method];
              return (
                <tr key={method}>
                  <td>
                    <span className="legend-swatch" style={{ background: METHOD_META[method].color }} />
                    {METHOD_META[method].label}
                  </td>
                  <td>{formatPercent(r.success_rate, 1)}</td>
                  <td>{formatCompactNumber(r.ending_balance_percentiles["50"])}</td>
                  <td>{formatPercent(r.withdrawal_rate, 2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="chart-meta">
        CAPE: {compare.cape.current_cape.toFixed(1)} → suggested withdrawal rate{" "}
        {formatPercent(compare.cape.suggested_withdrawal_rate, 2)} (R² = {compare.cape.model.r_squared.toFixed(2)},
        n = {compare.cape.model.n})
      </p>
    </div>
  );
}
