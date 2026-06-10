import numpy as np
import pytest

from fire_sim.engine.cape import fit_cape_swr_model, per_window_swr
from fire_sim.engine.historical import find_max_safe_withdrawal_rate
from fire_sim.engine.returns import load_monthly_returns


@pytest.fixture(scope="module")
def monthly_returns():
    return load_monthly_returns()


def test_per_window_swr_matches_binary_search(monthly_returns):
    swr_df = per_window_swr(monthly_returns, stock_alloc=0.6, horizon_years=30)
    worst_case = find_max_safe_withdrawal_rate(monthly_returns, stock_alloc=0.6, horizon_years=30)
    assert swr_df["swr"].min() == pytest.approx(worst_case, abs=1e-4)


def test_per_window_swr_shape_and_range(monthly_returns):
    swr_df = per_window_swr(monthly_returns, stock_alloc=0.6, horizon_years=30)
    assert len(swr_df) == 1473
    assert swr_df["start_date"].is_monotonic_increasing
    assert (swr_df["swr"] > 0).all()


def test_cape_swr_model_fits_expected_relationship(monthly_returns):
    model = fit_cape_swr_model(monthly_returns, stock_alloc=0.6, horizon_years=30)
    assert model.n > 1000
    # Higher CAPE yield (cheaper market) -> historically higher SWR.
    assert model.slope > 0
    # The relationship should be meaningfully predictive (Big ERN reports
    # similar magnitude R^2 for this regression).
    assert 0.2 <= model.r_squared <= 0.9


def test_cape_swr_predict_monotonic(monthly_returns):
    model = fit_cape_swr_model(monthly_returns, stock_alloc=0.6, horizon_years=30)
    # Cheaper market (lower CAPE) -> higher suggested SWR.
    assert model.predict(10) > model.predict(20) > model.predict(35)
