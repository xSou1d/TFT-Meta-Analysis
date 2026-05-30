# TFT Meta Shift Detection & Trait Performance Analysis

A quantitative research project applying time series methodology and statistical inference to detect meta shifts in *Teamfight Tactics* (TFT) — Riot Games' auto-battler strategy game.

## Overview

Each TFT patch introduces balance changes that alter the relative strength of traits and compositions. This project builds a data pipeline to collect high-elo match data via the Riot Games API, engineers time series features from raw match records, and applies statistical methods to formally detect which traits underwent significant performance shifts between patches.

The methodology mirrors **regime detection in financial markets** — identifying structural breaks in a time series where the underlying dynamics have measurably changed.

## Project Structure

```
TFT-Meta-Analysis/
├── data/
│   ├── raw/              # Raw match data from Riot API
│   └── processed/        # Engineered features and analysis outputs
├── pages/
│   ├── 1_Overview.py     # Heatmap dashboard page
│   ├── 2_Trait_Explorer.py  # Per-trait analysis page
│   └── 3_Significant_Shifts.py  # Validated shifts page
├── src/
│   ├── api.py            # Riot API request handling
│   ├── pipeline.py       # Data collection orchestration
│   ├── utils.py          # JSON parsing and patch cleaning
│   ├── features.py       # Feature engineering
│   └── analysis.py       # Time series modeling and statistical testing
├── app.py                # Streamlit dashboard entry point
└── requirements.txt
```

## Data Collection

Match data was collected from the top 150 Challenger and Grandmaster players in the NA region using the Riot Games TFT Match API. Each match record contains placement, traits, units, augments, and patch version for all 8 participants.

- **Total matches collected:** ~2,900 unique matches
- **Total participant records:** 23,374 rows
- **Patches covered:** 8, 9, 10, 11 (TFT Set 17)

High-elo players were specifically targeted because their decisions are less noisy and more reflective of the true optimal meta, reducing variance in the performance signals.

## Methodology

### Feature Engineering

Raw match records store traits as comma-separated strings per participant. The feature engineering layer explodes these into one row per trait per game, then aggregates by patch and trait to compute:

- **Play count** — number of appearances per patch
- **Average placement** — mean finish position (1–8, lower is better)
- **Top-4 rate** — fraction of games finishing in the top half

### Shift Detection

For each trait passing a minimum play count threshold (≥30 appearances per patch), consecutive patch pairs are examined for placement delta. A shift is recorded when the absolute difference in average placement exceeds the detection threshold.

### Statistical Significance Testing

Each detected shift is validated using a **permutation test** — a non-parametric approach that makes no distributional assumptions. For each shift:

1. The observed placement delta between two patches is computed
2. Placements from both patches are pooled and randomly shuffled 1,000 times
3. A p-value is computed as the fraction of permutations producing a delta as large as observed

Shifts with p < 0.05 are classified as statistically significant.

A permutation test was chosen over a standard t-test because per-patch sample sizes for individual traits are small and the normality assumption cannot be reliably met.

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

## Key Findings

**Patch 10→11 was the only patch transition producing statistically significant meta shifts.** Patches 8→9 and 9→10 showed larger raw placement deltas for some traits (e.g. SpaceGroove: -0.41) but these did not survive significance testing, indicating they were driven by variance rather than genuine balance changes.

**The high-elo meta was remarkably stable across this collection window.** This is consistent with the behavior of top players who adapt quickly to balance changes, compressing the performance gap between traits.

**RhaastUniqueTrait was consistently the strongest performing trait** across all patches, averaging well below 4.0 placement throughout the set.

## Limitations

- **Four patches** is a narrow window for time series analysis. Additional data collection across more patches would strengthen the findings.
- **Patch 8 data is sparse** — low play counts at patch 8 make trajectory estimates at that point unreliable.
- **Survivorship in trait filtering** — traits appearing fewer than 30 times per patch are excluded, which may omit niche compositions with meaningful shifts.
- **Per Riot Games developer policy**, augment win rate data is not displayed publicly in this project.

## Exploring the Results

Launch the interactive dashboard to explore all findings:

```bash
streamlit run app.py
```

The dashboard includes three pages:

- **Overview** — full trait performance heatmap across all patches with adjustable play count filter
- **Trait Explorer** — select any trait to see its full trajectory, play rate, and significance results
- **Significant Shifts** — all statistically validated meta shifts with interpretation and full results table

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