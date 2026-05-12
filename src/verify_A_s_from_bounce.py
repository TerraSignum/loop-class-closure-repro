"""Compute the primordial scalar amplitude A_s from V_inflation
slow-roll, with V_inflation derived from the framework reheat
temperature T_RH.

HONEST AUDIT (2026-05-03 evening):
  An earlier version of this audit used the FULL Planck mass
  M_Pl = 1.22 x 10^19 GeV in both the Friedmann relation
  H^2 = V / (3 M_Pl^2) and in the slow-roll A_s formula. The
  standard slow-roll formula uses the REDUCED Planck mass
  M_Pl_red = M_Pl / sqrt(8 pi) = 2.435 x 10^18 GeV. With the
  correct convention, the framework's available T_RH values do
  NOT match Planck A_s = 2.105 x 10^-9 within slow-roll precision.
  The earlier 'PRECISE 4.9%' claim was a unit-convention
  coincidence and is RETRACTED.

Current honest verdict:
  - Framework T_RH (v5 = 6.61e16 GeV) -> A_s = 1.26e-6 (600x too high)
  - Framework T_RH (Phase-III = 4.29e17 GeV) -> A_s = 2.24e-3 (10^6 too high)
  - Required for A_s match: V^(1/4) = 1.34e16 GeV, H_inf = 4.2e13 GeV

The framework's T_RH values are too high under the
instantaneous-reheat-equals-V-end assumption to match Planck A_s.
A separate, lower V_inflation scale must be derived from first
principles (the framework currently does not have this).

Reproducibility: requires only numpy.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent

# Framework constants
m_pl_full = 1.2209e19              # CODATA 2018
m_pl_red = m_pl_full / np.sqrt(8.0 * np.pi)  # = 2.435 x 10^18 GeV (reduced)

# Two candidate T_RH values from the broader corpus
t_rh_v5 = 6.61e16                  # gravitational inflaton-decay channel (v5)
t_rh_phase_iii = 4.29e17            # Kolb-Turner with kinetic correction (Phase-III)

# Tensor-to-scalar ratio framework prediction (P3, loop-class)
r_tensor_pred = 0.029

# Planck 2018 reference values (FOR COMPARISON ONLY)
n_s_obs = 0.9649
a_s_obs = 2.105e-9


def slow_roll_a_s(v_inf, m_pl_reduced, epsilon):
    """Standard slow-roll formula:
        A_s = V / (24 pi^2 M_Pl_reduced^4 epsilon).

    Uses the REDUCED Planck mass convention (Friedmann
    H^2 = V / (3 M_Pl_red^2), and A_s = H^2 / (8 pi^2 M_Pl_red^2 eps)).
    """
    return v_inf / (24.0 * np.pi ** 2 * m_pl_reduced ** 4 * epsilon)


def required_v_for_a_s(a_s_target, m_pl_reduced, epsilon):
    """Inverse of the slow-roll formula: V required to match a target A_s."""
    return a_s_target * 24.0 * np.pi ** 2 * m_pl_reduced ** 4 * epsilon


def main() -> int:
    print("=" * 78)
    print("A_s prediction from V_inflation slow-roll (honest audit)")
    print("=" * 78)
    print()
    print("Convention: REDUCED Planck mass M_Pl_red = 2.435 x 10^18 GeV")
    print("Standard slow-roll formula: A_s = V / (24 pi^2 M_Pl_red^4 eps)")
    print()

    epsilon = r_tensor_pred / 16.0
    print(f"Slow-roll epsilon = r/16 = {epsilon:.6f}")
    print()

    print(f"{'T_RH source':<25} {'T_RH [GeV]':>14} "
          f"{'V [GeV^4]':>14} {'A_s_pred':>12} "
          f"{'A_s/A_s_obs':>14}")
    print("-" * 85)
    bundle_rows = []
    for label, t_rh in [("v5 grav-decay", t_rh_v5),
                         ("Phase-III KT-kin", t_rh_phase_iii)]:
        v_inf = t_rh ** 4
        a_s_pred = slow_roll_a_s(v_inf, m_pl_red, epsilon)
        ratio = a_s_pred / a_s_obs
        print(f"{label:<25} {t_rh:>14.3e} {v_inf:>14.3e} "
              f"{a_s_pred:>12.3e} {ratio:>14.3e}")
        bundle_rows.append({
            "label": label,
            "T_RH_GeV": t_rh,
            "V_GeV4": v_inf,
            "A_s_pred": a_s_pred,
            "ratio_to_planck": ratio,
        })

    # What V is required for A_s = 2.105e-9?
    v_required = required_v_for_a_s(a_s_obs, m_pl_red, epsilon)
    t_rh_required = v_required ** 0.25
    h_inf_required = np.sqrt(v_required / (3.0 * m_pl_red ** 2))
    print()
    print(f"For A_s = {a_s_obs} (Planck observed):")
    print(f"  V_inflation = {v_required:.3e} GeV^4")
    print(f"  V^(1/4)     = {t_rh_required:.3e} GeV (~ GUT scale)")
    print(f"  H_inf       = {h_inf_required:.3e} GeV")
    print()

    # Honest verdict
    print("Honest verdict:")
    print("  The framework's available T_RH values (6.6e16 and 4.3e17 GeV)")
    print("  are too high under the instantaneous-reheat assumption")
    print("  V_inflation = T_RH^4 to match Planck A_s under standard")
    print("  slow-roll. The framework does not yet derive V_inflation")
    print("  from a separate first-principles calculation; the necessary")
    print("  V^(1/4) ~ 1.3e16 GeV would have to be lower than T_RH by a")
    print("  factor 5-30, requiring non-instantaneous reheat with")
    print("  a specific efficiency that has not been derived.")
    print()
    print("  A_s remains OPEN at strict-EXACT and at PRECISE-tier")
    print("  closure under the present framework.")

    bundle = {
        "method": "verify_A_s_from_T_RH_slow_roll_HONEST",
        "schema_version": "2.0.0",
        "convention": "reduced_planck_mass_standard_slow_roll",
        "M_Pl_full_GeV": m_pl_full,
        "M_Pl_reduced_GeV": m_pl_red,
        "epsilon_slow": epsilon,
        "r_tensor_framework": r_tensor_pred,
        "framework_T_RH_candidates": bundle_rows,
        "A_s_obs_planck": a_s_obs,
        "required_for_A_s_match": {
            "V_GeV4": v_required,
            "V_quarter_GeV": t_rh_required,
            "H_inf_GeV": h_inf_required,
        },
        "verdict": (
            "A_s remains OPEN: framework T_RH values are 5-30x too high "
            "under instantaneous-reheat assumption to match Planck A_s "
            "under standard slow-roll. An earlier 'PRECISE 4.9%' claim "
            "based on full-Planck-mass convention is RETRACTED."),
        "retraction_note": (
            "An earlier audit version used the FULL Planck mass in both "
            "Friedmann and slow-roll A_s formulas; the cancellation "
            "produced a misleading apparent match to Planck. Standard "
            "convention uses the REDUCED Planck mass throughout."),
    }
    out = REPO / "outputs" / "verify_A_s_from_bounce.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"\nSaved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
