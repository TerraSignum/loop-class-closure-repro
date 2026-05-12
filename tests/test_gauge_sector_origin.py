"""Tests for the bundled gauge-sector origin (SU(3) x SU(2) x U(1) from lattice features)."""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_gauge_sector_origin as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "gauge_sector_origin_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_three_subgroups_derived(bundle):
    origins = bundle["structural_origins"]
    assert len(origins) == 3
    subgroups = {o["subgroup"] for o in origins}
    assert subgroups == {"U(1)_Y", "SU(2)_L", "SU(3)_C"}


def test_each_origin_has_module_and_step(bundle):
    for o in bundle["structural_origins"]:
        assert "module" in o and o["module"]
        assert "derivation_step" in o and o["derivation_step"]


def test_five_consequences_derived(bundle):
    cons = bundle["structural_consequences"]
    assert len(cons) == 5
    ids = {c["id"] for c in cons}
    assert ids == {
        "asymptotic_freedom",
        "wilson_area_law",
        "yang_mills_kinetic",
        "GUT_coupling_unification",
        "sin2_theta_W",
    }


def test_qcd_one_loop_b0_positive_at_six_flavours():
    """QCD asymptotic freedom: b_0 = (33 - 2 N_f)/(12 pi) > 0 for N_f <= 16."""
    b0_6 = M.qcd_beta_zero_leading(6)
    assert b0_6 > 0
    b0_5 = M.qcd_beta_zero_leading(5)
    assert b0_5 > b0_6  # decoupling m_t below 2 GeV decreases b_0 -> wait, increases
    # Actually fewer active flavours means MORE asymptotic freedom (larger b_0)
    assert b0_5 > 0


def test_zero_fitted_parameters(bundle):
    assert bundle["summary"]["fitted_parameters"] == 0


def test_recompute_output_passes(output):
    assert output["verdict"] == "PASS"
    assert output["n_subgroups_derived"] == 3
    assert output["asymptotic_freedom_at_Nf_6"] is True
    assert output["fitted_parameters"] == 0
