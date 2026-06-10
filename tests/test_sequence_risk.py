import numpy as np
import pytest

from fire_sim.engine.returns import load_monthly_returns, portfolio_returns
from fire_sim.engine.sequence_risk import early_vs_late_sensitivity, run_sequence_risk_analysis

HORIZON_MONTHS = 30 * 12
PERIOD_MONTHS = 10 * 12


@pytest.fixture(scope="module")
def monthly_returns():
    return load_monthly_returns()


def test_shapes(monthly_returns):
    result = run_sequence_risk_analysis(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30, period_years=10
    )
    assert result.balances.shape == (result.n_windows, HORIZON_MONTHS + 1)
    assert result.early_return.shape == (result.n_windows,)
    assert result.late_return.shape == (result.n_windows,)
    assert result.start_dates.is_monotonic_increasing


def test_early_and_late_return_match_manual_calculation(monthly_returns):
    result = run_sequence_risk_analysis(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30, period_years=10
    )
    returns = portfolio_returns(monthly_returns, 0.6)

    early_growth = np.prod(1.0 + returns[:PERIOD_MONTHS])
    late_growth = np.prod(1.0 + returns[HORIZON_MONTHS - PERIOD_MONTHS : HORIZON_MONTHS])
    expected_early = early_growth ** (12.0 / PERIOD_MONTHS) - 1.0
    expected_late = late_growth ** (12.0 / PERIOD_MONTHS) - 1.0

    assert result.early_return[0] == pytest.approx(expected_early)
    assert result.late_return[0] == pytest.approx(expected_late)


def test_period_years_must_be_positive_and_within_horizon(monthly_returns):
    with pytest.raises(ValueError):
        run_sequence_risk_analysis(monthly_returns, horizon_years=30, period_years=0)
    with pytest.raises(ValueError):
        run_sequence_risk_analysis(monthly_returns, horizon_years=30, period_years=31)


def test_sensitivity_demonstrates_sequence_risk(monthly_returns):
    """The headline finding: early-period returns predict the outcome much
    more strongly than late-period returns of the same length."""
    result = run_sequence_risk_analysis(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.04, horizon_years=30, period_years=10
    )
    sens = early_vs_late_sensitivity(result)

    assert result.depleted.any()
    assert abs(sens["early_return_corr_with_ending_balance"]) > abs(
        sens["late_return_corr_with_ending_balance"]
    )
    # Cohorts that failed had much worse early-period returns than those that succeeded.
    assert sens["early_return_mean_failure"] < sens["early_return_mean_success"]


def test_sensitivity_handles_no_failures(monthly_returns):
    """A 0% withdrawal rate never depletes - failure-conditioned stats should be None."""
    result = run_sequence_risk_analysis(
        monthly_returns, stock_alloc=0.6, withdrawal_rate=0.0, horizon_years=30, period_years=10
    )
    assert not result.depleted.any()

    sens = early_vs_late_sensitivity(result)
    assert sens["early_return_mean_failure"] is None
    assert sens["late_return_mean_failure"] is None
