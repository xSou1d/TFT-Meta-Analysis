import os
import time
import pandas as pd
from tqdm import tqdm
from src.api import (
    get_challenger_players,
    get_grandmaster_players,
    get_puuid,
    get_match_ids,
    get_match
)
from src.utils import parse_participant, parse_patch

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def collect_match_ids(puuids, matches_per_player=20):
    """For each PUUID, fetch their recent ranked match IDs."""
    all_match_ids = set()

    print("Fetching match IDs...")
    for puuid in tqdm(puuids):
        ids = get_match_ids(puuid, count=matches_per_player)
        all_match_ids.update(ids)
        time.sleep(0.05)

    print(f"Collected {len(all_match_ids)} unique match IDs.")
    return list(all_match_ids)


def collect_matches(match_ids, output_path=None):
    """Fetch each match, parse all 8 participants, and save to CSV incrementally."""
    if output_path is None:
        output_path = os.path.join(ROOT_DIR, "data", "raw", "matches.csv")

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

        patch = parse_patch(match["info"].get("game_version", "unknown"))
        game_datetime = match["info"].get("game_datetime", None)
        participants = match["info"].get("participants", [])

        for participant in participants:
            row = parse_participant(participant, match_id, patch, game_datetime)
            rows.append(row)

        # Save incrementally every 100 matches
        if i % 100 == 0 and rows:
            chunk = pd.DataFrame(rows)
            write_header = not os.path.exists(output_path)
            chunk.to_csv(output_path, mode='a', header=write_header, index=False)
            total_saved += len(rows)
            rows = []

        time.sleep(0.05)

    # Save any remaining rows
    if rows:
        chunk = pd.DataFrame(rows)
        write_header = not os.path.exists(output_path)
        chunk.to_csv(output_path, mode='a', header=write_header, index=False)
        total_saved += len(rows)

    print(f"Done — {total_saved} total rows saved to {output_path}")
    return pd.read_csv(output_path)


def run_pipeline(max_players=100, matches_per_player=20):
    """Full pipeline: players → PUUIDs → match IDs → match data → CSV."""
    puuids = collect_puuids(max_players=max_players)
    match_ids = collect_match_ids(puuids, matches_per_player=matches_per_player)
    df = collect_matches(match_ids)
    return df


if __name__ == "__main__":
    run_pipeline(max_players=150, matches_per_player=30)