"""Verify that the deterministic loop-class mapping algorithm is unique.

the deterministic-mapping theorem says: given (n, g, s, double_wick, resummed) the
loop class is uniquely determined. This test exhaustively walks the
mapping table and asserts that every (n, g, s, double_wick, resummed)
combination has at most one entry.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import classify_observable as C


def _table():
    with open(REPO / "data" / "allowed_topological_multipliers.json", "r", encoding="utf-8") as f:
        return json.load(f)["mapping_algorithm_table"]


def test_table_loads():
    table = _table()
    assert len(table) >= 8


def test_classify_yukawa_damping():
    r = C.classify(n=1, g=0, s=0)
    assert r["lemma"] == 1
    assert r["name"] == "Yukawa-Damping"
    assert "gamma/4" in r["loop_class"]


def test_classify_pmns_self_energy():
    r = C.classify(n=1, g=0, s=0, double_wick=True)
    assert r["lemma"] == 2
    assert r["name"] == "PMNS-Self-Energy"


def test_classify_pure_self_energy():
    r = C.classify(n=4, g=0, s=0)
    assert r["lemma"] == 3
    assert r["name"] == "Pure-Self-Energy"


def test_classify_resummed_propagator():
    r = C.classify(n=4, g=0, s=0, resummed=True)
    assert r["lemma"] == 4
    assert r["name"] == "Resummed-Propagator"


def test_classify_cosmological_density():
    r = C.classify(n=2, g=0, s=0)
    assert r["lemma"] == 8
    assert r["name"] == "Cosmological-Density"


def test_classify_generation():
    r = C.classify(n=2, g="1/N_gen", s=0)
    assert r["lemma"] == 5
    assert r["name"] == "Generation"


def test_classify_sub_generation():
    r = C.classify(n=1, g="1/(2*N_gen)", s=0)
    assert r["lemma"] == 6
    assert r["name"] == "Sub-Generation"


def test_classify_ew_mixed():
    r = C.classify(n=1, g=0, s="eps^2")
    assert r["lemma"] == 7
    assert r["name"] == "EW-Mixed"


def test_classify_pure_sync():
    r = C.classify(n=0, g=0, s="eps^2 pure")
    assert r["lemma"] == "pure-eps2"


def test_unknown_topology_raises():
    """Unknown (n, g, s) must raise ValueError (NO_CLAIM)."""
    with pytest.raises(ValueError):
        C.classify(n=99, g="invalid", s="not-a-real-mode")


def test_table_has_no_duplicate_keys():
    """No two table entries may share (n, g, s, double_wick, resummed)."""
    table = _table()
    seen = set()
    for e in table:
        key = (e["n"], e["g"], e["s"],
               e.get("double_wick", False), e.get("resummed", False))
        assert key not in seen, f"Duplicate mapping key: {key}"
        seen.add(key)
