"""Tests for the bundled fermion-mass closure (9/9 FACTOR2 + F-05 m_e/m_mu)."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_fermion_mass_closure as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "fermion_mass_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_nine_of_nine_within_factor2(bundle):
    f = bundle["nine_dressed_fermion_masses"]
    assert f["n_within_factor2"] == 9
    assert f["n_total"] == 9
    assert f["tier"] == "FACTOR2"


def test_F05_GJ_charged_lepton_PRECISE(bundle):
    """The texture-null + bi-unitary GJ closure delivers PRECISE
    against pole-mass and PRECISE-loose at sub-1% against the
    Antusch M_Z MS-bar Yukawa anchor."""
    cl = bundle["charged_lepton_ratio_F05_closure"]
    # Top-level tier is PRECISE (driven by best regime).
    assert cl["tier"] == "PRECISE"
    # Best regime against the pole-mass anchor.
    assert cl["best_predicted_tier"] == "PRECISE"
    assert cl["best_predicted_residual_pct"] <= 5.0
    assert cl["best_predicted"] == pytest.approx(4.685e-3, abs=1e-5)
    assert cl["anchor_value"] == pytest.approx(4.836e-3, abs=1e-5)
    # Antusch 2025 M_Z MS-bar Yukawa-ratio cross-check is the
    # stronger anchor (m_e/m_mu is essentially RG-stable but
    # the framework's GJ texture-null prediction is delivered at
    # the unified Yukawa scale, so the running-mass ratio is the
    # correct comparator). Sub-1% is the load-bearing claim.
    ax = cl["antusch_2025_cross_check"]
    assert ax["anchor_value_MZ_MSbar"] == pytest.approx(
        4.747e-3, abs=1e-5)
    assert ax["predicted_p5n64_residual_pct_vs_antusch"] <= 1.0
    assert (cl["best_predicted_p5n64_via_antusch_anchor_pct"]
            == pytest.approx(0.80, abs=0.05))


def test_GJ_identity_is_one_ninth_of_md_over_ms(bundle):
    """The structural identity is (m_e/m_mu)_GJ = (1/9)(m_d/m_s)."""
    cl = bundle["charged_lepton_ratio_F05_closure"]
    formula = cl["structural_identity_GJ"]
    assert "1/9" in formula
    assert "m_d/m_s" in formula


def test_stop_rule_A_verified(bundle):
    cl = bundle["charged_lepton_ratio_F05_closure"]
    assert cl["stop_rule_A_verified"] is True
    assert "without the texture-null" in cl["stop_rule_A_explanation"]


def test_m_tau_channel_open(bundle):
    op = bundle["open_channel"]
    assert op["tier"] == "OPEN_AT_EXACT"
    assert "m_tau" in op["claim"] or "m_tau" in op["id"]


def test_zero_fitted_parameters(bundle):
    assert bundle["summary"]["fitted_parameters"] == 0


def test_recompute_output_passes(output):
    assert output["verdict"] == "PASS"
    assert output["nine_dressed_passed_FACTOR2"] is True
    assert output["F05_charged_lepton_PRECISE"] is True
    assert output["fitted_parameters"] == 0
