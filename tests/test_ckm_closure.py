"""Tests for the bundled CKM closure (full matrix + Jarlskog + delta_CP)."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_ckm_closure as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "ckm_closure_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_full_ckm_matrix_derived(bundle):
    m = bundle["ckm_matrix_closure"]
    assert m["tier"] == "DERIVED"


def test_jarlskog_EXACT_via_Wolfenstein_Compound(bundle):
    """Post-MD-57 Wolfenstein-Compound from existing closures gives
    J_CP EXACT 0.73% against PDG 2024."""
    j = bundle["jarlskog_invariant_closure"]
    assert j["tier"] == "EXACT"
    assert j["residual_pct"] <= 1.0
    assert j["predicted"] == pytest.approx(3.057e-5, rel=1e-2)
    assert j["anchor_value"] == pytest.approx(3.08e-5, rel=5e-2)


def test_jarlskog_ratio_close_to_one(bundle):
    j = bundle["jarlskog_invariant_closure"]
    assert abs(j["ratio_predicted_over_measured"] - 1.0) <= 0.02


def test_jarlskog_alternative_SYE_pipeline_FACTOR2(bundle):
    """The SYE-pipeline producer-method is reported as an independent
    direction-pass but is superseded as closure-domain verdict by
    the Wolfenstein-Compound construction."""
    alt = bundle["jarlskog_invariant_closure"]["alternative_method_SYE_pipeline"]
    assert alt["tier"] == "FACTOR2"
    assert 0.5 <= alt["ratio_predicted_over_measured"] <= 2.0


def test_ckm_magnitudes_all_EXACT(bundle):
    """V_us = gamma sqrt(5); V_cb = eps_sync^2 sqrt(2/N_gen);
    R_b = d gamma (1+eps_sync^2) all EXACT against PDG 2024."""
    m = bundle["ckm_magnitudes_closure"]
    for key in ("V_us", "V_cb", "R_b_apex_distance"):
        entry = m[key]
        assert entry["tier"] == "EXACT", f"{key} tier {entry['tier']}"
        assert entry["residual_pct"] <= 1.0


def test_delta_CP_EXACT(bundle):
    dcp = bundle["delta_CP_F02b_closure"]
    assert dcp["tier"] == "EXACT"
    assert dcp["residual_pct"] <= 1.5
    # Sanity: predicted 1.13 rad vs NuFIT ~1.14 rad
    assert dcp["predicted_rad"] == pytest.approx(1.1299, abs=1e-3)
    assert dcp["anchor_rad"] == pytest.approx(1.144, abs=5e-3)


def test_delta_CP_coherence_filter_at_0_05_rad(bundle):
    """The Wilson-holonomy coherence filter |delta^Berry - delta^largest|
    < 0.05 rad singles out a unique coherence-filtered lattice regime as
    the only coherent branch."""
    dcp = bundle["delta_CP_F02b_closure"]
    assert dcp["coherence_filter_rad"] == 0.05
    assert dcp["regime_selected"] == "coherence-filtered lattice regime"
    assert dcp["regime_selected_internal_label"] == "P5"


def test_zero_fitted_parameters(bundle):
    assert bundle["summary"]["fitted_parameters"] == 0


def test_recompute_output_passes(output):
    assert output["verdict"] == "PASS"
    assert output["jarlskog_EXACT_via_Wolfenstein_Compound"] is True
    assert output["delta_CP_EXACT"] is True
    assert output["fitted_parameters"] == 0
