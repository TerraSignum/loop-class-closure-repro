"""Structural-identity evaluator for closure_kind=structural observables.

Phase 5 of the tuple compiler. Where Phases 1-3 handled the loop-class
closures (tree x loop factor product), this module handles observables
whose closure mechanism is a direct System-R rational identity.

The evaluator uses sympy for exact symbolic arithmetic in the System-R
rational constants:

    gamma     = 1/10
    alpha_xi  = 9/10
    beta_pi   = 15/16
    eps_sync2 = 1/20         (alias: eps_sync^2)
    D_Omega   = 67/80
    N_gen     = 3
    d         = 4
    s_face    = 1/4          (BH-entropy face fraction; see
                              data/closure_derivations/HJ_Vus_alpha_xi_quarter.py)
    pi        = sympy.pi     (exact symbolic)

No float approximation, no fallback, no stub. Every structural_formula
must evaluate to a sympy expression whose rational coefficient matches
the claimed structural_rational EXACTLY (Fraction equality).
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any, Dict, Tuple

import sympy


# Symbol table -- every constant is an exact sympy expression.
SYSTEM_R_SYMBOLS: Dict[str, sympy.Expr] = {
    "gamma":      sympy.Rational(1, 10),
    "alpha_xi":   sympy.Rational(9, 10),
    "beta_pi":    sympy.Rational(15, 16),
    "eps_sync2":  sympy.Rational(1, 20),
    "D_Omega":    sympy.Rational(67, 80),
    "N_gen":      sympy.Integer(3),
    "d":          sympy.Integer(4),
    "s_face":     sympy.Rational(1, 4),
    "pi":         sympy.pi,
}


class StructuralEvaluationError(ValueError):
    """Raised when a structural expression cannot be evaluated exactly."""


def _normalise_expression(expr: str) -> str:
    """Convert YAML expression syntax to sympy-parseable Python syntax.

    Rules:
    - Strip leading/trailing whitespace.
    - Strip any '= <value>' or '(<comment>)' suffix appearing after a
      space in the expression. This handles registry strings like
      `2 gamma^2 (1+gamma) = 11/500 (H-K)` whose informative tail is
      not part of the algebraic expression.
    - Replace caret '^' with Python power '**'.
    - The expression MUST already use explicit '*' for multiplication.
    """
    s = expr.strip()
    # Strip ' = anything' tail (the registry comment after equals).
    if " = " in s:
        s = s.split(" = ", 1)[0].strip()
    # Strip a trailing parenthetical comment like "... (H-K)" only if it
    # is space-separated from the algebraic content. We do NOT strip
    # parenthesised SUB-expressions like "(1+gamma)".
    # Approach: if the string ends with a parenthesised group preceded by
    # whitespace AND that group contains no operator symbols, treat it as
    # a comment and remove.
    m = re.match(r"^(.+?)\s+\(([^()]*)\)\s*$", s)
    if m and not re.search(r"[+\-*/^]", m.group(2)):
        s = m.group(1).strip()
    s = s.replace("^", "**")
    # Reject consecutive binary-op typos like 'gamma + + alpha_xi' that
    # sympy silently collapses via unary-+ semantics. We DO permit '**'
    # (already converted from '^') and '+-' style unary ops only when
    # the second op is a unary-minus on a parenthesised group, which is
    # too unusual to write by accident. Strict rule: no two adjacent
    # binary operators with only whitespace between.
    if re.search(r"[+\-*/]\s*[+\-*/]", s.replace("**", "POW")):
        raise StructuralEvaluationError(
            f"Structural expression {expr!r} contains consecutive "
            f"binary operators (e.g. '+ +', '+ -'); sympy's unary-+/- "
            f"semantics would silently collapse these. Fix the typo "
            f"or rewrite using explicit parentheses."
        )
    return s


def parse_expression(expr: str) -> sympy.Expr:
    """Parse the YAML structural_formula into a sympy expression.

    Uses sympy.sympify with the SYSTEM_R_SYMBOLS dict as the local
    namespace, so every constant resolves to its exact rational value.
    Refuses any expression that uses an unknown identifier -- no
    silent zero-substitution.
    """
    normalised = _normalise_expression(expr)

    # Sympy will allow undefined symbols by default (they become free
    # variables). We want EXPLICIT failure on unknown identifiers, so
    # we collect the set of free symbols after parsing and refuse if
    # any are not in our table.
    try:
        parsed = sympy.sympify(normalised, locals=SYSTEM_R_SYMBOLS,
                                evaluate=True)
    except (sympy.SympifyError, SyntaxError, TypeError) as exc:
        raise StructuralEvaluationError(
            f"Failed to parse structural expression {expr!r} "
            f"(normalised={normalised!r}): {exc}"
        ) from exc

    unknown = parsed.free_symbols - set(
        sympy.Symbol(n) for n in SYSTEM_R_SYMBOLS
    )
    if unknown:
        raise StructuralEvaluationError(
            f"Structural expression {expr!r} uses unknown identifiers "
            f"{sorted(str(s) for s in unknown)} not in the System-R table "
            f"{sorted(SYSTEM_R_SYMBOLS.keys())}."
        )

    return parsed


def evaluate_structural(formula: str
                        ) -> Tuple[sympy.Expr, Fraction, bool]:
    """Evaluate a structural expression in the System-R rationals.

    Returns a tuple (symbolic, rational_coefficient, is_pure_rational):
    - symbolic: the sympy expression after substitution (may contain pi)
    - rational_coefficient: the Fraction part. For a pure rational
      expression, this IS the value. For a pi-containing expression,
      it is the rational coefficient of pi^1.
    - is_pure_rational: True iff the expression has no pi/transcendental
      content (sympy reports is_rational).

    Raises StructuralEvaluationError if the expression cannot be reduced
    to either a pure rational or (rational * pi).
    """
    parsed = parse_expression(formula)
    simplified = sympy.simplify(parsed)

    if simplified.is_rational:
        rat = sympy.Rational(simplified)
        return simplified, Fraction(rat.p, rat.q), True

    # Try to express as (rational) * pi.
    # Polynomial form in pi.
    poly_pi = sympy.Poly(simplified, sympy.pi)
    if poly_pi.degree() == 1 and poly_pi.nth(0) == 0:
        coeff = sympy.Rational(poly_pi.nth(1))
        return simplified, Fraction(coeff.p, coeff.q), False

    raise StructuralEvaluationError(
        f"Structural expression {formula!r} -> {simplified} is neither a "
        f"pure rational nor a clean (rational * pi) form. The Phase-5 "
        f"evaluator does not silently approximate; the YAML must declare "
        f"a closure that lands in one of these two exact classes."
    )


def parse_claimed_rational(claimed: str) -> Fraction:
    """Parse the structural_rational field of a YAML.

    Accepted forms:
    - 'p/q'    e.g. '49/160', '-1/200'
    - 'p'      e.g. '0', '5'
    No floats, no decimals -- the claimed rational must be exact.
    """
    s = claimed.strip()
    m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", s)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    if re.fullmatch(r"-?\d+", s):
        return Fraction(int(s))
    raise StructuralEvaluationError(
        f"structural_rational={claimed!r} is not an exact p/q rational. "
        f"Floats and decimals are not accepted -- declare the exact form."
    )


def verify_structural_match(formula: str, claimed_rational: str
                            ) -> Dict[str, Any]:
    """Evaluate the formula and assert it matches the claimed rational EXACTLY.

    Returns a result dict; raises StructuralEvaluationError if the
    evaluated value does not equal the claimed rational under
    Fraction equality. No tolerance, no approximate match.
    """
    symbolic, rational_coeff, is_pure_rational = evaluate_structural(formula)
    claimed = parse_claimed_rational(claimed_rational)

    if rational_coeff != claimed:
        raise StructuralEvaluationError(
            f"Structural mismatch: formula={formula!r} evaluates to "
            f"rational coefficient {rational_coeff} but claimed_rational "
            f"is {claimed} (rational forms differ EXACTLY)."
        )

    return {
        "formula":              formula,
        "symbolic":             str(symbolic),
        "rational_coefficient": str(rational_coeff),
        "claimed_rational":     str(claimed),
        "is_pure_rational":     is_pure_rational,
        "exact_match":          True,
    }
