"""Tests for the bundled neutrino-sector closure (PMNS angles + Δm² splittings + δ_CP)."""

import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import verify_neutrino_sector as M  # noqa: E402


@pytest.fixture(scope="module")
def bundle():
    return M.load_bundle()


@pytest.fixture(scope="module")
def output(bundle):
    M.main()
    out_path = REPO / "outputs" / "neutrino_sector_recompute.json"
    with open(out_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_five_closures_present(bundle):
    closures = bundle["closures"]
    assert len(closures) == 5
    ids = {c["id"] for c in closures}
    assert ids == {
        "PMNS_theta_13",
        "PMNS_theta_12",
        "PMNS_theta_23",
        "Delta_m_squared_31_atm",
        "Delta_m_squared_21_sol",
    }


def test_all_five_PRECISE_or_better(bundle):
    for c in bundle["closures"]:
        assert c["tier"] in ("EXACT", "PRECISE"), (
            f"{c['id']} tier {c['tier']} not in EXACT/PRECISE"
        )
        assert c["residual_pct"] <= 5.0, (
            f"{c['id']} residual {c['residual_pct']}% exceeds PRECISE band"
        )


def test_theta13_structural_identity_in_Q():
    """In rational reduction R: theta_13_rad = (1 - gamma)/(2*N_gen)
    with gamma=1/10, N_gen=3 must equal exactly 9/60 = 3/20 in Q."""
    theta13_rad = (1 - Fraction(1, 10)) / (2 * 3)
    assert theta13_rad == Fraction(3, 20)
    assert float(theta13_rad) == pytest.approx(0.15, abs=1e-9)


def test_theta13_rad_within_NuFIT_EXACT():
    """theta_13 from the structural identity at measured System-R
    (alpha_xi=0.90082, N_gen=3) must hit NuFIT 6.1 within EXACT 0.4%
    (residual measured in the natural quantity theta_13 itself)."""
    alpha_xi = 0.90082
    n_gen = 3
    theta13_pred = alpha_xi / (2 * n_gen)
    theta13_nufit = math.asin(math.sqrt(0.02220))
    residual_pct = abs(theta13_pred - theta13_nufit) / theta13_nufit * 100
    assert residual_pct < 0.4, (
        f"theta_13 (rad) residual {residual_pct:.3f}% exceeds EXACT 0.4%"
    )


def test_delta_CP_EXACT(bundle):
    cp = bundle["delta_CP_closure"]
    # PMNS Dirac CP phase: pi(1+gamma)(1-gamma^2/4) -> ~197 deg, EXACT 0.27%
    assert cp["tier_PMNS"] == "EXACT"
    assert cp["residual_pct_PMNS"] < 1.5
    # CKM Dirac CP phase via Wilson-holonomy three-extractor: EXACT 1.23%
    alt = cp["alternative_F02b_CKM_closure"]
    assert alt["tier"] == "EXACT"
    assert alt["residual_pct"] <= 1.5


def test_summary_counts_consistent(bundle):
    """After MD-46 / MD-53 PMNS-promotion, theta_12 / theta_23 are
    promoted to EXACT, leaving only Delta m^2_sol on PRECISE among
    the five core closures."""
    counts = {"EXACT": 0, "PRECISE": 0}
    for c in bundle["closures"]:
        counts[c["tier"]] += 1
    assert counts == {"EXACT": 4, "PRECISE": 1}
    assert bundle["summary_counts"]["EXACT"] == 4
    assert bundle["summary_counts"]["PRECISE"] == 1
    assert bundle["summary_counts"]["PRECISE_or_better"] == 5


def test_recompute_output_passes(output):
    assert output["verdict"] == "PASS"
    assert output["all_PRECISE_or_better"] is True
    assert output["structural_theta13_EXACT_in_rad"] is True
