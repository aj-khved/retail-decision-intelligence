# ADR-001: Postgres as the single database for pipeline and application

## Context
Need one database to hold raw/staging/mart data and to serve the FastAPI backend's read queries. Candidates: Postgres, DuckDB, SQLite.

## Options Considered
- **DuckDB**: embedded, file-based, excellent for single-user analytical SQL, zero server to run.
- **SQLite**: ubiquitous, zero server, but weak typing and limited concurrent-write support.
- **Postgres**: real client-server RDBMS, concurrent connections, standard in actual backend applications.

## Decision
Use Postgres for both the analytical pipeline and the application backend.

## Rationale
The project explicitly wants realistic backend/application experience, not just analytics. DuckDB would be the better *pure analytics* choice, but it's awkward as the backing store for a concurrently-queried API. Using one real RDBMS for everything avoids maintaining two database technologies and matches how this would actually be built.

## Tradeoffs
- Requires a running server (handled via Docker Compose from Phase 2 onward) instead of a single file.
- Slightly more setup than DuckDB/SQLite for local development.

## Consequences
- Local dev requires Postgres running (Docker) before any pipeline/API work.
- If analytical query performance becomes a real bottleneck at some point, DuckDB could be reconsidered for the mart layer specifically — not expected at this data scale.
