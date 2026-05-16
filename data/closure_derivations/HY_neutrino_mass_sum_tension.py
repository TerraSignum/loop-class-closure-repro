"""Closure-derivation H-Y: Sigma m_nu DESI tension + alternative closure.

Existing closure (memory): m_1 = m_3/(d+1) = m_3/5.
With H-T closure: m_3 = sqrt(Delta m^2_31) = sqrt(1/400) = 1/20 eV.
m_2 from oscillation: m_2 = sqrt(m_1^2 + Delta m^2_21).
Sum prediction: m_1 + m_2 + m_3 = 0.0732 eV.

SUPERSESSION NOTE (2026-05-14)
-----------------------------
This audit bundle uses the rounded m_3 = sqrt((d+1)^2 gamma^4) =
sqrt(1/400) = 0.0500 eV derived from the H-T Delta m^2_31 closure.
The CURRENT framework value of the heaviest eigenvalue is the
P-UV closure m_3 = 0.0511 eV (relational-uv-closure-repro, P6
Theorem on the vacuum reductions). With that m_3 the refined
closure m_1 = gamma^2 m_3 gives the corpus-authoritative
Sigma m_nu = 0.0603 eV, computed by
relational-uv-closure-repro/src/verify_neutrino_masses_m1_m2.py.
The m_3 = 0.0500 / Sigma = 0.0591 eV scenario below is retained
only as the documented superseded falsification-tension scenario;
it is NOT the current prediction. Tier: PRECISE (a derived sum of
three eigenvalues against a cosmological band, not a closed-form
R-rational landing).

DESI 2024 BAO+CMB combined upper bound (95% CL):
  Sum m_nu < 0.072 eV.

Excess: 1.7% over bound. The m_1 = m_3/(d+1) closure sits at
the edge.

Alternative closures (testable as DESI tightens):
  (a) m_1 = m_3/N_gen^2 = m_3/9 -> Sum = 0.066 eV (within bound)
  (b) m_1 = m_3 * gamma = 0.005 eV -> Sum = 0.065 eV (within bound)
  (c) m_1 = 0 (massless lightest) -> Sum = 0.059 eV (within bound)

The framework's m_1 closure is FALSIFIABLE by DESI 2025+. If
Sum m_nu < 0.067 eV becomes established, the m_1 = m_3/(d+1)
form is excluded and the alternative m_1 = m_3/N_gen^2 (cleaner
structural form using N_gen instead of d+1) is preferred.

Lower bound from oscillation alone (NO):
  Sum >= sqrt(Delta m^2_21) + sqrt(Delta m^2_31) = 0.0586 eV.

Discriminating measurement: future DESI / Euclid / CMB-S4 will
either rule out the framework's neutrino mass closure or
establish it as the primary identification of m_1.

Writes peer_reviews/HY_neutrino_mass_sum_tension.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "closure_derivations" / "HY_neutrino_mass_sum_tension.json"


def main():
    GAMMA = 0.1
    N_GEN = 3
    D = 4

    # H-T: Delta m^2_31 = (d+1)^2 * gamma^4 = 25/10^4 = 1/400 eV^2
    delta_m31_sq = (D+1)**2 * GAMMA**4  # 0.0025
    m_3 = math.sqrt(delta_m31_sq)        # 0.05 eV

    # Existing memory closure: m_1 = m_3/(d+1) = m_3/5
    m_1_existing = m_3 / (D+1)
    delta_m21_sq = 7.41e-5  # NuFIT 6.1
    m_2_existing = math.sqrt(m_1_existing**2 + delta_m21_sq)
    sum_existing = m_1_existing + m_2_existing + m_3

    # Alternative (a): m_1 = m_3/N_gen^2
    m_1_alt_a = m_3 / N_GEN**2
    m_2_alt_a = math.sqrt(m_1_alt_a**2 + delta_m21_sq)
    sum_alt_a = m_1_alt_a + m_2_alt_a + m_3

    # Alternative (c): m_1 = 0
    m_1_alt_c = 0.0
    m_2_alt_c = math.sqrt(delta_m21_sq)
    sum_alt_c = m_2_alt_c + m_3

    # Refined post-DESI-2025 closure on this audit's rounded m_3:
    # m_1 = gamma^2 m_3 (superseded scenario -- see SUPERSESSION NOTE).
    m_1_refined = GAMMA**2 * m_3
    m_2_refined = math.sqrt(m_1_refined**2 + delta_m21_sq)
    sum_refined = m_1_refined + m_2_refined + m_3

    # Current corpus-authoritative value uses the P-UV closure
    # m_3 = 0.0511 eV (P6), not the rounded m_3 of this audit.
    m_3_current = 0.0511
    m_1_current = GAMMA**2 * m_3_current
    m_2_current = math.sqrt(m_1_current**2 + delta_m21_sq)
    sum_current = m_1_current + m_2_current + m_3_current

    # Anchors
    DESI_2024 = 0.072  # 95% CL upper bound
    DESI_2025 = 0.0642  # DR2 BAO + DR1 full-shape 95% CL
    osc_lower = math.sqrt(delta_m21_sq) + math.sqrt(delta_m31_sq)  # ~0.059

    print(f"=== H-Y: Sum m_nu DESI tension audit ===")
    print(f"  m_3 = sqrt(Delta m^2_31) = sqrt(1/400) = 1/20 = {m_3:.5f} eV")
    print()
    print(f"  Existing m_1 = m_3/(d+1) = m_3/5:")
    print(f"    m_1 = {m_1_existing:.5f}, m_2 = {m_2_existing:.5f}, m_3 = {m_3:.5f}")
    print(f"    Sum = {sum_existing:.5f} eV")
    print(f"    vs DESI 2024 bound 0.072 eV: 1.7% over (TENSION)")
    print()
    print(f"  Alternative (a) m_1 = m_3/N_gen^2 = m_3/9:")
    print(f"    m_1 = {m_1_alt_a:.5f}")
    print(f"    Sum = {sum_alt_a:.5f} eV (within DESI)")
    print()
    print(f"  Alternative (c) m_1 = 0:")
    print(f"    Sum = {sum_alt_c:.5f} eV (osc lower bound)")
    print()
    print(f"  Oscillation absolute lower bound: {osc_lower:.5f} eV")
    print()

    print(f"  Refined (this audit's rounded m_3=0.05): "
          f"Sum = {sum_refined:.5f} eV (SUPERSEDED)")
    print(f"  Current (P-UV m_3=0.0511, corpus-authoritative): "
          f"Sum = {sum_current:.5f} eV")
    print()

    verdict = (
        f"CURRENT_PREDICTION Sigma m_nu = {sum_current:.4f} eV "
        f"(PRECISE), from the refined closure m_1 = gamma^2 m_3 with "
        f"the P-UV value m_3 = {m_3_current} eV; computed by "
        f"relational-uv-closure-repro/src/verify_neutrino_masses_m1_m2.py "
        f"and within the DESI 2025 bound 0.0642 eV at "
        f"{100*(sum_current-DESI_2025)/DESI_2025:.1f}% margin. "
        f"This audit's own scenarios use the rounded m_3 = "
        f"{m_3:.4f} eV: the legacy m_1 = m_3/(d+1) closure gives "
        f"Sum = {sum_existing:.4f} eV (DESI-2024-falsified) and the "
        f"refined m_1 = gamma^2 m_3 gives Sum = {sum_refined:.4f} eV "
        f"(SUPERSEDED -- rounded m_3, indistinguishable from the "
        f"m_1->0 oscillation lower bound at current DESI precision)."
    )
    print(f"=== Verdict ===")
    print(f"  {verdict}")

    bundle = {
        "method": "HY_neutrino_mass_sum_tension",
        "input_closure": {
            "Delta_m_31_squared": "(d+1)^2 gamma^4 = 1/400 eV^2 (H-T)",
            "m_3": float(m_3),
        },
        "scenarios": [
            {
                "label": "existing: m_1 = m_3/(d+1) = m_3/5",
                "m_1": m_1_existing,
                "m_2": m_2_existing,
                "m_3": m_3,
                "Sum": sum_existing,
                "rel_to_DESI_pct": 100*(sum_existing - DESI_2024)/DESI_2024,
                "verdict": "TENSION_AT_EDGE",
            },
            {
                "label": "alternative: m_1 = m_3/N_gen^2 = m_3/9",
                "m_1": m_1_alt_a,
                "m_2": m_2_alt_a,
                "m_3": m_3,
                "Sum": sum_alt_a,
                "rel_to_DESI_pct": 100*(sum_alt_a - DESI_2024)/DESI_2024,
                "verdict": "WITHIN_DESI",
            },
            {
                "label": "limit: m_1 = 0 (massless lightest)",
                "m_1": m_1_alt_c,
                "m_2": m_2_alt_c,
                "m_3": m_3,
                "Sum": sum_alt_c,
                "rel_to_DESI_pct": 100*(sum_alt_c - DESI_2024)/DESI_2024,
                "verdict": "OSCILLATION_LOWER_BOUND",
            },
            {
                "label": "SUPERSEDED: m_1 = gamma^2 m_3 on this "
                         "audit's rounded m_3 = 0.0500 eV",
                "m_1": m_1_refined,
                "m_2": m_2_refined,
                "m_3": m_3,
                "Sum": sum_refined,
                "rel_to_DESI_2025_pct": 100*(sum_refined-DESI_2025)/DESI_2025,
                "rel_to_oscillation_lower_pct":
                    100*(sum_refined - osc_lower)/osc_lower,
                "verdict": "SUPERSEDED_ROUNDED_M3; indistinguishable "
                           "from the m_1->0 oscillation lower bound at "
                           "current DESI precision",
            },
            {
                "label": "CURRENT: m_1 = gamma^2 m_3 with the P-UV "
                         "closure m_3 = 0.0511 eV (corpus-authoritative)",
                "m_1": m_1_current,
                "m_2": m_2_current,
                "m_3": m_3_current,
                "Sum": sum_current,
                "rel_to_DESI_2025_pct": 100*(sum_current-DESI_2025)/DESI_2025,
                "rel_to_oscillation_lower_pct":
                    100*(sum_current - osc_lower)/osc_lower,
                "tier": "PRECISE",
                "computed_by": "relational-uv-closure-repro/src/"
                               "verify_neutrino_masses_m1_m2.py",
                "verdict": "CURRENT_FRAMEWORK_PREDICTION",
            },
        ],
        "DESI_2024_upper_95pct": DESI_2024,
        "DESI_2025_upper_95pct": DESI_2025,
        "oscillation_lower_bound": osc_lower,
        "current_prediction_Sigma_m_nu_eV": sum_current,
        "current_prediction_tier": "PRECISE",
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
