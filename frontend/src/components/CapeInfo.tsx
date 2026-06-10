import type { CapeResponse } from "../lib/types";
import { formatPercent } from "../lib/format";

export default function CapeInfo({ cape }: { cape: CapeResponse }) {
  return (
    <div className="cape-info">
      <div className="stat-card">
        <span className="stat-label">Current CAPE ratio</span>
        <span className="stat-value stat-value-large">{cape.current_cape.toFixed(1)}</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Suggested withdrawal rate</span>
        <span className="stat-value stat-value-large">{formatPercent(cape.suggested_withdrawal_rate, 2)}</span>
        <span className="stat-sub">from regression of historical SWR on starting CAPE</span>
      </div>
      <div className="stat-card">
        <span className="stat-label">Regression fit</span>
        <span className="stat-value">R² = {cape.model.r_squared.toFixed(2)}</span>
        <span className="stat-sub">
          slope {cape.model.slope.toFixed(4)}, intercept {cape.model.intercept.toFixed(4)}, n={cape.model.n}
        </span>
      </div>
    </div>
  );
}
