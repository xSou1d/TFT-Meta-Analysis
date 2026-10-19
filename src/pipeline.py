import os
import random
import time
import pandas as pd
from tqdm import tqdm
from src.api import (
    get_challenger_players,
    get_grandmaster_players,
    get_league_entries,
    get_match_ids,
    get_match
)
from src.utils import parse_participant, parse_patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# v2 file: includes game_datetime, game_version, set_number and puuid columns.
# Kept separate from the original matches.csv, whose header lacks those columns
# (appending new rows to it would silently misalign every column).
RAW_PATH = os.path.join(ROOT_DIR, "data", "raw", "matches_v2.csv")


def collect_puuids(max_players=100):
    """Pull top players from Challenger and Grandmaster ladders and return their PUUIDs."""
    puuids = []

    print("Fetching Challenger ladder...")
    challenger = get_challenger_players()
    if challenger:
        entries = challenger.get("entries", [])
        for entry in entries[:max_players // 2]:
            puuid = entry.get("puuid")
            if puuid:
                puuids.append(puuid)

    print("Fetching Grandmaster ladder...")
    grandmaster = get_grandmaster_players()
    if grandmaster:
        entries = grandmaster.get("entries", [])
        for entry in entries[:max_players // 2]:
            puuid = entry.get("puuid")
            if puuid:
                puuids.append(puuid)

    print(f"Collected {len(puuids)} PUUIDs.")
    return list(set(puuids))


def collect_tier_puuids(tier, n_players=100, seed=42):
    """Sample PUUIDs from a non-apex tier (all four divisions), e.g. GOLD or PLATINUM.

    Takes the first page of each division and samples evenly, so the sample is
    spread across the tier rather than concentrated at its top.
    """
    rng = random.Random(seed)
    per_div = n_players // 4
    puuids = []
    print(f"Fetching {tier} ladder...")
    for division in ["I", "II", "III", "IV"]:
        entries = get_league_entries(tier, division, page=1)
        pool = [e["puuid"] for e in entries if e.get("puuid")]
        puuids.extend(rng.sample(pool, min(per_div, len(pool))))
    print(f"Collected {len(puuids)} {tier} PUUIDs.")
    return puuids


def collect_match_ids(puuids, matches_per_player=20, start_time=None, end_time=None):
    # Note: a match is tagged with the tier of the player it was found through.
    # TFT lobbies are matched by MMR, so this is a good proxy for lobby rank.
    """For each PUUID, fetch ranked match IDs (optionally inside a time window).

    Pages through results 100 at a time so matches_per_player can exceed the
    per-request cap and reach back across several patches.
    """
    all_match_ids = set()

    print("Fetching match IDs...")
    for puuid in tqdm(puuids):
        fetched = 0
        while fetched < matches_per_player:
            batch = min(100, matches_per_player - fetched)
            ids = get_match_ids(puuid, count=batch, start=fetched,
                                start_time=start_time, end_time=end_time)
            all_match_ids.update(ids)
            fetched += len(ids)
            if len(ids) < batch:
                break

    print(f"Collected {len(all_match_ids)} unique match IDs.")
    return list(all_match_ids)


def collect_matches(match_ids, output_path=None, set_number=None, sample_tier="HIGH_ELO"):
    """Fetch each match, parse all 8 participants, and save to CSV incrementally.

    If set_number is given, matches from any other TFT set are skipped so
    patches from different sets never get mixed into one time series.
    """
    if output_path is None:
        output_path = RAW_PATH

    rows = []
    seen = set()
    total_saved = 0

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Resume from existing CSV if present
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        seen.update(existing_df["match_id"].unique())
        total_saved = len(existing_df)
        print(f"Resuming — skipping {len(seen)} already collected matches.")

    print("Fetching match data...")
    for i, match_id in enumerate(tqdm(match_ids)):
        if match_id in seen:
            continue
        seen.add(match_id)

        match = get_match(match_id)
        if not match:
            continue

        info = match["info"]
        match_set = info.get("tft_set_number")
        if set_number is not None and match_set != set_number:
            continue
        game_version = info.get("game_version", "unknown")
        patch = parse_patch(game_version)
        game_datetime = info.get("game_datetime", None)
        participants = info.get("participants", [])

        for participant in participants:
            row = parse_participant(participant, match_id, patch, game_datetime,
                                    game_version, match_set)
            row["sample_tier"] = sample_tier
            rows.append(row)

        # Save incrementally every 100 matches
        if i % 100 == 0 and rows:
            chunk = pd.DataFrame(rows)
            write_header = not os.path.exists(output_path)
            chunk.to_csv(output_path, mode='a', header=write_header, index=False)
            total_saved += len(rows)
            rows = []

    # Save any remaining rows
    if rows:
        chunk = pd.DataFrame(rows)
        write_header = not os.path.exists(output_path)
        chunk.to_csv(output_path, mode='a', header=write_header, index=False)
        total_saved += len(rows)

    print(f"Done — {total_saved} total rows saved to {output_path}")
    return pd.read_csv(output_path)


def run_pipeline(max_players=100, matches_per_player=20, days_back=None,
                 set_number=None, tiers=("HIGH_ELO",)):
    """Full pipeline: players → PUUIDs → match IDs → match data → CSV.

    tiers: any of HIGH_ELO (Challenger + Grandmaster), GOLD, PLATINUM, ...
    Each tier is collected separately and tagged in the sample_tier column.
    """
    start_time = time.time() - days_back * 86400 if days_back else None
    df = None
    for tier in tiers:
        if tier == "HIGH_ELO":
            puuids = collect_puuids(max_players=max_players)
        else:
            puuids = collect_tier_puuids(tier, n_players=max_players)
        match_ids = collect_match_ids(puuids, matches_per_player=matches_per_player,
                                      start_time=start_time)
        df = collect_matches(match_ids, set_number=set_number, sample_tier=tier)
    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect high-elo TFT match data.")
    parser.add_argument("--players", type=int, default=150)
    parser.add_argument("--matches-per-player", type=int, default=60)
    parser.add_argument("--days-back", type=int, default=None,
                        help="Only pull matches from the last N days")
    parser.add_argument("--set", dest="set_number", type=int, default=None,
                        help="Keep only matches from this TFT set number")
    parser.add_argument("--tiers", nargs="+", default=["HIGH_ELO"],
                        help="HIGH_ELO and/or GOLD, PLATINUM, DIAMOND, ...")
    args = parser.parse_args()
    run_pipeline(args.players, args.matches_per_player, args.days_back,
                 args.set_number, args.tiers)