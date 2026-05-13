"""Phase-5 structural evaluator tests.

Each Phase-5 YAML declares a structural identity in the System-R
rationals. The structural compiler must evaluate the formula EXACTLY
(via sympy symbolic arithmetic) and the rational coefficient must
match the claimed structural_rational under Fraction equality.

No tolerance, no fallback, no stub. Every test asserts exact equality.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from tuple_compiler.structural_evaluator import (
    StructuralEvaluationError,
    SYSTEM_R_SYMBOLS,
    evaluate_structural,
    parse_claimed_rational,
    parse_expression,
    verify_structural_match,
)


# (yaml_id, structural_formula, claimed_rational, is_pure_rational)
PHASE5_CASES = [
    ("HK-09", "2 * gamma^2 * (1 + gamma)",          "11/500",   True),
    ("HK-10", "1/4 + alpha_xi/16",                   "49/160",   True),
    ("HK-11", "1/2 + alpha_xi/12",                   "23/40",    True),
    ("HK-12", "pi * (1 + gamma) * (1 - gamma^2/4)",  "4389/4000", False),
    ("HJ-13", "alpha_xi * s_face",                   "9/40",     True),
    ("HQ-14", "alpha_xi / (2 * (2*d + N_gen))",      "9/220",    True),
    ("O27",   "alpha_xi^2",                          "81/100",   True),
    ("O28",   "-gamma^2/2",                          "-1/200",   True),
]


@pytest.mark.parametrize("yid,formula,claimed,is_pure",
                          [(c[0], c[1], c[2], c[3]) for c in PHASE5_CASES])
def test_structural_form_evaluates_exactly(yid, formula, claimed, is_pure):
    """Every Phase-5 structural form MUST evaluate to exactly its
    claimed rational. EXACT means Fraction equality, no float tolerance."""
    symbolic, rational_coeff, is_pure_rational = evaluate_structural(formula)
    expected = parse_claimed_rational(claimed)
    assert rational_coeff == expected, (
        f"{yid}: {formula} -> {rational_coeff}, expected {expected}"
    )
    assert is_pure_rational == is_pure, (
        f"{yid}: is_pure_rational={is_pure_rational}, expected {is_pure}"
    )


@pytest.mark.parametrize("yid,formula,claimed,_is_pure",
                          [(c[0], c[1], c[2], c[3]) for c in PHASE5_CASES])
def test_verify_structural_match_passes(yid, formula, claimed, _is_pure):
    """verify_structural_match returns a clean match dict for each
    Phase-5 case without raising."""
    result = verify_structural_match(formula, claimed)
    assert result["exact_match"] is True
    assert result["rational_coefficient"] == str(parse_claimed_rational(claimed))


def test_unknown_identifier_rejected():
    """The evaluator must REFUSE expressions with unknown identifiers,
    not silently substitute zero or a default."""
    with pytest.raises(StructuralEvaluationError, match="unknown identifier"):
        parse_expression("alpha_xi * unknown_constant + gamma")


def test_float_in_claimed_rational_rejected():
    """Claimed rationals must be exact p/q, not floats."""
    with pytest.raises(StructuralEvaluationError, match="not an exact"):
        parse_claimed_rational("0.555")
    with pytest.raises(StructuralEvaluationError, match="not an exact"):
        parse_claimed_rational("9/40.0")


def test_mismatch_rejected_with_explicit_error():
    """If the formula evaluates to a different rational than claimed,
    verify_structural_match must raise -- no silent acceptance."""
    with pytest.raises(StructuralEvaluationError, match="rational forms differ"):
        verify_structural_match("alpha_xi^2", "82/100")


def test_no_fallback_for_unsupported_irrationals():
    """An expression with sqrt(2) or other irrationals not handled
    cleanly must raise -- no float fallback."""
    # sqrt(2) is irrational and not pi^1, so the evaluator should refuse.
    with pytest.raises(StructuralEvaluationError, match="neither a pure rational"):
        evaluate_structural("sqrt(2) * gamma")


def test_system_r_symbol_table_constants():
    """The System-R symbol table must contain the canonical rationals."""
    assert SYSTEM_R_SYMBOLS["gamma"]     == Fraction(1, 10)
    assert SYSTEM_R_SYMBOLS["alpha_xi"]  == Fraction(9, 10)
    assert SYSTEM_R_SYMBOLS["beta_pi"]   == Fraction(15, 16)
    assert SYSTEM_R_SYMBOLS["eps_sync2"] == Fraction(1, 20)
    assert SYSTEM_R_SYMBOLS["D_Omega"]   == Fraction(67, 80)
    assert SYSTEM_R_SYMBOLS["N_gen"]     == 3
    assert SYSTEM_R_SYMBOLS["d"]         == 4
    assert SYSTEM_R_SYMBOLS["s_face"]    == Fraction(1, 4)


def test_o27_and_o28_match_p4_branch_resolved():
    """O27 Lambda_t = alpha_xi^2 and O28 Lambda_s = -gamma^2/2 must
    match the P4 branch-resolved values 81/100 and -1/200 exactly.
    These are the canonical Lambda_munu tensor diagonal components
    (matter-branch trace and spatial component)."""
    _, t_rat, _ = evaluate_structural("alpha_xi^2")
    _, s_rat, _ = evaluate_structural("-gamma^2/2")
    assert t_rat == Fraction(81, 100)
    assert s_rat == Fraction(-1, 200)
    # P4 branch-resolved identity: T_00^vac = alpha_xi^2 + 3*gamma^2 = 84/100
    _, t00_vac, _ = evaluate_structural("alpha_xi^2 + 3*gamma^2")
    assert t00_vac == Fraction(84, 100)
    # P4 branch-resolved: Lambda_t^vac = alpha_xi^2 + 3*gamma^2/2 = 33/40
    _, lt_vac, _ = evaluate_structural("alpha_xi^2 + 3*gamma^2/2")
    assert lt_vac == Fraction(33, 40)
