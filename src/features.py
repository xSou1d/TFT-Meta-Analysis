import os
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(ROOT_DIR, "data", "raw", "matches.csv")
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")


def clean_patch(val):
    val = str(val)
    if val.startswith("Version"):
        # Format is "Version.11" — split on "." and take the last part
        return val.split(".")[-1]
    return val


def load_raw_data():
    """Load raw match data and do basic cleaning."""
    df = pd.read_csv(RAW_PATH)

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
    return df[["match_id", "patch", "trait", "placement"]]


if __name__ == "__main__":
    df = load_raw_data()
    trait_ts = build_trait_timeseries(df)
    print(trait_ts.head(10))
    print(f"Total trait-patch combinations: {len(trait_ts)}")
    save_processed(trait_ts, "trait_timeseries.csv")