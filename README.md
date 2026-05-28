# SWBW: Should We Be Worried About the Quality of Our Economic Accounts Data?

SWBW is a notebook-driven workspace for comparing multiple MRIO databases and
asking a practical question: how consistent are their economic accounts once
you line them up on the same regions, years, currencies, and indicators?

The repository combines lightweight Python helpers, a single orchestration
notebook, and precomputed parquet datasets under `databases/`. Its focus is on
harmonising and comparing trade and GDP estimates across MRIO sources, then
surfacing the differences through flat tables and interactive dashboards.

## Scope

The codebase supports a cross-database comparison workflow for economic
accounts. In practice, the notebook can:

- reload region-level MRIO datasets,
- compute total trade flows and GDP,
- harmonise country codes and currencies,
- export comparison tables,
- generate interactive HTML views for inspection.

The currently configured database families are:

- EXIOBASE
- EORA26
- FIGARO
- OECD-ICIO
- ADB
- EMERGING
- GLORIA

The current repository contents and generated outputs are centered on the trade
and GDP comparison side of this workflow, especially in `results/`, `support/`,
and `plots/`.

## Repository layout

```text
README.md                  project overview
run.ipynb                  main notebook; all workflows are orchestrated here
common.py                  path resolution, data reshaping, trade export helpers
database_properties.py     configured database families, versions, years, tables
plots.py                   harmonisation, comparison, and plotting utilities
paths.yml                  local absolute path templates for source databases

databases/                 local parquet datasets used for trade and GDP comparisons
other_data/                external raw trade data used for comparison work
results/                   generated flat outputs such as trades.csv and GDP.csv
support/                   harmonised intermediate outputs such as trades_comparison.csv
plots/                     generated HTML dashboards and other visual outputs
```

## Main outputs

Depending on which notebook sections you run, the repository generates:

- `results/trades.csv`, a combined table of inter-regional trade totals,
- `results/GDP.csv`, a combined table of GDP by region and database,
- `support/trades_comparison.csv`, a harmonised trade-comparison table with ISO3
  codes and currency normalization,
- interactive HTML dashboards such as `plots/trade_dashboard.html` and
  `plots/gdp_region_grid.html`.

Large generated CSV artifacts are tracked with Git LFS.

## Requirements

To reproduce the workflows, you need:

- a Python environment with the notebook dependencies used here,
- a local MARIO installation for loading MRIO datasets and computing database
  summaries such as trade totals and GDP,
- access to the proprietary or locally stored MRIO sources referenced in
  `paths.yml`,
- plotting dependencies such as `matplotlib` and `plotly`,
- optional helpers for country-code and currency harmonisation:
  `country_converter` and `forex_python`.

In practice, the notebook has been run from a dedicated MARIO-oriented Python
environment rather than as a standalone package install from this repository.

## How to use the repository

1. Update `paths.yml`.

   The file contains absolute local path templates for raw databases such as
   EXIOBASE, EORA26, EMERGING, GLORIA, FIGARO, OECD-ICIO, and ADB. Replace them
   with paths valid on your machine.

2. Open `run.ipynb` in the Python environment that can import MARIO.

   The notebook is the entry point. It contains the data-loading, export,
   harmonisation, and plotting steps.

3. Run only the sections relevant to your use case.

   Typical execution paths are:

   - trade and GDP extraction from local `*_region` parquet datasets,
   - creation of harmonised comparison tables,
   - export of interactive HTML dashboards.

4. Inspect the generated outputs.

   The notebook writes flat tables to `results/` and `support/`, while HTML
   visualizations are saved under `plots/`.

## Notes on configuration

- `database_properties.py` controls the database families, years, versions, and
  table types iterated by the notebook.
- `common.py` includes helpers to resolve paths and normalize exported trade
  outputs.
- `plots.py` contains the currency conversion, ISO3 harmonisation, and plotting
  code used by the comparison dashboards.
- `common.py` still supports the older `shared` + `user` layout in `paths.yml`,
  but this repository is currently configured with explicit absolute paths.

## Reproducibility boundary

This repository contains code, configuration, precomputed outputs, and some
prepared parquet datasets, but full reproduction still depends on local access
to the external MRIO databases referenced in `paths.yml` and on a working MARIO
environment.
