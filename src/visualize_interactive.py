import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")
FIGURES_PATH = os.path.join(ROOT_DIR, "figures", "interactive")


def setup():
    os.makedirs(FIGURES_PATH, exist_ok=True)


def plot_trait_trajectories(trait_ts):
    """Interactive line chart of avg_placement over patches for all filtered traits."""
    fig = go.Figure()

    traits = trait_ts["trait"].unique()
    for trait in traits:
        data = trait_ts[trait_ts["trait"] == trait].sort_values("patch")
        label = trait.replace("TFT17_", "")
        fig.add_trace(go.Scatter(
            x=data["patch"].astype(str),
            y=data["avg_placement"],
            mode="lines+markers",
            name=label,
            hovertemplate=(
                f"<b>{label}</b><br>" +
                "Patch: %{x}<br>" +
                "Avg Placement: %{y:.3f}<br>" +
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        title="Trait Performance Trajectories Across Patches",
        xaxis_title="Patch",
        yaxis_title="Average Placement (lower = better)",
        yaxis_autorange="reversed",
        legend=dict(
            orientation="v",
            x=1.02,
            y=1
        ),
        hovermode="x unified",
        template="plotly_dark",
        height=600
    )

    path = os.path.join(FIGURES_PATH, "trait_trajectories.html")
    fig.write_html(path)
    print("Saved trait_trajectories.html")


def plot_significant_shifts(shifts):
    """Interactive horizontal bar chart of significant shifts."""
    shifts = shifts.copy()
    shifts["label"] = shifts["trait"].str.replace("TFT17_", "") + \
                      " (" + shifts["patch_from"].astype(str) + \
                      "→" + shifts["patch_to"].astype(str) + ")"
    shifts["color"] = shifts["delta"].apply(lambda x: "#e74c3c" if x > 0 else "#2ecc71")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=shifts["delta"],
        y=shifts["label"],
        orientation="h",
        marker_color=shifts["color"],
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Delta: %{x:.4f}<br>" +
            "p-value: " + shifts["p_value"].round(3).astype(str) +
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title="Statistically Significant Meta Shifts (p < 0.05)",
        xaxis_title="Placement Delta (positive = worse, negative = better)",
        template="plotly_dark",
        height=500
    )

    path = os.path.join(FIGURES_PATH, "significant_shifts.html")
    fig.write_html(path)
    print("Saved significant_shifts.html")


def plot_play_rates(trait_ts):
    """Interactive line chart of play count over patches."""
    fig = go.Figure()

    traits = trait_ts["trait"].unique()
    for trait in traits:
        data = trait_ts[trait_ts["trait"] == trait].sort_values("patch")
        label = trait.replace("TFT17_", "")
        fig.add_trace(go.Scatter(
            x=data["patch"].astype(str),
            y=data["play_count"],
            mode="lines+markers",
            name=label,
            hovertemplate=(
                f"<b>{label}</b><br>" +
                "Patch: %{x}<br>" +
                "Play Count: %{y}<br>" +
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        title="Play Rate of Traits Across Patches",
        xaxis_title="Patch",
        yaxis_title="Play Count",
        legend=dict(orientation="v", x=1.02, y=1),
        hovermode="x unified",
        template="plotly_dark",
        height=600
    )

    path = os.path.join(FIGURES_PATH, "play_rates.html")
    fig.write_html(path)
    print("Saved play_rates.html")


def plot_heatmap(trait_ts):
    """Interactive heatmap of avg_placement across all traits and patches."""
    # Only include traits that appear in all patches
    patch_count = trait_ts.groupby("trait")["patch"].nunique()
    full_traits = patch_count[patch_count == trait_ts["patch"].nunique()].index
    filtered = trait_ts[trait_ts["trait"].isin(full_traits)]

    pivot = filtered.pivot(index="trait", columns="patch", values="avg_placement")
    pivot.index = pivot.index.str.replace("TFT17_", "").str.replace("TFT15_", "")
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=True)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"Patch {p}" for p in pivot.columns],
        y=pivot.index,
        colorscale="RdYlGn_r",
        zmid=4.5,
        hoverongaps=False,
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "%{x}<br>" +
            "Avg Placement: %{z:.3f}<br>" +
            "<extra></extra>"
        ),
        colorbar=dict(title="Avg Placement")
    ))

    fig.update_layout(
        title="Trait Performance Heatmap (lower placement = stronger trait)",
        xaxis_title="Patch",
        yaxis_title="Trait",
        template="plotly_dark",
        height=700,
        margin=dict(l=180)
    )

    path = os.path.join(FIGURES_PATH, "trait_heatmap.html")
    fig.write_html(path)
    print("Saved trait_heatmap.html")


if __name__ == "__main__":
    setup()

    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    patch_order = sorted(trait_ts["patch"].unique(), key=lambda x: int(x))
    trait_ts["patch"] = pd.Categorical(trait_ts["patch"], categories=patch_order, ordered=True)
    trait_ts = trait_ts.sort_values("patch")

    shifts = pd.read_csv(os.path.join(PROCESSED_PATH, "significant_shifts.csv"))

    plot_trait_trajectories(trait_ts)
    plot_significant_shifts(shifts)
    plot_play_rates(trait_ts)
    plot_heatmap(trait_ts)

    print("\nAll interactive figures saved to /figures/interactive")