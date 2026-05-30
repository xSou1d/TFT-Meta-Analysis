import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Trait Explorer", page_icon="🔍", layout="wide")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(ROOT_DIR, "..", "data", "processed")


@st.cache_data
def load_data():
    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    shifts = pd.read_csv(os.path.join(PROCESSED_PATH, "significant_shifts.csv"))
    trait_ts["patch"] = trait_ts["patch"].astype(str)
    patch_order = sorted(trait_ts["patch"].unique(), key=lambda x: int(x))
    trait_ts["patch"] = pd.Categorical(trait_ts["patch"], categories=patch_order, ordered=True)
    trait_ts = trait_ts.sort_values("patch")
    return trait_ts, shifts


st.title("🔍 Trait Explorer")
st.markdown("Select any trait to explore its performance trajectory, play rate, and significance results.")

trait_ts, shifts = load_data()

trait_names = sorted(trait_ts["trait"].unique())
display_names = [t.replace("TFT17_", "").replace("TFT15_", "") for t in trait_names]
name_map = dict(zip(display_names, trait_names))

selected_display = st.selectbox("Select a trait", display_names)
selected_trait = name_map[selected_display]

data = trait_ts[trait_ts["trait"] == selected_trait].sort_values("patch")

# Metrics row
st.markdown("---")
col1, col2, col3 = st.columns(3)
col1.metric("Best Avg Placement", f"{data['avg_placement'].min():.3f}",
            f"Patch {data.loc[data['avg_placement'].idxmin(), 'patch']}")
col2.metric("Best Top-4 Rate", f"{data['top4_rate'].max():.1%}",
            f"Patch {data.loc[data['top4_rate'].idxmax(), 'patch']}")
col3.metric("Peak Play Count", f"{data['play_count'].max():,}",
            f"Patch {data.loc[data['play_count'].idxmax(), 'patch']}")

# Charts
fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("Average Placement Over Patches",
                                    "Play Count Over Patches"),
                    vertical_spacing=0.15)

fig.add_trace(go.Scatter(
    x=data["patch"].astype(str),
    y=data["avg_placement"],
    mode="lines+markers",
    name="Avg Placement",
    line=dict(color="#4ecdc4", width=3),
    marker=dict(size=10),
    hovertemplate="Patch %{x}<br>Avg Placement: %{y:.3f}<extra></extra>"
), row=1, col=1)

fig.add_trace(go.Bar(
    x=data["patch"].astype(str),
    y=data["play_count"],
    name="Play Count",
    marker_color="#45b7d1",
    hovertemplate="Patch %{x}<br>Play Count: %{y}<extra></extra>"
), row=2, col=1)

fig.update_yaxes(autorange="reversed", row=1, col=1)
fig.update_layout(
    template="plotly_dark",
    height=600,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# Significance results for this trait
st.markdown("---")
st.subheader("Significance Testing Results")
trait_shifts = shifts[shifts["trait"] == selected_trait]

if trait_shifts.empty:
    st.info("No statistically significant shifts detected for this trait.")
else:
    st.success(f"**{len(trait_shifts)}** significant shift(s) detected for this trait.")
    display_df = trait_shifts[["patch_from", "patch_to", "placement_before",
                                "placement_after", "delta", "p_value"]].copy()
    display_df.columns = ["From Patch", "To Patch", "Placement Before",
                          "Placement After", "Delta", "P-Value"]
    display_df = display_df.round(4)
    st.dataframe(display_df, use_container_width=True)