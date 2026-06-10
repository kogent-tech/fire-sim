"""Parse Shiller's raw ie_data.xls into a clean, typed DataFrame.

Source sheet "Data" layout:
- Header spans rows 4-7 (0-indexed), data spans rows 8-1840.
- Row 1841 is a footnote ("Sept price is Sept 1st close...") and is dropped.
- Columns 13 and 15 are blank spacer columns and are dropped.
- The most recent 1-3 months commonly have NaN in lagging fields (D, E,
  Real Dividend, Real Earnings, CAPE, etc.) because those series are
  published with a delay relative to price/CPI. These NaNs are preserved
  as-is; consumers should truncate to the last fully-populated row if a
  complete record is required.
"""
from pathlib import Path

import pandas as pd

RAW_FILE = Path(__file__).resolve().parents[2] / "data" / "raw" / "ie_data.xls"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "shiller.parquet"

FIRST_DATA_ROW = 8
LAST_DATA_ROW = 1840  # inclusive

# Final column names, in source column order. Columns 13 and 15 are blank
# spacer columns in the source sheet and are dropped by position.
COLUMNS = [
    "date",
    "sp500_price",
    "dividend",
    "earnings",
    "cpi",
    "date_fraction",
    "long_rate_gs10",
    "real_price",
    "real_dividend",
    "real_total_return_price",
    "real_earnings",
    "real_tr_scaled_earnings",
    "cape",
    "tr_cape",
    "cape_yield",
    "monthly_total_bond_returns",
    "real_total_bond_returns",
    "ten_year_annualized_stock_real_return",
    "ten_year_annualized_bond_real_return",
    "excess_cape_yield_annualized_return",
]
BLANK_SOURCE_COLUMNS = [13, 15]


def _parse_date(value: float) -> pd.Timestamp:
    """Convert Shiller's YYYY.MM float date format to a Timestamp (month start)."""
    year = int(value)
    month = int(round((value - year) * 100))
    return pd.Timestamp(year=year, month=month, day=1)


def build(raw_file: Path = RAW_FILE) -> pd.DataFrame:
    raw = pd.read_excel(raw_file, sheet_name="Data", header=None)
    data = raw.iloc[FIRST_DATA_ROW : LAST_DATA_ROW + 1].reset_index(drop=True)
    keep_cols = [c for c in range(data.shape[1]) if c not in BLANK_SOURCE_COLUMNS]
    data = data.iloc[:, keep_cols]
    data.columns = COLUMNS

    data["date"] = data["date"].apply(_parse_date)
    data = data.drop(columns=["date_fraction"])

    return data


def main():
    df = build()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_FILE, index=False)
    print(f"Wrote {PROCESSED_FILE} ({len(df)} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()
