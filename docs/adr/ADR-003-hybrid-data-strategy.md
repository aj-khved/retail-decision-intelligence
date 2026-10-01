# ADR-003: Hybrid public + synthetic data

## Context
Need realistic multi-entity retail data (sales, inventory, suppliers, promotions) without using any real company's confidential or proprietary data.

## Options Considered
- **Fully synthetic**: generate everything, full control, but demand patterns (seasonality, intermittency, promo lift) are hard to fake convincingly and risk being "too clean."
- **Fully public dataset**: realistic sales/demand signal, but public retail datasets (e.g., Kaggle M5/Walmart) don't include inventory-on-hand, supplier, or PO-level data at all.
- **Hybrid**: public dataset for the demand signal, synthetic generation for everything it lacks.

## Decision
Hybrid. Use a public retail sales dataset for store/SKU/day sales and calendar/event structure; generate inventory snapshots, supplier/PO data, and any missing product/store attributes synthetically via a seeded, reproducible script.

## Rationale
This gives the realism of real demand data (seasonality, intermittent demand, genuine promo effects) while still covering every entity the problem needs, and keeps data generation fully reproducible and free of any confidentiality concern.

## Tradeoffs
- Synthetic and real data must be joined coherently (same store/SKU keys, aligned date ranges) — adds a bit of generation complexity.
- Synthetic portions (inventory, suppliers) won't have the same realism as the sales data; this is acceptable since their role is to exercise pipeline/modeling logic, not to be analytically "true."

## Consequences
- Every dataset and chart in the project must be clearly labeled real-public vs. synthetic, per the charter's realism/labeling requirement.
- Final dataset choice (exact public source) confirmed in Phase 2 before ingestion code is written.
