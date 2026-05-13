"""End-to-end test: extractor produces a tuples bundle, predictor
consumes it, and the resulting predictions match the expected
lemma_ids for the Phase-1 observables.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tuple_compiler.extract_topology_tuple import extract_all
from tuple_compiler.loop_class_predictor import match_one


EXPECTED_PREDICTIONS = {
    "O01": ("L1",   "1 + gamma/4"),
    "O07": ("TREE", "1"),
    "O13": ("L6",   "1 - gamma/(2*N_gen)"),
}


@pytest.fixture(scope="module")
def bundle():
    return extract_all()


@pytest.fixture(scope="module")
def loop_map(loop_map_path):
    return json.loads(loop_map_path.read_text(encoding="utf-8"))


def test_no_extraction_errors(bundle):
    assert bundle["n_errors"] == 0, bundle["errors"]


def test_three_observables_extracted(bundle):
    assert bundle["n_observables"] == 3


def test_target_isolation_locked(bundle):
    assert bundle["target_isolation_locked"] is True


def test_each_result_has_no_target_field(bundle):
    forbidden = {"target", "target_value", "expected_value",
                 "pdg_value", "residual"}
    for r in bundle["results"]:
        keys = set(r.keys()) | set(r["tuple"].keys())
        assert keys.isdisjoint(forbidden)


def test_predictions_match_expected(bundle, loop_map):
    classes = loop_map["classes"]
    tree_class = loop_map["tree_class"]

    by_id = {r["id"]: r for r in bundle["results"]}
    for obs_id, (expected_lemma, expected_factor) in EXPECTED_PREDICTIONS.items():
        r = by_id[obs_id]
        if not r["loop_dressed"]:
            assert tree_class["lemma_id"] == expected_lemma
            assert tree_class["factor_plus"] == expected_factor
        else:
            status, matches = match_one(r["tuple"], classes)
            assert status == "MATCHED"
            cls = matches[0]
            assert cls["lemma_id"] == expected_lemma
            sign = r["expected_sign"]
            factor = cls["factor_plus"] if sign > 0 else cls["factor_minus"]
            assert factor == expected_factor, (
                f"{obs_id}: expected {expected_factor}, got {factor}"
            )
