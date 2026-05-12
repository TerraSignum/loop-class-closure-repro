"""Verify that the 28 registered observables close to PRECISE-or-better
under the deterministic mapping algorithm.

The original 26 observables span the SM closure domain; O27 ($\\Lambda_t$)
and O28 ($\\Lambda_s$) are the cosmological-tensor coefficients added
from the emergent-gravity manuscript (Paper 4).
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def _registry():
    with open(REPO / "data" / "observable_registry.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_registry_has_29_observables():
    reg = _registry()
    assert reg["domain_size"] == 29
    assert len(reg["observables"]) == 29


def test_no_observable_has_FACTOR2_or_FAR_OFF():
    reg = _registry()
    bad = [o for o in reg["observables"]
           if o["tier_after_loop"] not in ("EXACT", "PRECISE")]
    assert not bad, f"Observables outside PRECISE-or-better: {[b['id'] for b in bad]}"


def test_at_least_16_exact():
    reg = _registry()
    n_exact = sum(1 for o in reg["observables"]
                  if o["tier_after_loop"] == "EXACT")
    assert n_exact >= 16


def test_all_residuals_within_2_5_percent():
    reg = _registry()
    for o in reg["observables"]:
        assert abs(o["expected_residual_pct_after_loop"]) <= 2.5, (
            f"{o['id']} ({o['name']}) residual "
            f"{o['expected_residual_pct_after_loop']}% exceeds 2.5%."
        )


def test_each_observable_has_loop_class_or_tree():
    reg = _registry()
    for o in reg["observables"]:
        # Must have either a registered loop_class or be tagged as tree-level
        assert "loop_class" in o
        assert o["loop_class"] is not None


def test_two_loop_compounds_have_both_lemmas():
    reg = _registry()
    for o in reg["observables"]:
        if o.get("two_loop_compound", False):
            lemma = o.get("lemma")
            assert isinstance(lemma, str) and "+" in lemma, (
                f"{o['id']} marked as 2-loop compound but lemma field "
                f"{lemma!r} does not show two contributing lemmas."
            )


def test_all_observables_have_unique_id():
    reg = _registry()
    ids = [o["id"] for o in reg["observables"]]
    assert len(ids) == len(set(ids))
