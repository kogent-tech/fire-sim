"""CAPE-based dynamic withdrawal: relate starting CAPE to historically sustainable SWRs.

Big ERN's "Safe Withdrawal Rate Series" found that the historical SWR for a
given retirement cohort correlates with the CAPE ratio (cyclically-adjusted
P/E) at the start of that retirement: a more expensive starting valuation
(high CAPE / low CAPE yield) tends to predict a lower sustainable withdrawal
rate. This module reproduces that relationship using our own data and
exposes it as a "current CAPE -> suggested SWR" model.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fire_sim.engine.returns import PROCESSED_FILE, load_monthly_returns, portfolio_returns


def per_window_swr(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    horizon_years: int = 30,
) -> pd.DataFrame:
    """The exact historical SWR for every rolling window.

    For a fixed return sequence, the withdrawal rate that exactly depletes
    the portfolio by the end of the horizon (without ever going negative
    along the way) has a closed form: with growth factors
    ``P_t = prod_{i<=t}(1 + r_i)``, the maximum sustainable monthly
    withdrawal (per unit of starting balance) is
    ``1 / max_t(sum_{k<=t} 1/P_k)``.

    Returns a DataFrame with columns ``start_date`` and ``swr`` (annualized,
    same units as `withdrawal_rate` elsewhere - e.g. 0.04 for 4%).
    """
    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    horizon_months = horizon_years * 12
    returns = portfolio_returns(monthly_returns, stock_alloc)
    windows = np.lib.stride_tricks.sliding_window_view(returns, horizon_months)

    growth = 1.0 + windows
    cum_growth = np.cumprod(growth, axis=1)
    cum_inv_sum = np.cumsum(1.0 / cum_growth, axis=1)
    monthly_swr = 1.0 / cum_inv_sum.max(axis=1)
    swr = monthly_swr * 12.0

    n_windows = len(swr)
    start_dates = pd.DatetimeIndex(monthly_returns["date"].iloc[:n_windows])
    return pd.DataFrame({"start_date": start_dates, "swr": swr})


def _linregress(x: np.ndarray, y: np.ndarray):
    slope, intercept = np.polyfit(x, y, 1)
    r_squared = float(np.corrcoef(x, y)[0, 1] ** 2)
    return float(slope), float(intercept), r_squared


@dataclass
class CapeSWRModel:
    """SWR as a linear function of CAPE yield (1 / CAPE): swr = intercept + slope * (1 / cape)."""

    slope: float
    intercept: float
    r_squared: float
    n: int
    stock_alloc: float
    horizon_years: int

    def predict(self, current_cape: float) -> float:
        """Suggested SWR for a portfolio starting at `current_cape`."""
        cape_yield = 1.0 / current_cape
        return self.intercept + self.slope * cape_yield


def fit_cape_swr_model(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    horizon_years: int = 30,
) -> CapeSWRModel:
    """Fit `swr = intercept + slope * (1 / cape)` across all historical rolling windows."""
    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    swr_df = per_window_swr(monthly_returns, stock_alloc=stock_alloc, horizon_years=horizon_years)

    shiller = pd.read_parquet(PROCESSED_FILE)[["date", "cape"]]
    merged = swr_df.merge(shiller, left_on="start_date", right_on="date", how="left")
    merged = merged.dropna(subset=["cape"])

    cape_yield = 1.0 / merged["cape"].to_numpy()
    swr = merged["swr"].to_numpy()
    slope, intercept, r_squared = _linregress(cape_yield, swr)

    return CapeSWRModel(
        slope=slope,
        intercept=intercept,
        r_squared=r_squared,
        n=len(merged),
        stock_alloc=stock_alloc,
        horizon_years=horizon_years,
    )
