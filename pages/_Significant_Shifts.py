import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Significant Shifts", page_icon="📊", layout="wide")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(ROOT_DIR, "..", "data", "processed")


@st.cache_data
def load_data():
    shifts = pd.read_csv(os.path.join(PROCESSED_PATH, "significant_shifts.csv"))
    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    trait_ts["patch"] = trait_ts["patch"].astype(str)
    patch_order = sorted(trait_ts["patch"].unique(), key=lambda x: int(x))
    trait_ts["patch"] = pd.Categorical(trait_ts["patch"], categories=patch_order, ordered=True)
    trait_ts = trait_ts.sort_values("patch")
    return shifts, trait_ts


st.title("📊 Significant Shifts")
st.markdown("""
Shifts validated using a **permutation test** (1,000 permutations). 
Only shifts with **p < 0.05** are shown.
""")

shifts, trait_ts = load_data()

# Bar chart
shifts_plot = shifts.copy()
shifts_plot["label"] = shifts_plot["trait"].str.replace("TFT17_", "") + \
                        " (" + shifts_plot["patch_from"].astype(str) + \
                        "→" + shifts_plot["patch_to"].astype(str) + ")"
shifts_plot["color"] = shifts_plot["delta"].apply(
    lambda x: "#e74c3c" if x > 0 else "#2ecc71"
)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=shifts_plot["delta"],
    y=shifts_plot["label"],
    orientation="h",
    marker_color=shifts_plot["color"],
    hovertemplate=(
        "<b>%{y}</b><br>" +
        "Delta: %{x:.4f}<br>" +
        "p-value: " + shifts_plot["p_value"].round(3).astype(str) +
        "<extra></extra>"
    )
))

fig.update_layout(
    title="Statistically Significant Meta Shifts (p < 0.05)",
    xaxis_title="Placement Delta (positive = worse, negative = better)",
    template="plotly_dark",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# Interpretation
st.markdown("---")
st.subheader("Interpretation")
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📈 Traits that got worse (patch 10→11)")
    worse = shifts[shifts["delta"] > 0].sort_values("delta", ascending=False)
    for _, row in worse.iterrows():
        trait_name = row["trait"].replace("TFT17_", "")
        st.markdown(f"**{trait_name}** — placement worsened by "
                    f"`{row['delta']:.3f}` (p={row['p_value']:.3f})")

with col2:
    st.markdown("#### 📉 Traits that got better (patch 10→11)")
    better = shifts[shifts["delta"] < 0].sort_values("delta")
    for _, row in better.iterrows():
        trait_name = row["trait"].replace("TFT17_", "")
        st.markdown(f"**{trait_name}** — placement improved by "
                    f"`{abs(row['delta']):.3f}` (p={row['p_value']:.3f})")

# Full results table
st.markdown("---")
st.subheader("Full Results Table")
display_df = shifts[["trait", "patch_from", "patch_to",
                      "placement_before", "placement_after",
                      "delta", "p_value"]].copy()
display_df["trait"] = display_df["trait"].str.replace("TFT17_", "")
display_df.columns = ["Trait", "From Patch", "To Patch",
                       "Placement Before", "Placement After",
                       "Delta", "P-Value"]
display_df = display_df.round(4)
st.dataframe(display_df, use_container_width=True)