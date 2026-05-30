import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(page_title="Stabilization", page_icon="📉", layout="wide")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_PATH = os.path.join(ROOT_DIR, "..", "data", "processed")

st.markdown("""
<style>
.page-title {
    color: #C89B3C;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-shadow: 0 0 30px #C89B3C44;
}
.section-header {
    color: #C89B3C;
    font-size: 1.4rem;
    font-weight: 600;
    margin-top: 2rem;
    margin-bottom: 0.5rem;
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
.limitation-box {
    background: #1a1a0d;
    border: 1px solid #C89B3C44;
    border-left: 4px solid #C89B3C88;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #aaa;
    font-size: 0.95rem;
    line-height: 1.6;
}
.divider {
    border: none;
    border-top: 1px solid #ffffff15;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📉 Stage 3 — Stabilization Analysis</div>',
            unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

st.markdown("""
<div class="section-header">The Question</div>
<div class="body-text">
<p>
Detection told us that patch 10→11 produced real meta shifts. But detection alone 
doesn't tell us how the meta evolved <em>within</em> patch 11 after those shifts occurred.
</p>
<p>
When a patch drops, even top players are still experimenting. Compositions are being 
tested, itemization is being refined, and the optimal strategy hasn't yet been 
discovered. Over time, the best approaches emerge and the player base converges. 
That convergence is measurable — it shows up as <strong style="color:#C89B3C">
variance compression</strong> in placement outcomes.
</p>
<p>
High variance early in a patch means players are getting wildly different results 
running the same trait — some finishing 1st, others 7th. Low variance late in a 
patch means the meta has stabilized and outcomes are more predictable. Tracking this 
compression tells us how quickly high-elo players figured out the new optimal strategy 
after the patch dropped.
</p>
</div>
<hr class="divider">
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    stab = pd.read_csv(os.path.join(PROCESSED_PATH, "stabilization.csv"))
    return stab


stab = load_data()
traits = stab["trait"].unique().tolist()
display_names = {t: t.replace("TFT17_", "") for t in traits}

# Variance compression chart
st.markdown('<div class="section-header">Placement Variance Across Patch 11</div>',
            unsafe_allow_html=True)
st.markdown("""
<div class="body-text">
<p>
Each line tracks placement variance for one significant trait across three equal 
time windows within patch 11 — early, mid, and late. A downward trend indicates 
the meta stabilizing as players converge on optimal play.
</p>
</div>
""", unsafe_allow_html=True)

fig_variance = go.Figure()
colors = ["#C89B3C", "#2ecc71", "#e74c3c", "#3498db", "#9b59b6"]

for i, trait in enumerate(traits):
    data = stab[stab["trait"] == trait]
    fig_variance.add_trace(go.Scatter(
        x=data["bucket"],
        y=data["variance"],
        mode="lines+markers",
        name=display_names[trait],
        line=dict(color=colors[i % len(colors)], width=2.5),
        marker=dict(size=10),
        hovertemplate=(
            f"<b>{display_names[trait]}</b><br>" +
            "Period: %{x}<br>" +
            "Variance: %{y:.3f}<br>" +
            "<extra></extra>"
        )
    ))

fig_variance.update_layout(
    xaxis_title="Patch 11 Period",
    yaxis_title="Placement Variance",
    template="plotly_dark",
    height=450,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    legend=dict(orientation="v", x=1.02, y=1)
)

st.plotly_chart(fig_variance, use_container_width=True)

# Avg placement chart
st.markdown('<div class="section-header">Average Placement Across Patch 11</div>',
            unsafe_allow_html=True)
st.markdown("""
<div class="body-text">
<p>
Average placement over the same three windows. Compare with the variance chart above 
— a trait can maintain stable average placement while variance compresses, indicating 
players learned to execute it more consistently without it becoming stronger or weaker.
</p>
</div>
""", unsafe_allow_html=True)

fig_placement = go.Figure()

for i, trait in enumerate(traits):
    data = stab[stab["trait"] == trait]
    fig_placement.add_trace(go.Scatter(
        x=data["bucket"],
        y=data["avg_placement"],
        mode="lines+markers",
        name=display_names[trait],
        line=dict(color=colors[i % len(colors)], width=2.5),
        marker=dict(size=10),
        hovertemplate=(
            f"<b>{display_names[trait]}</b><br>" +
            "Period: %{x}<br>" +
            "Avg Placement: %{y:.3f}<br>" +
            "<extra></extra>"
        )
    ))

fig_placement.update_layout(
    xaxis_title="Patch 11 Period",
    yaxis_title="Average Placement (lower = better)",
    yaxis_autorange="reversed",
    template="plotly_dark",
    height=450,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    legend=dict(orientation="v", x=1.02, y=1)
)

st.plotly_chart(fig_placement, use_container_width=True)

# Per trait breakdown
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<div class="section-header">Per-Trait Stabilization Summary</div>',
            unsafe_allow_html=True)

selected_display = st.selectbox(
    "Select a trait",
    [display_names[t] for t in traits]
)
selected_trait = [t for t in traits if display_names[t] == selected_display][0]
trait_data = stab[stab["trait"] == selected_trait]

early = trait_data[trait_data["bucket"] == "Early"].iloc[0]
late = trait_data[trait_data["bucket"] == "Late"].iloc[0]
variance_change = late["variance"] - early["variance"]
placement_change = late["avg_placement"] - early["avg_placement"]

col1, col2, col3 = st.columns(3)
col1.metric(
    "Variance Change (Early→Late)",
    f"{variance_change:+.3f}",
    delta_color="inverse"
)
col2.metric(
    "Placement Change (Early→Late)",
    f"{placement_change:+.3f}",
    delta_color="inverse"
)
col3.metric(
    "Total Games Analyzed",
    f"{trait_data['game_count'].sum():,}"
)

display_df = trait_data[["bucket", "avg_placement", "variance", "game_count"]].copy()
display_df.columns = ["Period", "Avg Placement", "Variance", "Games"]
display_df = display_df.round(3)
st.dataframe(display_df, use_container_width=True, hide_index=True)

# Key findings
st.markdown('<hr class="divider">', unsafe_allow_html=True)
st.markdown('<div class="section-header">What This Tells Us</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="finding-box">
<strong>RhaastUniqueTrait never fully stabilized.</strong> Variance increased from 
Early to Late patch 11, suggesting players were still adapting to its post-nerf 
state throughout the entire patch window.
</div>
<div class="finding-box">
<strong>HPTank showed clear late-patch compression.</strong> After an initial spike 
in mid-patch variance, placement outcomes tightened significantly by late patch — 
players found the optimal way to build and position around it.
</div>
<div class="finding-box">
<strong>DarkStar stabilized quickly.</strong> The trait that improved most from 
patch 10→11 showed the fastest variance compression, suggesting its buff was 
straightforward for high-elo players to identify and execute.
</div>
""", unsafe_allow_html=True)

# Limitation note
st.markdown("""
<div class="limitation-box">
⚠️ <strong>Methodology note:</strong> Game ordering within patch 11 is approximated 
using Riot match ID sequencing rather than explicit timestamps. Match IDs are 
sequential within a region, making them a reliable proxy for game order, but 
true timestamps would allow finer-grained analysis. Future pipeline runs collect 
<code>game_datetime</code> directly from the API for improved precision.
</div>
""", unsafe_allow_html=True)