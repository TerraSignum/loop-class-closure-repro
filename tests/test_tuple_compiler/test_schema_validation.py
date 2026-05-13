"""Schema validation tests: every enum domain is enforced."""
from __future__ import annotations

import pytest

from tuple_compiler.schema import SchemaError, validate


def _base() -> dict:
    return {
        "id":   "TEST",
        "name": "test",
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


@pytest.mark.parametrize("n_bad", [-1, 3, 5, 1.5, "1", None])
def test_n_outside_domain_rejected(n_bad):
    obs = _base()
    obs["operator"]["spinor_trace_count"] = n_bad
    with pytest.raises(SchemaError, match="spinor_trace_count"):
        validate(obs)


@pytest.mark.parametrize("support_bad", ["single", "full", "adjacent",
                                          "weird", "", None])
def test_generation_support_outside_domain_rejected(support_bad):
    obs = _base()
    obs["generation"]["support"] = support_bad
    with pytest.raises(SchemaError, match="generation.support"):
        validate(obs)


def test_generation_symbol_mismatch_rejected():
    """If support says full_generation but symbol says sub-gen, reject."""
    obs = _base()
    obs["generation"] = {"support": "full_generation", "symbol": "1/(2*N_gen)"}
    with pytest.raises(SchemaError, match="does not match"):
        validate(obs)


@pytest.mark.parametrize("channel_bad", ["1", "eps", "eps^4", "gamma",
                                          None, ""])
def test_sync_channel_outside_domain_rejected(channel_bad):
    obs = _base()
    obs["sync"]["channel"] = channel_bad
    with pytest.raises(SchemaError, match="sync.channel"):
        validate(obs)


@pytest.mark.parametrize("sign_bad", [0, 2, -2, "+1", None, True])
def test_expected_sign_outside_domain_rejected(sign_bad):
    obs = _base()
    obs["parity"]["expected_sign"] = sign_bad
    with pytest.raises(SchemaError, match="expected_sign"):
        validate(obs)


@pytest.mark.parametrize("wickr_bad", [0, 1, "false", None])
def test_w_r_non_boolean_rejected(wickr_bad):
    for field in ("double_wick", "resummed", "loop_dressed"):
        obs = _base()
        obs["operator"][field] = wickr_bad
        with pytest.raises(SchemaError, match=field):
            validate(obs)


@pytest.mark.parametrize("missing_field", [
    "id", "name", "sector", "operator", "generation",
    "sync", "parity", "anchors", "schema_version",
])
def test_missing_top_level_field_rejected(missing_field):
    obs = _base()
    del obs[missing_field]
    with pytest.raises(SchemaError, match=missing_field):
        validate(obs)
