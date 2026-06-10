"""Vectorized Monte Carlo SWR simulator.

Two return-generation modes, both fitted/sampled from the same monthly real
return series used by the historical engine (`fire_sim.engine.returns`):

- ``"lognormal"``: fit a joint lognormal distribution (a multivariate normal
  on log(1 + r)) to historical monthly stock/bond returns, preserving their
  mean, variance, and correlation, then draw i.i.d. monthly returns from it.
  This mode has no memory of historical sequencing - no autocorrelation,
  no mean reversion, no fat tails beyond what a normal distribution implies.

- ``"block_bootstrap"``: resample contiguous blocks of historical monthly
  returns (default 12 months) and concatenate them to build synthetic
  paths. This preserves within-block correlation, autocorrelation, and
  seasonality, at the cost of being limited to return patterns that
  actually occurred historically.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from fire_sim.engine.result import SimulationResult
from fire_sim.engine.returns import load_monthly_returns
from fire_sim.engine.simulate import simulate_balances

DEFAULT_N_PATHS = 10_000


@dataclass
class LognormalParams:
    mu: np.ndarray  # shape (2,): mean of [log(1 + stock_return), log(1 + bond_return)]
    cov: np.ndarray  # shape (2, 2): covariance of the same


def fit_lognormal(monthly_returns: pd.DataFrame) -> LognormalParams:
    """Fit a joint lognormal distribution to historical monthly stock/bond returns."""
    log_returns = np.log1p(monthly_returns[["stock", "bond"]].to_numpy())
    return LognormalParams(mu=log_returns.mean(axis=0), cov=np.cov(log_returns, rowvar=False))


def _generate_lognormal(
    params: LognormalParams, n_paths: int, horizon_months: int, rng: np.random.Generator
):
    draws = rng.multivariate_normal(params.mu, params.cov, size=(n_paths, horizon_months))
    simple = np.expm1(draws)
    return simple[..., 0], simple[..., 1]


def _generate_block_bootstrap(
    monthly_returns: pd.DataFrame,
    n_paths: int,
    horizon_months: int,
    block_months: int,
    rng: np.random.Generator,
):
    stock_pool = monthly_returns["stock"].to_numpy()
    bond_pool = monthly_returns["bond"].to_numpy()
    pool_len = len(stock_pool)
    if block_months > pool_len:
        raise ValueError("block_months cannot exceed the length of the historical return series")

    n_blocks = -(-horizon_months // block_months)  # ceil division
    starts = rng.integers(0, pool_len - block_months + 1, size=(n_paths, n_blocks))
    offsets = np.arange(block_months)
    idx = (starts[:, :, None] + offsets).reshape(n_paths, n_blocks * block_months)
    idx = idx[:, :horizon_months]
    return stock_pool[idx], bond_pool[idx]


@dataclass
class MonteCarloResult(SimulationResult):
    mode: str
    seed: int | None = None


def run_monte_carlo_simulation(
    monthly_returns: pd.DataFrame | None = None,
    *,
    stock_alloc: float = 0.6,
    withdrawal_rate: float = 0.04,
    horizon_years: int = 30,
    starting_balance: float = 1.0,
    n_paths: int = DEFAULT_N_PATHS,
    mode: str = "lognormal",
    block_months: int = 12,
    seed: int | None = None,
) -> MonteCarloResult:
    """Run a vectorized Monte Carlo simulation.

    Generates `n_paths` synthetic `horizon_years * 12`-month return
    sequences (see module docstring for `mode` options), blends them by
    `stock_alloc`/`(1 - stock_alloc)` rebalanced every month, and applies
    the same fixed real monthly withdrawal as the historical engine.
    """
    if not 0.0 <= stock_alloc <= 1.0:
        raise ValueError("stock_alloc must be between 0 and 1")

    if monthly_returns is None:
        monthly_returns = load_monthly_returns()

    horizon_months = horizon_years * 12
    bond_alloc = 1.0 - stock_alloc
    rng = np.random.default_rng(seed)

    if mode == "lognormal":
        params = fit_lognormal(monthly_returns)
        stock_returns, bond_returns = _generate_lognormal(params, n_paths, horizon_months, rng)
    elif mode == "block_bootstrap":
        stock_returns, bond_returns = _generate_block_bootstrap(
            monthly_returns, n_paths, horizon_months, block_months, rng
        )
    else:
        raise ValueError(f"Unknown mode {mode!r} (expected 'lognormal' or 'block_bootstrap')")

    portfolio = stock_alloc * stock_returns + bond_alloc * bond_returns
    monthly_withdrawal = starting_balance * withdrawal_rate / 12.0
    balances = simulate_balances(portfolio, starting_balance, monthly_withdrawal)

    depleted = balances[:, -1] <= 0.0
    success_rate = float(1.0 - depleted.mean())

    return MonteCarloResult(
        balances=balances,
        depleted=depleted,
        success_rate=success_rate,
        stock_alloc=stock_alloc,
        withdrawal_rate=withdrawal_rate,
        horizon_years=horizon_years,
        starting_balance=starting_balance,
        mode=mode,
        seed=seed,
    )
