"""Shared helpers: paths + emission-factor reshaping + CSV export.

The GHG aggregation itself is provided by ``Database.calc_ghg`` (added on
the MARIO ``dev_ghg`` branch).  This module only resolves dataset paths
and converts the resulting GHG row into a long-form CSV.
"""
from __future__ import annotations

from pathlib import Path
import yaml
import pandas as pd

ROOT = Path(__file__).resolve().parent


# --------------------------------------------------------------------- paths
def load_config():
    """Return (cfg dict, shared base Path) from paths.yml."""
    with open(ROOT / 'paths.yml') as fh:
        cfg = yaml.safe_load(fh)
    base = Path(cfg['shared'][cfg['user']])
    return cfg, base


def db_path(cfg, base, key, **fmt):
    """Resolve a database path relative to the shared base, formatting
    placeholders such as {version}, {year}, {system}, {table}, {archive}."""
    return base / cfg['databases'][key].format(**fmt)


# ------------------------------------------------------------ emission factors
def _unit_series(units):
    if isinstance(units, pd.DataFrame):
        if 'unit' in units.columns:
            return units['unit']
        return units.iloc[:, 0]
    return units


def _row_to_long(row, level, flow):
    """Reshape a single satellite row (Series indexed by columns of e/f) to
    a long-form dataframe with Region / <level> / Item / Value columns."""
    df = row.copy()
    df.index = df.index.set_names(['Region', level, 'Item'])
    out = df.rename('Value').reset_index()
    out.insert(0, 'Flow', flow)
    return out


def emission_factors(db, level, labels, ghg_label='GHG', ghg_unit='kg CO2eq'):
    """Return long-form GHG emission factors (Intensity + Footprint) for
    the given sector/commodity ``labels`` at ``level``.

    Requires that ``db.calc_ghg(..., inplace=True)`` was called beforehand
    (or that a row named ``ghg_label`` exists in ``db.e`` / ``db.f``).
    """
    e_row = db.e.loc[ghg_label, (slice(None), level, slice(None))]
    f_row = db.f.loc[ghg_label, (slice(None), level, slice(None))]

    efs = pd.concat([
        _row_to_long(e_row, level, 'Intensity'),
        _row_to_long(f_row, level, 'Footprint'),
    ], axis=0)
    efs = efs[efs['Item'].isin(labels)].copy()

    item_units = _unit_series(db.units[level])
    efs['Satellite account'] = ghg_label
    efs['Unit'] = (
        ghg_unit + '/' + efs['Item'].map(item_units).fillna('UNKNOWN').astype(str)
    )
    return efs[['Flow', 'Satellite account', 'Unit',
                'Region', level, 'Item', 'Value']]


# ------------------------------------------------------------------ export
def export_path(name, table, version, year, system=None, suffix=''):
    """Return the CSV path that ``export_efs`` would write to."""
    cfg, _ = load_config()
    out_dir = ROOT / cfg.get('export_dir', 'export')
    parts = [name, table, str(version)]
    if system is not None:
        parts.append(system)
    parts.append(str(year))
    if suffix:
        parts.append(suffix)
    return out_dir / ('_'.join(parts) + '.csv')


def should_skip(name, table, version, year, system=None, suffix='',
                policy='ask'):
    """Return True if the target CSV already exists and we should skip it.

    ``policy`` controls behaviour when the file exists:
        - ``'ask'`` (default): prompt y/n on stdin.
        - ``'skip'``: always skip.
        - ``'overwrite'``: never skip.
    """
    out = export_path(name, table, version, year, system, suffix)
    if not out.exists():
        return False
    if policy == 'skip':
        print(f'[skip] {out.name} already exists')
        return True
    if policy == 'overwrite':
        print(f'[overwrite] {out.name}')
        return False
    while True:
        ans = input(f'{out.name} exists. Overwrite? [y/N]: ').strip().lower()
        if ans in {'', 'n', 'no'}:
            print(f'[skip] {out.name}')
            return True
        if ans in {'y', 'yes'}:
            return False


def export_efs(efs, name, table, version, year, system=None, suffix=''):
    """Add metadata columns and write the CSV to <export_dir>/<...>.csv."""
    if system is not None:
        efs.insert(0, 'System', system)
    efs.insert(0, 'Year', year)
    efs.insert(0, 'Table', table)
    efs.insert(0, 'Version', version)
    efs.insert(0, 'Database', name)

    out = export_path(name, table, version, year, system, suffix)
    out.parent.mkdir(parents=True, exist_ok=True)
    efs.to_csv(out, index=False)
    print(f'-> exported {out}')
    return out
