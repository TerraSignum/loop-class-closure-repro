"""Phase-1 known-tuple regression: the 3 Phase-1 YAMLs must produce
the exact tuples documented in the existing P3 observable_registry,
and the predictor must assign them to the expected lemma_id.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tuple_compiler.loop_class_predictor import match_one
from tuple_compiler.tuple_rules import extract_tuple


EXPECTED = {
    "O07": {
        "name": "BH_entropy_quarter",
        "tuple": {"n": 1, "g": "0", "s": "0", "w": False, "r": False},
        "expected_sign": +1,
        "loop_dressed": False,
        "expected_lemma_id": "TREE",
    },
    "O13": {
        "name": "CKM_V_us",
        "tuple": {"n": 1, "g": "1/(2*N_gen)", "s": "0", "w": False, "r": False},
        "expected_sign": -1,
        "loop_dressed": True,
        "expected_lemma_id": "L6",
    },
    "O01": {
        "name": "alpha_dn_yukawa_exponent",
        "tuple": {"n": 1, "g": "0", "s": "0", "w": False, "r": False},
        "expected_sign": +1,
        "loop_dressed": True,
        "expected_lemma_id": "L1",
    },
}


def load_yaml_for(obs_id: str, yaml_dir: Path) -> dict:
    matches = list(yaml_dir.glob(f"{obs_id}_*.yaml"))
    assert len(matches) == 1, f"Expected one YAML for {obs_id}, found {matches}"
    with matches[0].open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize("obs_id,exp", sorted(EXPECTED.items()))
def test_phase1_tuple_matches_p3(obs_id, exp, yaml_dir):
    obs = load_yaml_for(obs_id, yaml_dir)
    result = extract_tuple(obs)
    assert result["id"] == obs_id
    assert result["name"] == exp["name"]
    assert result["tuple"] == exp["tuple"]
    assert result["expected_sign"] == exp["expected_sign"]
    assert result["loop_dressed"] == exp["loop_dressed"]


@pytest.mark.parametrize("obs_id,exp", sorted(EXPECTED.items()))
def test_phase1_lemma_match_unique_for_loop_dressed(
        obs_id, exp, yaml_dir, loop_map_path):
    """Loop-dressed observables must match exactly one lemma class."""
    if not exp["loop_dressed"]:
        pytest.skip(f"{obs_id} is tree-level; lemma assignment is TREE")

    classes = json.loads(
        loop_map_path.read_text(encoding="utf-8"))["classes"]
    obs = load_yaml_for(obs_id, yaml_dir)
    result = extract_tuple(obs)
    status, matches = match_one(result["tuple"], classes)
    assert status == "MATCHED", (
        f"{obs_id}: expected MATCHED, got {status}. "
        f"Matches: {[m['lemma_id'] for m in matches]}"
    )
    assert matches[0]["lemma_id"] == exp["expected_lemma_id"]


def test_no_loop_dressed_tuple_matches_multiple_lemmas(
        yaml_dir, loop_map_path):
    """No two lemma classes share the same (n, g, s, w, r) tuple."""
    classes = json.loads(
        loop_map_path.read_text(encoding="utf-8"))["classes"]
    seen = {}
    for cls in classes:
        key = (cls["match"]["n"], cls["match"]["g"], cls["match"]["s"],
               cls["match"]["w"], cls["match"]["r"])
        assert key not in seen, (
            f"Loop-class map has duplicate tuple {key}: "
            f"{seen[key]} vs {cls['lemma_id']}"
        )
        seen[key] = cls["lemma_id"]
