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
    """Return (cfg dict, shared base Path) from paths.yml.

    The preferred configuration stores full path templates directly under
    ``databases``. Older configs with ``user`` + ``shared`` are still
    supported for backwards compatibility, in which case ``base`` is the
    selected shared root.
    """
    with open(ROOT / 'paths.yml') as fh:
        cfg = yaml.safe_load(fh)
    base = None
    if 'shared' in cfg and 'user' in cfg:
        base = Path(cfg['shared'][cfg['user']])
    return cfg, base


def db_path(cfg, base, key, **fmt):
    """Resolve a database path from paths.yml.

    Full path templates under ``databases`` are used as-is. Legacy relative
    templates are resolved against ``base``.
    """
    template = Path(cfg['databases'][key].format(**fmt))
    if template.is_absolute() or base is None:
        return template
    return base / template


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


# ---------------------------------------------------------------- region trades
def parse_region_parquet_name(path):
    """Return metadata parsed from a <...>_region parquet directory name."""
    parts = Path(path).name.split('_')
    if len(parts) == 5 and parts[-1] == 'region':
        name, version, table, year, _ = parts
        system = None
    elif len(parts) == 6 and parts[-1] == 'region':
        name, version, table, system, year, _ = parts
    else:
        return None

    return {
        'Name': name,
        'Version': version,
        'Table': table,
        'System': system,
        'Year': int(year),
        'Path': Path(path),
    }


def iter_region_parquet_dirs(databases_dir=None):
    """Yield metadata for all <...>_region parquet directories in databases/."""
    root = ROOT / 'databases' if databases_dir is None else Path(databases_dir)
    for path in sorted(root.iterdir()):
        if not path.is_dir() or not path.name.endswith('_region'):
            continue
        metadata = parse_region_parquet_name(path)
        if metadata is not None:
            yield metadata


def _find_column(columns, *candidates):
    normalized = {
        str(column).strip().lower().replace('_', ' '): column
        for column in columns
    }
    for candidate in candidates:
        match = normalized.get(candidate)
        if match is not None:
            return match
    return None


def _resolve_trade_unit(db, trades):
    unit_col = _find_column(getattr(trades, 'columns', []), 'unit', 'units')
    if unit_col is not None:
        units = trades[unit_col].dropna().astype(str).unique()
        if len(units) == 1:
            return units[0]

    units = getattr(db, 'units', None)
    if not isinstance(units, dict):
        return 'UNKNOWN'

    candidates = []
    for value in units.values():
        series = _unit_series(value)
        unique_units = pd.Series(series).dropna().astype(str).unique()
        if len(unique_units) == 1:
            candidates.append(unique_units[0])

    return candidates[0] if len(set(candidates)) == 1 else 'UNKNOWN'


def normalize_region_trades(trades, default_unit='UNKNOWN'):
    """Convert ``db.calc_trades()`` output to a standard long-form table."""
    if isinstance(trades, pd.Series):
        frame = trades.rename('Value').reset_index()
        if frame.shape[1] >= 3:
            renamed = frame.rename(columns={frame.columns[0]: 'Origin region',
                                            frame.columns[1]: 'Destination region'})
            renamed['Unit'] = default_unit
            return renamed[['Origin region', 'Destination region', 'Unit', 'Value']]

    if not isinstance(trades, pd.DataFrame):
        raise TypeError(f'Unsupported trades type: {type(trades).__name__}')

    origin_col = _find_column(
        trades.columns,
        'origin region', 'origin', 'source region', 'from region', 'exporter',
    )
    destination_col = _find_column(
        trades.columns,
        'destination region', 'destination', 'target region', 'to region', 'importer',
    )
    unit_col = _find_column(trades.columns, 'unit', 'units')
    value_col = _find_column(trades.columns, 'value', 'trade', 'trades', 'amount', 'flow')

    if origin_col is not None and destination_col is not None and value_col is not None:
        frame = trades.copy()
        if unit_col is None:
            frame['Unit'] = default_unit
            unit_col = 'Unit'
        renamed = frame.rename(columns={
            origin_col: 'Origin region',
            destination_col: 'Destination region',
            unit_col: 'Unit',
            value_col: 'Value',
        })
        return renamed[['Origin region', 'Destination region', 'Unit', 'Value']]

    frame = trades.copy()

    if isinstance(frame.index, pd.MultiIndex):
        index_names = [name or f'Origin region {i + 1}' for i, name in enumerate(frame.index.names)]
        frame.index = frame.index.rename(index_names)
    else:
        frame.index = frame.index.rename('Origin region')

    if isinstance(frame.columns, pd.MultiIndex):
        column_names = [
            name or f'Destination region {i + 1}'
            for i, name in enumerate(frame.columns.names)
        ]
        frame.columns = frame.columns.rename(column_names)
    else:
        frame.columns = frame.columns.rename('Destination region')

    stacked = frame.stack().rename('Value').reset_index()
    if stacked.shape[1] < 3:
        raise ValueError('Could not normalize calc_trades() output')

    origin_col = _find_column(stacked.columns, 'origin region', 'origin region 1')
    destination_col = _find_column(
        stacked.columns,
        'destination region', 'destination region 1',
    )
    if origin_col is None or destination_col is None:
        origin_col, destination_col = stacked.columns[:2]

    renamed = stacked.rename(columns={
        origin_col: 'Origin region',
        destination_col: 'Destination region',
    })
    renamed['Unit'] = default_unit
    return renamed[['Origin region', 'Destination region', 'Unit', 'Value']]


def _get_parse_from_parquet(mario_module):
    parser = getattr(mario_module, 'parse_from_parquet', None)
    if parser is not None:
        return parser

    database = getattr(mario_module, 'Database', None)
    if database is not None:
        parser = getattr(database, 'parse_from_parquet', None)
        if parser is not None:
            return parser

    raise AttributeError('parse_from_parquet is not available in the current mario installation')


def export_region_trades(mario_module, databases_dir=None, output_path=None):
    """Read all <...>_region parquet databases, calculate total trades, export one CSV."""
    cfg, _ = load_config()
    out = ROOT / cfg.get('export_dir', 'export') / 'region_total_trades.csv'
    if output_path is not None:
        out = Path(output_path)

    parser = _get_parse_from_parquet(mario_module)
    frames = []

    for metadata in iter_region_parquet_dirs(databases_dir):
        print(f"\\n=== {metadata['Path'].name} ===")
        db = parser(
            path=str(metadata['Path'] / 'flows'),
            table=metadata['Table'],
            mode='flows',
        )
        trades = db.calc_trades()
        trade_table = normalize_region_trades(
            trades,
            default_unit=_resolve_trade_unit(db, trades),
        )
        trade_table.insert(0, 'Year', metadata['Year'])
        trade_table.insert(0, 'System', metadata['System'] or '')
        trade_table.insert(0, 'Table', metadata['Table'])
        trade_table.insert(0, 'Version', metadata['Version'])
        trade_table.insert(0, 'Name', metadata['Name'])
        frames.append(trade_table)

    columns = [
        'Name', 'Version', 'Table', 'System', 'Year',
        'Origin region', 'Destination region', 'Unit', 'Value',
    ]
    result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)
    if not result.empty:
        result = result[columns]

    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    print(f'-> exported {out}')
    return result, out
