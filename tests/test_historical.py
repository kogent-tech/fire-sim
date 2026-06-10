import numpy as np
import pytest

from fire_sim.engine.historical import (
    find_max_safe_withdrawal_rate,
    run_historical_simulation,
)
from fire_sim.engine.returns import load_monthly_returns, portfolio_returns


def test_load_monthly_returns():
    returns = load_monthly_returns()
    assert len(returns) > 1000
    assert returns["date"].is_monotonic_increasing
    assert not returns["stock"].isna().any()
    assert not returns["bond"].isna().any()


def test_portfolio_returns_blends_allocation():
    returns = load_monthly_returns()
    all_stock = portfolio_returns(returns, 1.0)
    all_bond = portfolio_returns(returns, 0.0)
    blended = portfolio_returns(returns, 0.6)

    np.testing.assert_allclose(all_stock, returns["stock"].to_numpy())
    np.testing.assert_allclose(all_bond, returns["bond"].to_numpy())
    np.testing.assert_allclose(blended, 0.6 * all_stock + 0.4 * all_bond)


def test_portfolio_returns_rejects_invalid_allocation():
    returns = load_monthly_returns()
    with pytest.raises(ValueError):
        portfolio_returns(returns, 1.5)


def test_simulation_shape_and_zero_withdrawal():
    result = run_historical_simulation(
        stock_alloc=0.6, withdrawal_rate=0.0, horizon_years=30, starting_balance=1.0
    )
    assert result.balances.shape == (result.n_windows, 30 * 12 + 1)
    assert np.all(result.balances[:, 0] == 1.0)
    # With no withdrawals, a portfolio of positive returns can never be
    # depleted, so every window should "succeed".
    assert result.success_rate == 1.0
    assert not result.depleted.any()


def test_success_rate_decreases_with_withdrawal_rate():
    low = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.03, horizon_years=30)
    mid = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.05, horizon_years=30)
    high = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.08, horizon_years=30)
    assert low.success_rate >= mid.success_rate >= high.success_rate


def test_percentile_bands_are_ordered():
    result = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    p10 = result.percentile(10)
    p50 = result.percentile(50)
    p90 = result.percentile(90)
    assert np.all(p10 <= p50 + 1e-12)
    assert np.all(p50 <= p90 + 1e-12)


def test_trinity_study_4_percent_60_40_30yr():
    """Reproduce the Trinity Study's headline result: a 4% withdrawal rate
    on a 60/40 portfolio over a 30-year horizon succeeds ~95% of the time.
    """
    result = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    assert 0.93 <= result.success_rate <= 1.0

    # Trinity Study's original sample covered starting years 1926-1995 for a
    # 30-year horizon (so the horizon ends by 1995-ish) - check the same
    # cohort window in our data lands in the same ballpark.
    mask = (result.start_dates.year >= 1926) & (result.start_dates.year <= 1965)
    assert mask.sum() > 100
    trinity_era_success = (result.ending_balances[mask] > 0).mean()
    assert 0.90 <= trinity_era_success <= 1.0


def test_ern_worst_case_swr_60_40_30yr():
    """Cross-check against Big ERN's "Safe Withdrawal Rate Series": the
    worst historical 30-year cohort for a 60/40 portfolio could sustain
    roughly a 3.5% real withdrawal rate, with the worst starting cohort
    in the mid-1960s (the classic "1966 retiree" sequence-of-returns case).
    """
    swr = find_max_safe_withdrawal_rate(stock_alloc=0.6, horizon_years=30)
    assert 0.030 <= swr <= 0.045

    result = run_historical_simulation(stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    worst_idx = np.argmin(result.ending_balances)
    worst_year = result.start_dates[worst_idx].year
    assert 1955 <= worst_year <= 1975


def test_higher_equity_allocation_has_lower_worst_case_swr():
    """Sanity check on sequence-of-returns risk: a 100% equity portfolio's
    worst-case 30-year SWR is lower than a 60/40 portfolio's, despite
    higher average returns, due to higher volatility.
    """
    swr_60_40 = find_max_safe_withdrawal_rate(stock_alloc=0.6, horizon_years=30)
    swr_100_0 = find_max_safe_withdrawal_rate(stock_alloc=1.0, horizon_years=30)
    assert swr_100_0 < swr_60_40
