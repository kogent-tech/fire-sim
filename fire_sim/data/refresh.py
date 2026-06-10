"""Re-pull the Shiller dataset and diff it against the bundled parquet.

Manual trigger (v1) — run after Shiller publishes a new month's data, or
periodically to check for revisions to historical values:

    python -m fire_sim.data.refresh          # report differences only
    python -m fire_sim.data.refresh --apply   # also overwrite the bundled parquet
"""
import argparse

import pandas as pd

from fire_sim.data.build import PROCESSED_FILE, RAW_FILE, build
from fire_sim.data.fetch import fetch

NUMERIC_TOLERANCE = 1e-9


def diff(old: pd.DataFrame, new: pd.DataFrame) -> dict:
    old_dates = set(old["date"])
    new_dates = set(new["date"])

    added = sorted(new_dates - old_dates)
    removed = sorted(old_dates - new_dates)

    common = old.merge(new, on="date", suffixes=("_old", "_new"))
    revised_columns = {}
    for col in old.columns:
        if col == "date":
            continue
        old_col, new_col = f"{col}_old", f"{col}_new"
        both_present = common[old_col].notna() & common[new_col].notna()
        changed = both_present & (
            (common[old_col] - common[new_col]).abs() > NUMERIC_TOLERANCE
        )
        if changed.any():
            revised_columns[col] = int(changed.sum())

    return {
        "added_months": added,
        "removed_months": removed,
        "revised_columns": revised_columns,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="overwrite the bundled parquet with the freshly downloaded data",
    )
    args = parser.parse_args()

    old = pd.read_parquet(PROCESSED_FILE)

    fetch(RAW_FILE)
    new = build(RAW_FILE)

    result = diff(old, new)

    if result["added_months"]:
        print(f"New months: {[d.strftime('%Y-%m') for d in result['added_months']]}")
    else:
        print("New months: none")

    if result["removed_months"]:
        print(f"Removed months: {[d.strftime('%Y-%m') for d in result['removed_months']]}")

    if result["revised_columns"]:
        print("Revised values (column: number of months changed):")
        for col, count in result["revised_columns"].items():
            print(f"  {col}: {count}")
    else:
        print("Revised values: none")

    if args.apply:
        new.to_parquet(PROCESSED_FILE, index=False)
        print(f"Wrote {PROCESSED_FILE} ({len(new)} rows)")
    elif result["added_months"] or result["removed_months"] or result["revised_columns"]:
        print("\nRun with --apply to update the bundled parquet.")


if __name__ == "__main__":
    main()
