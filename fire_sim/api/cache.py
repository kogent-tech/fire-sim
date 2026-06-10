"""Process-wide caches for deterministic, scenario-independent engine computations.

The Shiller dataset and the historical/CAPE-derived statistics are fixed for
the lifetime of the process (the dataset only changes via a manual refresh +
redeploy), so it's wasteful to recompute them on every request.
"""
from functools import lru_cache

import pandas as pd

from fire_sim.engine.cape import CapeSWRModel, fit_cape_swr_model
from fire_sim.engine.returns import PROCESSED_FILE, load_monthly_returns


@lru_cache(maxsize=1)
def get_monthly_returns() -> pd.DataFrame:
    return load_monthly_returns()


@lru_cache(maxsize=1)
def get_latest_cape() -> float:
    df = pd.read_parquet(PROCESSED_FILE)
    return float(df["cape"].dropna().iloc[-1])


@lru_cache(maxsize=8)
def get_cape_model(stock_alloc: float, horizon_years: int) -> CapeSWRModel:
    return fit_cape_swr_model(get_monthly_returns(), stock_alloc=stock_alloc, horizon_years=horizon_years)
