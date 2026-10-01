"""Load the M5 subset + synthetic supply-chain CSVs into Postgres's `raw`
schema. Deliberately minimal transformation here — typed columns and nothing
more. Cleaning/validation/dedup is staging's job (next step in the pipeline),
not ingestion's.

Uses COPY (via psycopg2) rather than pandas.to_sql, since the sales and
inventory-snapshot tables are a few million rows each and row-by-row inserts
would make this impractically slow.

Run: python -m ingestion.load_raw  (after activating the venv / pip install -e .)
"""
from pathlib import Path

import psycopg2

from ingestion.db import get_engine

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DERIVED_DIR = RAW_DIR / "derived"

TABLES = {
    "raw.calendar": (
        RAW_DIR / "calendar.csv",
        """
        CREATE TABLE raw.calendar (
            date date,
            wm_yr_wk integer,
            weekday text,
            wday integer,
            month integer,
            year integer,
            d text,
            event_name_1 text,
            event_type_1 text,
            event_name_2 text,
            event_type_2 text,
            snap_ca integer,
            snap_tx integer,
            snap_wi integer
        )
        """,
    ),
    "raw.sales": (
        DERIVED_DIR / "sales_subset.csv",
        """
        CREATE TABLE raw.sales (
            store_id text,
            item_id text,
            dept_id text,
            cat_id text,
            state_id text,
            date date,
            sales_units integer
        )
        """,
    ),
    "raw.sell_prices": (
        DERIVED_DIR / "sell_prices_subset.csv",
        """
        CREATE TABLE raw.sell_prices (
            store_id text,
            item_id text,
            wm_yr_wk integer,
            sell_price numeric
        )
        """,
    ),
    "raw.suppliers": (
        DERIVED_DIR / "suppliers.csv",
        """
        CREATE TABLE raw.suppliers (
            supplier_id text,
            supplier_name text,
            region text,
            default_lead_time_days integer,
            reliability_score numeric
        )
        """,
    ),
    "raw.product_supplier_map": (
        DERIVED_DIR / "product_supplier_map.csv",
        """
        CREATE TABLE raw.product_supplier_map (
            item_id text,
            supplier_id text
        )
        """,
    ),
    "raw.inventory_snapshots": (
        DERIVED_DIR / "inventory_snapshots.csv",
        """
        CREATE TABLE raw.inventory_snapshots (
            store_id text,
            item_id text,
            date date,
            on_hand_qty integer,
            on_order_qty integer
        )
        """,
    ),
    "raw.purchase_orders": (
        DERIVED_DIR / "purchase_orders.csv",
        """
        CREATE TABLE raw.purchase_orders (
            po_line_id text,
            supplier_id text,
            item_id text,
            store_id text,
            order_date date,
            expected_delivery_date date,
            actual_delivery_date date,
            qty_ordered integer,
            qty_received integer,
            unit_cost numeric
        )
        """,
    ),
    "raw.promotions": (
        DERIVED_DIR / "promotions.csv",
        """
        CREATE TABLE raw.promotions (
            promotion_id text,
            store_id text,
            item_id text,
            start_date date,
            end_date date,
            discount_pct numeric,
            promo_type text
        )
        """,
    ),
}


def main() -> None:
    engine = get_engine()
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")

        for table_name, (csv_path, ddl) in TABLES.items():
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            cur.execute(ddl)

            with open(csv_path, "r", encoding="utf-8") as f:
                cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)

            cur.execute(f"SELECT count(*) FROM {table_name}")
            row_count = cur.fetchone()[0]
            print(f"{table_name}: {row_count:,} rows loaded from {csv_path.name}")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
