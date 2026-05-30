import streamlit as st

st.set_page_config(
    page_title="TFT Meta Analysis",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 TFT Meta Shift Detection & Trait Performance Analysis")
st.markdown("""
A quantitative research project applying **time series methodology** and 
**statistical inference** to detect meta shifts in Teamfight Tactics (TFT).

---

### What this dashboard shows

This analysis examines **23,374 high-elo match records** across **4 patches** 
of TFT Set 17, collected from the top 150 Challenger and Grandmaster players 
in the NA region via the Riot Games API.

The methodology mirrors **regime detection in financial markets** — identifying 
structural breaks in a time series where the underlying dynamics have 
measurably changed.

---

### Navigate the dashboard

- **Overview** — Heatmap of all trait performance across patches
- **Trait Explorer** — Select any trait to see its full trajectory and statistics  
- **Significant Shifts** — Statistically validated meta shifts (p < 0.05)

---

### Key Finding

> Patch 10→11 was the only transition producing statistically significant 
> meta shifts. 5 traits shifted meaningfully, while patches 8→9 and 9→10 
> showed variance-driven fluctuations that did not survive significance testing.
""")

st.sidebar.success("Select a page above to get started.")