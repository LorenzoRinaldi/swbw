"""Shared helpers for dataset path resolution and export skipping."""
from __future__ import annotations

from pathlib import Path
import yaml

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


# ------------------------------------------------------------------ export
def export_path(name, table, version, year, system=None, suffix=''):
    """Return the target CSV path for one database/year export."""
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
    """Return True if the target CSV already exists and should be skipped.

    ``policy`` controls behavior when the file exists:
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
