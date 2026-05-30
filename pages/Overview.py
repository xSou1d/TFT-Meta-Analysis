import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Overview", page_icon="🗺️", layout="wide")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(ROOT_DIR, "..", "data", "processed")


@st.cache_data
def load_data():
    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    trait_ts["patch"] = trait_ts["patch"].astype(str)
    patch_order = sorted(trait_ts["patch"].unique(), key=lambda x: int(x))
    trait_ts["patch"] = pd.Categorical(trait_ts["patch"], categories=patch_order, ordered=True)
    trait_ts = trait_ts.sort_values("patch")
    return trait_ts


st.title("🗺️ Overview")
st.markdown("Trait performance across all patches. Hover over any cell to see exact placement values.")

trait_ts = load_data()

# Sidebar filters
min_play = st.sidebar.slider("Minimum play count per patch", 5, 100, 30)

# Filter traits
patch_count = trait_ts.groupby("trait")["patch"].nunique()
full_traits = patch_count[patch_count == trait_ts["patch"].nunique()].index
filtered = trait_ts[trait_ts["trait"].isin(full_traits)]
filtered = filtered.groupby("trait").filter(lambda x: x["play_count"].min() >= min_play)

st.sidebar.markdown(f"**{filtered['trait'].nunique()}** traits shown")

# Heatmap
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

st.plotly_chart(fig, use_container_width=True)

# Summary stats
st.markdown("---")
st.subheader("Summary Statistics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Matches", "~2,900")
col2.metric("Participant Records", "23,374")
col3.metric("Patches Analyzed", "4")
col4.metric("Unique Traits", str(trait_ts["trait"].nunique()))