# ADR-002: Streamlit for V1 UI, React deferred to a deliberate later experiment

## Context
The UI needs to support an overview → drill-down → explanation flow. We also want an honest read on whether real frontend engineering (React) is something I enjoy, which is part of the career-fit experiment.

## Options Considered
- **React (or Next.js) from the start**: realistic frontend engineering experience immediately.
- **Streamlit from the start**, React introduced later as its own milestone (M9).
- **Dash / Jinja+HTML**: alternatives with similar fast-build tradeoffs to Streamlit but smaller ecosystems for this use case.

## Decision
Build the V1 UI in Streamlit. Introduce React later (M9) as a standalone, deliberately-scoped experiment rather than building it in from day one.

## Rationale
The MVP's purpose is to validate the *entire* pipeline end-to-end (data → metrics → ML → API → UI → recommendation) as fast as possible, so that architectural problems surface early. Streamlit removes frontend build time from that critical path. Building React from day one risks the MVP stalling on frontend plumbing before the core data/analytics/ML loop is even proven. Deferring React to its own milestone also produces a *cleaner* career-fit signal: a dedicated frontend milestone, evaluated on its own, is more informative than frontend work tangled into the MVP crunch.

## Tradeoffs
- Streamlit UI skill doesn't transfer directly to general frontend engineering.
- Some UI logic built for Streamlit will likely need to be rebuilt, not reused, when React is introduced.

## Consequences
- M5 (MVP) ships with Streamlit.
- M9 is explicitly scoped to try React against the same backend, purely to generate career-fit evidence on frontend work — not because the product needs it.
