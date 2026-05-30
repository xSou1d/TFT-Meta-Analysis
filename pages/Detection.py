import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Detection", page_icon="🔬", layout="wide")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(ROOT_DIR, "..", "data", "processed")

st.markdown("""
<style>
.section-header {
    color: #C89B3C;
    font-size: 1.4rem;
    font-weight: 600;
    margin-top: 2rem;
    margin-bottom: 0.5rem;
}
.page-title {
    color: #C89B3C;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-shadow: 0 0 30px #C89B3C44;
}
.body-text p {
    font-size: 1.05rem;
    line-height: 1.7;
    color: #e0e0e0;
}
.finding-box {
    background: linear-gradient(135deg, #1a1d2e 0%, #16213e 100%);
    border-left: 4px solid #C89B3C;
    border-radius: 8px;
    padding: 20px 24px;
    margin: 12px 0;
    color: #e0e0e0;
    font-size: 1rem;
    line-height: 1.6;
}
.finding-box strong {
    color: #C89B3C;
}
.divider {
    border: none;
    border-top: 1px solid #ffffff15;
    margin: 2rem 0;
}
.answer-box {
    background: linear-gradient(135deg, #0d1f0d 0%, #0a1a0a 100%);
    border: 1px solid #2ecc7166;
    border-left: 4px solid #2ecc71;
    border-radius: 8px;
    padding: 24px 28px;
    margin: 1.5rem 0;
    font-size: 1.1rem;
    color: #e0e0e0;
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">🔬 Stage 2 — Shift Detection</div>', unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

st.markdown("""
<div class="section-header">The Approach</div>
<div class="body-text">
<p>
For each trait that appeared at least 30 times per patch, we examine every consecutive 
patch pair and ask: did the average placement of players running this trait change 
meaningfully between patches?
</p>
<p>
Raw placement deltas alone are not enough — a trait played by 35 players showing a 
0.4 placement swing could easily be noise. Every candidate shift is validated using a 
<strong style="color:#C89B3C">permutation test</strong>: we pool placements from both 
patches, shuffle them randomly 1,000 times, and measure how often a random shuffle 
produces a delta as large as the one we observed. If that happens less than 5% of the 
time, the shift is real.
</p>
</div>
<hr class="divider">
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    trait_ts = pd.read_csv(os.path.join(PROCESSED_PATH, "trait_timeseries.csv"))
    shifts = pd.read_csv(os.path.join(PROCESSED_PATH, "significant_shifts.csv"))
    trait_ts["patch"] = trait_ts["patch"].astype(str)
    patch_order = sorted(trait_ts["patch"].unique(), key=lambda x: int(x))
    trait_ts["patch"] = pd.Categorical(
        trait_ts["patch"], categories=patch_order, ordered=True
    )
    trait_ts = trait_ts.sort_values("patch")
    return trait_ts, shifts


trait_ts, shifts = load_data()

# Sidebar filter
min_play = st.sidebar.slider("Minimum play count per patch", 5, 100, 30)
patch_count = trait_ts.groupby("trait")["patch"].nunique()
full_traits = patch_count[patch_count == trait_ts["patch"].nunique()].index
filtered = trait_ts[trait_ts["trait"].isin(full_traits)]
filtered = filtered.groupby("trait").filter(
    lambda x: x["play_count"].min() >= min_play
)
st.sidebar.markdown(f"**{filtered['trait'].nunique()}** traits analyzed")

# Heatmap
st.markdown('<div class="section-header">Trait Performance Across Patches</div>',
            unsafe_allow_html=True)
st.markdown("""
<div class="body-text">
<p>
Each cell shows the average placement of players running that trait in that patch. 
Green means stronger performance, red means weaker. Traits with visible color shifts 
between patches are candidates for significant meta changes.
</p>
</div>
""", unsafe_allow_html=True)

pivot = filtered.pivot(index="trait", columns="patch", values="avg_placement")
pivot.index = pivot.index.str.replace("TFT17_", "").str.replace("TFT15_", "")
pivot = pivot.sort_values(by=list(pivot.columns), ascending=True)

fig_heatmap = go.Figure(data=go.Heatmap(
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

fig_heatmap.update_layout(
    template="plotly_dark",
    height=650,
    margin=dict(l=180),
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117"
)

st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Significant shifts
st.markdown('<div class="section-header">Statistically Significant Shifts</div>',
            unsafe_allow_html=True)
st.markdown("""
<div class="body-text">
<p>
Of all patch transitions tested, only the <strong style="color:#C89B3C">patch 10→11 
transition</strong> produced statistically significant shifts. Five traits changed 
meaningfully — three got worse, two improved.
</p>
</div>
""", unsafe_allow_html=True)

shifts_plot = shifts.copy()
shifts_plot["label"] = shifts_plot["trait"].str.replace("TFT17_", "") + \
                        " (" + shifts_plot["patch_from"].astype(str) + \
                        "→" + shifts_plot["patch_to"].astype(str) + ")"
shifts_plot["color"] = shifts_plot["delta"].apply(
    lambda x: "#e74c3c" if x > 0 else "#2ecc71"
)

fig_shifts = go.Figure()
fig_shifts.add_trace(go.Bar(
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

fig_shifts.update_layout(
    xaxis_title="Placement Delta (positive = worse, negative = better)",
    template="plotly_dark",
    height=400,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117"
)

st.plotly_chart(fig_shifts, use_container_width=True)

# Key findings
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<div class="section-header">What This Tells Us</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="finding-box">
<strong>Patch 10→11 was a genuine balance intervention.</strong> Five traits shifted 
in ways that cannot be explained by random variance. High-elo players detectably 
changed their composition choices in response.
</div>
<div class="finding-box">
<strong>Patches 8→9 and 9→10 were stable.</strong> Some traits showed large raw 
deltas — SpaceGroove moved 0.41 placement positions between patches 8 and 9 — but 
none survived significance testing. These swings were noise, not signal.
</div>
<div class="finding-box">
<strong>The answer to the first half of the research question is yes.</strong> 
Patch changes do produce statistically detectable shifts in high-elo trait performance. 
But not every patch — only patches with meaningful balance changes cross the threshold.
</div>

<hr class="divider">

<div class="answer-box">
✓ &nbsp;<strong style="color:#2ecc71">Detection confirmed.</strong> &nbsp;High-elo 
players demonstrably shifted their composition choices at patch 10→11 in ways 
statistically distinguishable from normal variance. Navigate to 
<strong>Stabilization</strong> to see how quickly the new meta settled.
</div>
""", unsafe_allow_html=True)