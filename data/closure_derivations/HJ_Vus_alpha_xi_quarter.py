"""Closure-derivation H-J: alternate V_us closure V_us = alpha_xi / 4 = 9/40.

The loop-class closure currently asserts V_us = gamma sqrt(5)
= 0.22361, with a 0.10% match in the manuscript citation
(against an internal reference). PDG 2024 gives
|V_us| = 0.22501 +/- 0.00046 (K_l3 + 0+ -> 0+ beta decay
combination, RPP 2024).

Cross-check: alpha_xi / 4 = 9/40 = 0.22500 is EXACTLY in the
PDG central value to <0.01%, and is purely rational (no
sqrt(5)). The two candidate forms differ:

  V_us = gamma sqrt(5)     = 0.22361   rel-err vs PDG 0.62%
  V_us = alpha_xi / 4 = 9/40 = 0.22500 rel-err vs PDG 0.005%

Both have clean structural form:
  gamma sqrt(5)   : (defect-coupling) x sqrt(generation count + d - 2)
  alpha_xi / 4    : (back-channel projection) / (BH entropy face)^{-1}
                  = back-channel projection x BH entropy face

The s_face = 1/4 reading gives:
  V_us = alpha_xi * s_face

i.e. V_us is the back-channel projection times the BH entropy
face fraction. This connects to H-I's
sin^2(theta_W) = 1/4 - tau/N_gen via the same s_face = 1/4
factor.

This script audits the comparison and reports the verdict.
Writes peer_reviews/HJ_Vus_alpha_xi_quarter.json
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path("C:/Users/user/Desktop/Emergence")
OUT = ROOT / "peer_reviews" / "HJ_Vus_alpha_xi_quarter.json"


def main():
    GAMMA = Fraction(1, 10)
    ALPHA_XI = Fraction(9, 10)
    S_FACE = Fraction(1, 4)

    # PDG 2024 |V_us|
    pdg_vus_central = 0.22501
    pdg_vus_uncertainty = 0.00046

    # Candidate 1: V_us = gamma sqrt(5) (existing loop-class closure)
    cand1_label = "gamma sqrt(5)"
    cand1_value = float(GAMMA) * math.sqrt(5)
    cand1_rel_err = abs(cand1_value - pdg_vus_central) / pdg_vus_central

    # Candidate 2: V_us = alpha_xi / 4 = alpha_xi * s_face
    cand2_label = "alpha_xi * s_face = 9/40"
    cand2_value = float(ALPHA_XI * S_FACE)
    cand2_rel_err = abs(cand2_value - pdg_vus_central) / pdg_vus_central

    # Candidate 3: V_us = (1+gamma)/(d+1) for cross-check
    cand3_label = "(1+gamma)/(d+1) = 11/50"
    cand3_value = float(Fraction(1+1, 4+1)) + 0  # not great
    # Actually let's compute: (1+gamma)/(d+1) = 1.1/5 = 0.22
    cand3_value = (1 + float(GAMMA)) / (4 + 1)
    cand3_rel_err = abs(cand3_value - pdg_vus_central) / pdg_vus_central

    candidates = [
        {"label": cand1_label, "form": "gamma * sqrt(5)",
         "value": cand1_value,
         "is_rational": False,
         "rel_err_PDG_pct": 100 * cand1_rel_err,
         "z_score_PDG": (cand1_value - pdg_vus_central) / pdg_vus_uncertainty},
        {"label": cand2_label, "form": "alpha_xi / 4 = 9/40",
         "value": cand2_value,
         "is_rational": True,
         "rel_err_PDG_pct": 100 * cand2_rel_err,
         "z_score_PDG": (cand2_value - pdg_vus_central) / pdg_vus_uncertainty},
        {"label": cand3_label, "form": "(1+gamma)/(d+1) = 11/50",
         "value": cand3_value,
         "is_rational": True,
         "rel_err_PDG_pct": 100 * cand3_rel_err,
         "z_score_PDG": (cand3_value - pdg_vus_central) / pdg_vus_uncertainty},
    ]

    print(f"=== |V_us| candidate comparison vs PDG 2024 ===")
    print(f"  PDG: |V_us| = {pdg_vus_central:.5f} +/- {pdg_vus_uncertainty:.5f}")
    print()
    print(f"{'Form':<32s} {'Value':>10s} {'rel-err':>10s} {'z-PDG':>10s}")
    for c in candidates:
        print(f"  {c['label']:<30s} {c['value']:>10.5f} "
              f"{c['rel_err_PDG_pct']:>9.3f}% {c['z_score_PDG']:>+10.2f}")
    print()

    candidates.sort(key=lambda c: c["rel_err_PDG_pct"])
    best = candidates[0]
    print(f"=== Best match: {best['label']} ===")
    print(f"  rel-err = {best['rel_err_PDG_pct']:.3f}% ({abs(best['z_score_PDG']):.2f} sigma)")
    print()

    # Test the s_face*alpha_xi reading vs sin^2(theta_W) reading
    sin2_theta_W_pred = 1.0/4.0 - (float(GAMMA)/2) / 3.0  # H-I
    print(f"=== Coherence with H-I and other s_face=1/4 closures ===")
    print(f"  sin^2(theta_W) = 1/4 - tau/N_gen = 7/30 = {sin2_theta_W_pred:.5f}  "
          f"(H-I, tau = gamma/2 = 1/20)")
    print(f"  V_us           = alpha_xi * 1/4   = 9/40 = "
          f"{float(ALPHA_XI*S_FACE):.5f}  (this hypothesis)")
    print(f"  Both use s_face = 1/4 = BH entropy face fraction;")
    print(f"  V_us = back-channel projection x s_face.")
    print()

    if best["label"] == cand2_label:
        verdict = (
            "ALPHA_XI_QUARTER_PREFERRED: V_us = alpha_xi / 4 = 9/40 "
            f"matches PDG 2024 V_us = 0.22501(46) at "
            f"{best['rel_err_PDG_pct']:.3f}% rel-err, dominating over "
            f"V_us = gamma*sqrt(5) (rel-err {cand1_rel_err*100:.2f}%). "
            "The reading V_us = alpha_xi * s_face = "
            "back-channel projection times BH entropy face fraction "
            "uses only System-R rationals and the same s_face=1/4 "
            "structure as H-I's sin^2(theta_W) closure."
        )
    else:
        verdict = f"GAMMA_SQRT5_RETAINED: best match = {best['label']}"
    print(f"Verdict: {verdict}")

    bundle = {
        "method": "HJ_Vus_alpha_xi_quarter",
        "PDG_2024_Vus": {
            "central": pdg_vus_central,
            "uncertainty": pdg_vus_uncertainty,
        },
        "framework_constants": {
            "gamma": "1/10", "alpha_xi": "9/10",
            "s_face": "1/4 (BH entropy face)",
        },
        "candidates": candidates,
        "best_match": best,
        "coherence_with_HI": {
            "sin2_theta_W": "1/4 - tau/N_gen = 7/30 = 0.2333",
            "V_us": "alpha_xi * 1/4 = 9/40 = 0.2250",
            "common_structure": "s_face = 1/4 appears in both",
        },
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print()
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
