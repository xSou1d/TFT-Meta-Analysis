"""
Export Tableau-ready flat files to tableau/ from the SQLite database and stats outputs.

    python -m src.database        # build data/tft.db first
    python -m src.stats           # build trait_summary.csv and shift_tests.csv
    python -m src.export_tableau

Files (all long/tidy format, one row per grain stated):
    trait_games.csv     one row per player-game x active trait (for custom calcs/filters)
    trait_summary.csv   one row per patch x trait: metrics, 95% CIs, EB-shrunk estimates
    shift_tests.csv     one row per trait x patch transition: deltas, effect sizes, q-values
    tier_gap.csv        one row per patch x trait x lower tier (once Gold/Plat data exists)
"""
import os
import sqlite3

import pandas as pd

from src.database import DB_PATH, run_query

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT_DIR, "tableau")
PROCESSED = os.path.join(ROOT_DIR, "data", "processed")


def pretty_trait(name):
    """TFT17_RhaastUniqueTrait -> Rhaast (Unique)."""
    n = str(name).split("_", 1)[-1]
    return n.replace("UniqueTrait", " (Unique)").replace("Trait", "")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sqlite3.connect(DB_PATH) as con:
        games = pd.read_sql_query("""
            SELECT m.match_id, m.patch, m.sample_tier, m.game_datetime,
                   p.participant_id, p.placement, p.level, p.last_round,
                   t.trait, t.tier AS trait_tier,
                   CASE WHEN p.placement <= 4 THEN 1 ELSE 0 END AS is_top4,
                   CASE WHEN p.placement = 1 THEN 1 ELSE 0 END AS is_win
            FROM participant_traits t
            JOIN participants p ON p.participant_id = t.participant_id
            JOIN matches m      ON m.match_id = p.match_id
        """, con)
    games["trait_name"] = games["trait"].map(pretty_trait)
    games["patch_num"] = games["patch"].astype(int)
    games.to_csv(os.path.join(OUT_DIR, "trait_games.csv"), index=False)

    summary = pd.read_csv(os.path.join(PROCESSED, "trait_summary.csv"))
    summary["trait_name"] = summary["trait"].map(pretty_trait)
    summary.to_csv(os.path.join(OUT_DIR, "trait_summary.csv"), index=False)

    shifts = pd.read_csv(os.path.join(PROCESSED, "shift_tests.csv"))
    shifts["trait_name"] = shifts["trait"].map(pretty_trait)
    shifts["transition"] = shifts["patch_from"].astype(str) + " → " + shifts["patch_to"].astype(str)
    shifts.to_csv(os.path.join(OUT_DIR, "shift_tests.csv"), index=False)

    gap = run_query("05")
    if not gap.empty:
        gap["trait_name"] = gap["trait"].map(pretty_trait)
        gap.to_csv(os.path.join(OUT_DIR, "tier_gap.csv"), index=False)

    print(f"Wrote Tableau files to {OUT_DIR}: trait_games ({len(games)} rows), "
          f"trait_summary ({len(summary)}), shift_tests ({len(shifts)}), "
          f"tier_gap ({len(gap)})")


if __name__ == "__main__":
    main()
