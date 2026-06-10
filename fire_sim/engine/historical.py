"""Rolling-window historical SWR simulator (Trinity Study / cFIREsim style).

Withdrawals are a fixed amount in *real* (inflation-adjusted) dollars, set
once from `starting_balance * withdrawal_rate / 12` and held constant for
the whole horizon. This is the standard "4% rule" definition: because the
underlying return series (`fire_sim.engine.returns`) are already real
returns, holding the withdrawal amount constant in nominal terms here is
equivalent to indexing it to inflation in nominal terms.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fire_sim.engine.returns import load_monthly_returns, portfolio_returns


@dataclass
class HistoricalResult:
    start_dates: pd.DatetimeIndex
    balances: np.ndarray  # shape (n_windows, horizon_months + 1), real dollars
    depleted: np.ndarray  # shape (n_windows,) bool
    success_rate: float
    stock_alloc: float
    withdrawal_rate: float
    horizon_years: int
    starting_balance: float

    @property
    def n_windows(self) -> int:
        return self.balances.shape[0]

    @property
    def ending_balances(self) -> np.ndarray:
        return self.balances[:, -1]

    def percentile(self, q) -> np.ndarray:
        """Percentile (0-100, scalar or sequence) of balance at each month, across windows."""
        return np.percentile(self.balances, q, axis=0)


def run_historical_simulation(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    withdrawal_rate: float = 0.04,
    horizon_years: int = 30,
    starting_balance: float = 1.0,
) -> HistoricalResult:
    """Run a rolling-window historical simulation.

    For every month in the dataset that has at least `horizon_years * 12`
    months of return data following it, simulate a portfolio starting at
    `starting_balance`, rebalanced to `stock_alloc`/`(1 - stock_alloc)`
    every month, withdrawing a fixed real amount
    (`starting_balance * withdrawal_rate / 12`) per month.

    A window "fails" if the balance is depleted (hits zero) at any point
    before the end of the horizon.
    """
    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    horizon_months = horizon_years * 12
    returns = portfolio_returns(monthly_returns, stock_alloc)
    n_returns = len(returns)
    n_windows = n_returns - horizon_months + 1
    if n_windows < 1:
        raise ValueError(
            f"Not enough data for a {horizon_years}-year horizon "
            f"({n_returns} months of returns available, need {horizon_months})"
        )

    monthly_withdrawal = starting_balance * withdrawal_rate / 12.0

    balances = np.empty((n_windows, horizon_months + 1))
    balances[:, 0] = starting_balance
    current = np.full(n_windows, starting_balance)
    for m in range(1, horizon_months + 1):
        r = returns[m - 1 : m - 1 + n_windows]
        current = np.maximum(current * (1.0 + r) - monthly_withdrawal, 0.0)
        balances[:, m] = current

    depleted = balances[:, -1] <= 0.0
    success_rate = float(1.0 - depleted.mean())
    start_dates = pd.DatetimeIndex(monthly_returns["date"].iloc[:n_windows])

    return HistoricalResult(
        start_dates=start_dates,
        balances=balances,
        depleted=depleted,
        success_rate=success_rate,
        stock_alloc=stock_alloc,
        withdrawal_rate=withdrawal_rate,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
    )


def find_max_safe_withdrawal_rate(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    horizon_years: int = 30,
    tol: float = 1e-4,
    lo: float = 0.0,
    hi: float = 0.10,
) -> float:
    """Binary search for the highest withdrawal rate with a 100% historical success rate.

    This is the historical "worst cohort" SWR for the given allocation and
    horizon (the rate that the worst-performing historical starting month
    can sustain without depleting the portfolio).
    """
    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        result = run_historical_simulation(
            monthly_returns,
            stock_alloc=stock_alloc,
            withdrawal_rate=mid,
            horizon_years=horizon_years,
        )
        if result.success_rate >= 1.0:
            lo = mid
        else:
            hi = mid
    return lo
