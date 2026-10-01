"""Reshape the raw M5 files (wide, 1,941 day-columns, 10 stores) into a
long-format subset scoped to config.STORES / config.HISTORY_DAYS, and cache it
under data/raw/derived/. This is the one place the wide->long melt happens so
ingestion and the synthetic supply-chain generators share a single definition
of "the subset" instead of re-deriving it separately.

Run: python data/synthetic_generators/subset_m5.py
"""
from pathlib import Path

import pandas as pd

from config import HISTORY_DAYS, STORES

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DERIVED_DIR = RAW_DIR / "derived"

ID_COLS = ["item_id", "dept_id", "cat_id", "store_id", "state_id"]


def _last_n_day_columns(sales_path: Path, n: int) -> list[str]:
    header = pd.read_csv(sales_path, nrows=0)
    day_cols = [c for c in header.columns if c.startswith("d_")]
    day_cols_sorted = sorted(day_cols, key=lambda c: int(c.split("_")[1]))
    return day_cols_sorted[-n:]


def build_sales_subset() -> pd.DataFrame:
    sales_path = RAW_DIR / "sales_train_evaluation.csv"
    day_cols = _last_n_day_columns(sales_path, HISTORY_DAYS)

    usecols = ID_COLS + day_cols
    wide = pd.read_csv(sales_path, usecols=usecols)
    wide = wide[wide["store_id"].isin(STORES)]

    long = wide.melt(
        id_vars=ID_COLS, value_vars=day_cols, var_name="d", value_name="sales_units"
    )

    calendar = pd.read_csv(RAW_DIR / "calendar.csv", usecols=["d", "date"])
    long = long.merge(calendar, on="d", how="left")

    return long[
        ["store_id", "item_id", "dept_id", "cat_id", "state_id", "date", "sales_units"]
    ].sort_values(["store_id", "item_id", "date"]).reset_index(drop=True)


def build_sell_prices_subset(item_ids: pd.Series) -> pd.DataFrame:
    prices = pd.read_csv(RAW_DIR / "sell_prices.csv")
    return prices[
        prices["store_id"].isin(STORES) & prices["item_id"].isin(item_ids)
    ].reset_index(drop=True)


def main() -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

    sales_subset = build_sales_subset()
    sales_subset.to_csv(DERIVED_DIR / "sales_subset.csv", index=False)
    print(f"sales_subset.csv: {len(sales_subset):,} rows")

    prices_subset = build_sell_prices_subset(sales_subset["item_id"].unique())
    prices_subset.to_csv(DERIVED_DIR / "sell_prices_subset.csv", index=False)
    print(f"sell_prices_subset.csv: {len(prices_subset):,} rows")


if __name__ == "__main__":
    main()
