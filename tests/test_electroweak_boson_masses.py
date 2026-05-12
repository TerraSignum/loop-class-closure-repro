"""Tests for the electroweak gauge-boson mass closure (m_W, m_Z)."""

import json
import math
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_electroweak_boson_masses as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "electroweak_boson_masses_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_m_W_EXACT_against_PDG(bundle):
    """m_W = 80.2345 GeV vs PDG 80.3692 GeV -> 0.168%, EXACT."""
    m = bundle["m_W_closure"]
    assert m["tier"] == "EXACT"
    assert m["residual_pct"] <= 0.4
    assert m["predicted_GeV"] == pytest.approx(80.2345, abs=1e-3)
    assert m["anchor_GeV"] == pytest.approx(80.3692, abs=1e-3)


def test_m_Z_EXACT_against_PDG(bundle):
    """m_Z = 91.5082 GeV vs PDG 91.1880 GeV -> 0.351%, EXACT."""
    m = bundle["m_Z_closure"]
    assert m["tier"] == "EXACT"
    assert m["residual_pct"] <= 0.4
    assert m["predicted_GeV"] == pytest.approx(91.5082, abs=1e-3)
    assert m["anchor_GeV"] == pytest.approx(91.1880, abs=1e-3)


def test_m_W_formula_recompute_matches_bundled(bundle):
    """m_W = sqrt(4 pi alpha_EM / sin^2 theta_W) * v_EW / 2."""
    inp = bundle["inputs"]
    m_w = M.recompute_m_w(
        inp["v_EW_GeV"], inp["sin2_theta_W"], inp["alpha_EM_inv_at_MZ"]
    )
    assert m_w == pytest.approx(bundle["m_W_closure"]["predicted_GeV"], abs=1e-3)


def test_m_Z_formula_recompute_matches_bundled(bundle):
    """m_Z = m_W / sqrt(1 - sin^2 theta_W)."""
    inp = bundle["inputs"]
    m_w = M.recompute_m_w(
        inp["v_EW_GeV"], inp["sin2_theta_W"], inp["alpha_EM_inv_at_MZ"]
    )
    m_z = M.recompute_m_z(m_w, inp["sin2_theta_W"])
    assert m_z == pytest.approx(bundle["m_Z_closure"]["predicted_GeV"], abs=1e-3)


def test_inputs_match_upstream_canonical_values(bundle):
    """v_EW from P1 = 246.2186 GeV; sin^2 theta_W from P2 L6 = 0.23122."""
    inp = bundle["inputs"]
    assert inp["v_EW_GeV"] == pytest.approx(246.2186, abs=1e-4)
    assert inp["sin2_theta_W"] == pytest.approx(0.23122, abs=1e-5)
    assert "P1" in inp["v_EW_source"]
    assert "P2" in inp["sin2_theta_W_source"] or "L6" in inp["sin2_theta_W_source"]


def test_lemma_assignment_EW_Mixed(bundle):
    """Both m_W and m_Z sit on Lemma 7 EW-Mixed loop class."""
    for closure in (bundle["m_W_closure"], bundle["m_Z_closure"]):
        assert closure["lemma"] == 7
        assert closure["lemma_name"] == "EW-Mixed"


def test_weinberg_cross_check_consistent(bundle):
    """The mass ratio m_Z/m_W = 1/sqrt(1 - sin^2 theta_W) cross-check."""
    cc = bundle["cross_check"]["weinberg_angle_consistency"]
    sin2 = bundle["inputs"]["sin2_theta_W"]
    expected_ratio = 1.0 / math.sqrt(1.0 - sin2)
    assert cc["m_Z_over_m_W_predicted"] == pytest.approx(expected_ratio, abs=1e-4)
    assert cc["ratio_consistency_pct"] <= 1.0  # consistency within 1%


def test_zero_fitted_parameters(bundle):
    assert bundle["summary"]["fitted_parameters"] == 0


def test_recompute_output_passes(output):
    assert output["verdict"] == "PASS"
    assert output["m_W_EXACT"] is True
    assert output["m_Z_EXACT"] is True
    assert output["formula_consistent_with_bundled"] is True
