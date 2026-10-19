# Tableau Dashboard: Build Guide

This builds one Tableau Public dashboard from the same data as the README charts. The goal is a link you can put on your resume and portfolio.

## 0. Setup (about 10 minutes)

1. Create a free account at **public.tableau.com**.
2. Download **Tableau Public** (the desktop app) from the same site and sign in.
3. Generate the data files. `trait_games.csv` is too big for the repo, so it's always built locally:
   ```bash
   python -m src.database && python -m src.stats && python -m src.export_tableau
   ```

## 1. Connect the data

1. Open Tableau Public, go to **Connect, then Text file**, and open `tableau/trait_summary.csv`.
2. Drag `shift_tests.csv` onto the canvas. When Tableau draws a relationship line, set it to **trait = trait**.
3. Add `trait_games.csv` as a relationship to `trait_summary` on **trait = trait** AND **patch = patch_num**. Make the types match first: click the `patch` field in `trait_summary`, then set it to Number (whole).
4. Relate `tier_gap.csv` on **trait = trait**.

Check the field types: `patch`, `patch_from` and `patch_to` should be **Dimensions, Discrete**. Placements and rates should be **Measures**.

## 2. Sheets

### Sheet 1: Meta Heatmap ("Where does each trait stand?")
- Columns: `patch` (discrete). Rows: `trait_name`.
- Marks: **Square**. Colour: `eb_avg_placement`, using a diverging palette (Orange-Blue, reversed so that low = good = blue), centred at 4.5.
- Label: `eb_avg_placement`, formatted to 2 decimals.
- Filter: `n` at least 30, shown as a slider.
- Tooltip: n, raw avg placement, EB avg placement, top-4 rate, win rate.
- Why EB: rarely played traits get pulled toward the patch average, so the heatmap doesn't flash red or blue on a 12-game sample. Say this in a caption.

### Sheet 2: Shift Forest Plot ("What changed, and how sure are we?")
- Source: `shift_tests`. Rows: `trait_name` × `transition`. Columns: `delta`.
- Marks: **Circle** at `delta`. Add the CI as a **Gantt bar**: start at `delta_lo`, with size from the calculated field `[delta_hi] - [delta_lo]`.
- Colour: calculated field `Significant (FDR)` = `IF [q_value_bh] < 0.05 THEN "Significant after FDR" ELSEIF [p_value] < 0.05 THEN "Raw p<0.05 only" ELSE "Not significant" END`.
- Reference line at 0. Sort by `delta`.
- This sheet makes the multiple-comparisons point visually.

### Sheet 3: Placement Distribution ("Placement isn't win/loss")
- Source: `trait_games`. Columns: `placement` (discrete, 1–8). Rows: `COUNT(participant_id)` as **Percent of Total**, computed along Table (across).
- Filter: `trait_name` (single-value dropdown) and `patch_num`.
- Colour: `patch_num`, so that two patches compare side by side.
- This shows *how* a trait changed, e.g. fewer 1sts versus more 8ths.

### Sheet 4: Three Metrics Card
- Source: `trait_summary`. Filter on the same `trait_name`.
- A text table with avg placement, top-4 rate and win rate, each with its CI columns, by `patch`.

### Sheet 5: Elo Gap ("Is a trait strong at every rank?")
- Source: `tier_gap` (one row per trait, all Set 18 patches pooled).
- Rows: `trait_name`, sorted by `gap`. Columns: `gap`.
- Marks: **Circle**, plus a Gantt bar for the CI: start at `gap_lo`, with size `[gap_hi] - [gap_lo]`.
- Colour: `pattern` (Stronger at high elo / Stronger in Gold/Plat / No clear difference).
- Reference line at 0. Caption: "Placement is measured against each tier's own baseline, because lower-tier losing boards activate fewer traits."

## 3. Dashboard

1. **New Dashboard**, size **Automatic** (or 1200×900).
2. Layout: a title across the top, then the Heatmap on the left (60%) and the Forest Plot on the right. Below them, the Placement Distribution next to the Metrics Card.
3. Make the heatmap drive everything else: **Dashboard, then Actions, then Add Filter Action**. Source: Heatmap. Targets: Distribution and Metrics Card. Field: `trait_name`.
4. Use gold `#C89B3C` on dark navy `#0A1428` for a TFT-style look (Format, then Dashboard Shading).
5. Add a one-line takeaway in a text box: what shifted, how confident you are.

## 4. Publish

**File, then Save to Tableau Public.** Then open the published page and set it to show on your profile. Put the link in the README (under "Exploring the Results") and on your portfolio site.
