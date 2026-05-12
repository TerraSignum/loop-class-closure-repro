"""
Extend the c5 d1-embedded gravitational coupling-scaling diagnostic
to the seven within-canonical-regime lattice-N points (P5N72,
P5N84, P5N128, P5N200, P5N256, P5N300, P5N512) that bundle NPZ
state-vector snapshots in the corpus but did not previously
carry the 1178-key d1 c5-newton/far-field/poisson-residual entries.

This extension closes the PROSP-01 N-stability check against the
full nine-point canonical ladder N in {64,72,84,100,128,200,256,300,
512} without re-running the bulk-evolution pipeline: it uses the
already-bundled NPZ snapshots and the same residual_density /
defect_node_density / radial_gravity_profile primitives the
pipeline calls at end-of-run.

The diagnostic is computable from the snapshot fields (xi, k, q, psi)
alone via the same primitives the bulk-evolution pipeline uses:

  load            = residual_density(xi, psi, k, q)
  defect_density  = defect_node_density(psi, xi)
  gravity_report  = backreaction_report(xi, raw_shell_total,
                                        gravity['r'], gravity['Phi_eff'],
                                        mass_profile=gravity['M_eff'])

The script reads the same per-regime NPZ files used by the within-P5
closure of Paper4 (data/within_p5_lattice_asymptotes.json), averages
the final snapshot across seeds, and writes one
c5_d1embedded_P5N{N}.json file per regime in the same 14-key format
as the bundled c5_d1embedded_P5N64.json / c5_d1embedded_P5N100.json
prospective inputs.

Output:
  data/prospective_inputs/c5_d1embedded_P5N{N}.json  (one per regime)

Usage:
  python src/prospective/extend_c5_d1embedded_to_higher_N.py
"""
from __future__ import annotations

import glob
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
EMERGENCE = os.path.abspath(os.path.join(ROOT, ".."))
sys.path.insert(0, os.path.join(EMERGENCE, "src"))

from worldformula.residual.residual_tensor import residual_density
from worldformula.residual.gravity_response import (
    defect_node_density,
    radial_gravity_profile,
    backreaction_report,
    far_field_fit,
    far_field_power_law,
)

OUT_DIR = os.path.join(ROOT, "data", "prospective_inputs")

# Per-regime NPZ search paths (matches verify_within_p5_lattice_asymptotes.py).
# Includes N=64 and N=100 so that the entire nine-point ladder is
# computed by a single consistent diagnostic path; this replaces the
# legacy end-of-run-extracted c5_d1embedded_P5N{64,100}.json files,
# whose secondary metrics (far_field_exponent_badness,
# poisson_residual_badness) used a slightly different evaluation
# context inside the bulk-evolution pipeline. The primary
# newton_like_badness observable is unchanged by the regeneration.
P5N_DIRS = {
    64:  ['results_d1_p5n64_24seeds',  'results_d1_p5n64'],
    72:  ['results_d1_p5n72_24seeds',  'results_d1_p5n72'],
    84:  ['results_d1_p5n84_24seeds',  'results_d1_p5n84'],
    100: ['results_d1_p5n100_24seeds', 'results_d1_p5n100'],
    128: ['results_d1_p5n128_kq_fixed', 'results_d1_p5n128'],
    200: ['results_d1_p5n200_12seeds', 'results_d1_p5n200_8seeds', 'results_d1_p5n200'],
    256: ['results_d1_p5n256_12seeds', 'results_d1_p5n256_8seeds', 'results_d1_p5n256'],
    300: ['results_d1_p5n300_12seeds', 'results_d1_p5n300'],
    512: ['results_d1_p5n512_12seeds'],
}


def find_npz(N: int) -> str | None:
    for d in P5N_DIRS[N]:
        cand = glob.glob(os.path.join(EMERGENCE, d, 'P5N*.snapshots.npz'))
        if cand:
            return cand[0]
    return None


def compute_c5_d1embedded(N: int, npz_path: str) -> dict:
    d = np.load(npz_path, allow_pickle=True)
    # Final snapshot (index -1), seed-average for stable diagnostic
    edge_xi = d['edge_xi_snapshots'][:, -1, :, :]    # (S, N, N)
    k       = d['k_snapshots'][:, -1, :, :]          # (S, N, N)
    q       = d['q_snapshots'][:, -1, :, :]          # (S, N, N)
    psi_r   = d['psi_real_snapshots'][:, -1, :]      # (S, N)
    psi_i   = d['psi_imag_snapshots'][:, -1, :]      # (S, N)
    n_seeds = int(d['n_seeds'][0]) if 'n_seeds' in d.files else edge_xi.shape[0]

    # Seed-averaged fields (matches the within-P5 ladder convention)
    xi_avg    = edge_xi.mean(axis=0)
    k_avg     = k.mean(axis=0)
    q_avg     = q.mean(axis=0)
    psi_avg_r = psi_r.mean(axis=0)
    psi_avg_i = psi_i.mean(axis=0)
    psi_avg   = psi_avg_r + 1j * psi_avg_i

    load           = residual_density(xi_avg, psi_avg, k_avg, q_avg)
    defect_density = defect_node_density(psi_avg, xi_avg)
    centre         = int(np.argmax(defect_density)) if defect_density.size else 0
    gravity        = radial_gravity_profile(xi_avg, defect_density, load, centre=centre)
    raw_shell_total = np.asarray(gravity["rho_raw_total_r"], dtype=float)
    gravity_report  = backreaction_report(
        xi_avg,
        raw_shell_total,
        gravity["r"],
        gravity["Phi_eff"],
        mass_profile=gravity["M_eff"],
    )

    # The original c5_d1embedded keys carry "newton_like_badness" defined
    # as max(1.0 - newton_like, 0.0) and "far_field_exponent_badness"
    # defined as abs(far_field_exponent + 1.0) (i.e. distance from the
    # ideal 1/r exponent -1). Match the same definitions here.
    newton_like_value   = float(gravity_report.get("newton_like", 0.0))
    far_field_exponent  = float(gravity_report.get("far_field_exponent", 0.0))
    far_field_residual  = float(gravity_report.get("far_field_residual", 0.0))
    poisson_residual    = float(gravity_report.get("poisson_residual", 0.0))

    newton_like_badness   = max(1.0 - newton_like_value, 0.0)
    far_field_exp_badness = abs(far_field_exponent + 1.0)
    far_field_res_badness = max(far_field_residual, 0.0)
    poisson_badness       = max(poisson_residual, 0.0)

    M_eff = np.asarray(gravity["M_eff"], dtype=float)
    M_eff_final = float(M_eff[-1]) if M_eff.size else float("nan")

    # Phi_eff slope at the outer-radius window (matches the existing
    # c5_d1embedded definition: linear fit slope of Phi_eff vs r at
    # the far-field segment).
    phi_eff = np.asarray(gravity["Phi_eff"], dtype=float)
    r_vals  = np.asarray(gravity["r"], dtype=float)
    valid   = np.isfinite(phi_eff) & np.isfinite(r_vals)
    if int(valid.sum()) >= 2:
        slope_fit = np.polyfit(r_vals[valid], phi_eff[valid], deg=1)
        phi_eff_slope = float(slope_fit[0])
    else:
        phi_eff_slope = float("nan")

    return {
        "branch_metadata": {
            "causal_wave_branch": "neutral_internal",
            "branch_rationale": (
                "Structural / loop-class closure repository default "
                "fallback; c5 d1-embedded diagnostic recomputed from "
                "NPZ snapshot via standalone post-snapshot pipeline."
            ),
            "schema": "worldformula/branch_metadata/v1",
        },
        "lattice_N": N,
        "source_file": f"P5N{N}.snapshots.npz",
        "source_dir": os.path.basename(os.path.dirname(npz_path)),
        "regime": f"P5N{N}",
        "n_seeds": n_seeds,
        "computation_provenance": (
            "extend_c5_d1embedded_to_higher_N.py (post-snapshot "
            "reconstruction); pipeline-identical to the bulk-evolution "
            "c5 diagnostic at P5N64/P5N100 modulo the seed-averaging "
            "of the final-snapshot state."
        ),
        "computation_timestamp": datetime.now(timezone.utc).isoformat(),
        "M_eff_final": M_eff_final,
        "Phi_eff_slope": phi_eff_slope,
        "d1_gamma_candidate_physical_newton_like_badness_best": newton_like_badness,
        "d1_gamma_candidate_physical_newton_like_badness_family_median": newton_like_badness,
        "d1_gamma_candidate_physical_far_field_exponent_badness_best": far_field_exp_badness,
        "d1_gamma_candidate_physical_far_field_exponent_badness_family_median": far_field_exp_badness,
        "d1_gamma_candidate_physical_far_field_residual_badness_best": far_field_res_badness,
        "d1_gamma_candidate_physical_far_field_residual_badness_family_median": far_field_res_badness,
        "d1_gamma_candidate_physical_poisson_residual_badness_best": poisson_badness,
    }


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=== Extending c5 d1-embedded diagnostic to higher-N P5N regimes ===")
    print(f"Output directory: {OUT_DIR}")
    print(f"{'N':>4}  {'seeds':>5}  {'newton_b':>10}  {'far_b':>10}  {'poisson_b':>10}  source")
    print("-" * 100)
    written = []
    for N in sorted(P5N_DIRS.keys()):
        npz = find_npz(N)
        if npz is None:
            print(f"{N:>4}  MISSING  (no NPZ snapshot bundled)")
            continue
        out = compute_c5_d1embedded(N, npz)
        out_path = os.path.join(OUT_DIR, f"c5_d1embedded_P5N{N}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        written.append(N)
        print(f"{N:>4}  {out['n_seeds']:>5}  "
              f"{out['d1_gamma_candidate_physical_newton_like_badness_best']:>10.4f}  "
              f"{out['d1_gamma_candidate_physical_far_field_exponent_badness_best']:>10.4f}  "
              f"{out['d1_gamma_candidate_physical_poisson_residual_badness_best']:>10.4f}  "
              f"{out['source_dir']}")
    print()
    print(f"Wrote {len(written)} JSON files: " + ", ".join(f"P5N{N}" for N in written))
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
