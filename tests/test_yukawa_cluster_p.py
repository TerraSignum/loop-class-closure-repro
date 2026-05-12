"""Tests for the Yukawa-Damping cluster joint-null computation.

The manuscript reports a joint random-null probability
P_combined approx 2.6e-5 (~4.0 sigma two-sided) via Fisher's
combined-p test on the three observables alpha_dn (0.0001%),
w_DE (0.05%), H_0 (0.6%) closing on the same loop class
(1+gamma/4) under a uniform null on [0, 2.5%].
The script compute_yukawa_cluster_p.py reproduces this end to end.
"""

import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import compute_yukawa_cluster_p as M  # noqa: E402


def test_per_observable_p_values():
    """Each observable's one-sided p-value under uniform null."""
    assert M.per_observable_p(0.0001, 2.5) == pytest.approx(4.0e-5, abs=1e-9)
    assert M.per_observable_p(0.05, 2.5) == pytest.approx(0.02, abs=1e-9)
    assert M.per_observable_p(0.6, 2.5) == pytest.approx(0.24, abs=1e-9)


def test_fisher_combined_p_matches_manuscript():
    """Fisher's combined-p on the three actual residuals must give
    p_combined ~ 2.6e-5 (~ 4.0 sigma)."""
    p_values = [
        M.per_observable_p(0.0001, 2.5),
        M.per_observable_p(0.05, 2.5),
        M.per_observable_p(0.6, 2.5),
    ]
    T, k, p_combined = M.fisher_combined_p(p_values)
    assert k == 3
    # T = -2 (ln(4e-5) + ln(0.02) + ln(0.24)) = ~30.93
    assert T == pytest.approx(30.93, abs=0.01)
    # p_combined = P(chi^2_6 >= 30.93) ~ 2.6e-5
    assert p_combined == pytest.approx(2.6e-5, rel=0.05)


def test_chi_square_survival_known_values():
    """Chi-square survival function on standard reference points."""
    # P(chi^2_2 >= 0) = 1
    assert M.chi_square_survival(0.0, 2) == pytest.approx(1.0, abs=1e-12)
    # P(chi^2_2 >= 2 ln(2)) = 1/2 (since chi^2_2 ~ Exp(1/2))
    assert M.chi_square_survival(2 * math.log(2), 2) == pytest.approx(0.5, abs=1e-6)
    # P(chi^2_6 >= 5.348) ~ 0.5 (median of chi^2_6)
    assert M.chi_square_survival(5.348, 6) == pytest.approx(0.5, abs=1e-2)


def test_sigma_equivalent_near_four():
    """Sigma equivalent of Fisher's combined p ~ 2.6e-5 is ~4.0."""
    p_values = [
        M.per_observable_p(0.0001, 2.5),
        M.per_observable_p(0.05, 2.5),
        M.per_observable_p(0.6, 2.5),
    ]
    _, _, p_combined = M.fisher_combined_p(p_values)
    sigma = M.sigma_from_p_two_sided(p_combined)
    assert sigma > 3.7
    assert sigma < 4.3


def test_legacy_threshold_formula_sensitivity_monotonic():
    """The legacy threshold-based formula is kept for traceability;
    its sensitivity sweep must be monotonic in the threshold."""
    pjs = []
    for thr in (0.01, 0.05, 0.1, 0.2, 0.5, 1.0):
        _, pj = M.joint_null_probability(thr, 2.5, 3)
        pjs.append(pj)
    for i in range(len(pjs) - 1):
        assert pjs[i] < pjs[i + 1]


def test_recompute_output_has_expected_structure():
    M.main()
    with open(REPO / "outputs" / "yukawa_cluster_joint_p.json",
              "r", encoding="utf-8") as f:
        out = json.load(f)
    pr = out["primary_result"]
    assert pr["method"] == "Fisher's combined-p test"
    assert pr["p_combined"] == pytest.approx(2.6e-5, rel=0.05)
    assert pr["sigma_equivalent"] > 3.7
    assert pr["sigma_equivalent"] < 4.3
    assert pr["df"] == 6
    assert out["shared_loop_class"] == "(1+gamma/4)"
    assert out["n_observables"] == 3
    assert len(out["cluster"]) == 3
    assert len(out["per_observable_p_values"]) == 3
    assert len(out["sensitivity_legacy"]) == 6
