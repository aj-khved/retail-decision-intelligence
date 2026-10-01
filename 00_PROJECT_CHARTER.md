# AI-Powered Retail Supply Chain & Decision Intelligence Platform
## Phase 0 Deliverable — Project Charter, Requirements, Architecture, Stack, MVP, Roadmap, Career-Fit Plan

Status: **Draft for review — no implementation yet.**

---

## 1. Project Charter

### 1.1 Problem Statement

A large retailer's inventory, sales, supplier, and promotion data lives in disconnected systems. Nobody can quickly answer:

- "Which SKUs at which stores are about to stock out?"
- "Which SKUs are overstocked and tying up working capital?"
- "Is this a real demand shift or a data/anomaly problem?"
- "Did the last promotion actually help, or did it just pull forward future sales?"

Analysts currently answer these questions with manual spreadsheet pulls, after the fact. The platform's job is to turn fragmented transactional data into **timely, explainable, trustworthy signals** that a human can act on — not to replace the human's judgment.

### 1.2 Target Users (synthetic personas, not real roles at any employer)

| Persona | Decisions they need to make | What they currently lack |
|---|---|---|
| **Store/Regional Inventory Analyst** | Which SKU/store combos need a manual reorder or markdown this week | A single ranked view of risk instead of 10 spreadsheets |
| **Category/Demand Planner** | Whether a demand shift is real, seasonal, or promo-driven | Trustworthy forecasts with visible confidence and drivers |
| **Supply Chain Ops Lead** | Which suppliers are reliably on-time vs. causing stockouts | Supplier performance tied to downstream stockout impact |

### 1.3 Business Context (simulated)

We are simulating an internal prototype for a mid-to-large multi-store retailer. The business pain is real-world-typical (fragmented data, reactive inventory management); the company, data, and outcomes are **not real** and will be clearly labeled synthetic/simulated throughout.

### 1.4 Core Use Cases

1. See a prioritized, store/SKU-level view of inventory risk (stockout + overstock).
2. Drill into *why* an item is flagged (recent sales trend, forecast, lead time, on-hand, anomalies).
3. View demand trend and forecast for a SKU/store, with a plain-language explanation.
4. Review supplier performance and its link to stockout risk.
5. Investigate flagged anomalies (e.g., a sales spike/drop that looks like a data issue vs. real).
6. Get a short list of recommended actions (reorder, investigate, no action) with the reasoning shown.
7. (Measurement layer) Compare system-flagged risk items against what actually happened, to assess whether the signal would have been useful.

### 1.5 Project Goals

- Experience the **full lifecycle**: raw data → pipeline → model → analytics → ML → API → UI → recommendation → measurement.
- Produce a system I can explain end-to-end, not one with hidden magic.
- Generate honest evidence about which parts of this work I enjoy, via the Career Fit Log (Section 9).

### 1.6 Non-Goals (V1)

- Not a general-purpose chatbot.
- Not a real-time/streaming system (daily or batch-interval granularity is enough to demonstrate the workflow).
- Not multi-tenant, not enterprise auth (SSO/RBAC) — simple single-user auth at most.
- Not a mobile app.
- Not a highly accurate production forecasting model — "reasonably good and evaluated" beats "state of the art."
- Not a big-data system — the data will comfortably fit on a laptop; we are not solving for petabyte scale.

### 1.7 Assumptions

- I will use my own time/laptop; no employer resources, data, or confidential information of any kind.
- Public or synthetic data only (Section 4).
- I have working knowledge of SQL/Python and will learn backend/frontend/deployment as I go — this is explicitly part of the experiment.

### 1.8 Constraints

- Zero/near-zero budget preferred; cloud costs introduced deliberately and only when justified (Phase 7).
- No employer or client data, ever.
- Time-boxed personal project — architecture must stay simple enough to actually finish an MVP.

---

## 2. Initial Requirements

### 2.1 Functional Requirements

- FR1: Ingest multi-entity retail data (sales, inventory, products, stores, suppliers, promotions/calendar).
- FR2: Clean and validate data; surface data-quality issues rather than silently hiding them.
- FR3: Model data into an analytical schema with clear grain (fact/dimension).
- FR4: Compute inventory-health metrics (days-of-supply, stockout risk, overstock risk) per store/SKU/day.
- FR5: Detect anomalies in sales/inventory series.
- FR6: Forecast demand per store/SKU at a useful horizon, with an evaluated baseline and (if justified) an ML model.
- FR7: Generate a ranked, explainable recommendation list (reorder / markdown / investigate / no action).
- FR8: Expose the above via an API.
- FR9: Provide an interactive UI: overview → drill-down → explanation, with search/filter.
- FR10: Produce a plain-language explanation of why an item was flagged (templated and/or LLM-generated, grounded only in the item's own computed metrics — no free-form LLM access to arbitrary data).
- FR11: Track a basic "did the flag turn out to be right" measurement once more days of data are simulated forward.

### 2.2 Non-Functional Requirements

- NFR1 (Correctness): Metrics must be traceable — every number in the UI must be explainable back to source rows.
- NFR2 (Reliability): Pipeline failures must be visible (logged, non-silent), not swallowed.
- NFR3 (Performance): Dashboard interactions return in well under 2s on the full synthetic dataset on a laptop.
- NFR4 (Testability): Core transformation and metric logic covered by unit tests; pipeline covered by data-quality tests.
- NFR5 (Security): No secrets in source control; input validation on the API; LLM calls use retrieved/grounded data only (prompt-injection awareness, Section on AI).
- NFR6 (Observability): Pipeline run logs, data-quality check results, and basic model-performance tracking are inspectable after the fact.
- NFR7 (Maintainability): A new contributor (future me) can read the code and docs and understand the system without me explaining it live.
- NFR8 (Reproducibility): Synthetic data generation and the full pipeline are re-runnable from scratch with one command and produce a working system.

### 2.3 Success Metrics for the Project Itself

- MVP runs end-to-end locally with one command.
- At least one ML/analytical capability is properly evaluated (not just "it ran").
- The system is deployed somewhere outside my laptop at least once.
- The Career Fit Log has enough entries across enough categories to support a real conclusion (not just 2-3 data points).

---

## 3. User Journeys

**J1 — Morning risk triage (Inventory Analyst).**
Opens dashboard → sees stores/SKUs ranked by risk → filters to their region → clicks a flagged SKU → sees on-hand, forecast, days-of-supply, and a plain-language reason → decides to reorder or dismiss.

**J2 — Investigating a weird number (Demand Planner).**
Notices a SKU's sales look off → opens its detail view → sees anomaly flag with the statistical reason (e.g., "3.2x normal daily volume, not aligned with any known promotion") → checks whether a promotion/calendar event explains it → concludes it's a data artifact or genuine demand shift.

**J3 — Supplier performance review (Supply Chain Ops Lead).**
Opens supplier view → sees on-time-delivery rate and how it correlates with stockout incidents for that supplier's SKUs → drills into the worst-performing supplier's affected products.

**J4 — Did the system help? (Me, as evaluator).**
After simulating additional days forward, opens the measurement view → compares items flagged as "high stockout risk" against which ones actually stocked out → records precision/recall-style numbers into the project's own documentation.

---

## 4. Data Strategy

### 4.1 Approach: hybrid real + synthetic

Pure synthetic data risks being *too* clean to produce real data-engineering pain, and pure public data may lack supplier/inventory granularity. Plan:

- **Base demand signal — public dataset:** [Kaggle M5 Forecasting / Walmart dataset] or similar public Walmart/retail sales dataset (store × item × day sales, with a calendar of events/promotions). Gives realistic seasonality, intermittent demand, and promo effects "for free."
  - *Decision deferred:* confirm exact dataset and license terms before use; if unavailable/unsuitable, fall back to fully synthetic generation using the same schema shape.
- **Everything the public dataset lacks — synthetic, generated reproducibly via a seeded script:**
  - Inventory on-hand/on-order snapshots per store/SKU/day
  - Supplier master data + purchase orders + lead times (with deliberately injected lateness/variance)
  - Product master data (category, cost, price) if not already in the public set
  - Store master data (region, format/size) if not already in the public set
  - Deliberately injected data-quality problems: missing values, duplicate rows, a schema drift event (e.g., a column renamed mid-dataset), a few orphaned foreign keys

### 4.2 Core Data Entities

`dim_product`, `dim_store`, `dim_supplier`, `dim_date`/calendar (incl. promotions/events), `fact_sales` (grain: store-sku-day), `fact_inventory_snapshot` (grain: store-sku-day), `fact_purchase_order` (grain: PO line).

### 4.3 Expected Pipeline

Raw files (CSV/Parquet) → **raw layer** (loaded as-is, typed loosely) → **cleaned/staging layer** (typed, deduplicated, validated) → **analytical mart** (fact/dim model) → metrics & features → forecast/risk tables consumed by the API.

### 4.4 Data Quality Challenges We Want (on purpose)

Missing inventory snapshots for some store/SKU/day combos; a supplier ID that changes format mid-history; duplicate sales rows from a simulated "double file load"; a few negative/zero-price rows; promotion calendar gaps. These exist so the data-quality layer (FR2) has real work to do.

---

## 5. Initial Architecture

### 5.1 Shape (V1)

```
[Public dataset + synthetic generators]
        |
        v
  Ingestion scripts  -->  raw tables (Postgres)
        |
        v
  Cleaning/validation (Python + SQL) --> staging tables
        |                                  |
        v                                  v
  Data-quality checks (great_expectations  Logged results
   or lightweight custom checks)
        |
        v
  Analytical mart (fact/dim tables, Postgres)
        |
        v
  Metrics layer (SQL/Python): inventory health, risk scores
        |
        v
  ML layer: forecasting model, anomaly detection, risk classifier
        |
        v
  FastAPI backend (serves metrics, forecasts, recommendations, explanations)
        |
        v
  Frontend (React or Streamlit — see Section 6 tradeoff)
        |
        v
  User (analyst persona)

Cross-cutting: logging, config/env management, tests, (later) Docker + deployment.
```

### 5.2 Data Architecture

Single Postgres instance, three schemas: `raw`, `staging`, `mart`. Keeps the project simple (no separate warehouse product to learn yet) while still giving real schema/grain/key design experience. DuckDB considered (see ADR in tech stack table) but Postgres chosen so the API and pipeline share one real, concurrent-capable database — closer to how an actual application behaves.

### 5.3 Application Architecture

FastAPI backend with a clear service layer (routers → services → data access), not a single `main.py` with everything inline. Backend exposes read endpoints over the mart; no business logic lives in the frontend.

### 5.4 AI/ML Architecture

Three distinct capabilities, each justified separately (see Section 6 AI/ML row and future ADRs):
1. **Demand forecast** — statistical baseline (e.g., seasonal naive / moving average) evaluated first; only add a learned model (e.g., gradient boosting) if it beats the baseline on held-out data.
2. **Anomaly detection** — statistical (rolling z-score / IQR), not ML, because the data volume and need for explainability favor a transparent method.
3. **Natural-language explanation** — a Claude API call that receives *only* the already-computed numeric facts for one flagged item (never raw free text from an untrusted source, never arbitrary database access) and returns a short explanation. This bounds prompt-injection risk because the model has no tool access and no untrusted input path.

### 5.5 API Architecture

REST, FastAPI, Pydantic schemas for request/response validation, versioned under `/api/v1`.

### 5.6 Deployment Architecture (future-state, not V1)

Local-first via Docker Compose (Postgres + API + frontend). A single low-cost deploy target (e.g., Fly.io/Render for the API+frontend, managed Postgres free tier) considered in Phase 7, only after local correctness is proven.

### 5.7 Security Approach

Input validation at the API boundary (Pydantic), no secrets in source control (`.env` + `.gitignore`, documented in a `.env.example`), least-privilege DB user for the app, and the LLM-grounding constraint from 5.4.

### 5.8 Testing Approach

Unit tests for transformation/metric functions, data-quality tests on the pipeline, API contract tests, and a basic forecast-evaluation report (not a unit test, but a tracked metric).

### 5.9 Observability Approach

Structured logging in the pipeline (what ran, row counts in/out, DQ check results) and in the API (request logging, error logging). A simple "last pipeline run" status page/table is enough for V1 — no dedicated monitoring stack yet.

---

## 6. Initial Technology Stack

| Technology | Why we need it | Alternatives considered | Tradeoff | Essential for V1? |
|---|---|---|---|---|
| **Python** | One language across pipeline, ML, and API keeps cognitive load down while learning the full lifecycle | — | None significant for this project's scope | Yes |
| **Postgres** | Real relational DB shared by pipeline and API; realistic schema/key/constraint design | DuckDB (simpler, file-based, great for pure analytics but awkward for a concurrently-queried app backend); SQLite (too limited for realistic constraint/indexing practice) | Slightly more setup (a running server) than DuckDB/SQLite | Yes |
| **pandas / SQL** | Transformation logic; SQL for set-based mart queries, pandas for generation/cleaning scripts | Polars (faster, modern) | Polars has a smaller ecosystem of examples; not essential to learn in V1 | Yes (pandas); Polars optional later |
| **FastAPI** | Modern, typed, async-capable Python API framework; widely used, good learning value | Flask (simpler, less built-in validation); Django (heavier, more than needed) | Slightly more boilerplate than Flask for simple routes | Yes |
| **Pydantic** | Request/response validation ships with FastAPI | Marshmallow | None meaningful | Yes |
| **Streamlit (V1) → React (V1.5/experiment)** | Streamlit gets a working, data-dense UI fast so we validate the *whole* pipeline quickly; React is introduced deliberately later as its own career-fit experiment in real frontend engineering | Plain Jinja/HTML; Dash; Next.js from day one | Streamlit UIs don't transfer directly to "real" frontend skill; accepted because the goal in V1 is validating the full loop, with React tried explicitly afterward | Streamlit: yes for V1. React: deliberate V1.5 experiment, not V1 |
| **scikit-learn / statsmodels** | Baseline forecasting, risk classification; simple, explainable, well-documented | Prophet, PyTorch/deep learning | Deep learning is unjustified at this data scale — would be complexity for its own sake | Yes, lightly |
| **Claude API (Anthropic)** | Natural-language explanation of already-computed flags (bounded, grounded use case) | Open-source local LLM | Local LLM adds infra complexity with no benefit for this bounded, low-volume use case | Yes, narrowly scoped |
| **pytest** | Standard, well-documented Python testing | unittest | None meaningful | Yes |
| **Great Expectations (or a lightweight custom DQ module)** | Explicit, inspectable data-quality checks instead of implicit "it probably worked" | Hand-rolled assertions only | GE has a learning curve and some setup overhead; may start with hand-rolled checks and introduce GE only if the custom checks get unwieldy | Lightweight custom checks: yes. GE: evaluate in Phase 2, not assumed |
| **Docker / Docker Compose** | Reproducible local environment; prerequisite for any deployment | Running everything natively | Adds a layer to learn, but this is explicitly a target skill area | Yes, by Phase 2 end |
| **GitHub + GitHub Actions** | Version control (needed regardless) and a lightweight CI target for the testing/career-fit experiment | GitLab | None meaningful | Git: yes immediately. Actions: Phase 6+ |
| **Fly.io / Render (TBD) + managed Postgres** | Cheap/free path to a real external deployment | AWS/GCP/Azure full stack | Full cloud providers teach more but add real cost and setup risk early; deliberately deferred | No — Phase 7 only |

---

## 7. MVP Scope

Smallest version that proves the **entire** workflow end-to-end:

1. One synthetic/public dataset ingested into `raw` Postgres tables via a reproducible script.
2. Cleaning + a handful of explicit data-quality checks into `staging`.
3. A minimal fact/dim mart (sales fact + product/store/date dims).
4. Two metrics: days-of-supply and a stockout-risk score, computed per store/SKU/day.
5. One evaluated forecasting baseline (even a simple seasonal-naive model, with an honest accuracy report).
6. One anomaly flag (rolling z-score on daily sales).
7. A ranked risk list + one drill-down view, served by FastAPI, shown in a Streamlit app.
8. One LLM-generated explanation for a flagged item, grounded in its own computed metrics only.
9. Runs locally via one documented command (`docker compose up` once Dockerized, or a documented script sequence before that).
10. A first Career Fit Log entry recorded after each major milestone above.

Explicitly **excluded from MVP**: supplier performance view, promotion-effect analysis, measurement/feedback loop, React frontend, any cloud deployment. These are real Phase 3+/7 work, added only after the MVP proves the loop.

---

## 8. Development Roadmap

| Milestone | Deliverable | Maps to Phase |
|---|---|---|
| M0 | This charter reviewed/approved; dataset selected | Phase 0 |
| M1 | Architecture + data model finalized (ERD); repo scaffolded; local Postgres running | Phase 1 |
| M2 | Ingestion + cleaning + DQ checks + mart tables, reproducible end-to-end | Phase 2 |
| M3 | Inventory-health metrics (days-of-supply, risk scores) computed and spot-checked by hand | Phase 3 |
| M4 | Forecast baseline evaluated; anomaly detection implemented; both documented with an ADR-style writeup | Phase 4 |
| M5 | FastAPI endpoints + Streamlit MVP UI showing ranked risk + drill-down + LLM explanation | Phase 5 (= MVP complete) |
| M6 | Tests (unit/DQ/API) in place; at least one deliberately-injected failure handled; Dockerized | Phase 6 |
| M7 | Deployed externally (API + UI + managed DB) | Phase 7 |
| M8 | Measurement view (flag-vs-outcome) + supplier performance + promotion-effect view, if time allows | Phase 3/8 extension |
| M9 | React frontend experiment (replace or sit alongside Streamlit) — explicit career-fit test of real frontend work | Post-MVP |
| M10 | Final career-fit synthesis using the accumulated log | Phase 8 |

Each milestone produces something runnable, not just a document.

---

## 9. Career Fit Experiment

### 9.1 Mechanism

A `career_fit_log.md` (separate file, created alongside this charter) will capture one entry per milestone/significant work session. After each milestone in Section 8, I'll answer a short subset of the ten reflection questions from the brief — not all ten every time, whichever are relevant to what was just done.

### 9.2 Activities we will deliberately pay attention to

Mapped to roadmap milestones so the log has real coverage, not just vague impressions:

- **Data cleaning/transformation & SQL** → M2
- **Data modeling** → M1/M2
- **Python (general + pipeline) & debugging** → M2–M6 throughout
- **Analytics/metric design** → M3
- **AI/ML (forecasting, anomaly detection, evaluation)** → M4
- **Backend/API development** → M5
- **Frontend/UX (Streamlit first, then React)** → M5 and M9 specifically (M9 is the clean A/B signal on "do I like real frontend work")
- **Testing** → M6
- **Deployment/infrastructure** → M7
- **Security (secrets, input validation, LLM grounding)** → woven through M5–M7
- **Technical documentation & ADRs** → throughout, each major decision
- **Requirements/problem definition** → M0/this document
- **Architecture/technical decision-making** → M1, every ADR
- **Debugging/problem investigation** → wherever something breaks (tracked explicitly, not just the happy path)

### 9.3 What "done" looks like for this experiment

At M10, enough log entries exist across *all* the categories above (not just the ones I naturally gravitate to) that I can honestly compare, e.g., "did I enjoy M2 (data cleaning) as much as M5 (backend) as much as M9 (frontend)" and locate myself among options A–G from the brief using evidence, not a guess made on day one.

---

## Open Decisions for Review Before Implementation Starts

1. **Dataset confirmation** — confirm the specific public dataset (e.g., Kaggle M5) is accessible and its license is compatible with a personal, non-commercial portfolio project; otherwise default to fully synthetic.
2. **Streamlit-then-React sequencing** — confirm you're fine deferring "real" frontend work to M9 rather than starting with React, given the MVP-speed rationale above.
3. **Great Expectations vs. hand-rolled DQ checks** — default is to start hand-rolled and upgrade only if needed; flag if you'd rather commit to GE from the start for the learning exposure.
4. **Cloud target for Phase 7** — no need to decide now; revisit once we reach M6.

Once you've reviewed and adjusted the above, next step is Phase 1: finalize the ERD and repo scaffold — still no feature code, just structure.
