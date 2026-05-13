"""Phase-3 cross-verification: 6 two-loop compounds + 2 structural
observables must reproduce the existing P3 registry without any
registry access during extraction.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tuple_compiler.extract_topology_tuple import extract_all
from tuple_compiler.loop_class_predictor import _predict_one


COMPOUND_IDS = {"O11", "O12", "O23", "O24", "O25", "O26"}
STRUCTURAL_IDS = {"O27", "O28"}
PHASE3_IDS = COMPOUND_IDS | STRUCTURAL_IDS


def _normalise(s: str) -> str:
    return "".join(s.split())


REGISTRY_TO_COMPILER = {
    "eps_sync2": "eps_sync^2",
    "**":        "^",  # alpha_xi**2 -> alpha_xi^2
}


def _normalise_registry(s: str) -> str:
    s = "".join(s.split())
    for k, v in REGISTRY_TO_COMPILER.items():
        s = s.replace(k, v)
    return s


@pytest.fixture(scope="module")
def registry(repo_root: Path) -> dict:
    return json.loads(
        (repo_root / "data" / "observable_registry.json").read_text(
            encoding="utf-8"))


@pytest.fixture(scope="module")
def predictions(repo_root: Path, loop_map_path: Path) -> dict:
    bundle = extract_all()
    assert bundle["n_errors"] == 0, bundle["errors"]
    loop_map = json.loads(loop_map_path.read_text(encoding="utf-8"))
    classes = loop_map["classes"]
    tree_class = loop_map["tree_class"]
    return {
        r["id"]: _predict_one(r, classes, tree_class)
        for r in bundle["results"]
    }


def test_all_phase3_observables_extracted(predictions):
    for obs_id in PHASE3_IDS:
        assert obs_id in predictions, f"{obs_id} missing from predictions"


@pytest.mark.parametrize("obs_id", sorted(COMPOUND_IDS))
def test_compound_factor_matches_registry(obs_id, predictions, registry):
    reg = next(o for o in registry["observables"] if o["id"] == obs_id)
    pred = predictions[obs_id]
    assert pred["status"] == "MATCHED", (
        f"{obs_id}: status={pred['status']}"
    )
    assert pred["closure_kind"] == "loop_compound"
    pred_factor = _normalise(pred["prediction"]["factor"])
    reg_factor  = _normalise_registry(reg["loop_class"])
    assert pred_factor == reg_factor, (
        f"{obs_id} ({reg['name']}): "
        f"compiler={pred_factor!r}, registry={reg_factor!r}"
    )


@pytest.mark.parametrize("obs_id", sorted(STRUCTURAL_IDS))
def test_structural_value_matches_registry(obs_id, predictions, registry):
    reg = next(o for o in registry["observables"] if o["id"] == obs_id)
    pred = predictions[obs_id]
    assert pred["closure_kind"] == "structural"
    assert pred["status"] == "MATCHED"
    pred_factor = _normalise(pred["prediction"]["factor"])
    reg_factor  = _normalise_registry(reg["loop_class"])
    assert pred_factor == reg_factor, (
        f"{obs_id} ({reg['name']}): "
        f"compiler={pred_factor!r}, registry={reg_factor!r}"
    )
    # Structural-rational must also match the registry's rational form.
    if "rational_form" in reg:
        pred_rat = _normalise(pred["prediction"]["rational"])
        reg_rat = _normalise(reg["rational_form"])
        assert pred_rat == reg_rat, (
            f"{obs_id}: compiler rational={pred_rat!r}, "
            f"registry rational_form={reg_rat!r}"
        )


def test_compound_lemma_id_format(predictions):
    """Compound lemma_id is a '+'-joined list of single-loop lemma_ids."""
    for obs_id in COMPOUND_IDS:
        pred = predictions[obs_id]
        lid = pred["prediction"]["lemma_id"]
        parts = lid.split("+")
        assert len(parts) >= 2, (
            f"{obs_id}: lemma_id={lid!r} should be '+'-joined (compound)"
        )


def test_factors_provenance_preserved(predictions):
    """Each compound's factors list must round-trip through the predictor."""
    for obs_id in COMPOUND_IDS:
        pred = predictions[obs_id]
        assert isinstance(pred["factors"], list)
        assert len(pred["factors"]) >= 2
        for f in pred["factors"]:
            assert "tuple" in f
            assert "expected_sign" in f
            assert f["expected_sign"] in (+1, -1)


def test_no_registry_access_during_extraction(predictions):
    """Predictor result must NOT carry any field from the registry
    (target, expected_residual_pct_after_loop, etc.)."""
    forbidden = {"target", "expected_residual_pct_after_loop",
                 "tier_after_loop", "pdg_value", "residual"}
    for obs_id, pred in predictions.items():
        all_keys = set(pred.keys())
        if "prediction" in pred:
            all_keys |= set(pred["prediction"].keys())
        assert all_keys.isdisjoint(forbidden), (
            f"{obs_id}: prediction leaks {all_keys & forbidden}"
        )
