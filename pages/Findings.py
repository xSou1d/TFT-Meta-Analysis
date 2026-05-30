import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Findings", page_icon="📋", layout="wide")

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
.body-text p {
    font-size: 1.05rem;
    line-height: 1.7;
    color: #e0e0e0;
}
.divider {
    border: none;
    border-top: 1px solid #ffffff15;
    margin: 2rem 0;
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📋 Findings & Conclusions</div>',
            unsafe_allow_html=True)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Restate the question
st.markdown("""
<div class="section-header">The Question Revisited</div>
<div class="body-text">
<p>
We set out to answer: <em>When a TFT patch changes the balance of traits, do 
high-elo players demonstrably shift their composition choices in ways that are 
statistically distinguishable from normal variance — and how quickly does a new 
meta stabilize?</em>
</p>
</div>
""", unsafe_allow_html=True)

# The answer
st.markdown("""
<div class="answer-box">
✓ &nbsp;<strong style="color:#2ecc71">Yes — with an important nuance.</strong>
&nbsp; Patch changes do produce statistically detectable shifts in high-elo trait 
performance, but only when the balance change is meaningful enough to cross the 
threshold of statistical significance. Of four patch transitions analyzed, only 
one — patch 10→11 — produced genuine meta shifts. The other transitions showed 
variance-driven fluctuations that did not survive significance testing.
<br><br>
Once a real shift occurs, stabilization is trait-dependent. Some traits settle 
quickly as players identify optimal execution. Others remain volatile throughout 
the patch as the player base continues to adapt.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Key findings
st.markdown('<div class="section-header">Key Findings</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="finding-box">
<strong>Finding 1 — Not every patch creates a new meta.</strong> Patches 8→9 and 
9→10 showed large raw placement deltas for some traits but none survived permutation 
testing. The high-elo meta was stable across these transitions, consistent with 
top players adapting quickly to minor balance adjustments.
</div>

<div class="finding-box">
<strong>Finding 2 — Patch 10→11 was a genuine balance intervention.</strong> Five 
traits shifted significantly — RhaastUniqueTrait, DRX, and HPTank were weakened 
while DarkStar and FlexTrait improved. These shifts are statistically 
indistinguishable from random chance less than 5% of the time.
</div>

<div class="finding-box">
<strong>Finding 3 — Stabilization speed varies by trait.</strong> DarkStar — the 
most improved trait — stabilized fastest, suggesting its buff was immediately 
identifiable and easy to execute. RhaastUniqueTrait — the most nerfed — never 
fully stabilized within the patch window, indicating ongoing adaptation throughout.
</div>

<div class="finding-box">
<strong>Finding 4 — High-elo players are a leading indicator.</strong> The 
compression of placement variance over time within a patch confirms that top 
players converge on optimal strategies faster than the broader player base. 
Tracking their behavior provides an early signal of where the meta is heading.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Summary stats
st.markdown('<div class="section-header">Study Summary</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="metric-row">
    <div class="metric-box">
        <div class="metric-value">23,374</div>
        <div class="metric-label">Participant Records</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">4</div>
        <div class="metric-label">Patches Analyzed</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">27</div>
        <div class="metric-label">Shifts Tested</div>
    </div>
    <div class="metric-box">
        <div class="metric-value">5</div>
        <div class="metric-label">Significant Shifts</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Limitations
st.markdown('<div class="section-header">Limitations</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="limitation-box">
⚠️ <strong>Narrow patch window.</strong> Four patches is a limited time series. 
Additional data collection across more patches would increase statistical power 
and allow detection of subtler shifts.
</div>
<div class="limitation-box">
⚠️ <strong>Patch 8 data is sparse.</strong> Low play counts at patch 8 make 
trajectory estimates at that point unreliable and reduce confidence in patch 8→9 
shift detection.
</div>
<div class="limitation-box">
⚠️ <strong>Stabilization uses approximate game ordering.</strong> Match ID 
sequencing is used as a proxy for game timestamps within a patch. Future runs 
collect explicit timestamps for finer-grained stabilization analysis.
</div>
<div class="limitation-box">
⚠️ <strong>Trait-level analysis only.</strong> This study examines individual 
traits in isolation. Composition-level analysis — tracking full team archetypes 
rather than individual traits — would capture interaction effects between traits 
that this methodology misses.
</div>
<div class="limitation-box">
⚠️ <strong>No multiple comparison correction.</strong> 27 simultaneous hypothesis 
tests increase the probability of false positives. A Benjamini-Hochberg FDR 
correction would provide stronger statistical guarantees and is a natural extension 
of this work.
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# Future work
st.markdown('<div class="section-header">Future Work</div>',
            unsafe_allow_html=True)

st.markdown("""
<div class="body-text">
<p>
The most natural extension of this work is adding a <strong style="color:#C89B3C">
predictive layer</strong> — using early-patch behavioral signals from high-elo 
players to forecast which traits will dominate before the broader meta fully 
stabilizes. If top players converge on a new optimal strategy within the first 
third of a patch, that signal is detectable before the rest of the ladder catches up.
</p>
<p>
Additional extensions include composition-level clustering to track full team 
archetypes rather than individual traits, multiple comparison correction for 
stronger statistical guarantees, and expanded data collection across more patches 
for a longer time series.
</p>
</div>
""", unsafe_allow_html=True)