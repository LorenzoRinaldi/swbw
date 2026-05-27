#%%
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.font_manager as fm
from pathlib import Path
from datetime import date

try:
    import country_converter as coco
except Exception:
    coco = None

try:
    from forex_python.converter import CurrencyRates
except Exception:
    CurrencyRates = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception:
    px = None
    go = None
    make_subplots = None

try:
    import ipywidgets as widgets
except Exception:
    widgets = None

try:
    from IPython.display import display
except Exception:
    display = None


# Annual average EUR->USD rates (approx.) for robust offline use.
# Values are only used when online providers are unavailable or not requested.
DEFAULT_EURUSD_BY_YEAR = {
    1995: 1.308, 1996: 1.270, 1997: 1.134, 1998: 1.121, 1999: 1.066,
    2000: 0.924, 2001: 0.896, 2002: 0.946, 2003: 1.131, 2004: 1.244,
    2005: 1.244, 2006: 1.256, 2007: 1.371, 2008: 1.471, 2009: 1.394,
    2010: 1.326, 2011: 1.392, 2012: 1.285, 2013: 1.328, 2014: 1.329,
    2015: 1.109, 2016: 1.106, 2017: 1.130, 2018: 1.181, 2019: 1.120,
    2020: 1.142, 2021: 1.183, 2022: 1.053, 2023: 1.082, 2024: 1.081,
    2025: 1.080,
}


SOURCE_LABEL_ALIASES = {
    "EMERGING 1": "EMERGING",
    "GLORA 0.6 act": "GLORIA 0.6 act",
    "GLORA 0.6 com": "GLORIA 0.6 com",
}


def load_inter_font(font_dir: str = "."):
    """
    Configura un font sans-serif in stile Helvetica, con fallback progressivi.
    """
    for ext in ("*.ttf", "*.ttc"):
        for ttf in Path(font_dir).glob(ext):
            fm.fontManager.addfont(str(ttf))

    available = {f.name for f in fm.fontManager.ttflist}
    preferred_fonts = [
        "Helvetica Neue",
        "Helvetica",
        "Arial",
        "Liberation Sans",
        "Nimbus Sans",
        "DejaVu Sans",
    ]
    for font_name in preferred_fonts:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            print(f"Font '{font_name}' caricato")
            return

    plt.rcParams["font.family"] = "sans-serif"
    print("Helvetica non trovata — uso il sans-serif di default")

#%%
# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
class Config:
    YEAR = 2023
    EF="CF"
    INPUT_FILE = f"{EF} united.xlsx"
    OUTPUT_FILE_png = f"{EF}_{YEAR}_by_country_new_axis.png"
    OUTPUT_FILE_svg = f"{EF}_{YEAR}_by_country_new_axis.svg"
    FIGSIZE = (18, 10)
    DPI = 200
    MARKER_SIZE = 40          # scatter s= parameter
    ALPHA = 0.85
    LINEWIDTHS = 0.6           # bordo del marker

    # Colori per Database type
    TYPE_COLORS = {
        "Monetary": "#E07B39",   # arancione
        "Physical": "#2C7BB6",   # blu
    }

    # Simboli per Source (11 sorgenti, marker matplotlib — solo contorno)
    SOURCE_MARKERS = {
        "EXIO pxp":  "<",   
        "EXIO ixi":  ">",   
        "EMERGING":           "P",   
        "EORA":               "D",   
        "GLORIA 0.6 act":     "^",   
        "GLORIA 0.6 com":     "v",   
        "EXIO Hybrid":        "*",   
        "Electricity Maps":   "s",   
        "EMBER":              "*",   
        "NREL":               "h",   
        "IPCC":               "p",   
        "JRC":                "o",   
        "GTAP 11":            "X",
    }

    # Ordine dei paesi sull'asse X (decrescente per media)
    SORT_BY_MEAN = True   # True = ordina per media decrescente; False = alfabetico
    FONT_DIR = "."         # Cartella con i file Inter*.ttf


# ─────────────────────────────────────────────
# Funzioni
# ─────────────────────────────────────────────

def _normalized_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.casefold()


def _normalized_column(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series("", index=df.index, dtype="object")
    return _normalized_text(df[column])


def add_plot_labels(df: pd.DataFrame, label_column: str = "plot_labels") -> pd.DataFrame:
    result = df.copy()

    if label_column not in result.columns:
        result[label_column] = pd.NA

    if "Source" in result.columns:
        result[label_column] = result[label_column].fillna(result["Source"])

    db = _normalized_column(result, "Database")
    version = _normalized_column(result, "Version")
    system = _normalized_column(result, "System")
    sector = _normalized_column(result, "Sector")

    label_rules = [
        ("EXIO pxp", db.eq("exiobase") & version.eq("3.10.2") & system.eq("pxp")),
        ("EXIO ixi", db.eq("exiobase") & version.eq("3.10.2") & system.eq("ixi")),
        ("EMERGING", db.eq("emerging")),
        ("EORA", db.isin(["eora", "eora26"])),
        ("GLORIA 0.6 act", db.eq("gloria") & sector.eq("activity")),
        ("GLORIA 0.6 com", db.eq("gloria") & sector.eq("commodity")),
        ("EXIO Hybrid", db.eq("exiobase") & version.eq("3.3.18_shocked".casefold())),
        ("GTAP 11", db.eq("gtap")),
        ("Electricity Maps", db.eq("electricity maps")),
        ("EMBER", db.eq("ember")),
        ("NREL", db.eq("nrel")),
        ("IPCC", db.eq("ipcc")),
        ("JRC", db.eq("jrc")),
    ]

    missing_labels = result[label_column].isna()
    for label, mask in label_rules:
        result.loc[missing_labels & mask, label_column] = label
        missing_labels = result[label_column].isna()

    result[label_column] = result[label_column].replace(SOURCE_LABEL_ALIASES)
    return result


def add_database_type(df: pd.DataFrame, source_column: str = "plot_labels") -> pd.DataFrame:
    result = df.copy()

    if "Type" in result.columns:
        result["Type"] = result["Type"].replace({"Hybrid": "Physical"})
        result["Database type"] = result["Type"]
        return result

    if "Database type" not in result.columns:
        result["Database type"] = pd.NA

    if source_column not in result.columns:
        return result

    sources = result[source_column].replace(SOURCE_LABEL_ALIASES)
    physical_sources = {"Electricity Maps", "EMBER", "NREL", "IPCC", "JRC"}
    physical_sources = physical_sources | {"EXIO Hybrid"}
    monetary_sources = set(Config.SOURCE_MARKERS) - physical_sources

    result.loc[sources.isin(monetary_sources), "Database type"] = "Monetary"
    result.loc[sources.isin(physical_sources), "Database type"] = "Physical"
    result["Type"] = result["Database type"]
    return result


def prepare_plot_dataframe(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    result = add_plot_labels(df)

    if "Country" not in result.columns and "Region" in result.columns:
        result["Country"] = result["Region"]

    if "GWP100" not in result.columns and "Value" in result.columns:
        result["GWP100"] = result["Value"]

    if "GWP100" in result.columns:
        result["GWP100"] = pd.to_numeric(result["GWP100"], errors="coerce")
        result = result[result["GWP100"].notna() & result["GWP100"].ne(0)].copy()

    result = add_database_type(result)

    if "plot_labels" in result.columns:
        result["plot_labels"] = result["plot_labels"].replace(SOURCE_LABEL_ALIASES)

    if "plot_labels" in result.columns:
        result["Source"] = result["plot_labels"]
    elif "Source" in result.columns:
        result["Source"] = result["Source"].replace(SOURCE_LABEL_ALIASES)

    if "Source" in result.columns:
        result = result[result["Source"].isin(Config.SOURCE_MARKERS)].copy()

    if "Type" in result.columns:
        result = result[result["Type"].isin(Config.TYPE_COLORS)].copy()

    countries_to_exclude = ["CY", "LU", "MT"]
    if "Country" in result.columns:
        result = result[~result["Country"].isin(countries_to_exclude)].copy()

    return result


def plot_physical_efs(physical_efs: pd.DataFrame, cfg: Config):
    df = prepare_plot_dataframe(physical_efs, cfg)
    country_order = compute_country_order(df, cfg)
    fig = build_figure(df, country_order, cfg)
    return df, country_order, fig

def load_data(cfg: Config) -> pd.DataFrame:
    df = pd.read_excel(cfg.INPUT_FILE)
    return prepare_plot_dataframe(df, cfg)


def compute_country_order(df: pd.DataFrame, cfg: Config) -> list:
    if cfg.SORT_BY_MEAN:
        order = (df.groupby("Country")["GWP100"]
                   .median()
                   .sort_values(ascending=False)
                   .index.tolist())
    else:
        order = sorted(df["Country"].unique())
    return order


def build_figure(df: pd.DataFrame, country_order: list, cfg: Config):
    fig, axes = plt.subplots(2, 2, figsize=cfg.FIGSIZE)
    axes = axes.flatten()

    available_sources = set(df["Source"].dropna().astype(str)) if "Source" in df.columns else set()
    available_types = set(df["Type"].dropna().astype(str)) if "Type" in df.columns else set()
    source_type_map = (
        df[["Source", "Type"]]
        .dropna()
        .drop_duplicates()
        .set_index("Source")["Type"]
        .to_dict()
        if {"Source", "Type"}.issubset(df.columns)
        else {}
    )
    panels = [
        ("Intensity", 2017, 'a) Direct carbon intensity of electricity generation by country (2017)'),
        ("Intensity", 2023, 'c) Direct carbon intensity of electricity generation by country (2023)'),
        ("Footprint", 2017, 'b) Life-cycle carbon intensity of electricity generation by country (2017)'),
        ("Footprint", 2023, 'd) Life-cycle carbon intensity of electricity generation by country (2023)'),
    ]

    for ax, (flow, year, title) in zip(axes, panels):
        panel_df = df[(df["Flow"] == flow) & (df["Year"] == year)]
        panel_order = compute_country_order(panel_df, cfg)
        x_positions = {country: i for i, country in enumerate(panel_order)}
        y_max = 1250 if flow == "Intensity" else 2000

        for source, marker in cfg.SOURCE_MARKERS.items():
            sub = panel_df[panel_df["Source"] == source]
            if sub.empty:
                continue
            plot_type = sub["Type"].iloc[0]
            color = cfg.TYPE_COLORS[plot_type]

            x_vals = [x_positions[c] for c in sub["Country"]]
            ax.scatter(
                x_vals,
                sub["GWP100"].values,
                marker=marker,
                facecolors="none",
                edgecolors=color,
                s=cfg.MARKER_SIZE,
                alpha=cfg.ALPHA,
                linewidths=cfg.LINEWIDTHS,
                zorder=3,
            )

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xticks(range(len(panel_order)))
        ax.set_xticklabels(panel_order, fontsize=8, rotation=0)
        ax.set_xlim(-0.7, len(panel_order) - 0.3)
        ax.set_ylim(0, y_max)
        ax.yaxis.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    for ax in axes:
        ax.set_xlabel("")

    for ax in axes:
        ax.set_ylabel("GWP 100 [g CO2eq/kWh]", fontsize=10)

    source_groups = []
    for plot_type in cfg.TYPE_COLORS:
        grouped_handles = []
        for source, marker in cfg.SOURCE_MARKERS.items():
            if source not in available_sources:
                continue
            if source_type_map.get(source) != plot_type:
                continue
            grouped_handles.append(
                mlines.Line2D(
                    [], [],
                    color=cfg.TYPE_COLORS[plot_type],
                    marker=marker,
                    linestyle="None",
                    markersize=8,
                    label=source,
                    markerfacecolor="none",
                    markeredgewidth=cfg.LINEWIDTHS,
                )
            )
        if grouped_handles:
            source_groups.append((plot_type, grouped_handles))

    fig.text(0.02, 0.095, "Sources:", ha="left", va="center", fontsize=10, fontweight="bold")
    anchor_x = 0.12
    gap = 0.015
    group_boxes = []
    for plot_type, handles in source_groups:
        legend = fig.legend(
            handles=handles,
            loc="lower left",
            bbox_to_anchor=(anchor_x, 0.06),
            ncol=len(handles),
            frameon=True,
            fancybox=False,
            edgecolor=cfg.TYPE_COLORS[plot_type],
            facecolor="white",
            framealpha=1.0,
            fontsize=8,
            handlelength=0.8,
            handletextpad=0.25,
            columnspacing=0.65,
            borderpad=0.35,
        )
        for text in legend.get_texts():
            text.set_color(cfg.TYPE_COLORS[plot_type])
        fig.add_artist(legend)
        fig.canvas.draw()
        bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
        group_boxes.append((plot_type, bbox))
        anchor_x = bbox.x1 + gap

    fig.text(0.02, 0.035, "Database type:", ha="left", va="center", fontsize=10, fontweight="bold")
    for plot_type, bbox in group_boxes:
        if plot_type not in available_types:
            continue
        center_x = (bbox.x0 + bbox.x1) / 2
        fig.text(
            center_x,
            0.035,
            plot_type,
            ha="center",
            va="center",
            fontsize=10,
            color=cfg.TYPE_COLORS[plot_type],
        )

    fig.suptitle("Carbon footprint and intensity of electricity generation by country", fontsize=13, fontweight="bold", y=0.985)
    fig.tight_layout(rect=(0, 0.14, 1, 0.95))
    return fig


# -----------------------------------------------------------------------------
# Cross-database trade comparison helpers
# -----------------------------------------------------------------------------
ROW_PATTERNS = (
    'rest of world',
    'rest-of-world',
    'rest of the world',
    'row',
    'ro w',
)


def _database_key(df: pd.DataFrame) -> pd.Series:
    system = df.get('System', pd.Series('', index=df.index)).fillna('').astype(str).str.strip()
    base = (
        df['Name'].astype(str).str.strip()
        + ' '
        + df['Version'].astype(str).str.strip()
    )
    has_system = system.ne('')
    base.loc[has_system] = base.loc[has_system] + ' ' + system.loc[has_system]
    return base


def _database_family_key(df: pd.DataFrame) -> pd.Series:
    if {'Name', 'Version'}.issubset(df.columns):
        version = df['Version'].fillna('').astype(str).str.strip()
        base = df['Name'].fillna('').astype(str).str.strip()
        has_version = version.ne('')
        base.loc[has_version] = base.loc[has_version] + ' ' + version.loc[has_version]
        return base.str.strip()

    if 'Database' in df.columns:
        return df['Database'].fillna('').astype(str).str.strip()

    raise ValueError("Missing columns to build database family key. Expected 'Name'/'Version' or 'Database'.")


def _resolve_trade_regions(regions: list[str], available_iso3) -> list[str]:
    if not regions:
        raise ValueError('regions must contain at least one region code or name')

    available = {
        str(code).strip().upper()
        for code in available_iso3
        if pd.notna(code) and str(code).strip()
    }
    resolved: list[str] = []
    unknown: list[str] = []

    for region in regions:
        label = str(region).strip()
        if not label:
            continue

        candidate = label.upper()
        if candidate not in available and coco is not None:
            converted = coco.convert(names=[label], to='ISO3', not_found=None)
            if isinstance(converted, list):
                converted = converted[0]
            if isinstance(converted, str):
                converted = converted.strip().upper()
                if converted in available:
                    candidate = converted

        if candidate in available:
            if candidate not in resolved:
                resolved.append(candidate)
            continue

        unknown.append(label)

    if unknown:
        raise ValueError(
            'Some requested regions were not found in the trade table after ISO3 harmonization: '
            + ', '.join(unknown)
        )
    if not resolved:
        raise ValueError('No valid regions left after ISO3 harmonization')

    return resolved


def _is_row(series: pd.Series) -> pd.Series:
    lowered = series.fillna('').astype(str).str.strip().str.casefold()
    mask = pd.Series(False, index=series.index)
    for pattern in ROW_PATTERNS:
        mask = mask | lowered.str.fullmatch(pattern)
    return mask


def _to_iso3(series: pd.Series) -> pd.Series:
    if coco is None:
        raise ImportError('country_converter is required. Install with: pip install country_converter')

    values = series.fillna('').astype(str).str.strip()
    upper = values.str.upper()

    legacy_iso3 = {
        'TMP': 'TLS',  # Timor-Leste legacy code
        'ROM': 'ROU',  # Romania legacy code
        'ZAR': 'COD',  # DR Congo legacy code
        'YUG': 'SRB',  # Yugoslavia -> Serbia proxy
        'SER': 'SRB',  # Serbia and Montenegro legacy shorthand
    }

    # Keep already-standard ISO3 codes, then map known legacy aliases.
    iso3 = pd.Series(pd.NA, index=series.index, dtype='object')
    looks_iso3 = upper.str.fullmatch(r'[A-Z]{3}')
    iso3.loc[looks_iso3] = upper.loc[looks_iso3]
    iso3 = iso3.replace(legacy_iso3)

    unresolved = iso3.isna() & values.ne('')
    if unresolved.any():
        converted = coco.convert(names=values.loc[unresolved].tolist(), to='ISO3', not_found=None)
        iso3.loc[unresolved] = pd.Series(converted, index=values.loc[unresolved].index, dtype='object')

    iso3 = iso3.replace({'not found': None})
    return iso3


def get_yearly_eur_usd_rates(
    years,
    source: str = 'builtin',
    reference_month: int = 7,
    reference_day: int = 1,
) -> pd.Series:
    """Return EUR->USD rates indexed by year.

    source:
      - 'builtin': use the internal annual table (offline, robust)
      - 'forex'  : fetch each year via forex_python, fallback to builtin if unavailable
    """
    year_values = sorted({int(y) for y in years if pd.notna(y)})
    rates = pd.Series(DEFAULT_EURUSD_BY_YEAR, dtype='float64')

    if source == 'forex':
        if CurrencyRates is None:
            raise ImportError('forex_python is required. Install with: pip install forex-python')

        client = CurrencyRates()
        for y in year_values:
            try:
                rates.loc[y] = client.get_rate('EUR', 'USD', date(y, reference_month, reference_day))
            except Exception:
                # Keep builtin fallback for this year.
                pass

    missing = [y for y in year_values if y not in rates.index or pd.isna(rates.loc[y])]
    if missing:
        raise ValueError(f'Missing EURUSD rates for years: {missing}')

    rates = rates.loc[year_values]
    rates.name = 'EURUSD'
    return rates


def _unit_to_million_factor(unit: pd.Series) -> pd.Series:
    text = unit.fillna('').astype(str).str.casefold()
    factor = pd.Series(1.0, index=unit.index)

    # Examples in this repo: "current 000 US$", "current million US$",
    # "M.EUR", "nominal million euros".
    is_thousand = text.str.contains('000', regex=False) | text.str.contains('thousand', regex=False)
    factor.loc[is_thousand] = 1e-3

    is_million = text.str.contains('million', regex=False) | text.str.startswith('m.')
    factor.loc[is_million] = 1.0

    return factor


def _currency_flags(unit: pd.Series):
    text = unit.fillna('').astype(str).str.casefold().str.replace(' ', '', regex=False)
    is_eur = (
        text.str.contains('eur', regex=False)
        | text.str.contains('euro', regex=False)
    )
    is_usd = (
        text.str.contains('usd', regex=False)
        | text.str.contains('us$', regex=False)
        | text.str.contains(r'us\$', regex=True)
    )
    return is_eur, is_usd


def _standardized_unit_label(target_currency: str) -> str:
    return f'million {target_currency.upper()}'


def _normalize_rate_mapping(eur_usd_by_year):
    if eur_usd_by_year is None:
        return None
    if isinstance(eur_usd_by_year, dict):
        eur_usd_by_year = pd.Series(eur_usd_by_year)
    if not isinstance(eur_usd_by_year, pd.Series):
        raise TypeError('eur_usd_by_year must be a dict or pandas Series indexed by year')

    rates = eur_usd_by_year.copy()
    rates.index = pd.to_numeric(rates.index, errors='coerce').astype('Int64')
    rates = pd.to_numeric(rates, errors='coerce')
    return pd.Series(rates, name='EURUSD')


def _convert_currency(
    value: pd.Series,
    unit: pd.Series,
    year: pd.Series,
    target_currency: str,
    eur_usd_by_year=None,
):
    target = target_currency.upper()
    src = unit.fillna('').astype(str)
    numeric_value = pd.to_numeric(value, errors='coerce')

    factor = pd.Series(1.0, index=value.index)
    out_unit = src.copy()

    is_eur, is_usd = _currency_flags(src)

    if target not in {'USD', 'EUR'}:
        raise ValueError("target_currency must be 'EUR' or 'USD'")

    needs_conversion = (target == 'USD' and is_eur) | (target == 'EUR' and is_usd)
    monetary_mask = is_eur | is_usd

    # First normalize magnitude into millions for any monetary row.
    factor = factor * _unit_to_million_factor(src)

    eurusd = pd.Series(pd.NA, index=value.index, dtype='Float64')
    rates = _normalize_rate_mapping(eur_usd_by_year)
    if rates is not None:

        year_idx = pd.to_numeric(year, errors='coerce').astype('Int64')
        eurusd = year_idx.map(rates)

    if needs_conversion.any() and rates is None:
        raise ValueError(
            'Year-dependent FX conversion requires eur_usd_by_year mapping (Year -> EURUSD rate)'
        )

    missing_rate = needs_conversion & eurusd.isna()
    if missing_rate.any():
        missing_years = sorted(pd.to_numeric(year[missing_rate], errors='coerce').dropna().astype(int).unique())
        raise ValueError(f'Missing EURUSD rates for years: {missing_years}')

    if target == 'USD':
        factor.loc[is_eur] = eurusd.loc[is_eur].astype(float)
    elif target == 'EUR':
        factor.loc[is_usd] = 1.0 / eurusd.loc[is_usd].astype(float)

    out_value = numeric_value * factor
    out_unit.loc[monetary_mask] = _standardized_unit_label(target)
    return out_value, out_unit


def prepare_trade_comparison_dataframe(
    trades: pd.DataFrame,
    target_currency: str = 'USD',
    eur_usd_by_year=None,
    drop_unknown_iso3: bool = True,
) -> pd.DataFrame:
    """Standardize trade table for cross-database country comparison.

    Expected input columns:
    Name, Version, System, Year, Origin region, Destination region, Unit, Value
    """
    df = trades.copy()
    if 'Origin region' not in df.columns and 'Origin' in df.columns:
        df = df.rename(columns={'Origin': 'Origin region'})
    if 'Destination region' not in df.columns and 'Destination' in df.columns:
        df = df.rename(columns={'Destination': 'Destination region'})

    required = [
        'Name', 'Version', 'System', 'Year',
        'Origin region', 'Destination region', 'Unit', 'Value',
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    df['Database'] = _database_key(df)

    row_mask = _is_row(df['Origin region']) | _is_row(df['Destination region'])
    df = df.loc[~row_mask].copy()

    df['Origin ISO3'] = _to_iso3(df['Origin region'])
    df['Destination ISO3'] = _to_iso3(df['Destination region'])

    if drop_unknown_iso3:
        df = df[df['Origin ISO3'].notna() & df['Destination ISO3'].notna()].copy()

    df['Value'], df['Unit'] = _convert_currency(
        value=df['Value'],
        unit=df['Unit'],
        year=df['Year'],
        target_currency=target_currency,
        eur_usd_by_year=eur_usd_by_year,
    )
    df = df[df['Value'].notna()].copy()
    return df


def aggregate_country_trade_totals(df: pd.DataFrame, flow: str = 'exports') -> pd.DataFrame:
    """Aggregate total exports/imports/balance by ISO3 and Database."""
    flow = flow.lower()
    if flow not in {'exports', 'imports', 'balance'}:
        raise ValueError("flow must be one of: 'exports', 'imports', 'balance'")

    exports = (
        df.groupby(['Database', 'Year', 'Origin ISO3', 'Unit'], as_index=False)['Value']
        .sum()
        .rename(columns={'Origin ISO3': 'ISO3', 'Value': 'Exports'})
    )
    imports = (
        df.groupby(['Database', 'Year', 'Destination ISO3', 'Unit'], as_index=False)['Value']
        .sum()
        .rename(columns={'Destination ISO3': 'ISO3', 'Value': 'Imports'})
    )

    if flow == 'exports':
        out = exports.rename(columns={'Exports': 'Value'})
        return out[['Database', 'Year', 'ISO3', 'Unit', 'Value']]

    if flow == 'imports':
        out = imports.rename(columns={'Imports': 'Value'})
        return out[['Database', 'Year', 'ISO3', 'Unit', 'Value']]

    merged = exports.merge(imports, on=['Database', 'Year', 'ISO3', 'Unit'], how='outer').fillna(0)
    merged['Value'] = merged['Exports'] - merged['Imports']
    return merged[['Database', 'Year', 'ISO3', 'Unit', 'Value']]


def plot_trade_country_comparison(
    trades: pd.DataFrame,
    flow: str = 'exports',
    year: int | None = None,
    top_n_countries: int = 15,
):
    """Line comparison across databases for top countries by total trade."""
    agg = aggregate_country_trade_totals(trades, flow=flow)
    if year is not None:
        agg = agg[agg['Year'] == year].copy()

    if agg.empty:
        raise ValueError('No data available for selected filters')

    order = (
        agg.groupby('ISO3', as_index=False)['Value']
        .sum()
        .sort_values('Value', ascending=False)
        .head(top_n_countries)['ISO3']
        .tolist()
    )
    plot_df = agg[agg['ISO3'].isin(order)].copy()

    pivot = (
        plot_df.pivot_table(index='ISO3', columns='Database', values='Value', aggfunc='sum')
        .reindex(order)
    )

    fig, ax = plt.subplots(figsize=(14, 6))
    for col in pivot.columns:
        ax.plot(pivot.index, pivot[col], marker='o', linewidth=1.2, alpha=0.9, label=col)

    unit = plot_df['Unit'].dropna().astype(str).mode()
    unit_label = unit.iloc[0] if not unit.empty else 'value'
    flow_label = flow.capitalize()
    year_label = f' - {year}' if year is not None else ''
    ax.set_title(f'{flow_label} by country across databases{year_label}')
    ax.set_ylabel(f'{flow_label} ({unit_label})')
    ax.set_xlabel('ISO3 country')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(title='Database', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
    fig.tight_layout()
    return fig, ax, pivot


def plot_trade_balance_heatmap(
    trades: pd.DataFrame,
    year: int | None = None,
    top_n_countries: int = 20,
):
    """Heatmap of trade balance (exports-imports) by country and database."""
    bal = aggregate_country_trade_totals(trades, flow='balance')
    if year is not None:
        bal = bal[bal['Year'] == year].copy()

    if bal.empty:
        raise ValueError('No data available for selected filters')

    top = (
        bal.groupby('ISO3', as_index=False)['Value']
        .sum()
        .assign(abs_value=lambda d: d['Value'].abs())
        .sort_values('abs_value', ascending=False)
        .head(top_n_countries)['ISO3']
        .tolist()
    )
    piv = (
        bal[bal['ISO3'].isin(top)]
        .pivot_table(index='ISO3', columns='Database', values='Value', aggfunc='sum')
        .reindex(top)
    )

    fig, ax = plt.subplots(figsize=(14, 7))
    vmax = piv.abs().max().max()
    im = ax.imshow(piv.fillna(0).values, cmap='RdBu_r', aspect='auto', vmin=-vmax, vmax=vmax)

    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=45, ha='right')
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index)
    ax.set_title('Trade balance by country and database' + (f' - {year}' if year is not None else ''))

    cbar = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.02)
    unit = bal['Unit'].dropna().astype(str).mode()
    unit_label = unit.iloc[0] if not unit.empty else 'value'
    cbar.set_label(f'Balance ({unit_label})')

    fig.tight_layout()
    return fig, ax, piv


def build_trade_bar_dashboard(
    trades: pd.DataFrame,
    default_origin: str | None = None,
    default_destination: str | None = None,
    default_year: int | None = None,
    html_output_path: str | Path = 'plots/trade_dashboard.html',
):
    """Interactive bar chart with 3 dropdowns: Origin, Destination, Year.

    Expects preprocessed trades dataframe from prepare_trade_comparison_dataframe.
    """
    required = ['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Value', 'Unit']
    missing = [col for col in required if col not in trades.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    if px is None:
        raise ImportError('plotly is required. Install with: pip install plotly')
    if widgets is None or display is None:
        raise ImportError('ipywidgets is required. Install with: pip install ipywidgets')

    base = (
        trades.groupby(['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Unit'], as_index=False)['Value']
        .sum()
    )

    origins = sorted(base['Origin ISO3'].dropna().astype(str).unique().tolist())
    destinations = sorted(base['Destination ISO3'].dropna().astype(str).unique().tolist())
    years = sorted(pd.to_numeric(base['Year'], errors='coerce').dropna().astype(int).unique().tolist())

    if not origins or not destinations or not years:
        raise ValueError('No valid Origin/Destination/Year combinations found for plotting')

    origin_value = default_origin if default_origin in origins else origins[0]
    destination_value = (
        default_destination if default_destination in destinations else destinations[0]
    )
    year_value = int(default_year) if default_year in years else years[0]

    origin_dd = widgets.Dropdown(options=origins, value=origin_value, description='Origin')
    destination_dd = widgets.Dropdown(
        options=destinations,
        value=destination_value,
        description='Destination',
    )
    year_dd = widgets.Dropdown(options=years, value=year_value, description='Year')
    save_btn = widgets.Button(description='Save HTML', button_style='success')
    status = widgets.HTML(value='')
    out = widgets.Output()

    state = {'figure': None}

    def _build_subset():
        return base[
            (base['Origin ISO3'] == origin_dd.value)
            & (base['Destination ISO3'] == destination_dd.value)
            & (pd.to_numeric(base['Year'], errors='coerce').astype('Int64') == int(year_dd.value))
        ].copy()

    def _build_figure(subset):
        subset = subset.sort_values('Value', ascending=False)
        unit_mode = subset['Unit'].dropna().astype(str).mode()
        unit_label = unit_mode.iloc[0] if not unit_mode.empty else 'value'

        fig = px.bar(
            subset,
            x='Database',
            y='Value',
            color='Database',
            title=(
                f'Trade value by database | Origin={origin_dd.value} '
                f'-> Destination={destination_dd.value} | Year={year_dd.value}'
            ),
        )
        fig.update_layout(
            xaxis_title='Database',
            yaxis_title=f'Value ({unit_label})',
            showlegend=False,
            template='plotly_white',
        )
        return fig

    def _draw(_=None):
        subset = _build_subset()

        with out:
            out.clear_output(wait=True)

            if subset.empty:
                state['figure'] = None
                print('No data for selected Origin/Destination/Year.')
                return

            fig = _build_figure(subset)
            state['figure'] = fig
            fig.show()

    def _save_html(_):
        subset = _build_subset()
        if subset.empty:
            status.value = '<span style="color:#b00020;">No data to save for current selection.</span>'
            return

        fig = _build_figure(subset)
        output = Path(html_output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(output), include_plotlyjs='cdn', full_html=True)
        status.value = f'<span style="color:#0b7a0b;">Saved: {output}</span>'

    origin_dd.observe(_draw, names='value')
    destination_dd.observe(_draw, names='value')
    year_dd.observe(_draw, names='value')
    save_btn.on_click(_save_html)
    _draw()

    controls = widgets.HBox([origin_dd, destination_dd, year_dd, save_btn])
    return widgets.VBox([controls, status, out])


def export_trade_bar_html(
    trades: pd.DataFrame,
    origin: str,
    destination: str,
    year: int,
    output_path: str | Path = 'plots/trade_dashboard.html',
):
    """Export a single Origin/Destination/Year trade bar chart to HTML."""
    required = ['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Value', 'Unit']
    missing = [col for col in required if col not in trades.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if px is None:
        raise ImportError('plotly is required. Install with: pip install plotly')

    base = (
        trades.groupby(['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Unit'], as_index=False)['Value']
        .sum()
    )

    subset = base[
        (base['Origin ISO3'] == origin)
        & (base['Destination ISO3'] == destination)
        & (pd.to_numeric(base['Year'], errors='coerce').astype('Int64') == int(year))
    ].copy()

    if subset.empty:
        raise ValueError('No data for selected Origin/Destination/Year')

    subset = subset.sort_values('Value', ascending=False)
    unit_mode = subset['Unit'].dropna().astype(str).mode()
    unit_label = unit_mode.iloc[0] if not unit_mode.empty else 'value'

    fig = px.bar(
        subset,
        x='Database',
        y='Value',
        color='Database',
        title=f'Trade value by database | Origin={origin} -> Destination={destination} | Year={year}',
    )
    fig.update_layout(
        xaxis_title='Database',
        yaxis_title=f'Value ({unit_label})',
        showlegend=False,
        template='plotly_white',
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output), include_plotlyjs='cdn', full_html=True)
    return fig, output


def export_trade_region_grid_html(
    trades: pd.DataFrame,
    regions: list[str],
    output_path: str | Path = 'plots/trade_region_grid.html',
    title_prefix: str = 'Trade value by database',
    title: str | None = None,
    years: list[int] | None = None,
    min_abs_value: float | None = None,
    round_decimals: int = 3,
):
    """Export a region-by-region trade matrix with one subplot per origin/destination pair.

    Rows are origin regions, columns are destination regions. Markers are colored by
    database family (`Name + Version`), while hover text keeps the full database label.
    """
    required = ['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Value', 'Unit']
    missing = [col for col in required if col not in trades.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if go is None or make_subplots is None:
        raise ImportError('plotly is required. Install with: pip install plotly')

    base = trades.copy()
    base['Database detail'] = base['Database'].fillna('').astype(str).str.strip()
    base['Database family'] = _database_family_key(base)
    base = (
        base.groupby(
            [
                'Database family',
                'Database detail',
                'Origin ISO3',
                'Destination ISO3',
                'Year',
                'Unit',
            ],
            as_index=False,
        )['Value']
        .sum()
    )

    if base.empty:
        raise ValueError('No data available to build region grid dashboard')

    base['Year'] = pd.to_numeric(base['Year'], errors='coerce').astype('Int64')
    base = base[base['Year'].notna()].copy()
    base['Year'] = base['Year'].astype(int)

    if years is not None:
        keep_years = {int(y) for y in years}
        base = base[base['Year'].isin(keep_years)].copy()

    if min_abs_value is not None:
        base = base[base['Value'].abs() >= float(min_abs_value)].copy()

    if round_decimals is not None:
        base['Value'] = pd.to_numeric(base['Value'], errors='coerce').round(int(round_decimals))
        base = base[base['Value'].notna()].copy()

    base = base[
        base['Database family'].notna()
        & base['Database family'].astype(str).str.strip().ne('')
        & base['Database detail'].notna()
        & base['Database detail'].astype(str).str.strip().ne('')
    ].copy()

    available_regions = set(base['Origin ISO3'].dropna()) | set(base['Destination ISO3'].dropna())
    region_codes = _resolve_trade_regions(regions, available_regions)

    base = base[
        base['Origin ISO3'].isin(region_codes)
        & base['Destination ISO3'].isin(region_codes)
    ].copy()
    if base.empty:
        raise ValueError('No trade records remain for the selected regions')

    year_values = sorted(base['Year'].dropna().astype(int).unique().tolist())
    if not year_values:
        raise ValueError('No valid years remain for the selected regions')

    annual_mean = (
        base.groupby(['Origin ISO3', 'Destination ISO3', 'Year'], as_index=False)['Value']
        .mean()
        .rename(columns={'Value': 'Annual mean value'})
    )
    base = base.merge(
        annual_mean,
        on=['Origin ISO3', 'Destination ISO3', 'Year'],
        how='left',
    )
    base = base[base['Annual mean value'].abs() > 1e-12].copy()
    if base.empty:
        raise ValueError('Annual mean is zero for all selected region/year combinations')

    base['Deviation pct'] = (
        100.0 * (base['Value'] - base['Annual mean value']) / base['Annual mean value']
    )
    base = base[base['Deviation pct'].notna()].copy()
    if base.empty:
        raise ValueError('No valid percent deviations could be computed for the selected regions')

    family_order = (
        base[['Database family']]
        .drop_duplicates()
        .sort_values('Database family')['Database family']
        .tolist()
    )

    palette = [
        '#264653',
        '#E76F51',
        '#2A9D8F',
        '#E9C46A',
        '#457B9D',
        '#A8DADC',
        '#D62828',
        '#6D597A',
        '#F4A261',
        '#4D908E',
    ]
    color_map = {
        family: palette[idx % len(palette)]
        for idx, family in enumerate(family_order)
    }

    lookup = {
        key: group.sort_values('Database detail').reset_index(drop=True)
        for key, group in base.groupby(
            ['Origin ISO3', 'Destination ISO3', 'Database family'],
            sort=False,
        )
    }
    y_min = float(base['Deviation pct'].min())
    y_max = float(base['Deviation pct'].max())
    if y_min == y_max:
        delta = max(abs(y_min) * 0.01, 1e-6)
        global_y_range = [y_min - delta, y_max + delta]
    else:
        global_y_range = [y_min, y_max]

    def _build_trace(origin: str, destination: str, family: str):
        subset = lookup.get((origin, destination, family))
        if subset is None or subset.empty:
            x_vals = []
            y_vals = []
            custom = []
        else:
            subset = subset.sort_values(['Year', 'Database detail']).reset_index(drop=True)
            x_vals = subset['Year'].astype(int).tolist()
            y_vals = subset['Deviation pct'].astype(float).tolist()
            custom = [
                [
                    db,
                    family,
                    unit,
                    origin,
                    destination,
                    int(year_value),
                    float(value),
                    float(mean_value),
                ]
                for db, unit, year_value, value, mean_value in zip(
                    subset['Database detail'],
                    subset['Unit'],
                    subset['Year'],
                    subset['Value'],
                    subset['Annual mean value'],
                )
            ]

        return go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='markers',
            marker={
                'size': 10,
                'color': color_map[family],
                'line': {'width': 0.7, 'color': 'white'},
            },
            name=family,
            legendgroup=family,
            showlegend=False,
            customdata=custom,
            hovertemplate=(
                'Origin=%{customdata[3]}<br>'
                'Destination=%{customdata[4]}<br>'
                'Database=%{customdata[1]}<br>'
                'Series=%{customdata[0]}<br>'
                'Year=%{customdata[5]}<br>'
                'Deviation=%{y:.2f}%<br>'
                'Value=%{customdata[6]:.3f} %{customdata[2]}<br>'
                'Annual mean=%{customdata[7]:.3f} %{customdata[2]}'
                '<extra></extra>'
            ),
        )

    n_regions = len(region_codes)
    fig = make_subplots(
        rows=n_regions,
        cols=n_regions,
        shared_xaxes=False,
        shared_yaxes=False,
        horizontal_spacing=0.01 if n_regions <= 4 else 0.01,
        vertical_spacing=0.01 if n_regions <= 4 else 0.01,
        row_titles=region_codes,
        column_titles=region_codes,
    )

    for row_idx, origin in enumerate(region_codes, start=1):
        for col_idx, destination in enumerate(region_codes, start=1):
            for family in family_order:
                fig.add_trace(
                    _build_trace(origin, destination, family),
                    row=row_idx,
                    col=col_idx,
                )

            fig.update_xaxes(
                showticklabels=(row_idx == n_regions),
                showgrid=True,
                gridcolor='rgba(0, 0, 0, 0.06)',
                zeroline=False,
                title_text='',
                showline=True,
                linecolor='rgba(0, 0, 0, 0.24)',
                linewidth=1.0,
                mirror=True,
                tickmode='array',
                tickvals=year_values,
                tickangle=-90 if row_idx == n_regions else 0,
                range=[min(year_values) - 0.5, max(year_values) + 0.5],
                row=row_idx,
                col=col_idx,
            )
            fig.update_yaxes(
                title_text='',
                showticklabels=(col_idx == 1),
                showgrid=True,
                gridcolor='rgba(0, 0, 0, 0.08)',
                zeroline=True,
                zerolinecolor='rgba(0, 0, 0, 0.28)',
                zerolinewidth=1.0,
                showline=True,
                linecolor='rgba(0, 0, 0, 0.24)',
                linewidth=1.0,
                mirror=True,
                ticksuffix='%',
                range=global_y_range,
                row=row_idx,
                col=col_idx,
            )

    for family in family_order:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='markers',
                marker={
                    'size': 10,
                    'color': color_map[family],
                    'line': {'width': 0.7, 'color': 'white'},
                },
                name=family,
                legendgroup=family,
                showlegend=True,
                hoverinfo='skip',
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        title=title or (
            f'{title_prefix} | rows = origin, columns = destination | '
            f'colors = database (Name + Version) | y = % deviation from annual mean'
        ),
        template='plotly_white',
        height=max(170 * n_regions + 100, 500),
        margin={'t': 110, 'r': 170, 'b': 70, 'l': 80},
        legend={
            'title': {'text': ''},
            'orientation': 'v',
            'x': 1.02,
            'xanchor': 'left',
            'y': 1.0,
            'yanchor': 'top',
            'groupclick': 'togglegroup',
        },
    )
    fig.add_annotation(
        x=-0.065,
        y=0.5,
        xref='paper',
        yref='paper',
        text='% deviation from annual mean',
        textangle=-90,
        showarrow=False,
        font={'size': 13},
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output), include_plotlyjs='cdn', full_html=True)
    return output


def export_trade_dashboard_html(
    trades: pd.DataFrame,
    output_path: str | Path = 'plots/trade_dashboard.html',
    title_prefix: str = 'Trade value by database',
    title: str | None = None,
    years: list[int] | None = None,
    top_n_pairs: int | None = 400,
    min_abs_value: float | None = None,
    round_decimals: int = 3,
    regions: list[str] | None = None,
):
    """Export a standalone HTML dashboard.

    Default mode exports the original Origin/Destination/Year dropdown chart.
    When `regions` is provided, exports a region-by-region subplot matrix.
    `title`, when provided, overrides the chart title in both modes.
    """
    if regions is not None:
        return export_trade_region_grid_html(
            trades=trades,
            regions=regions,
            output_path=output_path,
            title_prefix=title_prefix,
            title=title,
            years=years,
            min_abs_value=min_abs_value,
            round_decimals=round_decimals,
        )

    required = ['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Value', 'Unit']
    missing = [col for col in required if col not in trades.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')

    base = (
        trades.groupby(['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Unit'], as_index=False)['Value']
        .sum()
    )

    if base.empty:
        raise ValueError('No data available to build dashboard')

    base['Year'] = pd.to_numeric(base['Year'], errors='coerce').astype('Int64')
    base = base[base['Year'].notna()].copy()
    base['Year'] = base['Year'].astype(int)

    if years is not None:
        keep_years = {int(y) for y in years}
        base = base[base['Year'].isin(keep_years)].copy()

    if min_abs_value is not None:
        base = base[base['Value'].abs() >= float(min_abs_value)].copy()

    if top_n_pairs is not None and top_n_pairs > 0:
        pair_rank = (
            base.groupby(['Origin ISO3', 'Destination ISO3'], as_index=False)['Value']
            .sum()
            .assign(abs_value=lambda d: d['Value'].abs())
            .sort_values('abs_value', ascending=False)
            .head(int(top_n_pairs))
        )
        base = base.merge(
            pair_rank[['Origin ISO3', 'Destination ISO3']],
            on=['Origin ISO3', 'Destination ISO3'],
            how='inner',
        )

    if round_decimals is not None:
        base['Value'] = pd.to_numeric(base['Value'], errors='coerce').round(int(round_decimals))
        base = base[base['Value'].notna()].copy()

    origins = sorted(base['Origin ISO3'].dropna().astype(str).unique().tolist())
    destinations = sorted(base['Destination ISO3'].dropna().astype(str).unique().tolist())
    years = sorted(base['Year'].dropna().astype(int).unique().tolist())

    if not origins or not destinations or not years:
        raise ValueError('No valid Origin/Destination/Year values found')

    records = base[['Database', 'Origin ISO3', 'Destination ISO3', 'Year', 'Value', 'Unit']].to_dict('records')

    payload = {
        'records': records,
        'origins': origins,
        'destinations': destinations,
        'years': years,
        'n_records': len(records),
        'title_prefix': title_prefix,
        'title': title,
        'default_origin': origins[0],
        'default_destination': destinations[0],
        'default_year': years[0],
    }

    page_title = title if title else 'Trade Dashboard'

    html_doc = f"""<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{page_title}</title>
    <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 16px; }}
        .controls {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }}
        .control {{ display: flex; flex-direction: column; min-width: 160px; }}
        label {{ font-size: 12px; color: #444; margin-bottom: 4px; }}
        select {{ padding: 6px; font-size: 14px; }}
        #status {{ margin-top: 6px; min-height: 20px; color: #666; }}
        #chart {{ width: 100%; height: 70vh; }}
    </style>
</head>
<body>
    <div class=\"controls\">
        <div class=\"control\">
            <label for=\"originSelect\">Origin</label>
            <select id=\"originSelect\"></select>
        </div>
        <div class=\"control\">
            <label for=\"destinationSelect\">Destination</label>
            <select id=\"destinationSelect\"></select>
        </div>
        <div class=\"control\">
            <label for=\"yearSelect\">Year</label>
            <select id=\"yearSelect\"></select>
        </div>
    </div>
    <div id=\"status\"></div>
    <div style=\"font-size:12px;color:#666;margin-bottom:8px;\">Loaded records: <span id=\"recordCount\"></span></div>
    <div id=\"chart\"></div>

    <script>
        const payload = {json.dumps(payload)};
        const records = payload.records;

        const originSelect = document.getElementById('originSelect');
        const destinationSelect = document.getElementById('destinationSelect');
        const yearSelect = document.getElementById('yearSelect');
        const status = document.getElementById('status');
        const recordCount = document.getElementById('recordCount');
        recordCount.textContent = payload.n_records;

        function fillSelect(selectEl, values, defaultValue) {{
            selectEl.innerHTML = '';
            values.forEach(v => {{
                const opt = document.createElement('option');
                opt.value = String(v);
                opt.textContent = String(v);
                if (String(v) === String(defaultValue)) opt.selected = true;
                selectEl.appendChild(opt);
            }});
        }}

        function render() {{
            const origin = originSelect.value;
            const destination = destinationSelect.value;
            const year = Number(yearSelect.value);
            const chartTitle = payload.title || `${{payload.title_prefix}} | Origin=${{origin}} -> Destination=${{destination}} | Year=${{year}}`;

            const filtered = records
                .filter(r => r['Origin ISO3'] === origin && r['Destination ISO3'] === destination && Number(r['Year']) === year)
                .sort((a, b) => Number(b.Value) - Number(a.Value));

            if (!filtered.length) {{
                status.textContent = 'No data for selected Origin/Destination/Year.';
                Plotly.react('chart', [], {{
                    title: chartTitle
                }}, {{responsive: true}});
                return;
            }}

            status.textContent = '';

            const x = filtered.map(r => r.Database);
            const y = filtered.map(r => Number(r.Value));
            const unit = filtered[0].Unit || 'value';

            const trace = {{
                type: 'bar',
                x,
                y,
                marker: {{ color: '#2C7BB6' }},
                hovertemplate: 'Database=%{{x}}<br>Value=%{{y:.3f}}<extra></extra>',
            }};

            const layout = {{
                title: chartTitle,
                xaxis: {{ title: 'Database' }},
                yaxis: {{ title: `Value (${{unit}})` }},
                template: 'plotly_white',
                margin: {{ t: 60, r: 20, b: 90, l: 80 }},
            }};

            Plotly.react('chart', [trace], layout, {{responsive: true}});
        }}

        fillSelect(originSelect, payload.origins, payload.default_origin);
        fillSelect(destinationSelect, payload.destinations, payload.default_destination);
        fillSelect(yearSelect, payload.years, payload.default_year);

        originSelect.addEventListener('change', render);
        destinationSelect.addEventListener('change', render);
        yearSelect.addEventListener('change', render);
        render();
    </script>
</body>
</html>
"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_doc, encoding='utf-8')
    return output

def main(cfg: Config | None = None):
    cfg = cfg or Config()
    load_inter_font(cfg.FONT_DIR)
    df = load_data(cfg)
    country_order = compute_country_order(df, cfg)
    fig = build_figure(df, country_order, cfg)

    fig.savefig(cfg.OUTPUT_FILE_png, dpi=cfg.DPI, bbox_inches="tight")
    fig.savefig(cfg.OUTPUT_FILE_svg, dpi=cfg.DPI, bbox_inches="tight")
    print(f"Grafici salvati: {cfg.OUTPUT_FILE_png} e {cfg.OUTPUT_FILE_svg}")
    return df, country_order, fig


if __name__ == "__main__":
    main()

# %%
