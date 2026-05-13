"""The extractor MUST refuse any YAML that lets target values in.

This is the methodological lock: no observable definition can
sneak a target value past the extractor. The test exercises both
the anchors-block constraint and the "no extra fields" expectation
on the structural part of the YAML.
"""
from __future__ import annotations

import copy

import pytest

from tuple_compiler.schema import SchemaError
from tuple_compiler.tuple_rules import extract_tuple


def _valid_yaml() -> dict:
    return {
        "id":   "TEST",
        "name": "test_observable",
        "sector": "Test",
        "operator": {
            "kind": "test",
            "spinor_trace_count": 1,
            "double_wick": False,
            "resummed": False,
            "loop_dressed": True,
        },
        "generation": {"support": "none"},
        "sync":       {"channel": "0"},
        "parity":     {"expected_sign": +1},
        "anchors": {
            "target_value_allowed": False,
            "external_target_used_in_tuple": False,
        },
        "schema_version": "tuple-compiler-v0.1",
    }


def test_valid_yaml_passes():
    """Sanity: the baseline valid YAML extracts without error."""
    result = extract_tuple(_valid_yaml())
    assert result["tuple"]["n"] == 1


def test_target_value_allowed_true_rejected():
    """If target_value_allowed is true, extraction MUST fail."""
    obs = _valid_yaml()
    obs["anchors"]["target_value_allowed"] = True
    with pytest.raises(SchemaError, match="target_value_allowed"):
        extract_tuple(obs)


def test_external_target_used_in_tuple_true_rejected():
    """If external_target_used_in_tuple is true, extraction MUST fail."""
    obs = _valid_yaml()
    obs["anchors"]["external_target_used_in_tuple"] = True
    with pytest.raises(SchemaError, match="external_target_used_in_tuple"):
        extract_tuple(obs)


def test_missing_anchors_block_rejected():
    """If the anchors block is missing entirely, extraction MUST fail."""
    obs = _valid_yaml()
    del obs["anchors"]
    with pytest.raises(SchemaError, match="anchors"):
        extract_tuple(obs)


def test_target_value_truthy_not_just_truthy():
    """Anchors must be the literal boolean False, not just falsy."""
    for sneaky in (None, 0, "", "false"):
        obs = _valid_yaml()
        obs["anchors"]["target_value_allowed"] = sneaky
        with pytest.raises(SchemaError, match="literally false"):
            extract_tuple(obs)


def test_tuple_dict_contains_no_target_field():
    """The extracted tuple dict must not carry a target/expected field."""
    forbidden = {"target", "target_value", "expected_value",
                 "pdg_value", "residual"}
    obs = _valid_yaml()
    result = extract_tuple(obs)
    flat_keys = set(result.keys()) | set(result["tuple"].keys())
    assert flat_keys.isdisjoint(forbidden), (
        f"Tuple result leaks forbidden target-field(s): "
        f"{flat_keys & forbidden}"
    )


def test_deep_copy_of_input_not_required():
    """Extractor must not mutate the input dict in-place."""
    obs = _valid_yaml()
    snapshot = copy.deepcopy(obs)
    extract_tuple(obs)
    assert obs == snapshot, "Extractor mutated the input observable."
