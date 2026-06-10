import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SuccessRateCurveResponse } from "../../lib/types";
import { formatPercent } from "../../lib/format";

interface Props {
  curve: SuccessRateCurveResponse;
  currentWithdrawalRate?: number;
}

export default function SuccessRateCurveChart({ curve, currentWithdrawalRate }: Props) {
  const data = curve.points.map((p) => ({
    withdrawal_rate: p.withdrawal_rate,
    success_rate: p.success_rate,
  }));

  return (
    <div className="chart-container">
      <h3 className="chart-title">Success rate vs. withdrawal rate</h3>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="withdrawal_rate"
            tickFormatter={(v) => formatPercent(v, 1)}
            type="number"
            domain={["dataMin", "dataMax"]}
            stroke="#6b7280"
          />
          <YAxis
            tickFormatter={(v) => formatPercent(v, 0)}
            domain={[0, 1]}
            stroke="#6b7280"
            width={56}
          />
          <Tooltip
            labelFormatter={(v) => `Withdrawal rate: ${formatPercent(Number(v), 2)}`}
            formatter={(value) => [formatPercent(Number(value), 1), "Success rate"]}
          />
          {currentWithdrawalRate !== undefined && (
            <ReferenceLine
              x={currentWithdrawalRate}
              stroke="#dc2626"
              strokeDasharray="4 4"
              label={{ value: "Current", position: "top", fill: "#dc2626", fontSize: 12 }}
            />
          )}
          <Line
            dataKey="success_rate"
            stroke="#1d4ed8"
            strokeWidth={2}
            dot={{ r: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="chart-meta">
        {curve.method === "historical" ? "Historical rolling windows" : "Monte Carlo"} · {curve.horizon_years}-year
        horizon · {Math.round(curve.stock_alloc * 100)}% stocks
      </p>
    </div>
  );
}
