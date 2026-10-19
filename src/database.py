"""
Load raw match CSVs into a normalised SQLite database and run the SQL in sql/.

    python -m src.database            # build data/tft.db from the raw CSV
    python -m src.database --run 01   # run sql/01_*.sql and print the result
"""
import argparse
import glob
import os
import sqlite3

import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "data", "tft.db")
SQL_DIR = os.path.join(ROOT_DIR, "sql")


def _split(val):
    if not isinstance(val, str) or not val:
        return []
    return [x.strip() for x in val.split(",") if x.strip()]


def build_database(raw_path=None, db_path=DB_PATH):
    from src.features import load_clean_raw

    raw = load_clean_raw(raw_path)
    raw["traits"] = raw["traits"].fillna("")
    raw["trait_tiers"] = raw["trait_tiers"].fillna("")
    raw["patch"] = raw["patch"].astype(str).str.replace("Version.", "", regex=False)
    for col, default in [("sample_tier", "HIGH_ELO"), ("set_number", None),
                         ("game_datetime", None), ("puuid", None)]:
        if col not in raw.columns:
            raw[col] = default
    raw = raw.reset_index(drop=True)
    raw["participant_id"] = raw.index + 1

    matches = (raw.groupby("match_id", as_index=False)
                  .agg(patch=("patch", "first"), set_number=("set_number", "first"),
                       game_datetime=("game_datetime", "first"),
                       sample_tier=("sample_tier", "first")))
    participants = raw[["participant_id", "match_id", "puuid", "placement", "level",
                        "last_round", "gold_left", "time_eliminated"]]

    trait_rows = []
    for pid, tiers in zip(raw["participant_id"], raw["trait_tiers"]):
        for item in _split(tiers):
            name, _, tier = item.partition(":")
            trait_rows.append((pid, name, int(tier) if tier.isdigit() else None))
    traits = pd.DataFrame(trait_rows, columns=["participant_id", "trait", "tier"])
    traits = traits.drop_duplicates(["participant_id", "trait"])

    unit_rows = [(pid, i, u) for pid, units in zip(raw["participant_id"], raw["units"])
                 for i, u in enumerate(_split(units))]
    units = pd.DataFrame(unit_rows, columns=["participant_id", "slot", "character_id"])

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.executescript(open(os.path.join(SQL_DIR, "schema.sql")).read())
        matches.to_sql("matches", con, if_exists="append", index=False)
        participants.to_sql("participants", con, if_exists="append", index=False)
        traits.to_sql("participant_traits", con, if_exists="append", index=False)
        units.to_sql("participant_units", con, if_exists="append", index=False)
    print(f"Built {db_path}: {len(matches)} matches, {len(participants)} participants, "
          f"{len(traits)} trait rows, {len(units)} unit rows")
    return db_path


def run_query(name, db_path=DB_PATH):
    """Run a query from sql/ by file name or numeric prefix (e.g. '01')."""
    matches = sorted(glob.glob(os.path.join(SQL_DIR, f"{name}*.sql")))
    if not matches:
        raise FileNotFoundError(f"No SQL file matching {name!r} in {SQL_DIR}")
    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query(open(matches[0]).read(), con)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", help="Run a query in sql/ by prefix, e.g. 01")
    args = parser.parse_args()
    if args.run:
        print(run_query(args.run).to_string(max_rows=40))
    else:
        build_database()
