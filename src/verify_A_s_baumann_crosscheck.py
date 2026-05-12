"""A_s Baumann standard-convention cross-check.

The framework's GCC-03 instanton-modulation route gives
    A_s_phys = A_s_raw * exp(-S_inst) / sqrt(N_modes) = 3.36e-9 (P1)
matching Planck 2.105e-9 within factor 1.6 (PRECISE-tier, log10 0.20).

But the framework uses the FULL Planck mass in the slow-roll formula
    A_s_raw = V_0 / (24 pi^2 M_Pl^4 epsilon)
    M_Pl = 1.221e19 GeV (full)
The standard Liddle-Lyth / Baumann convention uses the REDUCED Planck
mass M_Pl,red = M_Pl/sqrt(8 pi) = 2.435e18 GeV with the same form
of the slow-roll formula:
    A_s_raw_std = V_0 / (24 pi^2 M_Pl,red^4 epsilon)

These conventions differ by (8 pi)^2 = 632.

This script compares the two conventions on the framework's V_0 and
identifies what additional suppression / V_0 reduction would be
needed to close A_s under the standard convention.

Reproducibility: numpy only. No external data required.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent

# Framework P1 inflation outputs (from gcc02_inflation.json, verified)
v_0_p1 = 3.25e74              # GeV^4 — framework V_0 at horizon crossing
epsilon_p1 = 0.001826          # slow-roll parameter
eta_S_p1 = 3.023577            # Sommerfeld parameter (P1, HBR)
n_modes = 13                    # one-loop fluctuation determinant modes

# Constants
m_pl_full = 1.221e19            # GeV (full Planck)
m_pl_red = m_pl_full / np.sqrt(8 * np.pi)   # = 2.435e18 GeV (reduced)

# Planck 2018 reference
a_s_obs = 2.105e-9
log10_a_s_obs = np.log10(a_s_obs)


def a_s_raw(v_0, m_pl_used, eps):
    """Slow-roll raw scalar amplitude:
        A_s_raw = V_0 / (24 pi^2 M_Pl^4 epsilon)"""
    return v_0 / (24.0 * np.pi**2 * m_pl_used**4 * eps)


def main() -> int:
    print("=" * 78)
    print("A_s Baumann cross-check: full vs reduced Planck mass conventions")
    print("=" * 78)
    print()
    print(f"Framework P1 inputs:")
    print(f"  V_0 = {v_0_p1:.3e} GeV^4")
    print(f"  epsilon = {epsilon_p1:.4f}")
    print(f"  eta_S = {eta_S_p1}")
    print(f"  N_modes = {n_modes}")
    print()
    print(f"Planck mass conventions:")
    print(f"  M_Pl_full = {m_pl_full:.4e} GeV")
    print(f"  M_Pl_red  = {m_pl_red:.4e} GeV")
    print(f"  Ratio (full/red)^4 = (8 pi)^2 = {(8*np.pi)**2:.2f}")
    print()

    # Convention A: framework (full M_Pl)
    a_s_raw_full = a_s_raw(v_0_p1, m_pl_full, epsilon_p1)

    # Convention B: standard Baumann (reduced M_Pl)
    a_s_raw_red = a_s_raw(v_0_p1, m_pl_red, epsilon_p1)

    print(f"A_s_raw under each convention:")
    print(f"  Full M_Pl   : A_s_raw = {a_s_raw_full:.3e}")
    print(f"  Reduced M_Pl: A_s_raw = {a_s_raw_red:.3e}")
    print(f"  Ratio (red/full) = {a_s_raw_red/a_s_raw_full:.2f}  "
          f"(= (8 pi)^2 = {(8*np.pi)**2:.2f})")
    print()

    # Instanton modulation
    s_inst = (np.pi**2 / 2.0) * eta_S_p1
    inst_factor = np.exp(-s_inst)
    one_loop = 1.0 / np.sqrt(n_modes)
    suppression = inst_factor * one_loop
    print(f"Instanton modulation:")
    print(f"  S_inst = (pi^2/2) eta_S = {s_inst:.3f}")
    print(f"  exp(-S_inst) = {inst_factor:.3e}")
    print(f"  1/sqrt(N_modes) = {one_loop:.4f}")
    print(f"  total suppression = {suppression:.3e}")
    print()

    # A_s_phys under both conventions
    a_s_phys_full = a_s_raw_full * suppression
    a_s_phys_red = a_s_raw_red * suppression

    print(f"A_s_phys after instanton modulation:")
    print(f"  Full M_Pl   : A_s_phys = {a_s_phys_full:.3e}  "
          f"(ratio to obs = {a_s_phys_full/a_s_obs:.3f}, "
          f"log10 = {np.log10(a_s_phys_full/a_s_obs):+.3f})")
    print(f"  Reduced M_Pl: A_s_phys = {a_s_phys_red:.3e}  "
          f"(ratio to obs = {a_s_phys_red/a_s_obs:.2e}, "
          f"log10 = {np.log10(a_s_phys_red/a_s_obs):+.2f})")
    print()
    print(f"Planck observed: A_s_obs = {a_s_obs:.3e}")
    print()

    # What additional suppression would close reduced convention?
    needed_extra = a_s_obs / a_s_phys_red
    print(f"Reduced-convention closure analysis:")
    print(f"  A_s_phys_red / A_s_obs = {a_s_phys_red/a_s_obs:.3e}")
    print(f"  Additional suppression needed: x{needed_extra:.3e} "
          f"(= 1/{1/needed_extra:.0f})")
    log_extra = np.log10(needed_extra)
    print(f"  Required: log10 suppression = {log_extra:+.3f}")
    print()

    # Could it come from S_inst correction?
    # If S_inst -> S_inst + dS, additional suppression exp(-dS) = needed_extra
    # dS = -ln(needed_extra)
    d_s_inst_required = -np.log(needed_extra)
    print(f"Possible mechanisms for additional suppression:")
    print(f"  (a) S_inst correction dS = {d_s_inst_required:.3f} "
          f"(would shift S_inst from {s_inst:.2f} to {s_inst+d_s_inst_required:.2f})")
    # Could it come from V_0 reduction? V_0 -> V_0 / x where x = needed
    print(f"  (b) V_0 reduction to V_0 x {needed_extra:.3e} = "
          f"{v_0_p1*needed_extra:.3e} GeV^4")
    print(f"      V_0^(1/4)_required = {(v_0_p1*needed_extra)**0.25:.3e} GeV")
    print()
    # This V_0^(1/4) corresponds to what scale relative to M_Pl?
    v_required = v_0_p1 * needed_extra
    v_quarter = v_required**0.25
    print(f"  Required V_0^(1/4) / M_Pl_red = {v_quarter/m_pl_red:.3e}")
    print(f"  ln(M_Pl_red / V_0^(1/4)_req)  = {np.log(m_pl_red/v_quarter):.3f}")

    # System-R check: gamma=1/10, eps_sync=sqrt(1/20)
    gamma = 0.10
    eps_sync_sq = 0.05
    print()
    print(f"System-R candidate matching for V_0^(1/4) suppression "
          f"factor {v_quarter/m_pl_red:.3e}:")
    candidates = {
        "gamma": gamma,
        "gamma^2": gamma**2,
        "gamma^3": gamma**3,
        "gamma * eps_sync^2": gamma * eps_sync_sq,
        "gamma^2 * eps_sync^2": gamma**2 * eps_sync_sq,
        "gamma^2 / eps_sync": gamma**2 / np.sqrt(eps_sync_sq),
        "gamma * eps_sync": gamma * np.sqrt(eps_sync_sq),
        "exp(-S_inst/4)": np.exp(-s_inst/4),
        "exp(-S_inst/8)": np.exp(-s_inst/8),
    }
    target = v_quarter / m_pl_red
    print(f"  target = {target:.4e}")
    for name, val in candidates.items():
        ratio = val / target
        print(f"  {name:<22} = {val:.4e}  (ratio {ratio:.3f})")
    print()

    # Verdict
    if abs(np.log10(a_s_phys_full/a_s_obs)) < 0.5:
        framework_verdict = ("PRECISE (full-M_Pl convention): "
                             f"factor {a_s_phys_full/a_s_obs:.2f}, "
                             f"log10 {np.log10(a_s_phys_full/a_s_obs):+.2f}")
    else:
        framework_verdict = ("FAIL (full-M_Pl): off by "
                             f"factor {abs(np.log10(a_s_phys_full/a_s_obs)):.2f} "
                             "log-orders")
    if abs(np.log10(a_s_phys_red/a_s_obs)) < 0.5:
        baumann_verdict = ("PRECISE (Baumann reduced): "
                           f"factor {a_s_phys_red/a_s_obs:.2f}")
    else:
        baumann_verdict = ("OPEN (Baumann reduced): off by "
                           f"factor {abs(np.log10(a_s_phys_red/a_s_obs)):.2f} "
                           "log-orders; additional suppression "
                           "mechanism needed to close")
    print(f"Framework convention verdict: {framework_verdict}")
    print(f"Baumann convention verdict:   {baumann_verdict}")
    print()

    bundle = {
        "method": "A_s_Baumann_crosscheck",
        "schema_version": "1.0.0",
        "framework_inputs": {
            "V_0_GeV4": v_0_p1, "epsilon": epsilon_p1,
            "eta_S": eta_S_p1, "N_modes": n_modes,
        },
        "M_Pl_conventions": {
            "M_Pl_full_GeV": m_pl_full,
            "M_Pl_red_GeV": m_pl_red,
            "ratio_full4_over_red4": (8*np.pi)**2,
        },
        "instanton_modulation": {
            "S_inst": s_inst, "exp_neg_S_inst": inst_factor,
            "one_loop_factor": one_loop, "total_suppression": suppression,
        },
        "A_s_predictions": {
            "framework_full_MPl": {
                "A_s_raw": a_s_raw_full,
                "A_s_phys": a_s_phys_full,
                "ratio_to_obs": a_s_phys_full / a_s_obs,
                "log10_ratio": np.log10(a_s_phys_full / a_s_obs),
                "verdict": framework_verdict,
            },
            "Baumann_reduced_MPl": {
                "A_s_raw": a_s_raw_red,
                "A_s_phys": a_s_phys_red,
                "ratio_to_obs": a_s_phys_red / a_s_obs,
                "log10_ratio": np.log10(a_s_phys_red / a_s_obs),
                "verdict": baumann_verdict,
            },
        },
        "Baumann_closure_required": {
            "additional_suppression": needed_extra,
            "delta_S_inst_required": d_s_inst_required,
            "V_0_required_GeV4": v_required,
            "V_0_quarter_required_GeV": v_quarter,
            "V_quarter_over_M_Pl_red": v_quarter / m_pl_red,
        },
    }
    out = REPO / "outputs" / "verify_A_s_baumann_crosscheck.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
