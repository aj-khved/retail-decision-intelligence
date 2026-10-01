"""Generate the supply-chain entities M5 doesn't have: suppliers, purchase
orders, daily inventory snapshots, and promotions. Everything is seeded off
config.SEED so re-running produces identical output (NFR8: reproducibility).

Inventory is simulated with a simple reorder-point policy per (store, item):
each day, subtract that day's real M5 sales from on-hand; when on-hand drops
to or below the reorder point and no PO is outstanding, place a PO sized to
cover a target days-of-supply, due after the assigned supplier's lead time.
Suppliers aren't perfectly reliable, so delivery lands early/on-time/late
according to each supplier's reliability_score, and a small fraction of POs
are partially fulfilled. This is what naturally produces stockout episodes
later rather than us hand-authoring risk labels.

A few rows are deliberately corrupted afterward (missing snapshot days,
occasional negative on-hand) as planned data-quality problems — see
01_DATA_MODEL.md / charter section 4.4.

Run: python data/synthetic_generators/generate_supply_chain.py
(requires subset_m5.py to have been run first)
"""
from pathlib import Path

import numpy as np
import pandas as pd

from config import N_SUPPLIERS, SEED

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DERIVED_DIR = RAW_DIR / "derived"

SUPPLIER_REGIONS = ["West", "Midwest", "South", "Northeast"]
PROMO_TYPES = ["PERCENT_OFF", "BOGO", "CLEARANCE"]


def generate_suppliers(rng: np.random.Generator) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "supplier_id": [f"SUP_{i:02d}" for i in range(N_SUPPLIERS)],
            "supplier_name": [f"Supplier {i:02d}" for i in range(N_SUPPLIERS)],
            "region": rng.choice(SUPPLIER_REGIONS, size=N_SUPPLIERS),
            "default_lead_time_days": rng.integers(3, 15, size=N_SUPPLIERS),
            "reliability_score": rng.uniform(0.75, 0.98, size=N_SUPPLIERS).round(3),
        }
    )


def assign_item_suppliers(item_ids: np.ndarray, suppliers: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    supplier_ids = rng.choice(suppliers["supplier_id"], size=len(item_ids))
    return pd.DataFrame({"item_id": item_ids, "supplier_id": supplier_ids})


def simulate_inventory_and_pos(
    sales_subset: pd.DataFrame,
    item_supplier_map: pd.DataFrame,
    suppliers: pd.DataFrame,
    rng: np.random.Generator,
):
    suppliers_idx = suppliers.set_index("supplier_id")
    item_to_supplier = item_supplier_map.set_index("item_id")["supplier_id"]

    snapshot_rows = []
    po_rows = []
    po_counter = 0

    group_keys = ["store_id", "item_id"]
    for (store_id, item_id), grp in sales_subset.groupby(group_keys, sort=False):
        grp = grp.sort_values("date")
        dates = grp["date"].to_numpy()
        sales = grp["sales_units"].to_numpy()

        avg_daily_demand = max(sales.mean(), 0.1)
        supplier_id = item_to_supplier.loc[item_id]
        supplier = suppliers_idx.loc[supplier_id]
        lead_time = int(supplier["default_lead_time_days"])
        reliability = float(supplier["reliability_score"])

        target_days_of_supply = 21
        safety_days = lead_time + 3
        reorder_point = avg_daily_demand * safety_days
        order_qty = avg_daily_demand * target_days_of_supply

        on_hand = avg_daily_demand * (safety_days + 7)
        on_order_qty = 0
        outstanding_po = None  # (expected_delivery_date, actual_delivery_date, qty_ordered)

        for date, units_sold in zip(dates, sales):
            if outstanding_po is not None and date == outstanding_po["actual_delivery_date"]:
                on_hand += outstanding_po["qty_received"]
                on_order_qty -= outstanding_po["qty_ordered"]
                outstanding_po = None

            on_hand = max(on_hand - units_sold, 0)

            if outstanding_po is None and on_hand <= reorder_point:
                lateness_draw = rng.random()
                if lateness_draw < reliability:
                    delivery_offset = lead_time
                elif lateness_draw < reliability + (1 - reliability) * 0.5:
                    delivery_offset = max(lead_time - rng.integers(1, 3), 1)
                else:
                    delivery_offset = lead_time + rng.integers(2, 8)

                qty_ordered = round(order_qty)
                fulfillment_rate = 1.0 if rng.random() > 0.05 else rng.uniform(0.6, 0.9)
                qty_received = round(qty_ordered * fulfillment_rate)

                order_date = pd.Timestamp(date)
                expected_delivery = order_date + pd.Timedelta(days=lead_time)
                actual_delivery = order_date + pd.Timedelta(days=delivery_offset)

                po_counter += 1
                po_rows.append(
                    {
                        "po_line_id": f"PO_{po_counter:07d}",
                        "supplier_id": supplier_id,
                        "item_id": item_id,
                        "store_id": store_id,
                        "order_date": order_date.date(),
                        "expected_delivery_date": expected_delivery.date(),
                        "actual_delivery_date": actual_delivery.date(),
                        "qty_ordered": qty_ordered,
                        "qty_received": qty_received,
                        "unit_cost": round(rng.uniform(2.0, 40.0), 2),
                    }
                )

                outstanding_po = {
                    "actual_delivery_date": actual_delivery.date(),
                    "qty_ordered": qty_ordered,
                    "qty_received": qty_received,
                }
                on_order_qty += qty_ordered

            snapshot_rows.append(
                {
                    "store_id": store_id,
                    "item_id": item_id,
                    "date": date,
                    "on_hand_qty": round(on_hand),
                    "on_order_qty": round(max(on_order_qty, 0)),
                }
            )

    return pd.DataFrame(snapshot_rows), pd.DataFrame(po_rows)


def inject_data_quality_problems(snapshots: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    snapshots = snapshots.copy()

    negative_idx = snapshots.sample(frac=0.002, random_state=rng.integers(0, 1_000_000)).index
    snapshots.loc[negative_idx, "on_hand_qty"] = -rng.integers(1, 10, size=len(negative_idx))

    missing_idx = snapshots.sample(frac=0.01, random_state=rng.integers(0, 1_000_000)).index
    return snapshots.drop(index=missing_idx)


def generate_promotions(sales_subset: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    pairs = sales_subset[["store_id", "item_id"]].drop_duplicates().reset_index(drop=True)
    min_date, max_date = pd.to_datetime(sales_subset["date"]).agg(["min", "max"])
    span_days = (max_date - min_date).days

    promo_rows = []
    promo_counter = 0
    n_promo_pairs = int(len(pairs) * 0.4)
    chosen = pairs.sample(n=n_promo_pairs, random_state=rng.integers(0, 1_000_000))

    for _, row in chosen.iterrows():
        n_promos = rng.integers(1, 4)
        for _ in range(n_promos):
            start_offset = rng.integers(0, max(span_days - 10, 1))
            duration = rng.integers(3, 8)
            start_date = min_date + pd.Timedelta(days=int(start_offset))
            end_date = start_date + pd.Timedelta(days=int(duration))

            promo_counter += 1
            promo_rows.append(
                {
                    "promotion_id": f"PROMO_{promo_counter:06d}",
                    "store_id": row["store_id"],
                    "item_id": row["item_id"],
                    "start_date": start_date.date(),
                    "end_date": end_date.date(),
                    "discount_pct": round(rng.uniform(0.10, 0.40), 2),
                    "promo_type": rng.choice(PROMO_TYPES),
                }
            )

    return pd.DataFrame(promo_rows)


def main() -> None:
    rng = np.random.default_rng(SEED)

    sales_subset = pd.read_csv(DERIVED_DIR / "sales_subset.csv")
    sales_subset["date"] = pd.to_datetime(sales_subset["date"]).dt.date

    suppliers = generate_suppliers(rng)
    item_supplier_map = assign_item_suppliers(sales_subset["item_id"].unique(), suppliers, rng)

    snapshots, purchase_orders = simulate_inventory_and_pos(sales_subset, item_supplier_map, suppliers, rng)
    snapshots = inject_data_quality_problems(snapshots, rng)

    promotions = generate_promotions(sales_subset, rng)

    suppliers.to_csv(DERIVED_DIR / "suppliers.csv", index=False)
    item_supplier_map.to_csv(DERIVED_DIR / "product_supplier_map.csv", index=False)
    snapshots.to_csv(DERIVED_DIR / "inventory_snapshots.csv", index=False)
    purchase_orders.to_csv(DERIVED_DIR / "purchase_orders.csv", index=False)
    promotions.to_csv(DERIVED_DIR / "promotions.csv", index=False)

    print(f"suppliers.csv: {len(suppliers):,} rows")
    print(f"inventory_snapshots.csv: {len(snapshots):,} rows")
    print(f"purchase_orders.csv: {len(purchase_orders):,} rows")
    print(f"promotions.csv: {len(promotions):,} rows")


if __name__ == "__main__":
    main()
