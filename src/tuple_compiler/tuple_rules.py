"""Deterministic rules mapping observable YAML to topology tuple.

Each rule reads one and only one declared field from the YAML and
returns the corresponding tuple component. There is no scoring,
no fuzzy matching, and no string parsing of physics formulae --
all structural information is declared directly in the YAML.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

from . import schema


def infer_n(obs: Dict[str, Any]) -> int:
    """n = spinor_trace_count, declared directly. Domain {0, 1, 2, 4}."""
    return int(obs["operator"]["spinor_trace_count"])


def infer_g(obs: Dict[str, Any]) -> str:
    """g = generation suppression symbol, derived from support enum."""
    support = obs["generation"]["support"]
    return schema.g_symbol_from_support(support)


def infer_s(obs: Dict[str, Any]) -> str:
    """s = sync.channel symbol, declared directly."""
    return str(obs["sync"]["channel"])


def infer_w(obs: Dict[str, Any]) -> bool:
    """w = operator.double_wick, declared directly."""
    return bool(obs["operator"]["double_wick"])


def infer_r(obs: Dict[str, Any]) -> bool:
    """r = operator.resummed, declared directly."""
    return bool(obs["operator"]["resummed"])


def expected_sign(obs: Dict[str, Any]) -> int:
    """Sign is metadata for the predictor, NOT part of the tuple."""
    return int(obs["parity"]["expected_sign"])


def loop_dressed(obs: Dict[str, Any]) -> bool:
    """Tree-level (False) vs loop-dressed (True) is a discrete axiom.

    Not part of the tuple itself -- the tuple encodes the structural
    operator signature; the dressing axiom decides whether the
    observable carries the lemma's loop factor or sits at tree-level
    with that same structural signature.
    """
    return bool(obs["operator"]["loop_dressed"])


def extract_tuple(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate then extract the (n, g, s, w, r) tuple.

    Returns a dict with the tuple plus passthrough metadata
    (expected_sign and loop_dressed). The target value is NEVER
    read or returned -- the YAML schema forbids carrying one.
    """
    schema.validate(obs)
    return {
        "id":   obs["id"],
        "name": obs["name"],
        "sector": obs["sector"],
        "tuple": {
            "n": infer_n(obs),
            "g": infer_g(obs),
            "s": infer_s(obs),
            "w": infer_w(obs),
            "r": infer_r(obs),
        },
        "expected_sign": expected_sign(obs),
        "loop_dressed":  loop_dressed(obs),
    }


def tuple_as_canonical_key(t: Dict[str, Any]) -> Tuple[Any, ...]:
    """Stable hashable key for a tuple dict, for dictionary lookup."""
    return (t["n"], t["g"], t["s"], t["w"], t["r"])
