"""Phase-6 tests: branch-resolved P4 + Lemma B + beta_pi structural
identities all evaluate EXACTLY against their claimed rationals.

The Phase-5 evaluator handled the 6 dual-state registry entries plus
O27/O28. Phase 6 closes the remaining structural-identity gap:
- P4 branch-resolved Eq. lambda_t_branch_resolved (manuscript line 3083)
- Lemma B family-coupling / skeleton / Kahale / 20/21 correction
- beta_pi refined-vacuum 143/144

Every test asserts Fraction-exact equality; no tolerance, no fallback.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from tuple_compiler.structural_evaluator import evaluate_structural


# (yaml_id, structural_formula, claimed_rational, is_pure_rational)
PHASE6_CASES = [
    # Branch-resolved P4 (Eq. lambda_t_branch_resolved)
    ("P4-VAC-T00",      "alpha_xi^2 + 3 * gamma^2",      "84/100",   True),
    ("P4-MAT-T00",      "alpha_xi^2",                    "81/100",   True),
    ("P4-VAC-G00",      "3 * gamma^2 / 2",               "3/200",    True),
    ("P4-MAT-G00",      "gamma^2 / 3",                   "1/300",    True),
    ("P4-VAC-LAMBDA-T", "alpha_xi^2 + 3 * gamma^2 / 2",  "33/40",    True),
    ("P4-VAC-LAMBDA-W", "(d - 1) / (2 * d)",             "3/8",      True),
    ("P4-MAT-LAMBDA-W", "(d - 1) / (2 * d) + 2 * gamma^2", "79/200", True),
    # Lemma B
    ("LEMB-FAMILY",     "(d + N_gen) / (2 * N_gen)",     "7/6",      True),
    ("LEMB-SKELETON",   "(d + N_gen) / (2 * d * N_gen)", "7/24",     True),
    ("LEMB-KAHALE",     "(d - 1) * N_gen / (d + N_gen)", "9/7",      True),
    ("LEMB-MASTER-CORRECTION",
                        "d * (d + 1) / (N_gen * (d + N_gen))",
                        "20/21",  True),
    # beta_pi refined
    ("BPI-REFINED-VACUUM",
                        "(2^d * N_gen^2 - 1) / (2^d * N_gen^2)",
                        "143/144", True),
]


@pytest.mark.parametrize("yid,formula,claimed,is_pure",
                          [(c[0], c[1], c[2], c[3]) for c in PHASE6_CASES])
def test_phase6_form_evaluates_exactly(yid, formula, claimed, is_pure):
    """Every Phase-6 structural form must evaluate to its exact claimed
    rational under Fraction equality."""
    symbolic, rational_coeff, is_pure_rational = evaluate_structural(formula)
    num, den = claimed.split("/")
    expected = Fraction(int(num), int(den))
    assert rational_coeff == expected, (
        f"{yid}: {formula} -> {rational_coeff}, expected {expected}"
    )
    assert is_pure_rational == is_pure, (
        f"{yid}: is_pure_rational={is_pure_rational}, expected {is_pure}"
    )


def test_lemma_b_master_identity():
    """The Lemma B master identity 7/6 = (9/10)*(9/7) + (1/100)*(20/21)
    must hold EXACTLY in the System-R rationals."""
    _, family,  _ = evaluate_structural("(d + N_gen) / (2 * N_gen)")
    _, kahale,  _ = evaluate_structural("(d - 1) * N_gen / (d + N_gen)")
    _, correct, _ = evaluate_structural(
        "d * (d + 1) / (N_gen * (d + N_gen))"
    )
    # Re-evaluate using sympy directly to compute alpha_xi * kahale + gamma^2 * correction
    _, master, _ = evaluate_structural(
        "alpha_xi * ((d - 1) * N_gen / (d + N_gen))"
        " + gamma^2 * (d * (d + 1) / (N_gen * (d + N_gen)))"
    )
    assert master == family == Fraction(7, 6)


def test_lemma_b_skeleton_via_spatial_dilution():
    """lambda_skel = (1/d) * lambda_family per the canonical
    1/d-spatial-dilution identification."""
    _, family,  _ = evaluate_structural("(d + N_gen) / (2 * N_gen)")
    _, skel,    _ = evaluate_structural("(d + N_gen) / (2 * d * N_gen)")
    assert skel == family / 4
    assert skel == Fraction(7, 24)


def test_lemma_b_lambda_w_chain():
    """3/8 = (7/24) * (9/7) = (d-1)/(2*d) EXACT closure of the
    weighted-Laplacian asymptote (vacuum branch)."""
    _, skel,   _ = evaluate_structural("(d + N_gen) / (2 * d * N_gen)")
    _, kahale, _ = evaluate_structural("(d - 1) * N_gen / (d + N_gen)")
    _, vac,    _ = evaluate_structural("(d - 1) / (2 * d)")
    assert skel * kahale == vac == Fraction(3, 8)


def test_branch_resolved_matter_shift_consistency():
    """The +2*gamma^2 matter-branch shift on lambda_w must equal the
    structural difference lambda_w^mat - lambda_w^vac."""
    _, vac, _ = evaluate_structural("(d - 1) / (2 * d)")
    _, mat, _ = evaluate_structural("(d - 1) / (2 * d) + 2 * gamma^2")
    _, shift, _ = evaluate_structural("2 * gamma^2")
    assert mat - vac == shift == Fraction(1, 50)


def test_t00_branch_difference_equals_3_gamma_squared():
    """T_00^vac - T_00^mat = 3*gamma^2 exactly (chirality-flip shift)."""
    _, vac, _ = evaluate_structural("alpha_xi^2 + 3 * gamma^2")
    _, mat, _ = evaluate_structural("alpha_xi^2")
    _, sh,  _ = evaluate_structural("3 * gamma^2")
    assert vac - mat == sh == Fraction(3, 100)


def test_x_minus_1_over_x_pattern_universal():
    """The (X-1)/X universal pattern: at X=21 (Lemma B family-coupling)
    and X=144 (beta_pi refined vacuum), both forms evaluate to
    (X-1)/X EXACTLY."""
    # X = 21 for Lemma B: 20/21
    _, lemma_b, _ = evaluate_structural(
        "d * (d + 1) / (N_gen * (d + N_gen))"
    )
    assert lemma_b == Fraction(20, 21)
    # X = 144 for beta_pi: 143/144
    _, bpi, _ = evaluate_structural(
        "(2^d * N_gen^2 - 1) / (2^d * N_gen^2)"
    )
    assert bpi == Fraction(143, 144)
    # Verify slot counts: 21 = N_gen*(d+N_gen), 144 = 2^d * N_gen^2
    _, x_lemb, _ = evaluate_structural("N_gen * (d + N_gen)")
    _, x_bpi,  _ = evaluate_structural("2^d * N_gen^2")
    assert x_lemb == 21
    assert x_bpi  == 144
