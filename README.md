# TFT Meta Shift Detection & Trait Performance Analysis

A quantitative research project applying time series methodology and statistical inference to detect meta shifts in *Teamfight Tactics* (TFT) — Riot Games' auto-battler strategy game.

## Research Question

> When a TFT patch changes the balance of traits, do high-elo players demonstrably shift their composition choices in ways that are statistically distinguishable from normal variance — and how quickly does a new meta stabilize?

## Overview

In Teamfight Tactics, high-elo players are not passive observers of the meta — they create it. They are the first to identify what is strongest after a patch, and the rest of the ladder follows their lead. This makes high-elo match data a uniquely valuable signal. Tracking the trait choices of the top 150 NA players over time is not just performance analysis — it is **behavioral signal extraction**.

The methodology mirrors **regime detection in financial markets** — identifying structural breaks in a time series where the underlying dynamics have measurably changed.

## Project Structure

```
TFT-Meta-Analysis/
├── data/
│   ├── raw/                    # Raw match data from Riot API
│   └── processed/              # Engineered features and analysis outputs
├── pages/
│   ├── 1_Detection.py          # Shift detection results
│   ├── 2_Trait_Explorer.py     # Per-trait analysis
│   ├── 3_Stabilization.py      # Meta stabilization analysis
│   └── 4_Findings.py           # Conclusions and limitations
├── src/
│   ├── api.py                  # Riot API request handling
│   ├── pipeline.py             # Data collection orchestration
│   ├── utils.py                # JSON parsing and patch cleaning
│   ├── features.py             # Feature engineering
│   └── analysis.py             # Time series modeling and statistical testing
├── app.py                      # Streamlit dashboard entry point
└── requirements.txt
```

## Methodology

### Stage 1 — Feature Engineering
Raw match records are transformed into a trait-level time series tracking play rate, average placement, and top-4 rate for every trait across every patch.

### Stage 2 — Shift Detection
For each trait passing a minimum play count threshold (≥30 appearances per patch), consecutive patch pairs are examined for placement delta. Each candidate shift is validated using a **permutation test** — a non-parametric approach that asks: is this change larger than what we would expect by random chance alone?

### Stage 3 — Stabilization Analysis
For patches where significant shifts are detected, games within the patch are divided into early, mid, and late windows using match ID sequencing as a game order proxy. Placement variance is tracked across these windows to measure how quickly high-elo players converge on optimal strategies after a balance change.

## Data

- **~2,900** unique ranked matches
- **23,374** participant records
- **4 patches** covered (TFT Set 17, Patches 8–11)
- **Top 150** Challenger and Grandmaster players, NA region

## Results

### Significant Meta Shifts Detected

All 5 statistically significant shifts occurred at the patch 10→11 transition:

| Trait | Direction | Delta | p-value |
|---|---|---|---|
| RhaastUniqueTrait | Worse | +0.228 | 0.000 |
| DRX | Worse | +0.210 | 0.001 |
| HPTank | Worse | +0.167 | 0.009 |
| DarkStar | Better | -0.162 | 0.007 |
| FlexTrait | Better | -0.116 | 0.036 |

### Key Findings

**Not every patch creates a new meta.** Patches 8→9 and 9→10 showed large raw placement deltas but none survived significance testing — these were variance-driven fluctuations, not genuine balance shifts.

**Patch 10→11 was a genuine balance intervention.** Five traits shifted in ways statistically indistinguishable from random chance less than 5% of the time.

**Stabilization speed varies by trait.** DarkStar stabilized fastest after its buff. RhaastUniqueTrait never fully stabilized within the patch window, indicating ongoing adaptation throughout.

**High-elo players are a leading indicator.** Variance compression over time within a patch confirms that top players converge on optimal strategies faster than the broader player base.

## Limitations

- Four patches is a narrow window for time series analysis
- Patch 8 data is sparse due to limited collection at that point
- Stabilization analysis uses match ID sequencing as a game order proxy rather than explicit timestamps — future pipeline runs collect `game_datetime` directly
- No multiple comparison correction applied across the 27 simultaneous hypothesis tests
- Trait-level analysis only — composition-level clustering would capture interaction effects between traits

## Exploring the Results

Launch the interactive dashboard:

```bash
streamlit run app.py
```

The dashboard walks through the full analysis across four pages — detection, trait exploration, stabilization, and findings.

## Requirements

```
requests
python-dotenv
pandas
numpy
tqdm
scipy
plotly
streamlit
```

Install with: `pip install -r requirements.txt`

## Pipeline Usage

```bash
# Collect match data
python src/pipeline.py

# Build feature engineering
python src/features.py

# Run statistical analysis
python src/analysis.py

# Launch dashboard
streamlit run app.py
```

**Note:** A valid Riot Games API key is required. Development keys expire every 24 hours and can be obtained at [developer.riotgames.com](https://developer.riotgames.com).