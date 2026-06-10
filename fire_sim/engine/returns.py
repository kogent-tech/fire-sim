"""Monthly real-return series derived from the Shiller dataset."""
from pathlib import Path

import pandas as pd

PROCESSED_FILE = Path(__file__).resolve().parents[2] / "data" / "processed" / "shiller.parquet"


def load_monthly_returns(parquet_file: Path = PROCESSED_FILE) -> pd.DataFrame:
    """Monthly real total-return series for stocks and bonds.

    Returns are month-over-month ratios of the real total-return index
    columns (`real_total_return_price`, `real_total_bond_returns`), so
    they're already inflation-adjusted. The result has one row per month,
    starting from the second month of the source data (the first month has
    no prior value to compute a return from).
    """
    df = pd.read_parquet(parquet_file)
    return pd.DataFrame({
        "date": df["date"].iloc[1:].reset_index(drop=True),
        "stock": (
            df["real_total_return_price"].to_numpy()[1:]
            / df["real_total_return_price"].to_numpy()[:-1]
            - 1.0
        ),
        "bond": (
            df["real_total_bond_returns"].to_numpy()[1:]
            / df["real_total_bond_returns"].to_numpy()[:-1]
            - 1.0
        ),
    })


def portfolio_returns(monthly_returns: pd.DataFrame, stock_alloc: float):
    """Blended monthly portfolio returns, rebalanced to `stock_alloc` every month."""
    if not 0.0 <= stock_alloc <= 1.0:
        raise ValueError("stock_alloc must be between 0 and 1")
    bond_alloc = 1.0 - stock_alloc
    return (
        stock_alloc * monthly_returns["stock"].to_numpy()
        + bond_alloc * monthly_returns["bond"].to_numpy()
    )
