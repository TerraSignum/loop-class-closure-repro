"""Tests for the Phase I-IV cross-sector closure bundle."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_phase_i_iv_bundle as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "phase_i_iv_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_four_phases_present(bundle):
    for phase in ("phase_i", "phase_ii", "phase_iii", "phase_iv"):
        assert phase in bundle


def test_phase_i_six_closures(bundle):
    assert len(bundle["phase_i"]["closures"]) == 6
    ids = [c["id"] for c in bundle["phase_i"]["closures"]]
    assert "Lambda_QCD_threshold_matching" in ids
    assert "alpha_s_from_Lambda_QCD" in ids
    assert "EW_decay_widths" in ids


def test_phase_iv_six_closures(bundle):
    assert len(bundle["phase_iv"]["closures"]) == 6
    ids = [c["id"] for c in bundle["phase_iv"]["closures"]]
    assert "alpha_s_forward_4loop" in ids
    assert "einstein_gap_5point_fit" in ids
    assert "chiral_index_theorem" in ids


def test_summary_counts_match_actual(bundle):
    """Counts in summary_counts must agree with the actual closure lists."""
    s = bundle["summary_counts"]
    total = sum(len(bundle[ph]["closures"])
                for ph in ("phase_i", "phase_ii", "phase_iii", "phase_iv"))
    assert s["total_closures"] == total
    n_exact = sum(1 for ph in ("phase_i", "phase_ii", "phase_iii", "phase_iv")
                  for c in bundle[ph]["closures"] if c.get("tier") == "EXACT")
    n_precise = sum(1 for ph in ("phase_i", "phase_ii", "phase_iii", "phase_iv")
                    for c in bundle[ph]["closures"] if c.get("tier") == "PRECISE")
    assert s["EXACT"] == n_exact
    assert s["PRECISE"] == n_precise


def test_lambda_qcd_threshold_matching_precise(bundle):
    entry = next(c for c in bundle["phase_i"]["closures"]
                 if c["id"] == "Lambda_QCD_threshold_matching")
    assert entry["tier"] == "PRECISE"
    assert entry["ratio"] == pytest.approx(0.948, abs=0.005)


def test_alpha_s_forward_4loop_exact(bundle):
    entry = next(c for c in bundle["phase_iv"]["closures"]
                 if c["id"] == "alpha_s_forward_4loop")
    assert entry["tier"] == "EXACT"
    assert entry["ratio"] == pytest.approx(0.994, abs=0.001)


def test_einstein_gap_5point_alpha_close_to_two_thirds(bundle):
    entry = next(c for c in bundle["phase_iv"]["closures"]
                 if c["id"] == "einstein_gap_5point_fit")
    assert entry["ratio_alpha"] == pytest.approx(0.953, abs=0.01)


def test_recompute_consistent_with_bundled(output):
    assert output["consistent_with_bundled"] is True
    assert output["total_recomputed"] == 20
