"""Shared result type for the historical and Monte Carlo simulation engines."""
from dataclasses import dataclass

import numpy as np


@dataclass
class SimulationResult:
    balances: np.ndarray  # shape (n_paths, horizon_months + 1), real dollars
    depleted: np.ndarray  # shape (n_paths,) bool
    success_rate: float
    stock_alloc: float
    withdrawal_rate: float
    horizon_years: int
    starting_balance: float

    @property
    def n_paths(self) -> int:
        return self.balances.shape[0]

    @property
    def ending_balances(self) -> np.ndarray:
        return self.balances[:, -1]

    def percentile(self, q) -> np.ndarray:
        """Percentile (0-100, scalar or sequence) of balance at each month, across paths."""
        return np.percentile(self.balances, q, axis=0)
