import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")
FIGURES_PATH = os.path.join(ROOT_DIR, "figures")


def setup():
    os.makedirs(FIGURES_PATH, exist_ok=True)
    sns.set_theme(style="darkgrid")
    plt.rcParams["figure.figsize"] = (12, 6)


def plot_trait_trajectories(trait_ts, traits_to_plot):
    """Line chart of avg_placement over patches for selected traits."""
    fig, ax = plt.subplots()

    for trait in traits_to_plot:
        data = trait_ts[trait_ts["trait"] == trait].sort_values("patch")
        label = trait.replace("TFT17_", "")
        ax.plot(data["patch"].astype(str), data["avg_placement"],
                marker="o", label=label, linewidth=2)

    ax.set_title("Trait Performance Trajectories Across Patches", fontsize=14)
    ax.set_xlabel("Patch")
    ax.set_ylabel("Average Placement (lower = better)")
    ax.invert_yaxis()
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_PATH, "trait_trajectories.png"), dpi=150)
    plt.close()
    print("Saved trait_trajectories.png")


def plot_significant_shifts(shifts):
    """Bar chart of significant shift deltas."""
    fig, ax = plt.subplots()

    shifts = shifts.copy()
    shifts["label"] = shifts["trait"].str.replace("TFT17_", "") + \
                      "\n(" + shifts["patch_from"].astype(str) + \
                      "→" + shifts["patch_to"].astype(str) + ")"
    colors = ["#e74c3c" if d > 0 else "#2ecc71" for d in shifts["delta"]]

    bars = ax.barh(shifts["label"], shifts["delta"], color=colors)
    ax.axvline(x=0, color="white", linewidth=0.8)
    ax.set_title("Statistically Significant Meta Shifts (p < 0.05)", fontsize=14)
    ax.set_xlabel("Placement Delta (positive = worse, negative = better)")

    for bar, p in zip(bars, shifts["p_value"]):
        width = bar.get_width()
        ax.text(width + 0.005 if width >= 0 else width - 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"p={p:.3f}", va="center",
                ha="left" if width >= 0 else "right", fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_PATH, "significant_shifts.png"), dpi=150)
    plt.close()
    print("Saved significant_shifts.png")


def plot_play_rates(trait_ts, traits_to_plot):
    """Line chart of play count over patches for significant traits."""
    fig, ax = plt.subplots()

    for trait in traits_to_plot:
        data = trait_ts[trait_ts["trait"] == trait].sort_values("patch")
        label = trait.replace("TFT17_", "")
        ax.plot(data["patch"].astype(str), data["play_count"],
                marker="o", label=label, linewidth=2)

    ax.set_title("Play Rate of Significant Traits Across Patches", fontsize=14)
    ax.set_xlabel("Patch")
    ax.set_ylabel("Play Count")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_PATH, "play_rates.png"), dpi=150)
    plt.close()
    print("Saved play_rates.png")


if __name__ == "__main__":
    setup()

    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    shifts = pd.read_csv(os.path.join(PROCESSED_PATH, "significant_shifts.csv"))

    significant_traits = shifts["trait"].unique().tolist()

    plot_trait_trajectories(trait_ts, significant_traits)
    plot_significant_shifts(shifts)
    plot_play_rates(trait_ts, significant_traits)

    print("\nAll figures saved to /figures")