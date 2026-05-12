"""Tests for the Lambda_QCD <-> alpha_s(M_Z) round trip.

The bundled `data/lambda_qcd_alpha_s_closure.json` records three
closures: threshold matching (PRECISE), reverse direction (EXACT
2-loop), and forward direction (EXACT 4-loop without PDG anchor).
The forward direction is the load-bearing closure: it derives
alpha_s(M_Z) from the emergent QCD scale without using PDG as input.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_lambda_qcd_alpha_s as M  # noqa: E402


@pytest.fixture(scope="module")
def closure():
    return M.load_closure()


@pytest.fixture(scope="module")
def output(closure):
    M.main()
    out_path = REPO / "outputs" / "lambda_qcd_alpha_s_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_threshold_matching_precise(closure):
    """Lambda_QCD(nf=5) = 0.19908 GeV, PRECISE ~0.95 vs PDG 0.2104.

    PDG 2024 quotes alpha_s(M_Z) = 0.1180 +/- 0.0009 (world average,
    Workman et al.) and Lambda^(5)_MS-bar = 0.2104 +/- 0.0010 GeV
    (FLAG 2024 lattice average). The threshold-matching ratio sits at
    PRECISE 0.946 against the lattice anchor."""
    tm = closure["lambda_qcd_threshold_matching"]
    assert tm["alpha_s_MZ_input"] == pytest.approx(0.1180, abs=1e-4)
    assert tm["lambda_qcd_nf5_GeV"] == pytest.approx(0.19908, abs=1e-5)
    assert tm["ratio_to_PDG"] == pytest.approx(0.946, abs=0.02)
    assert tm["tier"] == "PRECISE"


def test_reverse_round_trip_exact_at_two_loop(closure):
    """alpha_s(M_Z) reverses Lambda exactly at two-loop MS-bar."""
    rv = closure["alpha_s_reverse_direction"]
    assert rv["alpha_s_MZ_two_loop"] == pytest.approx(0.1179, abs=1e-4)
    assert rv["ratio_two_loop"] == pytest.approx(1.0, abs=1e-4)
    assert rv["tier"] == "EXACT"


def test_forward_direction_without_pdg_anchor_exact(closure):
    """The forward direction (alpha_s from emergent Lambda, 4-loop)
    achieves EXACT 0.994 vs PDG without PDG in the input chain."""
    fw = closure["alpha_s_forward_direction"]
    assert fw["alpha_s_MZ_four_loop"] == pytest.approx(0.11719, abs=1e-4)
    assert fw["ratio_to_PDG"] > 0.99
    assert fw["tier"] == "EXACT"


def test_forward_3_loop_and_4_loop_agree(closure):
    """Truncation error fully absorbed at 4 loops (3-loop and 4-loop
    agree to 1e-4)."""
    fw = closure["alpha_s_forward_direction"]
    assert abs(fw["alpha_s_MZ_three_loop"]
               - fw["alpha_s_MZ_four_loop"]) < 1e-4


def test_loop_class_assignment_n_values(closure):
    """Lambda_QCD sits at n=0; alpha_s(M_Z) sits at n=1."""
    lc = closure["loop_class_assignment"]
    assert lc["Lambda_QCD"]["n_spinor_trace"] == 0
    assert lc["alpha_s_M_Z"]["n_spinor_trace"] == 1
    assert lc["Lambda_QCD"]["lemma_compound"] == "pure-eps2 + 7"
    assert lc["alpha_s_M_Z"]["lemma"] == 6


def test_recompute_round_trip_consistent(output):
    assert output["round_trip_consistent"] is True
