def parse_participant(participant, match_id, patch, game_datetime=None):
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


def parse_patch(game_version):
    split_version = game_version.split(".")
    new_split = split_version[0].split(" ")
    return f"{new_split[1]}.{split_version[1]}"