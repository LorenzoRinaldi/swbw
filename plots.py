#%%
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.font_manager as fm
from pathlib import Path


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
