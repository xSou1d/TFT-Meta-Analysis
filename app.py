import streamlit as st

st.set_page_config(
    page_title="TFT Meta Shift Detection",
    page_icon="🎮",
    layout="wide"
)

st.markdown("""
<style>
@keyframes twinkle {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 1; }
}
.hero-banner {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 40%, #1a0a2e 100%);
    border-radius: 16px;
    padding: 60px 40px;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    border: 1px solid #C89B3C44;
}
.hero-banner::before {
    content: '✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦';
    position: absolute;
    top: 10px;
    left: 0;
    right: 0;
    text-align: center;
    color: #C89B3C33;
    font-size: 1.2rem;
    letter-spacing: 8px;
    animation: twinkle 3s infinite;
}
.hero-banner::after {
    content: '✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦ ✧ ✦';
    position: absolute;
    bottom: 10px;
    left: 0;
    right: 0;
    text-align: center;
    color: #C89B3C33;
    font-size: 1.2rem;
    letter-spacing: 8px;
    animation: twinkle 3s infinite 1.5s;
}
.hero-title {
    font-size: 3.2rem;
    font-weight: 900;
    color: #C89B3C;
    letter-spacing: 2px;
    text-shadow: 0 0 40px #C89B3C66;
    margin: 0;
    line-height: 1.2;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #aaaaaa;
    margin-top: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
}
.hero-divider {
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #C89B3C, transparent);
    margin: 16px auto;
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
.metric-row {
    display: flex;
    gap: 20px;
    margin: 1.5rem 0;
}
.metric-box {
    background: #1a1d2e;
    border: 1px solid #C89B3C44;
    border-radius: 10px;
    padding: 20px 28px;
    flex: 1;
    text-align: center;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #C89B3C;
}
.metric-label {
    font-size: 0.85rem;
    color: #888;
    margin-top: 4px;
}
.research-question {
    background: linear-gradient(135deg, #1a1d2e 0%, #16213e 100%);
    border-left: 4px solid #C89B3C;
    border-radius: 8px;
    padding: 24px 28px;
    margin: 1.5rem 0;
    font-size: 1.15rem;
    font-style: italic;
    color: #e0e0e0;
    line-height: 1.7;
}
.stage-box {
    background: #1a1d2e;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 8px 0;
    border: 1px solid #ffffff11;
}
.stage-title {
    color: #C89B3C;
    font-weight: 600;
    font-size: 1rem;
}
.divider {
    border: none;
    border-top: 1px solid #ffffff15;
    margin: 2rem 0;
}
</style>

<div class="hero-banner">
    <div class="hero-title">TFT Meta Shift Detection</div>
    <div class="hero-divider"></div>
    <div class="hero-subtitle">High-Elo Behavioral Signal Extraction · Set 17 · NA Region</div>
</div>

<div class="section-header">The Question</div>
<div class="research-question">
When a TFT patch changes the balance of traits, do high-elo players demonstrably 
shift their composition choices in ways that are statistically distinguishable from 
normal variance — and how quickly does a new meta stabilize?
</div>

<hr class="divider">

<div class="section-header">Context</div>
<div class="body-text">
<p>
In Teamfight Tactics, the competitive landscape resets with every balance patch. 
High-elo players — those ranked Challenger and Grandmaster — are not passive observers 
of the meta. <strong style="color:#C89B3C">They create it.</strong> They are the first 
to identify what is strongest after a patch, and the rest of the ladder follows their lead.
</p>
<p>
This makes high-elo match data a uniquely valuable signal. Tracking the trait choices 
of the top 150 NA players over time is not just performance analysis — it is 
<strong style="color:#C89B3C">behavioral signal extraction</strong>. When these players 
shift their compositions en masse, something real has changed in the game's balance.
</p>
<p>
The question is whether those shifts are statistically real, or whether what looks like 
a meta change is just normal variance in a noisy game.
</p>
</div>

<hr class="divider">

<div class="section-header">Methodology</div>
<div class="stage-box">
    <div class="stage-title">Stage 1 — Feature Engineering</div>
    <p style="color:#aaa; margin:6px 0 0 0; font-size:0.95rem">
    Raw match records are transformed into a trait-level time series tracking 
    play rate, average placement, and top-4 rate for every trait across every patch.
    </p>
</div>
<div class="stage-box">
    <div class="stage-title">Stage 2 — Shift Detection</div>
    <p style="color:#aaa; margin:6px 0 0 0; font-size:0.95rem">
    Consecutive patch pairs are examined for placement delta. Each candidate shift 
    is validated using a permutation test — asking: is this change larger than what 
    we would expect by random chance alone?
    </p>
</div>
<div class="stage-box">
    <div class="stage-title">Stage 3 — Stabilization Analysis</div>
    <p style="color:#aaa; margin:6px 0 0 0; font-size:0.95rem">
    For patches where significant shifts are detected, placement variance is tracked 
    within the patch to measure how quickly the high-elo meta converges on a new 
    equilibrium after the balance change.
    </p>
</div>

<hr class="divider">

<div class="section-header">Data</div>
<div class="metric-row">
    <div class="metric-box">
        <div class="metric-value">~2,900</div>
        <div class="metric-label">Unique Ranked Matches</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">23,374</div>
        <div class="metric-label">Participant Records</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">4</div>
        <div class="metric-label">Patches Analyzed</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">150</div>
        <div class="metric-label">Top Players Tracked</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### Navigation")
st.sidebar.success("Use the pages above to follow the analysis from detection through findings.")