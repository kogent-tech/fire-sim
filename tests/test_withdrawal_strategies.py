import numpy as np
import pytest

from fire_sim.engine.historical import run_historical_simulation
from fire_sim.engine.returns import load_monthly_returns
from fire_sim.engine.withdrawal_strategies import (
    run_constant_percentage_simulation,
    run_guyton_klinger_simulation,
)

HORIZON_MONTHS = 30 * 12


@pytest.fixture(scope="module")
def monthly_returns():
    return load_monthly_returns()


def test_guyton_klinger_shapes(monthly_returns):
    result = run_guyton_klinger_simulation(
        monthly_returns, stock_alloc=0.6, initial_withdrawal_rate=0.05, horizon_years=30
    )
    assert result.balances.shape == (result.n_windows, HORIZON_MONTHS + 1)
    assert result.withdrawals.shape == (result.n_windows, HORIZON_MONTHS)


def test_guyton_klinger_wide_guardrails_match_fixed_withdrawal(monthly_returns):
    """With guardrails that never trigger, GK should reduce to a fixed
    real withdrawal - i.e. match the historical engine exactly."""
    gk = run_guyton_klinger_simulation(
        monthly_returns,
        stock_alloc=0.6,
        initial_withdrawal_rate=0.04,
        horizon_years=30,
        upper_guardrail=1e9,
        lower_guardrail=0.0,
    )
    hist = run_historical_simulation(monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    np.testing.assert_allclose(gk.balances, hist.balances)
    assert gk.success_rate == hist.success_rate


def test_guyton_klinger_improves_on_fixed_withdrawal(monthly_returns):
    """Guardrails should improve (or at least not worsen) the historical
    success rate relative to a fixed real withdrawal at the same rate."""
    hist = run_historical_simulation(monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    gk = run_guyton_klinger_simulation(
        monthly_returns, stock_alloc=0.6, initial_withdrawal_rate=0.04, horizon_years=30
    )
    assert gk.success_rate >= hist.success_rate


def test_guyton_klinger_supports_higher_initial_rate(monthly_returns):
    """GK's headline claim: a higher initial withdrawal rate (5%) with
    guardrails can match or beat a 4% fixed-real success rate."""
    hist_4pct = run_historical_simulation(monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30)
    gk_5pct = run_guyton_klinger_simulation(
        monthly_returns, stock_alloc=0.6, initial_withdrawal_rate=0.05, horizon_years=30
    )
    assert gk_5pct.success_rate >= hist_4pct.success_rate - 0.02


def test_constant_percentage_never_depletes(monthly_returns):
    """Withdrawing a percentage of the current balance can asymptotically
    approach zero but never actually deplete the portfolio."""
    result = run_constant_percentage_simulation(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30
    )
    assert result.success_rate == 1.0
    assert (result.balances > 0).all()


def test_constant_percentage_withdrawals_track_balance(monthly_returns):
    result = run_constant_percentage_simulation(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30
    )
    monthly_rate = 0.04 / 12.0
    np.testing.assert_allclose(result.withdrawals, result.balances[:, :-1] * monthly_rate)

    # First-month withdrawal is identical for every window (same starting balance).
    assert np.allclose(result.withdrawals[:, 0], result.starting_balance * monthly_rate)
    # Later withdrawals diverge across windows as balances diverge.
    assert result.withdrawals[:, -1].std() > 0
