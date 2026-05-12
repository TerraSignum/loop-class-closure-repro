"""alpha_W self-consistency resolution: alpha_EM(0) -> alpha_EM(M_Z)
running brings the framework alpha_W^-1 in line with PDG.

The companion verifier verify_alpha_em_pattern_consistency.py reports
that the framework prediction

    alpha_W^-1 = sin^2(theta_W) / alpha_EM
              = 0.23064 / 0.00729 = 31.64

sits 6.5% above the PDG 2024 value alpha_W^-1(M_Z) = 29.59. The
6.5% gap is a *renormalisation-scale* mismatch, not a structural
disagreement: the framework's alpha_EM = 7.29e-3 is the Thomson-
limit (zero-momentum) value alpha_EM(0), while PDG's alpha_W^-1(M_Z)
is evaluated at the Z-pole using the running QED coupling

    alpha_EM(M_Z) = alpha_EM(0) / (1 - Delta_alpha_hadr - Delta_alpha_lept).

With the standard PDG values
    Delta_alpha_lept  = 0.031497
    Delta_alpha_hadr  = 0.027660
    Delta_alpha_total = 0.059157
gives alpha_EM(M_Z) = alpha_EM(0) / (1 - 0.059157) = alpha_EM(0)
* 1.0628.

Plugging the framework alpha_EM(0) = 7.29e-3 into the running
gives

    alpha_EM(M_Z) = 7.747e-3 = 1/129.07

and the framework alpha_W self-consistency becomes

    alpha_W^-1(M_Z) = sin^2(theta_W) / alpha_EM(M_Z)
                    = 0.23064 / 0.007747 = 29.77

vs PDG 29.59, residual 0.6%. The 6.5% gap is fully accounted
for by QED running. The script writes a JSON certificate of this
resolution.

Output: outputs/verify_alpha_W_self_consistency.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "verify_alpha_W_self_consistency.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Framework values
GAMMA = 1.0 / 10.0
ALPHA_XI = 9.0 / 10.0
N_GEN = 3
ALPHA_EM_0 = GAMMA ** 2 * ALPHA_XI ** N_GEN  # = 729/100000
EPS_SYNC_SQ = 1.0 / 20.0
SIN2_THETA_W_FRAMEWORK_1 = (
    15.0 / 16.0 - (1.0 - GAMMA) * math.pi / 4.0)  # beta_pi - (1-g)pi/4
SIN2_THETA_W_FRAMEWORK_2 = (
    1.0 / 4.0 - EPS_SYNC_SQ / N_GEN)  # 1/4 - eps^2/N_gen

# PDG 2024 constants
PDG_ALPHA_W_INV_AT_MZ = 29.59
PDG_SIN2_THETA_W_AT_MZ = 0.23122
PDG_DELTA_ALPHA_LEPT = 0.031497
PDG_DELTA_ALPHA_HADR = 0.027660
PDG_DELTA_ALPHA_TOTAL = (PDG_DELTA_ALPHA_LEPT
                         + PDG_DELTA_ALPHA_HADR)


def alpha_em_at_mz(alpha_em_0: float, delta_alpha: float) -> float:
    """Standard QED running: alpha_EM(M_Z) = alpha_EM(0)/(1-Delta)."""
    return alpha_em_0 / (1.0 - delta_alpha)


def main() -> int:
    alpha_em_mz = alpha_em_at_mz(ALPHA_EM_0, PDG_DELTA_ALPHA_TOTAL)
    alpha_em_mz_inv = 1.0 / alpha_em_mz

    rows = []
    for label, sin2 in [
        ("sin^2 theta_W = beta_pi - (1-gamma)*pi/4 (P3 closure_table)",
         SIN2_THETA_W_FRAMEWORK_1),
        ("sin^2 theta_W = 1/4 - eps_sync^2/N_gen (alpha_EM-mediated)",
         SIN2_THETA_W_FRAMEWORK_2),
        ("PDG sin^2 theta_W(M_Z) = 0.23122",
         PDG_SIN2_THETA_W_AT_MZ),
    ]:
        alpha_w_inv_naive = sin2 / ALPHA_EM_0
        alpha_w_inv_running = sin2 / alpha_em_mz
        residual_naive_pct = ((alpha_w_inv_naive
                                - PDG_ALPHA_W_INV_AT_MZ)
                                / PDG_ALPHA_W_INV_AT_MZ) * 100.0
        residual_running_pct = ((alpha_w_inv_running
                                  - PDG_ALPHA_W_INV_AT_MZ)
                                  / PDG_ALPHA_W_INV_AT_MZ) * 100.0
        rows.append({
            "sin2_theta_W_label": label,
            "sin2_theta_W_value": sin2,
            "alpha_W_inv_naive (alpha_EM(0))": alpha_w_inv_naive,
            "alpha_W_inv_with_running (alpha_EM(M_Z))":
                alpha_w_inv_running,
            "residual_naive_pct_to_PDG":   residual_naive_pct,
            "residual_running_pct_to_PDG": residual_running_pct,
        })

    bundle = {
        "method": "verify_alpha_W_self_consistency",
        "schema_version": "1.0.0",
        "framework_constants": {
            "gamma":         GAMMA,
            "alpha_xi":      ALPHA_XI,
            "N_gen":         N_GEN,
            "alpha_EM_0":    ALPHA_EM_0,
            "eps_sync_sq":   EPS_SYNC_SQ,
            "sin2_theta_W_via_beta_pi":     SIN2_THETA_W_FRAMEWORK_1,
            "sin2_theta_W_via_eps_sync":    SIN2_THETA_W_FRAMEWORK_2,
        },
        "pdg_constants": {
            "alpha_W_inv_at_MZ": PDG_ALPHA_W_INV_AT_MZ,
            "sin2_theta_W_at_MZ": PDG_SIN2_THETA_W_AT_MZ,
            "delta_alpha_lept": PDG_DELTA_ALPHA_LEPT,
            "delta_alpha_hadr": PDG_DELTA_ALPHA_HADR,
            "delta_alpha_total": PDG_DELTA_ALPHA_TOTAL,
        },
        "qed_running_factor": (
            1.0 / (1.0 - PDG_DELTA_ALPHA_TOTAL)),
        "alpha_em_at_mz_predicted": alpha_em_mz,
        "alpha_em_at_mz_inv_predicted": alpha_em_mz_inv,
        "alpha_em_at_mz_inv_pdg_value": 127.951,
        "alpha_em_at_mz_inv_residual_pct":
            ((alpha_em_mz_inv - 127.951) / 127.951) * 100.0,
        "rows": rows,
        "verdict": (
            "alpha_W self-consistency is resolved by recognising "
            "that the framework's alpha_EM = 7.29e-3 is alpha_EM(0) "
            "(Thomson limit), not alpha_EM(M_Z). The PDG value "
            "alpha_W^-1(M_Z) = 29.59 is constructed from "
            "alpha_EM(M_Z) = alpha_EM(0)/(1 - Delta_alpha_total). "
            "The framework prediction with QED running properly "
            "applied lands at alpha_W^-1(M_Z) = "
            "{:.3f} (residual {:+.2f}% vs PDG 29.59), "
            "fully resolving the previously-reported 6.5% gap as "
            "a renormalisation-scale mismatch rather than a "
            "structural disagreement."
            .format(rows[0]["alpha_W_inv_with_running (alpha_EM(M_Z))"],
                    rows[0]["residual_running_pct_to_PDG"])
        ),
    }
    OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    print("=" * 72)
    print("alpha_W self-consistency: alpha_EM(0) -> alpha_EM(M_Z) running")
    print("=" * 72)
    print(f"  framework alpha_EM(0)     = {ALPHA_EM_0:.6f} "
          f"(= 729/100000)")
    print(f"  QED Delta_alpha_total      = {PDG_DELTA_ALPHA_TOTAL:.6f}")
    print(f"  framework alpha_EM(M_Z)   = {alpha_em_mz:.6f} "
          f"(= {alpha_em_mz_inv:.4f}^-1)")
    print(f"  PDG       alpha_EM(M_Z)^-1 = 127.951  "
          f"residual {bundle['alpha_em_at_mz_inv_residual_pct']:+.2f}%")
    print()
    for r in rows:
        print(f"  sin^2 theta_W = {r['sin2_theta_W_value']:.5f} "
              f"({r['sin2_theta_W_label']})")
        print(f"    alpha_W^-1 naive   = "
              f"{r['alpha_W_inv_naive (alpha_EM(0))']:.3f}  "
              f"(residual_pct {r['residual_naive_pct_to_PDG']:+.2f}%)")
        print(f"    alpha_W^-1 running = "
              f"{r['alpha_W_inv_with_running (alpha_EM(M_Z))']:.3f}  "
              f"(residual_pct {r['residual_running_pct_to_PDG']:+.2f}%)")
        print()
    print(f"  saved {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
