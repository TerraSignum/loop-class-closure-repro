"""Phase-7 tests: PROSP-01/02/03 prospective stability diagnostics.

The stability-diagnostic harness reads bundle JSON files from the
broader Emergence corpus and extracts the named diagnostic fields
deterministically. These tests:

(1) Pin the SHA-256 of each bundle so silent upstream data drift
    fails the test immediately.
(2) Pin the EXACT extracted value of each declared field so any
    accidental schema change (e.g. field rename) is caught.
(3) Verify the verdict status is BASELINE_RECOVERED for each PROSP
    (the prospective POST-T_0 residual is not in the corpus at T_0
    and is not reproduced here -- the registry's no-back-fill clause
    means only the pre-T_0 baseline is reproducible without a new
    lattice run).

No tolerance, no fallback, no fabrication. The harness reads what is
on disk; the tests pin what the harness must return.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tuple_compiler.stability_diagnostic import (
    EMERGENCE_ROOT,
    bundle_sha256,
    evaluate_diagnostic,
    extract_dotted,
    resolve_bundle_path,
)


def _load_yaml(yaml_id: str, yaml_dir: Path) -> dict:
    matches = list(yaml_dir.glob(f"{yaml_id}_*.yaml")) + \
              list(yaml_dir.glob(f"{yaml_id.replace('-', '_')}*.yaml"))
    assert matches, f"YAML for {yaml_id} not found"
    with matches[0].open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Pinned SHA-256 hashes of the bundle files at the current commit.
# If a bundle's content changes, this test will fail; that is the
# intended behaviour (silent data drift is exactly what these tests
# guard against).
PINNED_BUNDLE_SHA256 = {
    "results_c5_fix4/c5_p0.json":
        "418e52d0d4ed",      # leading 12 hex chars suffice for drift detection
    "results_c5_fix4/c5_p1.json":
        "73bd64efb234",
    "results_c5_fix4/c5_p2prime.json":
        "4f3246bdd34d",
    "outputs_theory_closure/pg_vtx02_cosmo_gate.json":
        "03e3898370b9",
    "outputs_cwbp_patch_cw/zmeq_b2_p2prime_core_patch_self_closure_audit.json":
        "ee959a22b8fc",
}


@pytest.mark.parametrize("rel_path,expected_prefix",
                          sorted(PINNED_BUNDLE_SHA256.items()))
def test_bundle_sha256_pinned(rel_path, expected_prefix):
    """The bundle JSON's SHA-256 must match the pinned prefix; otherwise
    a silent upstream data change has occurred."""
    path = resolve_bundle_path(rel_path)
    assert path is not None, f"Bundle {rel_path} not resolved under {EMERGENCE_ROOT}"
    actual = bundle_sha256(path)
    assert actual.startswith(expected_prefix), (
        f"{rel_path}: SHA-256 prefix drift. expected {expected_prefix}*, "
        f"got {actual[:12]}*. Update PINNED_BUNDLE_SHA256 if intentional."
    )


# --- PROSP-01 -------------------------------------------------------

def test_prosp01_status_baseline_recovered(yaml_dir):
    obs = _load_yaml("PROSP_01", yaml_dir)
    v = evaluate_diagnostic(obs)
    assert v["status"] == "BASELINE_RECOVERED"
    assert v["id"] == "PROSP-01"
    assert len(v["bundles"]) == 3


def test_prosp01_pinned_per_regime_values(yaml_dir):
    """Pin the EXACT diagnostic values per regime in the c5 ladder."""
    obs = _load_yaml("PROSP_01", yaml_dir)
    v = evaluate_diagnostic(obs)
    by_regime = {b["regime"]: b for b in v["extract_per_bundle"]}

    # p0: negative-control, newton_like_pass = 0
    assert by_regime["p0"]["newton_like_pass"] == 0.0
    assert abs(by_regime["p0"]["far_field_exponent"] -
               (-0.023672148212929872)) < 1e-15
    # p1: clean Newton, newton_like_pass = 1, far_field = -1
    assert by_regime["p1"]["newton_like_pass"] == 1.0
    assert abs(by_regime["p1"]["far_field_exponent"] - (-1.0)) < 1e-12
    # p2prime: newton_like_pass = 13/14 ≈ 0.9286, far_field = -1
    assert abs(by_regime["p2prime"]["newton_like_pass"] -
               0.9285714285714286) < 1e-15
    assert abs(by_regime["p2prime"]["far_field_exponent"] -
               (-1.0)) < 1e-12


# --- PROSP-02 -------------------------------------------------------

def test_prosp02_status_baseline_recovered(yaml_dir):
    obs = _load_yaml("PROSP_02", yaml_dir)
    v = evaluate_diagnostic(obs)
    assert v["status"] == "BASELINE_RECOVERED"
    assert v["id"] == "PROSP-02"


def test_prosp02_pinned_p1_values(yaml_dir):
    """Pin the EXACT vcg01/vcg03 P1 diagnostic values."""
    obs = _load_yaml("PROSP_02", yaml_dir)
    v = evaluate_diagnostic(obs)
    bundle = v["extract_per_bundle"][0]
    assert abs(bundle["vcg01.cosmo_compat_p1"] - 0.689578) < 1e-9
    assert abs(bundle["vcg01.dm_mode_score_p1"] - 0.841311) < 1e-9
    assert abs(bundle["vcg01.grav_consistency_p1"] - 0.898661) < 1e-9
    assert abs(bundle["vcg01.e1_mean_support_p1"] - 0.805037) < 1e-9
    assert abs(bundle["vcg03.gate_gap_p1"] - 0.240422) < 1e-9
    assert abs(bundle["vcg03.dm_share_p1"] - 0.348774) < 1e-9
    assert abs(bundle["vcg03.grav_share_p1"] - 0.222727) < 1e-9


# --- PROSP-03 -------------------------------------------------------

def test_prosp03_status_baseline_recovered(yaml_dir):
    obs = _load_yaml("PROSP_03", yaml_dir)
    v = evaluate_diagnostic(obs)
    assert v["status"] == "BASELINE_RECOVERED"
    assert v["id"] == "PROSP-03"


def test_prosp03_pinned_g_old_ratios(yaml_dir):
    """Pin the EXACT g_old = 2.00 baseline ratios from the audit bundle.
    The post-T_0 re-run at g_new = 1.42 is NOT bundled and NOT reproduced."""
    obs = _load_yaml("PROSP_03", yaml_dir)
    v = evaluate_diagnostic(obs)
    bundle = v["extract_per_bundle"][0]
    cw_net = bundle["gap_analysis_p2p_s1_vs_p5_ref.cw_net_corrected"]
    abs_sf = bundle["gap_analysis_p2p_s1_vs_p5_ref.abs_over_sync_floor"]
    assert cw_net["ratio_p2p_over_p5"] == 3.43
    assert cw_net["delta"] == 0.0153
    assert cw_net["verdict"] == "OVERSHOOT_FACTOR_3p43"
    assert abs_sf["ratio_p2p_over_p5"] == 3.17
    assert abs_sf["delta"] == 1.615
    assert abs_sf["verdict"] == "OVERSHOOT_FACTOR_3p17"


# --- Generic harness invariants -------------------------------------

def test_emergence_root_is_parent_of_repo():
    """The Emergence root must be the directory containing the
    loop-class-closure-repro and the broader corpus subdirectories."""
    assert (EMERGENCE_ROOT / "loop-class-closure-repro").is_dir()
    assert (EMERGENCE_ROOT / "results_c5_fix4").is_dir()


def test_missing_bundle_reports_explicit_status():
    """A YAML referencing a missing bundle must produce status
    BUNDLE_MISSING, not silently succeed."""
    fake_obs = {
        "id":   "FAKE-PROSP",
        "name": "Fake test",
        "sector": "Test",
        "diagnostic": {
            "bundle_files": [
                {"path": "does_not_exist/nope.json"}
            ],
            "extract": [
                {"field": "some_field"}
            ],
        },
    }
    v = evaluate_diagnostic(fake_obs)
    assert v["status"] == "BUNDLE_MISSING"
    assert "does_not_exist/nope.json" in v["missing_paths"]


def test_extract_dotted_missing_field_raises():
    """extract_dotted must raise KeyError on missing field, not return None."""
    with pytest.raises(KeyError, match="missing"):
        extract_dotted({"a": {"b": 1}}, "a.c.d")
