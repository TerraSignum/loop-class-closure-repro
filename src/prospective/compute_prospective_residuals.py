"""
Standalone computation of the prospective-cluster residuals registered in
data/prospective_cluster_registry.json.

Three observables are pre-registered (PROSP-01..03). For each, this script
either
  (a) computes the residual from broader-corpus baseline data bundled
      under data/prospective_inputs/, or
  (b) reports NOT_YET_COMPUTED with a precise specification of what
      lattice-extension run is required, so the residual can be
      filled in once the run lands.

Bundled inputs (data/prospective_inputs/):
  c5_bareflavour_p0.json, _p1.json, _p2prime.json (results_c5_fix4)
    -- the gravitational coupling-scaling diagnostic on the bare
       Phi_eff field, the theory-conformant Newton-asymptote
       measurement standard (P_1 newton_like_pass = 1.0,
       P_2' = 0.929, far_field_exponent = -1.000 i.e. clean 1/r).
  c5_p1.json, c5_p2prime.json (results_c5_real)
  c5_p3.json, c5_p4.json, c5_p5.json, c5_p6.json (results_c5_pX_extension)
    -- the same diagnostic on the Xi-projected Phi_eff, the
       projector-diagnostic reading (newton_like_pass = 0 across all
       six regimes, far_field_exponent in [-0.05, -0.003], a flat
       far-field artefact of Xi-coarse-graining bandwidth, not a
       physics readout). Documented in Paper 05 Section 6 as
       'PROJECTOR_BANDWIDTH_REGRESSION' under the
       theory-backbone Resolution (b).
  vcg_canonical_regimes.json (outputs_theory_closure/pg_vtx02_cosmo_gate)
  vcg_lambda_DM_self_consistency.json
    -- the vortex-cosmological-gate diagnostic on the canonical-regime
       baseline, including the lattice rho_DM/rho_DE FRW-ratio check.
  baseline_xi_reactivity_p2prime.json
    -- the existing P_2'/P_5 charged-current Xi-reactivity audit at the
       heuristic carrier-defect coupling g_old = 2.00.

Output: data/prospective_cluster_residuals.json (machine-readable) and a
short stdout summary. The Fisher combination on residuals computed from
explicit post-T_0 lattice-extension runs is the C3-addressing test
described in the bridge note's Section 'loop-class registry' caveats
block; leading-order broader-corpus projections are reported separately.

Usage:
  python src/prospective/compute_prospective_residuals.py

Author: Sandro Bucciarelli, 2026-05-03
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "src")
sys.path.insert(0, SRC)
# Reuse the bridge note's existing Fisher-combined-p implementation
# (src/compute_yukawa_cluster_p.py), rather than reimplementing it.
from compute_yukawa_cluster_p import fisher_combined_p  # noqa: E402

INPUTS = os.path.join(ROOT, "data", "prospective_inputs")
REGISTRY = os.path.join(ROOT, "data", "prospective_cluster_registry.json")
OUT = os.path.join(ROOT, "data", "prospective_cluster_residuals.json")

RESIDUAL_CUT = 0.025  # uniform null upper edge, matches registry


def _load(p: str) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _two_sided_uniform_pvalue(residual: float, cut: float) -> float:
    """Two-sided p under a Uniform(0, cut) null. Residuals at or beyond
    the cut return p = 0 (the analytic result; downstream Fisher
    combinations should clamp such cases explicitly)."""
    if residual <= 0:
        return 0.0
    if residual >= cut:
        return 0.0
    f = residual / cut
    return 2.0 * min(f, 1.0 - f)


# Fisher combination is supplied by the bridge note's existing
# compute_yukawa_cluster_p.fisher_combined_p, imported above.


# -----------------------------------------------------------------------------
# PROSP-01: gravitational coupling-scaling diagnostic on lattice-extension regimes
# -----------------------------------------------------------------------------
# Broader-corpus baseline: the Xi-projected gravitational coupling-scaling
# diagnostic on the canonical-regime ladder P1..P6 (six regimes). Bundled
# inputs: c5_p1..c5_p6.json. The diagnostic reports newton_like_pass = 0
# uniformly (flat far-field, far_field_exponent in the range
# [-0.05, -0.003]) with rho_res_mean concentrated in [0.012, 0.022] across
# all six regimes -- i.e. the diagnostic is cross-regime stable.
#
# The bundled lambda_DM-cosmological-gate self-consistency block, although
# strictly belonging to PROSP-02, doubles as a coarse far-field check on
# the same regimes; it is reported under PROSP-02 below.
#
# The pre-registered prospective is the LATTICE-N extension of the same
# diagnostic on the lattice-extension regimes P5N64..P5N300; the
# corresponding diagnostic-pipeline outputs are NOT in the broader corpus
# at the registry timestamp (only the d1 state-vector NPZ files for these
# lattice-N points exist). PROSP-01 is therefore PENDING.
def _row_for(prefix, regime):
    d = _load(os.path.join(INPUTS, f"{prefix}{regime}.json"))
    return {
        "regime": regime,
        "newton_like_pass": d.get("newton_like_pass"),
        "far_field_exponent": d.get("far_field_exponent"),
        "poisson_residual": d.get("poisson_residual"),
        "rho_res_mean": d.get("rho_res_mean"),
        "M_eff_final": d.get("M_eff_final"),
        "Phi_eff_slope": d.get("Phi_eff_slope"),
        "seed_count": d.get("seed_count"),
        "iterations": d.get("iterations"),
    }


def _summary_for(rows):
    far = [r["far_field_exponent"] for r in rows]
    rho = [r["rho_res_mean"] for r in rows]
    return {
        "regimes_used": [r["regime"] for r in rows],
        "per_regime": rows,
        "far_field_exponent_mean": sum(far) / len(far),
        "far_field_exponent_spread": max(far) - min(far),
        "rho_res_mean_mean": sum(rho) / len(rho),
        "rho_res_mean_spread": max(rho) - min(rho),
    }


def _d1embedded_row(N: int):
    d = _load(os.path.join(INPUTS, f"c5_d1embedded_P5N{N}.json"))
    return {
        "lattice_N": N,
        "regime": d.get("regime"),
        "n_seeds": d.get("n_seeds"),
        "M_eff_final": d.get("M_eff_final"),
        "Phi_eff_slope": d.get("Phi_eff_slope"),
        "newton_like_badness_best": d.get(
            "d1_gamma_candidate_physical_newton_like_badness_best"),
        "newton_like_badness_family_median": d.get(
            "d1_gamma_candidate_physical_newton_like_badness_family_median"),
        "far_field_exponent_badness_best": d.get(
            "d1_gamma_candidate_physical_far_field_exponent_badness_best"),
        "far_field_residual_badness_best": d.get(
            "d1_gamma_candidate_physical_far_field_residual_badness_best"),
    }


def compute_prosp_01() -> dict:
    bare_rows = [_row_for("c5_bareflavour_", r) for r in ("p0", "p1", "p2prime")]
    proj_rows = [_row_for("c5_", r) for r in ("p1", "p2prime", "p3", "p4", "p5", "p6")]
    # Full nine-point lattice-N ladder. The N=64 and N=100 entries
    # come from the original 1178-key d1 outputs (results_d1_p5n64/
    # and results_d1_p5n100/); the seven higher-N entries
    # (P5N72/84/128/200/256/300/512) are computed by the
    # post-snapshot reconstruction script
    # src/prospective/extend_c5_d1embedded_to_higher_N.py from the
    # bundled NPZ state-vector snapshots via the same
    # residual_density / defect_node_density / radial_gravity_profile
    # primitives the bulk-evolution pipeline uses.
    lattice_ladder = (64, 72, 84, 100, 128, 200, 256, 300, 512)
    lattice_rows = [_d1embedded_row(N) for N in lattice_ladder]
    newton_b = [r["newton_like_badness_best"] for r in lattice_rows]
    far_b = [r["far_field_exponent_badness_best"] for r in lattice_rows]
    return {
        "id": "PROSP-01",
        "status": "PARTIAL_BROADER_CORPUS_RESULT",
        "post_loop_residual": None,
        "p_value": None,
        "broader_corpus_baseline": {
            "theory_conformant_bare_phi_field": {
                "diagnostic": "Bare-Phi_eff gravitational coupling-scaling on canonical regimes (results_c5_fix4)",
                "summary": _summary_for(bare_rows),
                "newton_pass_at_P1": bare_rows[1]["newton_like_pass"],
                "newton_pass_at_P2prime": bare_rows[2]["newton_like_pass"],
                "far_field_at_P1": bare_rows[1]["far_field_exponent"],
                "interpretation": (
                    "Theory-conformant Newton-asymptote standard: "
                    "newton_like_pass = 1.0 on P_1, 0.929 on P_2', "
                    "far_field_exponent = -1.000 on both (clean 1/r); "
                    "matches the SCD-01 Xi-perturbation backbone "
                    "delta_Xi(r) ~ -GM/r."
                ),
            },
            "xi_projected_projector_diagnostic": {
                "diagnostic": "Xi-projected Phi_eff (results_c5_real + results_c5_pX_extension)",
                "summary": _summary_for(proj_rows),
                "interpretation": (
                    "Xi-projected reading: newton_like_pass = 0 on all "
                    "six regimes, far_field_exponent in [-0.05, -0.003]. "
                    "Per Paper 05 Section 6 Resolution (b), this is a "
                    "PROJECTOR_BANDWIDTH_REGRESSION (the Xi-coarse-graining "
                    "kernel washes out the 1/r far-field of the bare "
                    "delta_Xi field), NOT a physics result. The "
                    "Newton-asymptote claim is carried by the bare-Phi "
                    "reading above and by the Schwarzschild defect "
                    "derivation upstream."
                ),
            },
            "d1_embedded_lattice_N_extension": {
                "diagnostic": "d1-embedded gravitational coupling-scaling diagnostic on lattice-N variants of P_5 (results_d1_p5n64 + results_d1_p5n100, the full 1178-key d1 outputs; remaining lattice-N points P5N72/84/128/200/256/300 carry only the 33-key subset and do not embed the c5 diagnostic)",
                "lattice_points": lattice_rows,
                "newton_like_badness_at_N64": newton_b[0],
                "newton_like_badness_at_N100": newton_b[1],
                "newton_like_badness_N_stable": (
                    abs(newton_b[0] - newton_b[1]) < 0.05
                    if newton_b[0] is not None and newton_b[1] is not None
                    else None
                ),
                "far_field_exponent_badness_at_N64": far_b[0],
                "far_field_exponent_badness_at_N100": far_b[1],
                "interpretation": (
                    "The d1-embedded reading on the lattice-N extension "
                    "is N-stable in the SAME projector-bandwidth-regression "
                    "mode as the canonical-regime Xi-projected reading: "
                    "newton_like_badness ~ 1.0 (i.e. far-from-Newton) at "
                    "BOTH N=64 and N=100. The diagnostic does not flip "
                    "sign or shift across the two lattice-N points "
                    "available; the projector-bandwidth issue is "
                    "lattice-N-stable. The bare-Phi standard remains the "
                    "theory-conformant Newton-asymptote measure."
                ),
            },
        },
        "what_is_partial": (
            "The d1-embedded c5 diagnostic is bundled at TWO lattice-N "
            "points (P5N64, P5N100) with the full 1178-key d1 output. "
            "The remaining lattice-N regimes (P5N72/84/128/200/256/300) "
            "carry only the 33-key subset that does not embed the c5 "
            "Newton/far-field/poisson keys. A run extending the 1178-key "
            "format to those higher-N points would close PROSP-01 with "
            "a 6-point Symanzik-2 fit; the present 2-point N-stability "
            "check is the broader-corpus partial result."
        ),
    }


# -----------------------------------------------------------------------------
# PROSP-02: vortex-cosmological-gate diagnostic on lattice-extension regimes
# -----------------------------------------------------------------------------
# Broader-corpus baseline: the vortex-cosmological-gate diagnostic on the
# canonical-regime baseline (P1, with lambda_DM/lambda_DE self-consistency
# computed at the FRW-ratio level). Bundled inputs:
#   vcg_canonical_regimes.json (status: COSMO_GATE_OPEN at canonical P1)
#   vcg_lambda_DM_self_consistency.json (rho_DM_lat = 0.936,
#                                        rho_DE_lat = 0.437,
#                                        round-trip self-consistent)
#
# Pre-registered prospective: the LATTICE-N extension on P5N64..P5N300.
# Not in the broader corpus at the registry timestamp; PROSP-02 is
# PENDING.
def compute_prosp_02() -> dict:
    vcg = _load(os.path.join(INPUTS, "vcg_canonical_regimes.json"))
    lam = _load(os.path.join(INPUTS, "vcg_lambda_DM_self_consistency.json"))
    return {
        "id": "PROSP-02",
        "status": "NOT_YET_COMPUTED",
        "post_loop_residual": None,
        "p_value": None,
        "broader_corpus_baseline": {
            "diagnostic": "Vortex-cosmological-gate on canonical regime",
            "P1_summary": {
                "cosmo_compat_p1": vcg["vcg01"]["cosmo_compat_p1"],
                "e1_support_p1": vcg["vcg02"]["e1_support_p1"],
                "gate_gap_p1": vcg["vcg03"]["gate_gap_p1"],
                "dm_share_p1": vcg["vcg03"]["dm_share_p1"],
                "theory_status": vcg["vcg05"]["theory_status"],
            },
            "lambda_DM_self_consistency": {
                "rho_DM_lattice": lam["phase_S_inputs"]["rho_DM_lattice"],
                "rho_DE_lattice": lam["phase_S_inputs"]["rho_DE_lattice"],
                "ratio_lattice": lam["phase_S_inputs"]["ratio_lattice"],
                "z_solution": lam["cosmological_epoch_interpretation"]["z_solution"],
                "round_trip_lattice_to_z0": (
                    lam["cosmological_epoch_interpretation"]["round_trip_lattice_to_z0"]
                ),
                "headline": lam["headline"],
            },
        },
        "what_is_pending": (
            "The pre-registered prospective is the LATTICE-N extension "
            "of the diagnostic on P5N64..P5N300, which is not in the "
            "broader corpus at the registry timestamp; the run is "
            "required before the residual can be filled in."
        ),
    }


# -----------------------------------------------------------------------------
# PROSP-03: charged-current Xi-reactivity ratio at P_2', after coupling re-run
# -----------------------------------------------------------------------------
# Bundled baseline (baseline_xi_reactivity_p2prime.json) reports the
# existing P_2'/P_5 ratio at the heuristic coupling g_old = 2.00. Two
# ratio definitions are present:
#     ratio_cw_net = 3.43
#     ratio_abs_over_sync = 3.17
# The pre-registered prediction is that at g_new = 1.42, the ratio drops
# to ~ 1.0 +/- 0.05.
#
# Leading-order analytic projection via g^2-rescaling:
#     ratio(g_new) ~ ratio(g_old) * (g_new / g_old)^2
# gives projected ratios ~1.73 and ~1.60, whose mean ~1.66 corresponds to
# a residual r ~ 0.66 -- well outside the uniform-null support [0, 0.025]
# and the prediction window 0.05.
#
# The leading-order analytic projection therefore FALSIFIES the
# prediction at leading order. The full re-run at g_new = 1.42 is still
# pending and will determine whether sub-leading corrections close the
# gap. We do NOT report this leading-order projection as the prospective
# residual (the registry's no-back-fill clause excludes pre-T_0 inputs);
# we report it as a separate broader-corpus diagnostic.
def compute_prosp_03() -> dict:
    src = _load(os.path.join(INPUTS, "baseline_xi_reactivity_p2prime.json"))
    g_old = 2.00
    g_new = 1.42
    g_new_minus = 1.32
    g_new_plus = 1.52
    rescale = (g_new / g_old) ** 2
    rescale_lo = (g_new_minus / g_old) ** 2
    rescale_hi = (g_new_plus / g_old) ** 2

    ratio_cw_net = src["gap_analysis_p2p_s1_vs_p5_ref"]["cw_net_corrected"]["ratio_p2p_over_p5"]
    ratio_abs    = src["gap_analysis_p2p_s1_vs_p5_ref"]["abs_over_sync_floor"]["ratio_p2p_over_p5"]

    proj_cw_net = ratio_cw_net * rescale
    proj_abs    = ratio_abs    * rescale
    proj_combined = 0.5 * (proj_cw_net + proj_abs)
    residual = abs(proj_combined - 1.0)

    return {
        "id": "PROSP-03",
        "status": "PENDING_RUN_BUT_LEADING_ORDER_ANALYTICALLY_FALSIFIED",
        "post_loop_residual": None,
        "p_value": None,
        "leading_order_analytic_residual": residual,
        "leading_order_analytic_pvalue": _two_sided_uniform_pvalue(residual, RESIDUAL_CUT),
        "registry_compliance_note": (
            "The prospective residual is to be filled in only by the "
            "explicit re-run at g = 1.42 (data computed AFTER T_0), per "
            "the registry's no-back-fill clause. The leading-order "
            "analytic projection below uses pre-T_0 baseline inputs and "
            "is a broader-corpus consistency check, not the prospective "
            "residual itself."
        ),
        "details": {
            "g_old_heuristic": g_old,
            "g_new_rigorous": g_new,
            "g_new_envelope": [g_new_minus, g_new_plus],
            "g_squared_rescale": rescale,
            "g_squared_rescale_envelope": [rescale_lo, rescale_hi],
            "baseline_ratio_cw_net": ratio_cw_net,
            "baseline_ratio_abs_over_sync": ratio_abs,
            "projected_ratio_cw_net": proj_cw_net,
            "projected_ratio_abs_over_sync": proj_abs,
            "projected_ratio_combined": proj_combined,
            "predicted_ratio": 1.0,
            "predicted_residual_window": 0.05,
            "leading_order_analytic_residual": residual,
        },
        "verdict": (
            "Leading-order g^2-rescaling alone does NOT bring the P_2' "
            "Xi-reactivity ratio back to the predicted 1.0 +/- 0.05 "
            "window. The analytic projected residual ~0.66 is well "
            "outside the null support [0, 0.025] and the prediction "
            "window. The full re-run at g = 1.42 is still required to "
            "test whether sub-leading corrections close the gap; the "
            "leading-order result is reported here as the honest "
            "broader-corpus prospective check."
        ),
    }


def main():
    registry = _load(REGISTRY)
    out = {
        "computation_timestamp": datetime.now(timezone.utc).isoformat(),
        "registry_timestamp": registry["registration_timestamp"],
        "null_model": registry["null_model"],
        "prospective_residuals": [
            compute_prosp_01(),
            compute_prosp_02(),
            compute_prosp_03(),
        ],
    }

    # Only post-T_0 prospective residuals enter the cluster combination;
    # leading-order analytic broader-corpus projections do not.
    computed_pvalues = [
        e["p_value"] for e in out["prospective_residuals"]
        if e.get("p_value") is not None
    ]
    if len(computed_pvalues) >= 2:
        nz = [p for p in computed_pvalues if p > 0]
        if nz:
            T, _k, p_comb = fisher_combined_p(nz)
        else:
            T, _k, p_comb = (float("inf"), len(computed_pvalues), 0.0)
        out["fisher_combination_on_computed_subset"] = {
            "k_observables_in_combination": len(computed_pvalues),
            "chi2": T,
            "combined_p": p_comb,
            "note": (
                "Fisher combination computed on the subset of prospective "
                "observables whose residuals are computable from the "
                "broader corpus at the registry timestamp. Pending "
                "lattice-extension residuals are excluded; the registry's "
                "fail-safe clause closes the cluster-p on the converged "
                "subset at the 2026-12-31 expiry."
            ),
        }
    else:
        out["fisher_combination_on_computed_subset"] = {
            "k_observables_in_combination": len(computed_pvalues),
            "note": (
                "No prospective residuals are post-T_0 yet (all three "
                "require dedicated lattice-extension or coupling re-runs). "
                "The multi-observable Fisher combination is therefore not "
                "yet defined; the registry remains open until the runs "
                "land or the 2026-12-31 fail-safe expires."
            ),
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote {OUT}")
    print()
    for e in out["prospective_residuals"]:
        print(f"  {e['id']}: {e['status']}")
        if e.get("post_loop_residual") is not None:
            print(f"    residual = {e['post_loop_residual']:.4f}, "
                  f"uniform-null p = {e['p_value']:.4g}")
        if e.get("leading_order_analytic_residual") is not None:
            print(f"    leading-order analytic residual = "
                  f"{e['leading_order_analytic_residual']:.4f}, "
                  f"uniform-null p = "
                  f"{e['leading_order_analytic_pvalue']:.4g} "
                  f"(broader-corpus check, not the prospective residual)")
        if e.get("broader_corpus_baseline") is not None:
            b = e["broader_corpus_baseline"]
            if "theory_conformant_bare_phi_field" in b:
                bare = b["theory_conformant_bare_phi_field"]
                proj = b["xi_projected_projector_diagnostic"]
                lat = b.get("d1_embedded_lattice_N_extension")
                print(f"    bare-Phi (theory-conformant): "
                      f"newton_pass_P1={bare['newton_pass_at_P1']}, "
                      f"newton_pass_P2'={bare['newton_pass_at_P2prime']:.3f}, "
                      f"far_field_P1={bare['far_field_at_P1']:.3f} "
                      f"(clean 1/r)")
                print(f"    Xi-projected (projector-diagnostic): "
                      f"6 regimes, far_field_mean="
                      f"{proj['summary']['far_field_exponent_mean']:.4f} "
                      f"(washed-out, PROJECTOR_BANDWIDTH_REGRESSION per "
                      f"Paper 05 Sec.6 Res.(b))")
                if lat is not None:
                    Ns = [pt["lattice_N"] for pt in lat["lattice_points"]]
                    nbs = [pt["newton_like_badness_best"] for pt in lat["lattice_points"]]
                    print(f"    d1-embedded lattice-N "
                          f"({len(Ns)}-point ladder "
                          f"N in [{min(Ns)},{max(Ns)}]): "
                          f"newton_like_badness range = "
                          f"{min(nbs):.3f}-{max(nbs):.3f}, "
                          f"N-stable={lat['newton_like_badness_N_stable']}")
            elif "P1_summary" in b:
                p = b["P1_summary"]
                print(f"    canonical baseline: cosmo_compat_p1="
                      f"{p['cosmo_compat_p1']:.4f}, gate_gap_p1="
                      f"{p['gate_gap_p1']:.4f}, "
                      f"theory_status='{p['theory_status']}'")

    f_ = out["fisher_combination_on_computed_subset"]
    print()
    if "chi2" in f_:
        print(f"Fisher combination on {f_['k_observables_in_combination']} "
              f"computable residuals: chi2={f_['chi2']:.3g}, "
              f"p={f_['combined_p']:.4g}")
    else:
        print(f"Fisher combination not yet defined "
              f"(k={f_['k_observables_in_combination']} < 2 post-T_0 "
              f"residuals).")


if __name__ == "__main__":
    main()
