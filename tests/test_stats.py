import numpy as np
import pandas as pd

from src import stats as S


def test_cliffs_delta_matches_brute_force():
    rng = np.random.default_rng(1)
    a, b = rng.integers(1, 9, 200), rng.integers(1, 9, 150)
    brute = np.mean(np.sign(b[:, None] - a[None, :]))
    assert abs(S.cliffs_delta(a, b) - brute) < 1e-12


def test_permutation_pvalue_is_calibrated_under_null():
    rng = np.random.default_rng(2)
    pvals = [S.permutation_pvalue(rng.integers(1, 9, 80), rng.integers(1, 9, 80),
                                  n_perm=499, rng=rng) for _ in range(300)]
    # Under the null, about 5% should fall below 0.05
    assert 0.02 < np.mean(np.array(pvals) < 0.05) < 0.09


def test_permutation_detects_real_shift_and_never_returns_zero():
    rng = np.random.default_rng(3)
    a = rng.integers(1, 9, 2000)
    b = np.clip(a[:1500] + 1, 1, 8)
    p = S.permutation_pvalue(a, b, n_perm=999, rng=rng)
    assert 0 < p < 0.01


def test_bh_and_holm_match_reference():
    p = np.array([0.01, 0.04, 0.03, 0.005, 0.5])
    # Reference values from statsmodels.multipletests
    np.testing.assert_allclose(S.benjamini_hochberg(p), [0.025, 0.05, 0.05, 0.025, 0.5])
    np.testing.assert_allclose(S.holm(p), [0.04, 0.09, 0.09, 0.025, 0.5])


def test_eb_shrinks_small_samples_more():
    summ = pd.DataFrame({
        "patch": ["1"] * 4, "trait": list("abcd"),
        "n": [1000, 1000, 1000, 5], "avg_placement": [4.4, 4.5, 4.6, 2.0],
        "sd": [2.29] * 4,
    })
    out = S.eb_shrink_placement(summ).set_index("trait")
    assert out.loc["d", "eb_shrinkage"] > out.loc["a", "eb_shrinkage"]
    assert out.loc["d", "eb_avg_placement"] > 3.5          # pulled hard toward ~4.5
    assert abs(out.loc["a", "eb_avg_placement"] - 4.4) < 0.05  # barely moved


def test_wilson_ci_bounds():
    lo, hi = S.wilson_ci(np.array([0, 5, 10]), np.array([10, 10, 10]))
    assert (lo >= -1e-12).all() and (hi <= 1 + 1e-12).all()
    assert abs(lo[0]) < 1e-12 and abs(hi[2] - 1) < 1e-12
