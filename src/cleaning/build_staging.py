"""Build the `staging` schema from `raw`: typed, deduplicated, validated.

Philosophy: checks are run and *logged* before any fix is applied, so the
scale of a problem is visible (staging._dq_log), not just the end result.
Only one kind of fix happens automatically here — clipping a physically
impossible negative on-hand quantity to zero, since that's a known sensor/feed
error we deliberately injected, not a judgment call. Missing rows (e.g. a
snapshot that simply doesn't exist for a given day) are left missing rather
than invented — deciding how to handle a gap (ignore it vs. forward-fill vs.
flag the item) is a metrics-layer decision, not a cleaning-layer one.

Run: python -m cleaning.build_staging
"""
from sqlalchemy import text

from cleaning.dq_checks import DQCheck, ensure_dq_log_table, run_check
from ingestion.db import get_engine


def build_calendar(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "calendar_date_not_unique",
            "raw.calendar",
            "SELECT count(*) - count(DISTINCT date) FROM raw.calendar",
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.calendar"))
    conn.execute(
        text(
            """
            CREATE TABLE staging.calendar AS
            SELECT date, wm_yr_wk, weekday, wday, month, year, d,
                   event_name_1, event_type_1, event_name_2, event_type_2,
                   snap_ca::boolean AS snap_ca,
                   snap_tx::boolean AS snap_tx,
                   snap_wi::boolean AS snap_wi
            FROM raw.calendar
            """
        )
    )


def build_sales(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "sales_duplicate_store_item_date",
            "raw.sales",
            """
            SELECT coalesce(sum(c - 1), 0) FROM (
                SELECT count(*) c FROM raw.sales
                GROUP BY store_id, item_id, date HAVING count(*) > 1
            ) x
            """,
        ),
    )
    run_check(
        conn,
        DQCheck(
            "sales_negative_units",
            "raw.sales",
            "SELECT count(*) FROM raw.sales WHERE sales_units < 0",
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.sales"))
    conn.execute(
        text(
            """
            CREATE TABLE staging.sales AS
            SELECT DISTINCT ON (store_id, item_id, date)
                   store_id, item_id, dept_id, cat_id, state_id, date, sales_units
            FROM raw.sales
            WHERE sales_units >= 0
            ORDER BY store_id, item_id, date
            """
        )
    )


def build_sell_prices(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "sell_prices_non_positive",
            "raw.sell_prices",
            "SELECT count(*) FROM raw.sell_prices WHERE sell_price <= 0",
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.sell_prices"))
    conn.execute(
        text(
            """
            CREATE TABLE staging.sell_prices AS
            SELECT DISTINCT ON (store_id, item_id, wm_yr_wk)
                   store_id, item_id, wm_yr_wk, sell_price
            FROM raw.sell_prices
            WHERE sell_price > 0
            ORDER BY store_id, item_id, wm_yr_wk
            """
        )
    )


def build_inventory_snapshots(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "inventory_negative_on_hand",
            "raw.inventory_snapshots",
            "SELECT count(*) FROM raw.inventory_snapshots WHERE on_hand_qty < 0",
        ),
    )
    run_check(
        conn,
        DQCheck(
            "inventory_missing_vs_sales_days",
            "raw.inventory_snapshots",
            """
            SELECT count(*) FROM (
                SELECT store_id, item_id, date FROM raw.sales
                EXCEPT
                SELECT store_id, item_id, date FROM raw.inventory_snapshots
            ) missing
            """,
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.inventory_snapshots"))
    conn.execute(
        text(
            """
            CREATE TABLE staging.inventory_snapshots AS
            SELECT store_id, item_id, date,
                   GREATEST(on_hand_qty, 0) AS on_hand_qty,
                   on_order_qty
            FROM raw.inventory_snapshots
            """
        )
    )


def build_purchase_orders(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "po_received_exceeds_ordered",
            "raw.purchase_orders",
            "SELECT count(*) FROM raw.purchase_orders WHERE qty_received > qty_ordered",
        ),
    )
    run_check(
        conn,
        DQCheck(
            "po_delivered_before_ordered",
            "raw.purchase_orders",
            "SELECT count(*) FROM raw.purchase_orders WHERE actual_delivery_date < order_date",
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.purchase_orders"))
    conn.execute(
        text(
            """
            CREATE TABLE staging.purchase_orders AS
            SELECT * FROM raw.purchase_orders
            WHERE qty_received <= qty_ordered
              AND actual_delivery_date >= order_date
            """
        )
    )


def build_promotions(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "promotions_end_before_start",
            "raw.promotions",
            "SELECT count(*) FROM raw.promotions WHERE end_date < start_date",
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.promotions"))
    conn.execute(text("CREATE TABLE staging.promotions AS SELECT * FROM raw.promotions"))


def build_suppliers_and_map(conn) -> None:
    run_check(
        conn,
        DQCheck(
            "product_supplier_orphaned_item",
            "raw.product_supplier_map",
            """
            SELECT count(*) FROM (
                SELECT item_id FROM raw.product_supplier_map
                EXCEPT
                SELECT DISTINCT item_id FROM raw.sales
            ) orphaned
            """,
        ),
    )
    conn.execute(text("DROP TABLE IF EXISTS staging.suppliers"))
    conn.execute(text("CREATE TABLE staging.suppliers AS SELECT * FROM raw.suppliers"))
    conn.execute(text("DROP TABLE IF EXISTS staging.product_supplier_map"))
    conn.execute(
        text("CREATE TABLE staging.product_supplier_map AS SELECT * FROM raw.product_supplier_map")
    )


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS staging"))
        ensure_dq_log_table(conn)

        print("calendar:")
        build_calendar(conn)
        print("sales:")
        build_sales(conn)
        print("sell_prices:")
        build_sell_prices(conn)
        print("inventory_snapshots:")
        build_inventory_snapshots(conn)
        print("purchase_orders:")
        build_purchase_orders(conn)
        print("promotions:")
        build_promotions(conn)
        print("suppliers / product_supplier_map:")
        build_suppliers_and_map(conn)

        for table in [
            "calendar", "sales", "sell_prices", "inventory_snapshots",
            "purchase_orders", "promotions", "suppliers", "product_supplier_map",
        ]:
            count = conn.execute(text(f"SELECT count(*) FROM staging.{table}")).scalar()
            print(f"staging.{table}: {count:,} rows")


if __name__ == "__main__":
    main()
