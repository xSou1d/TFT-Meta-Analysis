def parse_participant(participant, match_id, patch, game_datetime=None,
                      game_version=None, set_number=None):
    all_augments = participant.get("augments", [])
    all_units = participant.get("units", [])
    active_traits = [t for t in participant.get("traits", []) if t["style"] > 0]

    traits_str = ",".join([t["name"] for t in active_traits])
    trait_tiers_str = ",".join(f"{t['name']}:{t['tier_current']}" for t in active_traits)
    units_str = ",".join([u["character_id"] for u in all_units])
    augments_str = ",".join(all_augments)

    participant_dict = {
        "match_id": match_id,
        "patch": patch,
        "game_datetime": game_datetime,
        "game_version": game_version,
        "set_number": set_number,
        "puuid": participant.get("puuid"),
        "placement": participant.get("placement"),
        "level": participant.get("level"),
        "last_round": participant.get("last_round"),
        "gold_left": participant.get("gold_left"),
        "time_eliminated": participant.get("time_eliminated"),
        "traits": traits_str,
        "trait_tiers": trait_tiers_str,
        "augments": augments_str,
        "units": units_str
    }

    return participant_dict


import re
from datetime import datetime, timedelta, timezone

# Since Set 18 moved to Unreal Engine, match-v1 returns game_version as
# "TFT Unreal Version ?.?.?.?" -- no patch number. We assign patches from
# game_datetime using Riot's published patch schedule instead.
# Dates are when each patch went live (Pacific). B-patches and mid-patch updates
# are folded into their parent patch.
# Source: esports.gg TFT patch schedule 2026, tftsense.gg Set 18 news log.
PATCH_CALENDAR = {
    18: [
        ("1", "2026-08-26"),
        ("2", "2026-09-10"),
        ("3", "2026-09-23"),
        ("4", "2026-10-07"),
        ("5", "2026-10-21"),
        ("6", "2026-11-04"),
    ],
}
PACIFIC = timezone(timedelta(hours=-7))  # PDT; all Set 18 dates fall before Nov 1
# Games this close to a patch boundary are dropped, since rollout times vary by
# region and the client can lag the server.
BOUNDARY_BUFFER = timedelta(hours=12)


def patch_from_datetime(game_datetime_ms, set_number):
    """Map a game's epoch-ms timestamp to a patch label using PATCH_CALENDAR.

    Returns None if the set isn't in the calendar or the game is within
    BOUNDARY_BUFFER of a patch change.
    """
    schedule = PATCH_CALENDAR.get(set_number)
    if not schedule or game_datetime_ms is None:
        return None
    t = datetime.fromtimestamp(game_datetime_ms / 1000, tz=timezone.utc)
    starts = [(label, datetime.fromisoformat(d).replace(hour=10, tzinfo=PACIFIC))
              for label, d in schedule]
    current = None
    for label, start in starts:
        if abs(t - start) < BOUNDARY_BUFFER:
            return None
        if t >= start:
            current = label
    return current


def patch_windows(set_number):
    """(label, start_epoch_s, end_epoch_s) for each patch of a set that has started,
    with BOUNDARY_BUFFER trimmed off both ends."""
    schedule = PATCH_CALENDAR.get(set_number, [])
    now = datetime.now(timezone.utc)
    starts = [(label, datetime.fromisoformat(d).replace(hour=10, tzinfo=PACIFIC))
              for label, d in schedule]
    windows = []
    for i, (label, start) in enumerate(starts):
        if start >= now:
            break
        end = starts[i + 1][1] if i + 1 < len(starts) else now
        end = min(end, now)
        windows.append((label, int((start + BOUNDARY_BUFFER).timestamp()),
                        int((end - BOUNDARY_BUFFER).timestamp()) if end < now else int(now.timestamp())))
    return windows


def parse_patch(game_version, game_datetime_ms=None, set_number=None):
    """Return the patch label for a match.

    Old clients: "Linux Version 16.11.712.6420 ..." -> "Version.11" (the original
    format this project used; features.clean_patch strips it to "11").
    Unreal clients: no digits in game_version -> look up by timestamp.
    """
    if not re.search(r"\d+\.\d+", str(game_version)):
        return patch_from_datetime(game_datetime_ms, set_number)
    split_version = game_version.split(".")
    new_split = split_version[0].split(" ")
    return f"{new_split[1]}.{split_version[1]}"
