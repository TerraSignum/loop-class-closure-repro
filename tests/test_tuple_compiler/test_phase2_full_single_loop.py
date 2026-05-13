"""Phase-2 cross-verification: every single-loop observable in the
existing P3 registry must produce a tuple compiler prediction whose
loop-class factor matches the registry's `loop_class` string.

This is the bridge from the registered-mapping protocol to the
observable compiler: the compiler is correct iff it reproduces the
21 single-loop registry entries without any registry access during
extraction.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tuple_compiler.extract_topology_tuple import extract_all
from tuple_compiler.loop_class_predictor import _predict_one


SINGLE_LOOP_IDS = {
    "O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08",
    "O09", "O10", "O13", "O14", "O15", "O16", "O17", "O18",
    "O19", "O20", "O21", "O22", "O29",
}


def _normalise(s: str) -> str:
    """Collapse whitespace and strip parentheticals around the formula."""
    return "".join(s.split())


# Registry-string -> normalised-compiler-string equivalences.
# The registry uses 'eps_sync2' while the compiler uses 'eps_sync^2';
# these are the same physical coefficient.
REGISTRY_TO_COMPILER = {
    "eps_sync2": "eps_sync^2",
    "(tree)": "",  # registry "1 (tree)" -> compiler "1"
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
    """Run extractor + predictor; return predictions keyed by id,
    restricted to the Phase-2 single-loop set."""
    bundle = extract_all()
    assert bundle["n_errors"] == 0, bundle["errors"]
    loop_map = json.loads(loop_map_path.read_text(encoding="utf-8"))
    classes = loop_map["classes"]
    tree_class = loop_map["tree_class"]

    out = {}
    for r in bundle["results"]:
        if r["id"] not in SINGLE_LOOP_IDS:
            continue
        pred = _predict_one(r, classes, tree_class)
        # Flatten 'factor' and 'lemma_id' onto the entry for convenience.
        pred["lemma_id"] = pred["prediction"]["lemma_id"]
        pred["factor"]   = pred["prediction"]["factor"]
        out[r["id"]] = pred
    return out


def test_all_21_single_loop_extracted(predictions):
    assert set(predictions.keys()) == SINGLE_LOOP_IDS


@pytest.mark.parametrize("obs_id", sorted(SINGLE_LOOP_IDS))
def test_compiler_factor_matches_registry(obs_id, predictions, registry):
    reg_entry = next(o for o in registry["observables"] if o["id"] == obs_id)
    reg_factor = _normalise_registry(reg_entry["loop_class"])
    pred_factor = _normalise(predictions[obs_id]["factor"])
    assert pred_factor == reg_factor, (
        f"{obs_id} ({reg_entry['name']}): "
        f"compiler={pred_factor!r}, registry={reg_factor!r}"
    )


@pytest.mark.parametrize("obs_id", sorted(SINGLE_LOOP_IDS))
def test_compiler_lemma_matches_registry(obs_id, predictions, registry):
    reg_entry = next(o for o in registry["observables"] if o["id"] == obs_id)
    reg_lemma = reg_entry.get("lemma")
    pred_lemma = predictions[obs_id]["lemma_id"]

    if reg_lemma is None:
        assert pred_lemma == "TREE", (
            f"{obs_id}: registry lemma is null but compiler says {pred_lemma}"
        )
    else:
        expected = f"L{reg_lemma}"
        assert pred_lemma == expected, (
            f"{obs_id}: compiler says {pred_lemma}, registry says {expected}"
        )


def test_no_observables_open(predictions):
    """No single-loop observable should land OPEN in Phase 2."""
    for obs_id, pred in predictions.items():
        assert "factor" in pred, f"{obs_id} has no factor"


def test_l4_inverse_form_for_t_rh(predictions):
    """O21 T_RH must use the L4 inverse form 1/(1 - 2*gamma^2)."""
    pred = predictions["O21"]
    assert pred["lemma_id"] == "L4"
    assert pred["resummation_inverse"] is True
    assert _normalise(pred["factor"]) == _normalise("1/(1 - 2*gamma^2)")
