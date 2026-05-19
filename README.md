# 2026_JIE_Citterio_CFe — electricity GHG emission factors

Streamlined re-implementation of the `review/` exploratory scripts. A single
notebook drives all databases; configuration lives in `paths.yml` +
`database_properties.py`. GHG aggregation is delegated to MARIO via
`Database.calc_ghg` (added on the `dev_ghg` branch).

## Layout

```
paths.yml                 paths to shared dataset folder + per-DB templates
database_properties.py    versions / years / systems / electricity labels
common.py                 path resolver + GHG row reshaping + CSV export
run.ipynb                 unified pipeline (one section per database)
merge.py                  concat all per-DB CSVs -> export/combined_results.csv (kg/EUR)
export/                   per-database CSVs + combined_results.csv
```

## Usage

Activate the `mario` env (with the `dev_ghg` branch checked out so that
`Database.calc_ghg` is available), then open `run.ipynb` and run the cells
of the databases you need. The last cell runs `merge.py` to produce
`export/combined_results.csv`.

To run as another user, add your initials and shared-folder path under
`shared:` in `paths.yml` and set `user:` accordingly.
