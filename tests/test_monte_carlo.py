import numpy as np
import pytest

from fire_sim.engine.historical import run_historical_simulation
from fire_sim.engine.monte_carlo import (
    _generate_block_bootstrap,
    fit_lognormal,
    run_monte_carlo_simulation,
)
from fire_sim.engine.returns import load_monthly_returns

HORIZON_MONTHS = 30 * 12


@pytest.fixture(scope="module")
def monthly_returns():
    return load_monthly_returns()


def test_fit_lognormal_shapes_and_values(monthly_returns):
    params = fit_lognormal(monthly_returns)
    assert params.mu.shape == (2,)
    assert params.cov.shape == (2, 2)

    log_returns = np.log1p(monthly_returns[["stock", "bond"]].to_numpy())
    np.testing.assert_allclose(params.mu, log_returns.mean(axis=0))
    # Stocks should have higher expected log-return and variance than bonds.
    assert params.mu[0] > params.mu[1]
    assert params.cov[0, 0] > params.cov[1, 1]


def test_lognormal_shape_and_reproducibility(monthly_returns):
    result = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, horizon_years=30, mode="lognormal", seed=1
    )
    assert result.balances.shape == (500, HORIZON_MONTHS + 1)
    assert result.mode == "lognormal"

    again = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, horizon_years=30, mode="lognormal", seed=1
    )
    np.testing.assert_array_equal(result.balances, again.balances)

    different = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, horizon_years=30, mode="lognormal", seed=2
    )
    assert not np.array_equal(result.balances, different.balances)


def test_block_bootstrap_shape_and_reproducibility(monthly_returns):
    result = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, horizon_years=30, mode="block_bootstrap",
        block_months=12, seed=1,
    )
    assert result.balances.shape == (500, HORIZON_MONTHS + 1)
    assert result.mode == "block_bootstrap"

    again = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, horizon_years=30, mode="block_bootstrap",
        block_months=12, seed=1,
    )
    np.testing.assert_array_equal(result.balances, again.balances)


def test_block_bootstrap_returns_drawn_from_historical_pool(monthly_returns):
    """Block-bootstrap returns must be drawn from the historical pool, never invented."""
    rng = np.random.default_rng(3)
    stock_returns, bond_returns = _generate_block_bootstrap(
        monthly_returns, n_paths=20, horizon_months=60, block_months=12, rng=rng
    )
    assert stock_returns.shape == (20, 60)
    assert np.isin(stock_returns, monthly_returns["stock"].to_numpy()).all()
    assert np.isin(bond_returns, monthly_returns["bond"].to_numpy()).all()


def test_block_months_too_large_raises(monthly_returns):
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(
            monthly_returns, n_paths=10, horizon_years=1, mode="block_bootstrap",
            block_months=len(monthly_returns) + 1, seed=1,
        )


def test_unknown_mode_raises(monthly_returns):
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(monthly_returns, n_paths=10, horizon_years=1, mode="bogus")


def test_invalid_stock_alloc_raises(monthly_returns):
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(monthly_returns, n_paths=10, horizon_years=1, stock_alloc=1.5)


def test_zero_withdrawal_always_succeeds(monthly_returns):
    for mode in ("lognormal", "block_bootstrap"):
        result = run_monte_carlo_simulation(
            monthly_returns, n_paths=2000, withdrawal_rate=0.0, horizon_years=30,
            mode=mode, seed=7,
        )
        assert result.success_rate == 1.0


def test_output_contract_matches_historical(monthly_returns):
    """MonteCarloResult exposes the same interface as HistoricalResult."""
    hist = run_historical_simulation(monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    mc = run_monte_carlo_simulation(
        monthly_returns, n_paths=500, stock_alloc=0.6, withdrawal_rate=0.04,
        horizon_years=30, mode="lognormal", seed=1,
    )

    for attr in ("balances", "depleted", "success_rate", "ending_balances", "n_paths"):
        assert hasattr(hist, attr)
        assert hasattr(mc, attr)

    assert mc.ending_balances.shape == (mc.n_paths,)
    assert mc.percentile(50).shape == (HORIZON_MONTHS + 1,)
    assert mc.percentile([5, 50, 95]).shape == (3, HORIZON_MONTHS + 1)


def test_lognormal_success_rate_in_plausible_range(monthly_returns):
    result = run_monte_carlo_simulation(
        monthly_returns, n_paths=10_000, stock_alloc=0.6, withdrawal_rate=0.04,
        horizon_years=30, mode="lognormal", seed=42,
    )
    assert 0.85 <= result.success_rate <= 1.0
