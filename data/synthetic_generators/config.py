"""Shared generation parameters. Change these to widen/narrow scope; everything
downstream (subsetting, supply-chain simulation, ingestion row counts) derives
from here so there's one place that controls dataset size.
"""

SEED = 42

# M5 has 10 stores across CA/TX/WI and ~1,941 days of history. Full scope is
# ~58M sales rows, which is more than this laptop-first project needs to prove
# the workflow (see charter non-goal: not a big-data system). Subsetting to 2
# stores and ~18 months keeps iteration fast while preserving real seasonality,
# holidays, and SNAP effects from the source data.
STORES = ["CA_1", "CA_2"]
HISTORY_DAYS = 548

N_SUPPLIERS = 8
