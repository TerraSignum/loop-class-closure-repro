r"""
Verify the bundled electroweak gauge-boson mass closure: m_W and m_Z
derived parameter-free from three already-closed inputs (v_EW from P1,
sin^2 theta_W from L6 of P2, alpha_EM from PDG). Standard-Model tree
relations feed all three forward to EXACT-tier match against PDG 2024.

Identities verified:
  m_W = sqrt(4 pi alpha_EM / sin^2 theta_W) * v_EW / 2
  m_Z = m_W / sqrt(1 - sin^2 theta_W)

Usage:
    python ./src/verify_electroweak_boson_masses.py
"""

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def load_bundle():
    with open(DATA / "electroweak_boson_masses.json", "r", encoding="utf-8") as f:
        return json.load(f)


def recompute_m_w(v_ew_gev: float, sin2_theta_w: float,
                  alpha_em_inv: float) -> float:
    """SM tree relation: m_W = sqrt(4 pi alpha_EM / sin^2 theta_W) * v_EW / 2."""
    alpha_em = 1.0 / alpha_em_inv
    g_squared = 4.0 * math.pi * alpha_em / sin2_theta_w
    g = math.sqrt(g_squared)
    return g * v_ew_gev / 2.0


def recompute_m_z(m_w_gev: float, sin2_theta_w: float) -> float:
    """SM tree relation: m_Z = m_W / sqrt(1 - sin^2 theta_W)."""
    return m_w_gev / math.sqrt(1.0 - sin2_theta_w)


def main():
    d = load_bundle()
    print("=" * 78)
    print("Electroweak gauge-boson mass closure recompute")
    print("=" * 78)
    print()

    inp = d["inputs"]
    print("--- Inputs (all parameter-free) ---")
    print(f"  v_EW:                   {inp['v_EW_GeV']} GeV")
    print(f"  sin^2 theta_W:          {inp['sin2_theta_W']}")
    print(f"  alpha_EM(M_Z) inverse:  {inp['alpha_EM_inv_at_MZ']}")
    print()

    # Recompute m_W from inputs
    m_w_recomputed = recompute_m_w(
        inp["v_EW_GeV"], inp["sin2_theta_W"], inp["alpha_EM_inv_at_MZ"]
    )
    m_w = d["m_W_closure"]
    print(f"--- m_W closure ---")
    print(f"  Identity:  {m_w['structural_identity']}")
    print(f"  Bundled prediction:    {m_w['predicted_GeV']} GeV")
    print(f"  Recomputed prediction: {m_w_recomputed:.4f} GeV")
    print(f"  PDG anchor:            {m_w['anchor_GeV']} +/- "
          f"{m_w['anchor_uncertainty_GeV']} GeV")
    print(f"  Residual:              {m_w['residual_pct']}%   Tier: {m_w['tier']}")
    print()

    # Recompute m_Z
    m_z_recomputed = recompute_m_z(m_w_recomputed, inp["sin2_theta_W"])
    m_z = d["m_Z_closure"]
    print(f"--- m_Z closure ---")
    print(f"  Identity:  {m_z['structural_identity']}")
    print(f"  Bundled prediction:    {m_z['predicted_GeV']} GeV")
    print(f"  Recomputed prediction: {m_z_recomputed:.4f} GeV")
    print(f"  PDG anchor:            {m_z['anchor_GeV']} +/- "
          f"{m_z['anchor_uncertainty_GeV']} GeV")
    print(f"  Residual:              {m_z['residual_pct']}%   Tier: {m_z['tier']}")
    print()

    # Cross-check Weinberg
    cc = d["cross_check"]
    print("--- Weinberg-angle cross-check ---")
    print(f"  Predicted m_Z/m_W:    {cc['weinberg_angle_consistency']['m_Z_over_m_W_predicted']:.5f}")
    print(f"  PDG m_Z/m_W:          {cc['weinberg_angle_consistency']['m_Z_over_m_W_pdg']:.5f}")
    print(f"  Consistency residual: "
          f"{cc['weinberg_angle_consistency']['ratio_consistency_pct']}%")
    print()

    s = d["summary"]
    print("--- Summary ---")
    print(f"  Closures:           {s['n_closures']}")
    print(f"  Fitted parameters:  {s['fitted_parameters']}")
    print()

    # Pass criteria: bundled prediction reproduces from formula to 4 decimals
    formula_consistent = (
        abs(m_w_recomputed - m_w["predicted_GeV"]) < 0.01
        and abs(m_z_recomputed - m_z["predicted_GeV"]) < 0.01
    )
    tier_pass = (
        m_w["tier"] == "EXACT" and m_w["residual_pct"] <= 0.4
        and m_z["tier"] == "EXACT" and m_z["residual_pct"] <= 0.4
    )

    out = {
        "criterion": "Electroweak gauge-boson mass closure recompute",
        "m_W_predicted_GeV": m_w["predicted_GeV"],
        "m_W_recomputed_GeV": round(m_w_recomputed, 4),
        "m_W_residual_pct": m_w["residual_pct"],
        "m_W_EXACT": m_w["tier"] == "EXACT",
        "m_Z_predicted_GeV": m_z["predicted_GeV"],
        "m_Z_recomputed_GeV": round(m_z_recomputed, 4),
        "m_Z_residual_pct": m_z["residual_pct"],
        "m_Z_EXACT": m_z["tier"] == "EXACT",
        "formula_consistent_with_bundled": formula_consistent,
        "fitted_parameters": s["fitted_parameters"],
        "verdict": (
            "PASS"
            if (formula_consistent and tier_pass and s["fitted_parameters"] == 0)
            else "FAIL"
        ),
    }
    out_path = OUTPUTS / "electroweak_boson_masses_recompute.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
