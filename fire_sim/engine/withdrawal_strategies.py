"""Alternative withdrawal strategies, run over the same rolling historical windows.

Both strategies here are *dynamic*: the withdrawal amount changes over time
based on portfolio performance, unlike the historical/Monte Carlo engines'
fixed real-dollar withdrawal.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fire_sim.engine.result import SimulationResult
from fire_sim.engine.returns import load_monthly_returns, portfolio_returns


@dataclass
class GuytonKlingerResult(SimulationResult):
    start_dates: pd.DatetimeIndex
    withdrawals: np.ndarray  # shape (n_windows, horizon_months), real dollars
    upper_guardrail: float
    lower_guardrail: float
    adjustment_pct: float

    @property
    def n_windows(self) -> int:
        return self.n_paths


def run_guyton_klinger_simulation(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    initial_withdrawal_rate: float = 0.05,
    horizon_years: int = 30,
    starting_balance: float = 1.0,
    upper_guardrail: float = 1.20,
    lower_guardrail: float = 0.80,
    adjustment_pct: float = 0.10,
) -> GuytonKlingerResult:
    """Guyton-Klinger guardrails: a dynamic withdrawal strategy.

    The withdrawal amount starts at `starting_balance * initial_withdrawal_rate
    / 12` per month and is held flat until a year-end check. At each
    12-month mark, the current annualized withdrawal rate
    (``12 * monthly_withdrawal / current_balance``) is compared to
    `initial_withdrawal_rate`:

    - **Capital preservation rule**: if the current rate exceeds
      `initial_withdrawal_rate * upper_guardrail`, cut the withdrawal by
      `adjustment_pct`.
    - **Prosperity rule**: if the current rate falls below
      `initial_withdrawal_rate * lower_guardrail`, raise the withdrawal by
      `adjustment_pct`.

    Returns the same shape of result as the historical engine, plus the
    `withdrawals` array (monthly withdrawal amount per window/month).
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

    windows = np.lib.stride_tricks.sliding_window_view(returns, horizon_months)

    balances = np.empty((n_windows, horizon_months + 1))
    balances[:, 0] = starting_balance
    withdrawals = np.empty((n_windows, horizon_months))
    current = np.full(n_windows, starting_balance)
    monthly_withdrawal = np.full(n_windows, starting_balance * initial_withdrawal_rate / 12.0)

    for m in range(horizon_months):
        w = np.where(current > 0, monthly_withdrawal, 0.0)
        withdrawals[:, m] = w
        current = np.maximum(current * (1.0 + windows[:, m]) - w, 0.0)
        balances[:, m + 1] = current

        if (m + 1) % 12 == 0:
            with np.errstate(divide="ignore", invalid="ignore"):
                current_wr = np.where(current > 0, (monthly_withdrawal * 12.0) / current, np.inf)
            cut = current_wr > initial_withdrawal_rate * upper_guardrail
            raise_ = (current_wr < initial_withdrawal_rate * lower_guardrail) & ~cut
            monthly_withdrawal = np.where(cut, monthly_withdrawal * (1.0 - adjustment_pct), monthly_withdrawal)
            monthly_withdrawal = np.where(raise_, monthly_withdrawal * (1.0 + adjustment_pct), monthly_withdrawal)
            monthly_withdrawal = np.where(current <= 0, 0.0, monthly_withdrawal)

    depleted = balances[:, -1] <= 0.0
    success_rate = float(1.0 - depleted.mean())
    start_dates = pd.DatetimeIndex(monthly_returns["date"].iloc[:n_windows])

    return GuytonKlingerResult(
        balances=balances,
        depleted=depleted,
        success_rate=success_rate,
        stock_alloc=stock_alloc,
        withdrawal_rate=initial_withdrawal_rate,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
        start_dates=start_dates,
        withdrawals=withdrawals,
        upper_guardrail=upper_guardrail,
        lower_guardrail=lower_guardrail,
        adjustment_pct=adjustment_pct,
    )


@dataclass
class ConstantPercentageResult(SimulationResult):
    start_dates: pd.DatetimeIndex
    withdrawals: np.ndarray  # shape (n_windows, horizon_months), real dollars

    @property
    def n_windows(self) -> int:
        return self.n_paths


def run_constant_percentage_simulation(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    withdrawal_rate: float = 0.04,
    horizon_years: int = 30,
    starting_balance: float = 1.0,
) -> ConstantPercentageResult:
    """Baseline comparator: withdraw a fixed percentage of the *current*
    balance every month, instead of a fixed real amount.

    Because the withdrawal shrinks along with the balance, this strategy
    can never fully deplete the portfolio (`success_rate` is always ~1.0)
    - the interesting comparison is the `withdrawals` series itself, which
    fluctuates with the portfolio rather than staying flat.
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

    windows = np.lib.stride_tricks.sliding_window_view(returns, horizon_months)
    monthly_rate = withdrawal_rate / 12.0

    balances = np.empty((n_windows, horizon_months + 1))
    balances[:, 0] = starting_balance
    withdrawals = np.empty((n_windows, horizon_months))
    current = np.full(n_windows, starting_balance)

    for m in range(horizon_months):
        w = current * monthly_rate
        withdrawals[:, m] = w
        current = np.maximum(current * (1.0 + windows[:, m]) - w, 0.0)
        balances[:, m + 1] = current

    depleted = balances[:, -1] <= 0.0
    success_rate = float(1.0 - depleted.mean())
    start_dates = pd.DatetimeIndex(monthly_returns["date"].iloc[:n_windows])

    return ConstantPercentageResult(
        balances=balances,
        depleted=depleted,
        success_rate=success_rate,
        stock_alloc=stock_alloc,
        withdrawal_rate=withdrawal_rate,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
        start_dates=start_dates,
        withdrawals=withdrawals,
    )
