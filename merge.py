"""Combine all per-database CSVs in <export_dir> into combined_results.csv,
converting every emission factor to kg CO2-eq / EUR.
"""
# %%
from pathlib import Path
from datetime import datetime
import pandas as pd
from forex_python.converter import CurrencyRates

from common import load_config, ROOT

cfg, _ = load_config()
EXPORT_DIR = ROOT / cfg.get('export_dir', 'export')

# %%
csv_files = sorted(p for p in EXPORT_DIR.glob('*.csv')
                   if p.name != 'combined_results.csv')
print(f'Merging {len(csv_files)} CSVs from {EXPORT_DIR}')

df = pd.concat([pd.read_csv(p) for p in csv_files], ignore_index=True)

# Drop any leftover Activity/Commodity columns (only GLORIA may have them)
df = df.drop(columns=[c for c in ('Activity', 'Commodity') if c in df.columns])
df = df[df['Satellite account'] == 'GHG']

# Move Value to last
df = df[[c for c in df.columns if c != 'Value'] + ['Value']]

# %% --------------------------------------------------- unit normalisation
_rates = CurrencyRates()
_cache = {}


def usd_to_eur(year):
    year = int(year)
    if year not in _cache:
        _cache[year] = _rates.get_rate('USD', 'EUR', datetime(year, 6, 15))
    return _cache[year]


def to_kg_per_eur(row):
    unit, value, year = row['Unit'], row['Value'], row['Year']
    if unit == 'kg/EUR':
        return value
    if unit == 'kg/M.EUR':
        return value / 1_000_000
    if unit == 'Gg/M EUR':                   # 1 Gg / 1 M EUR == 1 kg / EUR
        return value
    if unit in {'Mt CO2eq/current million US$', 'kilotonnes/current 000 US$'}:
        return value * 1_000 / usd_to_eur(year)
    return value


df['Value'] = df.apply(to_kg_per_eur, axis=1)
df['Unit'] = 'kg/EUR'

# %%
out = EXPORT_DIR / 'combined_results.csv'
df.to_csv(out, index=False)
print(f'-> wrote {out}  ({len(df):,} rows)')
