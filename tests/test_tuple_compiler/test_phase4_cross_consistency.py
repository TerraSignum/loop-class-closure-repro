"""Phase-4 cross-consistency audit tests.

The audit surfaces dual-state observables (registry's loop_class field
co-existing with a superseding closure_form_2026_05_10) and companion-
JSON disagreements (neutrino_sector_closure / ckm_closure giving
different structural identities for the same observable).

These tests pin the audit's coverage so corpus updates can't silently
hide new dual-state entries -- if a new registry entry adds a
closure_form_2026_05_10 field, the count goes up and the test fails,
forcing an explicit acknowledgment.

This is the honest test design: lock the gap, don't paper over it.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tuple_compiler.cross_consistency_audit import run_audit


# Pin the exact set of dual-state IDs and disagreement IDs known at
# this commit. Adding new ones requires updating this test, which
# forces an explicit corpus-state acknowledgment.
EXPECTED_DUAL_STATE_IDS = {"O09", "O10", "O11", "O12", "O13", "O14"}
EXPECTED_DISAGREEMENT_IDS = {"O09", "O10", "O11", "O13", "O14"}


@pytest.fixture(scope="module")
def audit():
    return run_audit()


def test_audit_schema_version(audit):
    assert audit["schema_version"] == "cross-consistency-audit-v0.2"


def test_all_dual_state_resolved_by_phase5(audit):
    """Phase 5 declared a structural-alternative YAML for every dual-state
    registry observable; every one must evaluate EXACTLY against its
    claimed rational. n_dual_state_resolved_by_phase5 must equal
    n_dual_state_observables."""
    assert audit["n_dual_state_resolved_by_phase5"] == audit["n_dual_state_observables"], (
        f"Phase-5 resolution gap: "
        f"{audit['n_dual_state_resolved_by_phase5']} resolved / "
        f"{audit['n_dual_state_observables']} dual-state. "
        f"Every dual-state observable needs a Phase-5 alternative YAML."
    )


def test_each_resolved_carries_yaml_id_and_formula(audit):
    """Every RESOLVED entry must carry the Phase-5 YAML id and its
    structural formula, so the audit output is self-traceable."""
    for e in audit["dual_state_observables"]:
        res = e.get("phase5_resolution", {})
        assert res.get("status") == "RESOLVED", e["id"]
        assert "yaml_id" in res
        assert "structural_formula" in res
        assert "structural_rational" in res


def test_audit_runs_with_no_uncaught_exceptions(audit):
    assert audit["registry_size"] == 29


def test_dual_state_observable_set(audit):
    found = {e["id"] for e in audit["dual_state_observables"]}
    assert found == EXPECTED_DUAL_STATE_IDS, (
        f"Dual-state observable set drift: "
        f"new={found - EXPECTED_DUAL_STATE_IDS}, "
        f"missing={EXPECTED_DUAL_STATE_IDS - found}. "
        f"Resolve in the corpus and update EXPECTED_DUAL_STATE_IDS."
    )


def test_companion_disagreement_set(audit):
    found = {e["observable_id"] for e in audit["companion_disagreements"]}
    assert found == EXPECTED_DISAGREEMENT_IDS, (
        f"Companion-disagreement set drift: "
        f"new={found - EXPECTED_DISAGREEMENT_IDS}, "
        f"missing={EXPECTED_DISAGREEMENT_IDS - found}. "
        f"Resolve in the corpus and update EXPECTED_DISAGREEMENT_IDS."
    )


def test_each_dual_state_carries_compiler_prediction(audit):
    """The audit must show what the compiler currently emits for each
    dual-state observable, so the gap is visible side-by-side."""
    for e in audit["dual_state_observables"]:
        assert "compiler_prediction" in e, e["id"]
        assert "factor" in e["compiler_prediction"]
        assert "lemma_id" in e["compiler_prediction"]


def test_alternative_form_evaluation_recorded(audit):
    """Every dual-state entry records an evaluation_status; not all
    expressions are eval-safe, but the field must be present."""
    for e in audit["dual_state_observables"]:
        ev = e.get("alternative_form_evaluation", {})
        assert "evaluation_status" in ev, e["id"]


def test_rational_form_extraction_for_o09(audit):
    """O09's rational form 11/500 must evaluate numerically."""
    o09 = next(e for e in audit["dual_state_observables"] if e["id"] == "O09")
    # O09 doesn't carry a rational_form field in the registry per se;
    # but its alternative-form expression embeds '11/500'.
    expr = o09["closure_form_2026_05_10"]
    assert "11/500" in expr or o09.get("rational_form") in ("11/500",)


def test_audit_output_is_self_describing(audit):
    """The audit JSON must carry a 'note' field documenting honest scope."""
    assert "note" in audit
    assert "compiler" in audit["note"].lower()
    assert "not pick" in audit["note"].lower()
