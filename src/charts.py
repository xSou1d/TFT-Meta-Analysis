"""
Static README figures (PNG) from the stats outputs.

    python -m src.stats            # writes data/processed/*.csv
    python -m src.charts           # writes figures/*.png

Figures:
    shift_forest.png     every tested patch-to-patch shift, with 95% CI, by significance
    meta_heatmap.png     EB-shrunk average placement, trait x patch
    elo_gap.png          per-trait high elo vs Gold/Plat gap, all patches pooled
"""
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(ROOT_DIR, "data", "processed")
FIG_DIR = os.path.join(ROOT_DIR, "figures")

# Palette (validated categorical slots + chart chrome)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GRAY = "#b5b3ab"
RED = "#e34948"
DIVERGING = LinearSegmentedColormap.from_list(
    "placement", ["#1c5cab", "#6da7ec", "#f0efec", "#ef8f8e", "#b8302f"])

from matplotlib import font_manager

_installed = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((f for f in ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"] if f in _installed),
            "sans-serif")

plt.rcParams.update({
    "font.family": FONT,
    "font.size": 10,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": AXIS,
    "axes.labelcolor": INK_2,
    "axes.titlecolor": INK,
    "axes.titleweight": "semibold",
    "axes.titlesize": 13,
    "axes.titlelocation": "left",
    "xtick.color": MUTED,
    "ytick.color": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": SURFACE,
})


SET_PREFIX = ""  # filled in main() from the raw data, e.g. "18."


def patch_label(p):
    return f"{SET_PREFIX}{p}"


def pretty_trait(name):
    # Prefixes vary by set: "TFT17_Rhaast..." (Set 17); Set 18 uses both
    # "DA_18_Battlemage" and "DA_Juggernaut18"
    n = re.sub(r"^(TFT\d+|[A-Z]+_\d+|[A-Z]+)_", "", str(name))
    n = re.sub(r"(?<=[a-z])\d+$", "", n)
    n = re.sub(r"_?UniqueTrait", " (Unique)", n)
    return n.replace("Trait", "").replace("_", " ").strip()


def _subtitle(ax, text):
    # Anchored in points above the axes so it sits under the title at any figure height
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction", xytext=(0, 6),
                textcoords="offset points", color=INK_2, fontsize=9.5, va="bottom")


def shift_forest(shifts, path, top_n=20):
    """Dot + CI per shift. Colour = how much evidence survives correction.

    Shows the top_n tests by p-value so the chart stays readable; the subtitle
    says how many tests were run in total (the correction uses all of them).
    """
    n_tests = len(shifts)
    df = shifts.nsmallest(top_n, "p_value").copy()
    df["label"] = (df["trait"].map(pretty_trait) + "  " + df["patch_from"].astype(str).map(patch_label)
                   + " → " + df["patch_to"].astype(str).map(patch_label))
    df["status"] = np.select(
        [df["q_value_bh"] < 0.05, df["p_value"] < 0.05],
        ["Significant after FDR correction", "p < 0.05 before correction only"],
        "Not significant")
    df = df.sort_values("delta").reset_index(drop=True)
    colors = {"Significant after FDR correction": BLUE,
              "p < 0.05 before correction only": ORANGE,
              "Not significant": GRAY}

    fig, ax = plt.subplots(figsize=(8.5, 0.28 * len(df) + 1.6))
    y = np.arange(len(df))
    ax.axvline(0, color=AXIS, lw=1, zorder=1)
    for status, c in colors.items():
        m = df["status"] == status
        ax.hlines(y[m], df.loc[m, "delta_lo"], df.loc[m, "delta_hi"], color=c, lw=2, zorder=2)
        ax.scatter(df.loc[m, "delta"], y[m], s=36, color=c, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    ax.set_yticks(y, df["label"], fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Change in average placement   ← better  ·  worse →")
    ax.set_title("Which traits shifted between patches?", pad=22)
    _subtitle(ax, f"High-elo NA · {top_n} strongest of {n_tests} tests shown · 95% bootstrap CI · "
                  "Benjamini-Hochberg correction across all tests")
    handles = [Line2D([], [], marker="o", color=c, lw=2, markersize=6, label=s) for s, c in colors.items()]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK_2)
    fig.savefig(path)
    plt.close(fig)


def meta_heatmap(summary, path, min_games=30, max_traits=25):
    """EB-shrunk average placement; blue = better than 4.5, red = worse."""
    df = summary[summary["n"] >= min_games].copy()
    df["trait_name"] = df["trait"].map(pretty_trait)
    df["patch"] = df["patch"].astype(str)
    # Keep the most-played traits so the chart stays readable
    top = df.groupby("trait_name")["n"].sum().nlargest(max_traits).index
    pivot = (df[df["trait_name"].isin(top)]
             .pivot(index="trait_name", columns="patch", values="eb_avg_placement"))
    pivot = pivot[sorted(pivot.columns, key=lambda p: [int(x) for x in p.split(".") if x.isdigit()])]
    pivot = pivot.loc[pivot.mean(axis=1).sort_values().index]

    fig, ax = plt.subplots(figsize=(1.1 * pivot.shape[1] + 3.2, 0.32 * len(pivot) + 1.8))
    lim = max(0.6, np.nanmax(np.abs(pivot.values - 4.5)))
    norm = TwoSlopeNorm(vcenter=4.5, vmin=4.5 - lim, vmax=4.5 + lim)
    im = ax.imshow(pivot.values, cmap=DIVERGING, norm=norm, aspect="auto")
    # 2px surface gap between cells
    ax.set_xticks(np.arange(-.5, pivot.shape[1]), minor=True)
    ax.set_yticks(np.arange(-.5, pivot.shape[0]), minor=True)
    ax.grid(which="minor", color=SURFACE, lw=2)
    ax.tick_params(which="minor", length=0)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            if np.isfinite(v):
                dark_cell = abs(v - 4.5) > 0.65 * lim
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                        color=SURFACE if dark_cell else INK)
    ax.set_xticks(range(pivot.shape[1]), [f"Patch {patch_label(p)}" for p in pivot.columns])
    ax.set_yticks(range(pivot.shape[0]), pivot.index, fontsize=8.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Trait strength by patch", pad=22)
    _subtitle(ax, f"Average placement, empirical-Bayes shrunk. Blue = better than 4.5. Traits with ≥{min_games} games.")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, length=0)
    cb.set_label("Avg placement (lower = better)", color=INK_2)
    fig.savefig(path)
    plt.close(fig)


def elo_gap(pooled, path):
    """Per-trait gap between Gold/Plat and high elo, relative to each tier's baseline.

    Right of zero = relatively weaker in Gold/Plat, i.e. a trait that rewards
    high-elo execution. Left = a trait that over-performs in lower tiers.
    """
    df = pooled.copy()
    df["label"] = df["trait"].map(pretty_trait)
    df = df.sort_values("gap").reset_index(drop=True)
    colors = {"Stronger at high elo": BLUE, "Stronger in Gold/Plat": ORANGE,
              "No clear difference": GRAY}

    fig, ax = plt.subplots(figsize=(8.5, 0.27 * len(df) + 1.6))
    y = np.arange(len(df))
    ax.axvline(0, color=AXIS, lw=1, zorder=1)
    for pattern, c in colors.items():
        m = df["pattern"] == pattern
        ax.hlines(y[m], df.loc[m, "gap_lo"], df.loc[m, "gap_hi"], color=c, lw=2, zorder=2)
        ax.scatter(df.loc[m, "gap"], y[m], s=36, color=c, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    ax.set_yticks(y, df["label"], fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Gold/Plat minus high elo, placement vs. each tier's baseline\n"
                  "← over-performs in Gold/Plat  ·  rewards high-elo play →")
    ax.set_title("Is a trait strong at every rank?", pad=22)
    _subtitle(ax, f"Set {SET_PREFIX.rstrip('.')} · all patches pooled · 95% bootstrap CI · "
                  "colour = significant after FDR correction")
    handles = [Line2D([], [], marker="o", color=c, lw=2, markersize=6, label=s) for s, c in colors.items()]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8.5, labelcolor=INK_2)
    fig.savefig(path)
    plt.close(fig)


def main():
    global SET_PREFIX
    os.makedirs(FIG_DIR, exist_ok=True)
    from src.features import RAW_PATH
    raw_sets = pd.read_csv(RAW_PATH, usecols=lambda c: c == "set_number")
    if "set_number" in raw_sets and raw_sets["set_number"].notna().any():
        SET_PREFIX = f"{int(raw_sets['set_number'].mode()[0])}."
    shifts = pd.read_csv(os.path.join(PROCESSED, "shift_tests.csv"))
    shift_forest(shifts, os.path.join(FIG_DIR, "shift_forest.png"))
    summary = pd.read_csv(os.path.join(PROCESSED, "trait_summary.csv"))
    meta_heatmap(summary, os.path.join(FIG_DIR, "meta_heatmap.png"))
    made = ["shift_forest.png", "meta_heatmap.png"]
    gap_path = os.path.join(PROCESSED, "tier_gap_pooled.csv")
    if os.path.exists(gap_path):
        elo_gap(pd.read_csv(gap_path), os.path.join(FIG_DIR, "elo_gap.png"))
        made.append("elo_gap.png")
    print(f"Wrote {', '.join(made)} to {FIG_DIR}")


if __name__ == "__main__":
    main()
