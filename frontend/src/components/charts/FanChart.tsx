import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { PercentileBands } from "../../lib/types";
import { formatCompactNumber, formatMonthsAsYears } from "../../lib/format";
import InfoLink from "../InfoLink";

interface Props {
  bands: PercentileBands;
  title?: string;
  onOpenInfo?: (topic: string) => void;
}

const BAND_FILL = "#60a5fa";

/**
 * Renders percentile bands as a "fan chart": each gap between adjacent
 * percentiles becomes a stacked, semi-transparent area, with the median
 * (p50, if present) drawn as a solid line on top.
 */
export default function FanChart({ bands, title, onOpenInfo }: Props) {
  const percentileKeys = Object.keys(bands.series)
    .map(Number)
    .sort((a, b) => a - b);

  const data = bands.months.map((month, i) => {
    const row: Record<string, number> = { month };
    for (const p of percentileKeys) {
      row[String(p)] = bands.series[String(p)][i];
    }
    return row;
  });

  // Build stacked deltas between adjacent percentiles so Recharts can render
  // them as a fan. The lowest percentile is an invisible base.
  const stackedData = data.map((row) => {
    const out: Record<string, number> = { month: row.month };
    for (let i = 0; i < percentileKeys.length; i++) {
      const p = percentileKeys[i];
      if (i === 0) {
        out[`base`] = row[String(p)];
      } else {
        const prev = percentileKeys[i - 1];
        out[`band_${prev}_${p}`] = row[String(p)] - row[String(prev)];
      }
    }
    if (percentileKeys.includes(50)) out["p50"] = row["50"];
    return out;
  });

  const bandKeys: { key: string; opacity: number }[] = [];
  for (let i = 1; i < percentileKeys.length; i++) {
    const lo = percentileKeys[i - 1];
    const hi = percentileKeys[i];
    // Outer bands (e.g. 5-25, 75-95) lighter than inner bands (e.g. 25-75).
    const isOuter = i === 1 || i === percentileKeys.length - 1;
    bandKeys.push({ key: `band_${lo}_${hi}`, opacity: isOuter ? 0.15 : 0.35 });
  }

  return (
    <div className="chart-container">
      {title && (
        <h3 className="chart-title">
          {title}
          {onOpenInfo && <InfoLink topic="percentile-bands" label="percentile bands" onOpen={onOpenInfo} />}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={360}>
        <ComposedChart data={stackedData} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="month" tickFormatter={formatMonthsAsYears} stroke="#6b7280" />
          <YAxis tickFormatter={formatCompactNumber} stroke="#6b7280" width={64} />
          <Tooltip
            labelFormatter={(month) => `Year ${(Number(month) / 12).toFixed(1)}`}
            formatter={(value, name) => {
              const formatted = formatCompactNumber(Number(value));
              const key = String(name);
              if (key === "p50") return [formatted, "Median"];
              if (key === "base") return [formatted, `p${percentileKeys[0]}`];
              const m = key.match(/^band_(\d+)_(\d+)$/);
              if (m) return [formatted, `+ to p${m[2]}`];
              return [formatted, key];
            }}
          />
          <Area dataKey="base" stackId="fan" stroke="none" fill="transparent" isAnimationActive={false} />
          {bandKeys.map(({ key, opacity }) => (
            <Area
              key={key}
              dataKey={key}
              stackId="fan"
              stroke="none"
              fill={BAND_FILL}
              fillOpacity={opacity}
              isAnimationActive={false}
            />
          ))}
          {percentileKeys.includes(50) && (
            <Line dataKey="p50" stroke="#1d4ed8" strokeWidth={2} dot={false} isAnimationActive={false} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
      <p className="chart-meta">
        <span className="legend-swatch" style={{ background: BAND_FILL, opacity: 0.35 }} />
        p{percentileKeys[0]}–p{percentileKeys[percentileKeys.length - 1]} range
        {percentileKeys.includes(50) && (
          <>
            {" "}
            &nbsp; <span className="legend-swatch" style={{ background: "#1d4ed8" }} /> Median (p50)
          </>
        )}
      </p>
    </div>
  );
}
