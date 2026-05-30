import os
import pandas as pd
import numpy as np
from scipy import stats
from src.features import build_exploded_df

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_PATH = os.path.join(ROOT_DIR, "data", "processed")


def load_trait_timeseries():
    """Load the processed trait time series."""
    path = os.path.join(PROCESSED_PATH, "trait_timeseries.csv")
    df = pd.read_csv(path)
    df["patch"] = pd.Categorical(df["patch"],
                                  categories=sorted(df["patch"].unique(), key=lambda x: int(x)),
                                  ordered=True)
    return df


def filter_traits(df, min_play_count=30):
    """Keep only traits that appear at least min_play_count times in every patch."""
    patch_counts = df.groupby("trait")["play_count"].min()
    valid_traits = patch_counts[patch_counts >= min_play_count].index
    filtered = df[df["trait"].isin(valid_traits)]
    print(f"Traits passing filter: {filtered['trait'].nunique()} of {df['trait'].nunique()}")
    return filtered


def detect_shifts(df):
    detected_shifts = []

    for trait in df["trait"].unique():
        trait_df = df[df["trait"] == trait].sort_values("patch")
        placements = trait_df["avg_placement"].tolist()
        patches = trait_df["patch"].tolist()

        for i in range(len(placements) - 1):
            delta = placements[i + 1] - placements[i]
            detected_shifts.append({
                "trait": trait,
                "patch_from": patches[i],
                "patch_to": patches[i + 1],
                "placement_before": placements[i],
                "placement_after": placements[i + 1],
                "delta": delta
            })

    if not detected_shifts:
        return pd.DataFrame(columns=["trait", "patch_from", "patch_to",
                                     "placement_before", "placement_after", "delta"])

    result = pd.DataFrame(detected_shifts)
    result = result.sort_values("delta", key=abs, ascending=False)
    return result


def permutation_test(group_a, group_b, n_permutations=1000):
    """
    Test whether the difference in mean placement between two groups
    is statistically significant using a permutation test.

    Returns the p-value.
    """
    observed_delta = np.mean(group_b) - np.mean(group_a)
    combined = np.concatenate([group_a, group_b])
    count = 0

    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_a = combined[:len(group_a)]
        perm_b = combined[len(group_a):]
        perm_delta = np.mean(perm_b) - np.mean(perm_a)
        if abs(perm_delta) >= abs(observed_delta):
            count += 1

    return count / n_permutations


def test_shifts(df, shifts):
    shifts["patch_from"] = shifts["patch_from"].astype(str)
    shifts["patch_to"] = shifts["patch_to"].astype(str)

    for idx, row in shifts.iterrows():
        mask_a = (df["trait"] == row["trait"]) & (df["patch"] == row["patch_from"])
        mask_b = (df["trait"] == row["trait"]) & (df["patch"] == row["patch_to"])

        group_a = df[mask_a]["placement"].values
        group_b = df[mask_b]["placement"].values

        p_val = permutation_test(group_a, group_b)
        shifts.at[idx, "p_value"] = p_val

    shifts["significant"] = shifts["p_value"] < 0.05
    return shifts


if __name__ == "__main__":
    from src.features import load_raw_data, build_exploded_df

    raw_df = load_raw_data()
    exploded_df = build_exploded_df(raw_df)

    trait_ts = load_trait_timeseries()
    filtered = filter_traits(trait_ts, min_play_count=30)
    shifts = detect_shifts(filtered)

    tested = test_shifts(exploded_df, shifts)
    print(tested[["trait", "patch_from", "patch_to", "delta", "p_value", "significant"]].to_string())

    save_processed = tested[tested["significant"] == True]
    save_processed.to_csv(
        os.path.join(ROOT_DIR, "data", "processed", "significant_shifts.csv"),
        index=False
    )
    print(f"\nSaved {len(save_processed)} significant shifts.")