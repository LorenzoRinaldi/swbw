# Electricity carbon footprint

This repository accompanies the manuscript currently under review at the
Journal of Industrial Ecology, "Carbon footprint of electricity: a systematic
methodological and quantitative review". It collects the workflow used to
calculate and compare electricity carbon footprint indicators across multiple
input-output databases with a single, reproducible pipeline.

The implementation is a streamlined rework of the exploratory `review/`
scripts. A single notebook orchestrates the runs, configuration is kept in
`paths.yml` and `database_properties.py`, and greenhouse-gas aggregation is
delegated to MARIO through `Database.calc_ghg`.

## What this repository does

The workflow computes electricity-related GHG intensity and footprint results
for the database combinations configured in `database_properties.py`, including:

- EXIOBASE monetary IOT releases (`ixi` and `pxp` systems)
- EXIOBASE hybrid results (`3.3.18_shocked`)
- EORA26
- EMERGING
- GTAP
- GLORIA

Each run exports long-form CSV files, which are then converted from monetary
units to `g/kWh` using country-year electricity prices and merged with
additional non-IO sources into a single physical comparison table.

## Repository layout

```
paths.yml                 full local path templates for each database
database_properties.py    database versions, years, systems, GWP factors, labels
common.py                 path resolution, GHG reshaping, CSV export helpers
run.ipynb                 main execution notebook, one section per database
export/                   exported per-database result files
emission factors/         physical comparison table and figure outputs
plots.py                  plotting helpers for Figure 2
```

## Requirements

- Python environment with the dependencies used by the notebook and helper scripts
- A local MARIO installation with `Database.calc_ghg` available
- Access to local copies of the input-output databases referenced in `paths.yml`
- Plotting dependencies used in the notebook, including `matplotlib`
- Optional exchange-rate and country-code helpers used in the physical-unit conversion step (`forex_python`, `country_converter`)

## How to use it

1. Configure your data paths in `paths.yml`.
	Each database entry is a full local path template. Update those paths so they point to your own copies of EXIOBASE, EORA26, EMERGING, and GLORIA.

	This is intentionally explicit: the repository no longer relies on a separate `shared` root plus user initials to reconstruct the full paths.

2. Prepare the Python environment.
	Activate the environment you use for MARIO and make sure the MARIO version you are running exposes `Database.calc_ghg`.

3. Open `run.ipynb`.
	The notebook is the main entry point. Each section loads one database, computes the aggregated GHG indicator, filters the electricity activities or commodities of interest, and exports a CSV to `export/`.

4. Run only the database sections you need.
	The available versions, years, systems, GWP factors, and electricity labels are defined in `database_properties.py`.

5. Convert the monetary results to physical units.
	The notebook converts all selected monetary estimates to `g/kWh` using the electricity-price table in `support/Electricity_Prices.xlsx`, harmonises country codes, and writes the combined table to `emission factors/physical_efs.csv`.

6. Generate Figure 2.
	The plotting cell loads `physical_efs.csv`, maps each source to the plotting labels used in the manuscript, and creates the 4-panel comparison figure.

7. Export high-resolution figures.
	The final notebook cell saves the current figure to `export/figures/` in `svg`, `jpg`, and `tiff` formats.

## Outputs

- Per-database CSV files named from database, table, version, system, and year
- `emission factors/physical_efs.csv`, a merged table harmonised to `g/kWh`
- High-resolution figure exports in `export/figures/`

## Adapting the repository

- To run the project on another machine, replace the absolute path templates in `paths.yml` with paths valid on that machine.
- To change years, versions, systems, or electricity labels, edit
	`database_properties.py`.
- To change export behaviour or output naming, update the helpers in
	`common.py` and `plots.py`.

Legacy note: `common.py` still accepts the older `shared` + `user` configuration format for backwards compatibility, but the repository now uses explicit per-database paths by default.
