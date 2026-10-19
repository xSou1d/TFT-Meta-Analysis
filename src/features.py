import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_V2_PATH = os.path.join(ROOT_DIR, "data", "raw", "matches_v2.csv")
RAW_V1_PATH = os.path.join(ROOT_DIR, "data", "raw", "matches.csv")
# Prefer the refreshed v2 data (with real timestamps) when it exists
RAW_PATH = RAW_V2_PATH if os.path.exists(RAW_V2_PATH) else RAW_V1_PATH
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")


def clean_patch(val):
    val = str(val)
    if val.startswith("Version"):
        # Format is "Version.11" — split on "." and take the last part
        return val.split(".")[-1]
    return val


def load_raw_data(sample_tier="HIGH_ELO"):
    """Load raw match data and do basic cleaning.

    The shift-detection and stabilization analyses are about high elo, so by
    default only HIGH_ELO rows are kept (Gold/Plat rows are used separately by
    src.stats.compare_tiers). Pass sample_tier=None to keep every tier.
    """
    df = pd.read_csv(RAW_PATH)
    if sample_tier and "sample_tier" in df.columns:
        df = df[df["sample_tier"] == sample_tier]

    # Drop rows missing critical fields
    df = df.dropna(subset=["placement", "patch", "traits"])
    df["augments"] = df["augments"].fillna("").astype(str)

    # Ensure placement is integer
    df["patch"] = df["patch"].apply(clean_patch)

    # Order patches chronologically
    df["patch"] = df["patch"].astype(str)
    patch_order = sorted(df["patch"].unique(), key=lambda x: int(x))
    df["patch"] = pd.Categorical(df["patch"], categories=patch_order, ordered=True)

    print(f"Loaded {len(df)} rows across {df['patch'].nunique()} patches.")
    print(f"Patches: {list(df['patch'].cat.categories)}")
    return df


def build_trait_timeseries(df):
    df["trait"] = df["traits"].str.split(",")
    df = df.explode("trait")

    df["trait"] = df["trait"].str.strip()
    df = df[df["trait"] != ""]

    grouped = df.groupby(["patch", "trait"]).agg(
        play_count=("placement", "count"),
        avg_placement=("placement", "mean"),
        top4_rate=("placement", lambda x: (x <= 4).mean())
    )

    grouped = grouped.reset_index()
    return grouped


def save_processed(df, filename):
    """Save a processed DataFrame to the processed data folder."""
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    output_path = os.path.join(PROCESSED_PATH, filename)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")


def build_exploded_df(df):
    """Return a per-trait-per-game DataFrame for statistical testing."""
    df = df.copy()
    df["trait"] = df["traits"].str.split(",")
    df = df.explode("trait")
    df["trait"] = df["trait"].str.strip()
    df = df[df["trait"] != ""]
    df["patch"] = df["patch"].astype(str)
    cols = ["match_id", "patch", "trait", "placement"]
    if "game_datetime" in df.columns:
        cols.append("game_datetime")
    return df[cols]


if __name__ == "__main__":
    df = load_raw_data()
    trait_ts = build_trait_timeseries(df)
    print(trait_ts.head(10))
    print(f"Total trait-patch combinations: {len(trait_ts)}")
    save_processed(trait_ts, "trait_timeseries.csv")