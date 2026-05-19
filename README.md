# Electricity carbon footprint

This repository accompanies the manuscript currently under review at the
Journal of Industrial Ecology. It collects the workflow used to calculate and
compare electricity carbon footprint indicators across multiple input-output
databases with a single, reproducible pipeline.

The implementation is a streamlined rework of the exploratory `review/`
scripts. A single notebook orchestrates the runs, configuration is kept in
`paths.yml` and `database_properties.py`, and greenhouse-gas aggregation is
delegated to MARIO through `Database.calc_ghg`.

## What this repository does

The workflow computes electricity-related GHG intensity and footprint results
for the database combinations configured in `database_properties.py`, including:

- EXIOBASE monetary IOT releases (`ixi` and `pxp` systems)
- EORA26
- EMERGING
- GLORIA

Each run exports long-form CSV files in `export/`, and `merge.py` combines them
into a harmonised `combined_results.csv` with values normalised to `kg/EUR`.

## Repository layout

```
paths.yml                 local/shared dataset roots and path templates
database_properties.py    database versions, years, systems, GWP factors, labels
common.py                 path resolution, GHG reshaping, CSV export helpers
run.ipynb                 main execution notebook, one section per database
merge.py                  merges exported CSVs into export/combined_results.csv
export/                   exported per-database result files
```

## Requirements

- Python environment with the dependencies used by the notebook and helper scripts
- A local MARIO installation with `Database.calc_ghg` available
- Access to the shared input-output database archive referenced in `paths.yml`

## How to use it

1. Configure your data paths in `paths.yml`.
	Set `user:` to your initials and add or update the matching entry under `shared:` so it points to your local copy of the IO database collection.

2. Prepare the Python environment.
	Activate the environment you use for MARIO and make sure the MARIO version you are running exposes `Database.calc_ghg`.

3. Open `run.ipynb`.
	The notebook is the main entry point. Each section loads one database, computes the aggregated GHG indicator, filters the electricity activities or commodities of interest, and exports a CSV to `export/`.

4. Run only the database sections you need.
	The available versions, years, systems, GWP factors, and electricity labels are defined in `database_properties.py`.

5. Merge the exported results.
	Run the final notebook cell or execute `merge.py` to combine all per-database CSVs into `export/combined_results.csv`.

## Outputs

- Per-database CSV files named from database, table, version, system, and year
- `export/combined_results.csv`, a merged table with units harmonised to `kg/EUR`

## Adapting the repository

- To add a new collaborator, add a new key under `shared:` in `paths.yml` and switch `user:` to that key.
- To change years, versions, systems, or electricity labels, edit
	`database_properties.py`.
- To change export behaviour or output naming, update the helpers in
	`common.py`.
