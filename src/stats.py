"""
Placement-aware statistics for TFT trait analysis.

TFT results are ordinal placements (1st-8th), not win/loss, so every trait is
summarised with three complementary metrics:
    - average placement (lower is better)
    - top-4 rate (the "did you gain LP" line)
    - win rate (1st place)
each with a 95% confidence interval.

This module also adds, on top of the permutation tests in analysis.py:
    - effect sizes (placement delta with bootstrap CI, Cohen's d, Cliff's delta)
    - multiple-comparison correction (Benjamini-Hochberg FDR, plus Holm)
    - empirical Bayes shrinkage for rarely played traits
    - a selection-bias check: level-adjusted (difference-in-differences) tests, and
      player fixed effects when player IDs are available
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")
Z = 1.959963984540054  # 95% two-sided
MIN_PLAYER_GAMES = 5  # for the player fixed-effects check


# ---------------------------------------------------------------------------
# Confidence intervals
# ---------------------------------------------------------------------------

def wilson_ci(successes, n, z=Z):
    """Wilson score interval for a proportion (well-behaved for small n / extreme p)."""
    successes = np.asarray(successes, dtype=float)
    n = np.asarray(n, dtype=float)
    p = np.divide(successes, n, out=np.zeros_like(n), where=n > 0)
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def summarize_traits(exploded, by=("patch", "trait")):
    """Average placement, top-4 rate and win rate with 95% CIs per group."""
    by = list(by)
    g = exploded.groupby(by, observed=True)["placement"]
    out = g.agg(n="count", avg_placement="mean", sd="std",
                top4=lambda x: (x <= 4).sum(), wins=lambda x: (x == 1).sum())
    out = out.reset_index()

    se = out["sd"] / np.sqrt(out["n"])
    tcrit = stats.t.ppf(0.975, np.maximum(out["n"] - 1, 1))
    out["avg_placement_lo"] = out["avg_placement"] - tcrit * se
    out["avg_placement_hi"] = out["avg_placement"] + tcrit * se

    out["top4_rate"] = out["top4"] / out["n"]
    out["top4_lo"], out["top4_hi"] = wilson_ci(out["top4"], out["n"])
    out["win_rate"] = out["wins"] / out["n"]
    out["win_lo"], out["win_hi"] = wilson_ci(out["wins"], out["n"])
    return out.drop(columns=["top4", "wins"])


# ---------------------------------------------------------------------------
# Effect sizes
# ---------------------------------------------------------------------------

def cohens_d(a, b):
    """Standardised mean difference (b - a) using the pooled SD."""
    na, nb = len(a), len(b)
    pooled = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    return (np.mean(b) - np.mean(a)) / pooled if pooled > 0 else 0.0


def cliffs_delta(a, b):
    """P(b > a) - P(b < a). Ordinal effect size suited to 1-8 placements.

    Positive = placements in b tend to be *higher numbers* (worse) than in a.
    Rough guide: |d| < 0.147 negligible, < 0.33 small, < 0.474 medium, else large.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    # Placements only take values 1..8, so count via histograms (O(8^2), not O(n*m))
    ca = np.bincount(a.astype(int), minlength=9)[1:9].astype(float)
    cb = np.bincount(b.astype(int), minlength=9)[1:9].astype(float)
    cum_a = np.cumsum(ca)
    less_a = np.concatenate([[0], cum_a[:-1]])      # # of a strictly below each value
    greater = (cb * less_a).sum()                    # pairs where b > a
    less = (cb * (len(a) - cum_a)).sum()            # pairs where b < a
    return (greater - less) / (len(a) * len(b))


def bootstrap_delta_ci(a, b, n_boot=2000, rng=None):
    """Percentile bootstrap CI for mean(b) - mean(a)."""
    rng = rng or np.random.default_rng(0)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ia = rng.integers(0, len(a), size=(n_boot, len(a)))
    ib = rng.integers(0, len(b), size=(n_boot, len(b)))
    deltas = b[ib].mean(axis=1) - a[ia].mean(axis=1)
    return np.percentile(deltas, [2.5, 97.5])


def effect_label(cliff):
    d = abs(cliff)
    if d < 0.147:
        return "negligible"
    if d < 0.33:
        return "small"
    if d < 0.474:
        return "medium"
    return "large"


# ---------------------------------------------------------------------------
# Permutation tests (vectorised) and multiple-comparison correction
# ---------------------------------------------------------------------------

def permutation_pvalue(a, b, n_perm=10000, strata_a=None, strata_b=None, rng=None):
    """Two-sided permutation test on the difference in mean placement.

    If strata are given, patch labels are shuffled *within* each stratum
    (e.g. final level), so the null distribution holds the strata mix fixed.
    Returns (count + 1) / (n_perm + 1), which is never exactly 0.
    """
    rng = rng or np.random.default_rng(0)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    combined = np.concatenate([a, b])
    is_b = np.concatenate([np.zeros(len(a), bool), np.ones(len(b), bool)])

    if strata_a is None:
        observed = b.mean() - a.mean()
        perm = np.empty(n_perm)
        chunk = max(1, 2_000_000 // len(combined))  # keep memory bounded
        for start in range(0, n_perm, chunk):
            k = min(chunk, n_perm - start)
            shuffled = rng.permuted(np.tile(combined, (k, 1)), axis=1)
            sums_b = shuffled[:, :len(b)].sum(axis=1)
            perm[start:start + k] = sums_b / len(b) - (combined.sum() - sums_b) / len(a)
    else:
        strata = np.concatenate([np.asarray(strata_a), np.asarray(strata_b)])
        observed = _stratified_delta(combined, is_b, strata)
        if np.isnan(observed):
            return np.nan
        perm = np.empty(n_perm)
        groups = [np.where(strata == s)[0] for s in np.unique(strata)]
        labels = is_b.copy()
        for k in range(n_perm):
            for idx in groups:
                labels[idx] = rng.permutation(is_b[idx])
            perm[k] = _stratified_delta(combined, labels, strata)

    count = np.sum(np.abs(perm) >= abs(observed) - 1e-12)
    return (count + 1) / (n_perm + 1)


def _stratified_delta(values, is_b, strata):
    """Weighted mean of within-stratum deltas (weights = stratum size)."""
    total, weight = 0.0, 0
    for s in np.unique(strata):
        m = strata == s
        vb = values[m & is_b]
        va = values[m & ~is_b]
        if len(va) == 0 or len(vb) == 0:
            continue
        w = m.sum()
        total += w * (vb.mean() - va.mean())
        weight += w
    return total / weight if weight else np.nan


def benjamini_hochberg(pvals):
    """BH-adjusted q-values (controls the false discovery rate)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (controls the family-wise error rate)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adj = np.maximum.accumulate(p[order] * (n - np.arange(n)))
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


# ---------------------------------------------------------------------------
# Empirical Bayes shrinkage
# ---------------------------------------------------------------------------

def eb_shrink_placement(summary, group_col="patch"):
    """Normal-normal empirical Bayes shrinkage of average placement.

    Within each patch, each trait's observed mean x_i has sampling variance
    v_i = s_i^2 / n_i. The prior is N(mu, tau^2) across traits, estimated by
    method of moments. The posterior mean is

        theta_i = B_i * mu + (1 - B_i) * x_i,   B_i = v_i / (v_i + tau^2)

    so rarely played traits (large v_i) are pulled toward the patch average.
    """
    frames = []
    for _, grp in summary.groupby(group_col, observed=True):
        g = grp.copy()
        # Pool the within-trait SD so 1-2 game traits don't get a tiny/undefined v_i
        pooled_var = np.nansum((g["n"] - 1) * g["sd"] ** 2) / max(np.nansum(g["n"] - 1), 1)
        v = pooled_var / g["n"]
        w = 1 / v
        mu = np.sum(w * g["avg_placement"]) / np.sum(w)
        # Method-of-moments (DerSimonian-Laird style) estimate of tau^2
        Q = np.sum(w * (g["avg_placement"] - mu) ** 2)
        k = len(g)
        c = np.sum(w) - np.sum(w**2) / np.sum(w)
        tau2 = max((Q - (k - 1)) / c, 1e-6) if c > 0 else 1e-6
        B = v / (v + tau2)
        g["eb_avg_placement"] = B * mu + (1 - B) * g["avg_placement"]
        g["eb_shrinkage"] = B
        g["eb_prior_mean"] = mu
        g["eb_tau"] = np.sqrt(tau2)
        post_sd = np.sqrt(v * tau2 / (v + tau2))
        g["eb_lo"] = g["eb_avg_placement"] - Z * post_sd
        g["eb_hi"] = g["eb_avg_placement"] + Z * post_sd
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def eb_shrink_rate(summary, rate_col="top4_rate", group_col="patch"):
    """Beta-binomial empirical Bayes for a rate (top-4 or win), fit by moments per patch."""
    frames = []
    for _, grp in summary.groupby(group_col, observed=True):
        g = grp.copy()
        k = g[rate_col] * g["n"]
        p = g[rate_col]
        m = np.average(p, weights=g["n"])
        var = np.average((p - m) ** 2, weights=g["n"])
        # Remove expected binomial noise to get the between-trait variance
        noise = np.mean(m * (1 - m) / g["n"])
        between = max(var - noise, 1e-6)
        strength = max(m * (1 - m) / between - 1, 1.0)  # alpha + beta
        alpha, beta = m * strength, (1 - m) * strength
        g[f"eb_{rate_col}"] = (k + alpha) / (g["n"] + alpha + beta)
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# Full shift-testing workflow
# ---------------------------------------------------------------------------

def test_all_shifts(rows, min_games=30, n_perm=10000, seed=0):
    """Test every eligible trait across every consecutive patch pair.

    rows: one row per (player-game, trait) with columns patch, trait, placement,
          level and optionally puuid.
    Returns one row per test with deltas, CIs, effect sizes, raw and adjusted
    p-values, and selection-bias robustness checks.
    """
    rng = np.random.default_rng(seed)
    patches = sorted(rows["patch"].astype(str).unique(), key=_patch_key)
    counts = rows.groupby(["trait", "patch"]).size().unstack(fill_value=0)
    eligible = counts[(counts[patches] >= min_games).all(axis=1)].index

    has_player = "puuid" in rows.columns and rows["puuid"].notna().all()
    if has_player:
        # Player fixed effects: compare each game to that player's own average,
        # removing stable skill differences between players who favour a trait.
        # Only players with >= MIN_PLAYER_GAMES games count; for someone seen
        # once, "vs their own average" is always 0 and carries no information.
        rows = rows.copy()
        games_per_player = rows.drop_duplicates(["match_id", "puuid"]).groupby("puuid").size()
        regulars = games_per_player[games_per_player >= MIN_PLAYER_GAMES].index
        per_game = rows.drop_duplicates(["match_id", "puuid"])
        player_mean = per_game[per_game["puuid"].isin(regulars)].groupby("puuid")["placement"].mean()
        rows["placement_vs_player"] = rows["placement"] - rows["puuid"].map(player_mean)

    results = []
    for trait in eligible:
        t = rows[rows["trait"] == trait]
        for p_from, p_to in zip(patches[:-1], patches[1:]):
            A = t[t["patch"].astype(str) == p_from]
            B = t[t["patch"].astype(str) == p_to]
            a, b = A["placement"].to_numpy(), B["placement"].to_numpy()
            lo, hi = bootstrap_delta_ci(a, b, rng=rng)
            res = {
                "trait": trait, "patch_from": p_from, "patch_to": p_to,
                "n_from": len(a), "n_to": len(b),
                "placement_from": a.mean(), "placement_to": b.mean(),
                "delta": b.mean() - a.mean(), "delta_lo": lo, "delta_hi": hi,
                "top4_from": (a <= 4).mean(), "top4_to": (b <= 4).mean(),
                "win_from": (a == 1).mean(), "win_to": (b == 1).mean(),
                "cohens_d": cohens_d(a, b), "cliffs_delta": cliffs_delta(a, b),
                "p_value": permutation_pvalue(a, b, n_perm=n_perm, rng=rng),
            }
            res["effect_size"] = effect_label(res["cliffs_delta"])

            # Selection-bias check 1: level-adjusted placement. Each game is
            # compared with the average placement of *all* players who finished
            # at the same level in the same patch, so the delta is a
            # difference-in-differences that removes patch-wide changes in how
            # high players level. Level is partly an outcome of the game, so
            # this is a robustness check, not a causal fix.
            ra = A["placement_vs_level"].to_numpy()
            rb = B["placement_vs_level"].to_numpy()
            res["delta_level_adj"] = rb.mean() - ra.mean()
            res["p_level_adj"] = permutation_pvalue(ra, rb, n_perm=n_perm, rng=rng)

            # Selection-bias check 2: player fixed effects (needs puuid)
            if has_player:
                fa = A["placement_vs_player"].dropna().to_numpy()
                fb = B["placement_vs_player"].dropna().to_numpy()
                res["n_player_fe"] = len(fa) + len(fb)
                if len(fa) >= 10 and len(fb) >= 10:
                    res["delta_player_fe"] = fb.mean() - fa.mean()
                    res["p_player_fe"] = permutation_pvalue(fa, fb, n_perm=n_perm, rng=rng)
            results.append(res)

    out = pd.DataFrame(results)
    out["q_value_bh"] = benjamini_hochberg(out["p_value"])
    out["p_holm"] = holm(out["p_value"])
    out["significant_raw"] = out["p_value"] < 0.05
    out["significant_fdr"] = out["q_value_bh"] < 0.05
    out["direction"] = np.where(out["delta"] < 0, "Better", "Worse")
    return out.sort_values("p_value").reset_index(drop=True)


def _patch_key(p):
    return tuple(int(x) for x in str(p).replace("Version.", "").split(".") if x.isdigit())


def build_rows(raw):
    """Explode raw match rows into one row per (player-game, active trait)."""
    df = raw.copy()
    df["patch"] = df["patch"].astype(str).str.replace("Version.", "", regex=False)
    # Baseline placement for each (patch, final level) across ALL players,
    # computed before exploding so each player-game counts once.
    df["level_bucket"] = df["level"].clip(7, 10)
    tier_col = ["sample_tier"] if "sample_tier" in df.columns else []
    base = df.groupby(tier_col + ["patch", "level_bucket"])["placement"].transform("mean")
    df["placement_vs_level"] = df["placement"] - base
    df["trait"] = df["traits"].str.split(",")
    df = df.explode("trait")
    df["trait"] = df["trait"].str.strip()
    df = df[df["trait"].notna() & (df["trait"] != "")]
    if "sample_tier" not in df.columns:
        df["sample_tier"] = "HIGH_ELO"
    keep = ["match_id", "patch", "trait", "placement", "level", "placement_vs_level", "sample_tier"]
    keep += [c for c in ["puuid", "game_datetime"] if c in df.columns]
    return df[keep].reset_index(drop=True)


def compare_tiers(rows, min_games=30):
    """Trait strength by rank: high elo vs lower tiers in the same patch.

    Raw trait placements can't be compared across tiers directly: in lower
    tiers, losing boards activate far fewer traits, so the *trait-weighted*
    average placement sits below 4.5 (about 4.2 in Gold vs 4.3 in high elo)
    for every trait at once. Each trait is therefore measured relative to its
    own tier-and-patch baseline before comparing:

        gap = (trait - baseline) in the lower tier  -  (trait - baseline) in high elo

    Positive gap = the trait is relatively weaker in the lower tier than at the
    top. Estimates are EB-shrunk; p-values come from a permutation test on the
    baseline-centred placements.
    """
    if rows["sample_tier"].nunique() < 2:
        return pd.DataFrame()
    rows = rows.copy()
    rows["baseline"] = rows.groupby(["sample_tier", "patch"])["placement"].transform("mean")
    rows["placement_rel"] = rows["placement"] - rows["baseline"]

    summ = summarize_traits(rows, by=("sample_tier", "patch", "trait"))
    summ["group"] = summ["sample_tier"] + "|" + summ["patch"]
    summ = eb_shrink_placement(summ, group_col="group")
    base = rows.groupby(["sample_tier", "patch"])["placement"].mean()
    summ["eb_rel"] = summ["eb_avg_placement"] - [base[(t, p)] for t, p in zip(summ["sample_tier"], summ["patch"])]
    wide = summ.pivot_table(index=["patch", "trait"], columns="sample_tier",
                            values=["eb_avg_placement", "eb_rel", "n"])
    out = []
    rng = np.random.default_rng(1)
    for (patch, trait), r in wide.iterrows():
        for tier in [t for t in rows["sample_tier"].unique() if t != "HIGH_ELO"]:
            if r.get(("n", "HIGH_ELO"), 0) < min_games or r.get(("n", tier), 0) < min_games:
                continue
            m = (rows["patch"] == patch) & (rows["trait"] == trait)
            hi = rows.loc[m & (rows["sample_tier"] == "HIGH_ELO"), "placement_rel"].to_numpy()
            lo = rows.loc[m & (rows["sample_tier"] == tier), "placement_rel"].to_numpy()
            out.append({
                "patch": patch, "trait": trait, "tier": tier,
                "n_high_elo": int(r[("n", "HIGH_ELO")]), "n_tier": int(r[("n", tier)]),
                "eb_placement_high_elo": r[("eb_avg_placement", "HIGH_ELO")],
                "eb_placement_tier": r[("eb_avg_placement", tier)],
                "rel_high_elo": r[("eb_rel", "HIGH_ELO")],
                "rel_tier": r[("eb_rel", tier)],
                "gap": r[("eb_rel", tier)] - r[("eb_rel", "HIGH_ELO")],
                "p_value": permutation_pvalue(hi, lo, n_perm=5000, rng=rng),
            })
    res = pd.DataFrame(out)
    if not res.empty:
        res["q_value_bh"] = benjamini_hochberg(res["p_value"])
    return res


def compare_tiers_pooled(rows, min_games=100, n_perm=5000, seed=2):
    """Set-wide version of compare_tiers: one test per trait.

    Per-patch, per-tier cells are too small in Gold/Plat for individual tests
    to survive FDR correction (282 tests, often 100-300 games each). Pooling
    all patches and both lower tiers asks the simpler question a designer
    cares about -- "across this set, is this trait relatively stronger or weaker
    below Diamond than at the top?" -- with several times the sample size.
    Placements are still centred on each tier-and-patch baseline first.
    """
    if rows["sample_tier"].nunique() < 2:
        return pd.DataFrame()
    rows = rows.copy()
    rows["placement_rel"] = rows["placement"] - rows.groupby(["sample_tier", "patch"])["placement"].transform("mean")
    rows["is_high"] = rows["sample_tier"] == "HIGH_ELO"
    rng = np.random.default_rng(seed)
    out = []
    for trait, g in rows.groupby("trait"):
        hi = g.loc[g["is_high"], "placement_rel"].to_numpy()
        lo = g.loc[~g["is_high"], "placement_rel"].to_numpy()
        if len(hi) < min_games or len(lo) < min_games:
            continue
        ci_lo, ci_hi = bootstrap_delta_ci(hi, lo, rng=rng)
        out.append({
            "trait": trait, "n_high_elo": len(hi), "n_lower": len(lo),
            "rel_high_elo": hi.mean(), "rel_lower": lo.mean(),
            "gap": lo.mean() - hi.mean(), "gap_lo": ci_lo, "gap_hi": ci_hi,
            "p_value": permutation_pvalue(hi, lo, n_perm=n_perm, rng=rng),
        })
    res = pd.DataFrame(out)
    res["q_value_bh"] = benjamini_hochberg(res["p_value"])
    res["significant_fdr"] = res["q_value_bh"] < 0.05
    res["pattern"] = np.select(
        [res["significant_fdr"] & (res["gap"] > 0), res["significant_fdr"] & (res["gap"] < 0)],
        ["Stronger at high elo", "Stronger in Gold/Plat"], "No clear difference")
    return res.sort_values("gap", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from src.features import load_clean_raw

    raw = load_clean_raw()
    raw["traits"] = raw["traits"].fillna("")
    rows = build_rows(raw)
    high = rows[rows["sample_tier"] == "HIGH_ELO"]

    summary = summarize_traits(high)
    summary = eb_shrink_placement(summary)
    summary = eb_shrink_rate(summary, "top4_rate")
    summary = eb_shrink_rate(summary, "win_rate")
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    summary.to_csv(os.path.join(PROCESSED_PATH, "trait_summary.csv"), index=False)
    print(f"Saved trait_summary.csv ({len(summary)} trait-patch rows)")

    shifts = test_all_shifts(high)
    shifts.to_csv(os.path.join(PROCESSED_PATH, "shift_tests.csv"), index=False)
    cols = ["trait", "patch_from", "patch_to", "delta", "delta_lo", "delta_hi",
            "cliffs_delta", "effect_size", "p_value", "q_value_bh", "p_holm",
            "delta_level_adj", "p_level_adj"]
    print(shifts[cols].head(12).round(3).to_string())
    print(f"\n{shifts['significant_raw'].sum()} of {len(shifts)} tests significant at p<0.05; "
          f"{shifts['significant_fdr'].sum()} survive BH FDR correction.")

    tiers = compare_tiers(rows)
    if not tiers.empty:
        tiers.to_csv(os.path.join(PROCESSED_PATH, "tier_comparison.csv"), index=False)
        print(f"Saved tier_comparison.csv ({len(tiers)} rows)")
        pooled = compare_tiers_pooled(rows)
        pooled.to_csv(os.path.join(PROCESSED_PATH, "tier_gap_pooled.csv"), index=False)
        print(f"Saved tier_gap_pooled.csv: {pooled['significant_fdr'].sum()} of {len(pooled)} "
              "traits differ between high elo and Gold/Plat after FDR correction")
