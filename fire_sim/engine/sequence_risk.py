"""Sequence-of-returns risk: does the *order* of returns matter, not just
their average?

For a fixed-withdrawal retiree, a market crash in the first few years of
retirement is far more damaging than the same crash in the last few years -
even if the average return over the full horizon is identical - because
early losses are realized on a larger balance and compound against ongoing
withdrawals. This module quantifies that asymmetry by splitting each
historical rolling window into an "early" and "late" period and comparing
how strongly each predicts the window's outcome.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fire_sim.engine.result import SimulationResult
from fire_sim.engine.returns import load_monthly_returns, portfolio_returns
from fire_sim.engine.simulate import simulate_balances


@dataclass
class SequenceRiskResult(SimulationResult):
    start_dates: pd.DatetimeIndex
    early_return: np.ndarray  # shape (n_windows,), annualized return over the first `period_years`
    late_return: np.ndarray  # shape (n_windows,), annualized return over the last `period_years`
    period_years: int

    @property
    def n_windows(self) -> int:
        return self.n_paths


def run_sequence_risk_analysis(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    withdrawal_rate: float = 0.04,
    horizon_years: int = 30,
    starting_balance: float = 1.0,
    period_years: int = 10,
) -> SequenceRiskResult:
    """Run the standard historical simulation, plus annualized "early" and
    "late" period returns for each rolling window.

    `early_return`/`late_return` are the annualized portfolio return over
    the first/last `period_years` of each window - the per-window
    `balances` paths are returned alongside them so a caller (e.g. a
    "path colored by early-period performance" chart) can pair each path
    with its early-period return.
    """
    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    horizon_months = horizon_years * 12
    period_months = period_years * 12
    if not 0 < period_months <= horizon_months:
        raise ValueError(
            f"period_years ({period_years}) must be positive and at most "
            f"horizon_years ({horizon_years})"
        )

    returns = portfolio_returns(monthly_returns, stock_alloc)
    n_returns = len(returns)
    n_windows = n_returns - horizon_months + 1
    if n_windows < 1:
        raise ValueError(
            f"Not enough data for a {horizon_years}-year horizon "
            f"({n_returns} months of returns available, need {horizon_months})"
        )

    windows = np.lib.stride_tricks.sliding_window_view(returns, horizon_months)
    monthly_withdrawal = starting_balance * withdrawal_rate / 12.0
    balances = simulate_balances(windows, starting_balance, monthly_withdrawal)

    depleted = balances[:, -1] <= 0.0
    success_rate = float(1.0 - depleted.mean())

    early_growth = np.prod(1.0 + windows[:, :period_months], axis=1)
    late_growth = np.prod(1.0 + windows[:, -period_months:], axis=1)
    early_return = early_growth ** (12.0 / period_months) - 1.0
    late_return = late_growth ** (12.0 / period_months) - 1.0

    start_dates = pd.DatetimeIndex(monthly_returns["date"].iloc[:n_windows])

    return SequenceRiskResult(
        balances=balances,
        depleted=depleted,
        success_rate=success_rate,
        stock_alloc=stock_alloc,
        withdrawal_rate=withdrawal_rate,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
        start_dates=start_dates,
        early_return=early_return,
        late_return=late_return,
        period_years=period_years,
    )


def early_vs_late_sensitivity(result: SequenceRiskResult) -> dict:
    """Quantify how much more the early period predicts the outcome than the
    late period - the empirical signature of sequence-of-returns risk.

    Returns a dict with the Pearson correlation of early/late period returns
    against the ending balance, and the mean early/late period return for
    windows that succeeded vs. depleted. If sequence risk is present, the
    early-period correlation and success/failure gap should both be much
    larger than the late-period ones.
    """
    ending = result.ending_balances
    early_corr = float(np.corrcoef(result.early_return, ending)[0, 1])
    late_corr = float(np.corrcoef(result.late_return, ending)[0, 1])

    success = ~result.depleted
    out = {
        "early_return_corr_with_ending_balance": early_corr,
        "late_return_corr_with_ending_balance": late_corr,
        "early_return_mean_success": float(result.early_return[success].mean()),
        "late_return_mean_success": float(result.late_return[success].mean()),
        "early_return_mean_failure": None,
        "late_return_mean_failure": None,
    }
    if result.depleted.any():
        out["early_return_mean_failure"] = float(result.early_return[result.depleted].mean())
        out["late_return_mean_failure"] = float(result.late_return[result.depleted].mean())
    return out
