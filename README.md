# AI-Powered Retail Supply Chain & Decision Intelligence Platform

A personal, portfolio/career-experiment project — a prototype decision-support system for retail inventory risk, demand, and supplier performance. All data is public or synthetic; no employer, client, or confidential data of any kind is used.

Start here:
- [00_PROJECT_CHARTER.md](00_PROJECT_CHARTER.md) — problem, requirements, architecture, stack, MVP scope, roadmap
- [01_DATA_MODEL.md](01_DATA_MODEL.md) — ERD and modeling rationale
- [career_fit_log.md](career_fit_log.md) — ongoing log for the career-fit experiment this project is also testing
- [docs/adr/](docs/adr/) — architecture decision records

## Status

Phase 2 (data foundation): real M5 data + synthetic supply-chain data loaded into Postgres's `raw` schema.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
pip install -e .                # makes src/ packages (ingestion, mart, ...) importable
cp .env.example .env            # then fill in real values
docker compose up -d            # starts local Postgres on localhost:5433
```

Kaggle credentials (for `data/raw/` ingestion) go in `~/.kaggle/access_token` — never committed. See the Kaggle API docs for generating a token.

Re-running the full data foundation from scratch:
```bash
python data/synthetic_generators/subset_m5.py
python data/synthetic_generators/generate_supply_chain.py
python -m ingestion.load_raw
```

## Repo layout

```
data/synthetic_generators/   reproducible synthetic data generation scripts
data/raw/                    local-only landing zone for raw files (gitignored)
src/ingestion/                raw -> staging loaders
src/cleaning/                 staging validation/cleaning
src/mart/                     staging -> mart (fact/dim) build
src/metrics/                  inventory-health / risk metric computation
src/ml/                       forecasting, anomaly detection, LLM explanation
src/api/                      FastAPI service
src/app/                      Streamlit UI (V1)
tests/unit|data_quality|api/  test suites
docs/adr/                     architecture decision records
```
