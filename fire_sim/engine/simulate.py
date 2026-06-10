"""Shared withdrawal-recursion core, used by both the historical and Monte Carlo engines."""
import numpy as np


def simulate_balances(
    returns: np.ndarray, starting_balance: float, monthly_withdrawal: float
) -> np.ndarray:
    """Simulate balance paths given a (n_paths, horizon_months) matrix of monthly portfolio returns.

    Returns balances of shape (n_paths, horizon_months + 1), with column 0
    equal to `starting_balance`. A path that is depleted (balance <= 0) is
    floored at 0 and stays there for all subsequent months.
    """
    n_paths, horizon_months = returns.shape
    balances = np.empty((n_paths, horizon_months + 1))
    balances[:, 0] = starting_balance
    current = np.full(n_paths, starting_balance)
    for m in range(horizon_months):
        current = np.maximum(current * (1.0 + returns[:, m]) - monthly_withdrawal, 0.0)
        balances[:, m + 1] = current
    return balances
