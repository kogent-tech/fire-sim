# Data Dictionary — `data/processed/shiller.parquet`

Source: Robert Shiller's "Irrational Exuberance" dataset (`ie_data.xls`,
"Data" sheet), published at
http://www.econ.yale.edu/~shiller/data/ie_data.xls. Rebuild with
`python -m fire_sim.data.fetch && python -m fire_sim.data.build`.

Monthly data, January 1871 – September 2023 (1,833 rows). One row per month.

| Column | Type | Description |
|---|---|---|
| `date` | datetime | First day of the month |
| `sp500_price` | float | S&P Composite price (nominal), monthly average |
| `dividend` | float | S&P Composite dividend (nominal), 12-month total, interpolated from quarterly data |
| `earnings` | float | S&P Composite earnings (nominal), 12-month total, interpolated from quarterly data |
| `cpi` | float | Consumer Price Index (CPI-U), used to convert nominal to real values |
| `long_rate_gs10` | float | 10-year U.S. Treasury bond yield (%) |
| `real_price` | float | `sp500_price` adjusted to real (inflation-adjusted) terms |
| `real_dividend` | float | `dividend` adjusted to real terms |
| `real_total_return_price` | float | Real S&P Composite price index assuming all dividends are reinvested. Index value, not directly comparable to `real_price`. **Primary series for historical SWR simulation.** |
| `real_earnings` | float | `earnings` adjusted to real terms |
| `real_tr_scaled_earnings` | float | Real earnings rescaled onto the `real_total_return_price` index basis |
| `cape` | float | Cyclically Adjusted P/E ratio (P/E10): real price divided by the 10-year average of real earnings |
| `tr_cape` | float | CAPE computed using the total-return price/earnings series |
| `cape_yield` | float | Inverse of `cape` (earnings yield), expressed as a fraction |
| `monthly_total_bond_returns` | float | Monthly total return index for 10-year Treasury bonds (nominal) |
| `real_total_bond_returns` | float | `monthly_total_bond_returns` adjusted to real terms |
| `ten_year_annualized_stock_real_return` | float | Forward 10-year annualized real return of `real_total_return_price`, as of this date |
| `ten_year_annualized_bond_real_return` | float | Forward 10-year annualized real return of `real_total_bond_returns`, as of this date |
| `excess_cape_yield_annualized_return` | float | Forward 10-year annualized excess return of stocks over bonds (`ten_year_annualized_stock_real_return` minus `ten_year_annualized_bond_real_return`) |

## Known gaps / quirks

- **Trailing-month NaNs**: `dividend`, `earnings`, `real_dividend`,
  `real_earnings`, and `real_tr_scaled_earnings` are published with a lag and
  are commonly `NaN` for the most recent 1-3 months. `cape`/`tr_cape`/
  `cape_yield` for those months are computed from trailing 10-year averages
  and may still be populated even when the current month's `earnings` is
  `NaN`.
- The "10 year annualized" columns are necessarily `NaN` for the most recent
  ~10 years of data (no future return to measure yet) — by design, not a
  data error.
- `real_total_return_price` is an index series (large, monotonically
  increasing-ish numbers in the millions by 2023) — what matters for
  simulation is the *month-over-month ratio*, not the absolute value.
- Two blank spacer columns present in the source spreadsheet (positions 13
  and 15) are dropped during processing.
- A trailing footnote row in the source sheet ("Sept price is Sept 1st
  close...") is dropped during processing.

## Source columns dropped

- `date_fraction` — a redundant float encoding of `date` (e.g. `1871.0417`),
  not useful once `date` is a proper datetime.
