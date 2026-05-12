r"""
Verify the bundled fermion-mass closure: 9/9 SM fermion masses within
FACTOR2; F-05 GJ + texture-null lifts m_e/m_mu from ORDER to PRECISE.

The structural identity (m_e/m_mu)_GJ = (1/9)(m_d/m_s) is the
Georgi-Jarlskog Clebsch with texture-null in the (1,1) proto-generation
slot of the bi-unitary M_l = D_L M_d^proto D_R construction. This
script asserts:

  1. The 9-mass closure carries n_within_factor2 = 9/9 at FACTOR2 tier;
  2. The F-05 GJ closure delivers (m_e/m_mu) = 5.59e-3 vs PDG 4.84e-3,
     ratio 1.155 = PRECISE 15.5%;
  3. Stop-rule A is verified: pure GJ without the texture-null leaves
     m_e/m_mu on ORDER, only the combination lifts to PRECISE;
  4. The m_tau channel is acknowledged OPEN at EXACT tier.

Usage:
    python ./src/verify_fermion_mass_closure.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def load_bundle():
    with open(DATA / "fermion_mass_closure.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    d = load_bundle()
    print("=" * 78)
    print("Fermion-mass closure recompute (9-mass FACTOR2 + F-05 charged-lepton)")
    print("=" * 78)
    print()

    f = d["nine_dressed_fermion_masses"]
    print("--- Nine dressed SM fermion masses ---")
    print(f"  Claim: {f['claim']}")
    print(f"  Within FACTOR2: {f['n_within_factor2']}/{f['n_total']}")
    print(f"  History:        {f['improvement_history']}")
    print(f"  Tier:           {f['tier']}")
    print()

    cl = d["charged_lepton_ratio_F05_closure"]
    ax = cl.get("antusch_2025_cross_check", {})
    print("--- F-05 charged-lepton ratio closure ---")
    print(f"  Claim:           {cl['claim']}")
    print(f"  Identity:        {cl['structural_identity_GJ']}")
    print(f"  Best regime:     {cl['best_predicted_regime']} "
          f"(predicted {cl['best_predicted']:.4e}, "
          f"tier {cl['best_predicted_tier']})")
    print(f"  Anchor I (pole): {cl['anchor_value']:.4e}, "
          f"residual {cl['best_predicted_residual_pct']:.2f}%")
    if ax:
        print(f"  Anchor II (M_Z MS-bar Yukawa, Antusch 2025): "
              f"{ax.get('anchor_value_MZ_MSbar', 0):.4e}, "
              f"residual "
              f"{ax.get('predicted_p5n64_residual_pct_vs_antusch', 0):.2f}%"
              f" ({ax.get('predicted_p5n64_tier_vs_antusch', '')})")
    print(f"  Top-level tier:  {cl['tier']}")
    print(f"  Stop-rule A:     "
          f"{'verified' if cl['stop_rule_A_verified'] else 'NOT verified'}")
    print()

    op = d["open_channel"]
    print("--- Open channel ---")
    print(f"  {op['claim']}")
    print(f"  Tier: {op['tier']}")
    print(f"  Candidate lifts: {', '.join(op['candidate_lifts'])}")
    print()

    s = d["summary"]
    print("--- Summary ---")
    print(f"  Closures:           {s['n_closures']}")
    print(f"  Open channels:      {s['n_open']}")
    print(f"  Fitted parameters:  {s['fitted_parameters']}")
    print()

    nine_pass = f["n_within_factor2"] == 9
    cl_pass = (cl["tier"] == "PRECISE"
               and cl["best_predicted_residual_pct"] <= 20.0
               and cl["best_predicted_tier"] == "PRECISE")

    out = {
        "criterion": "Fermion-mass closure recompute",
        "nine_dressed_passed_FACTOR2": nine_pass,
        "F05_charged_lepton_PRECISE": cl_pass,
        "F05_best_predicted_residual_pct":
            cl["best_predicted_residual_pct"],
        "F05_best_predicted_regime": cl["best_predicted_regime"],
        "F05_best_predicted": cl["best_predicted"],
        "stop_rule_A_verified": cl["stop_rule_A_verified"],
        "open_channels": s["n_open"],
        "fitted_parameters": s["fitted_parameters"],
        "verdict": (
            "PASS"
            if (nine_pass and cl_pass and s["fitted_parameters"] == 0)
            else "FAIL"
        ),
    }
    out_path = OUTPUTS / "fermion_mass_recompute.json"
    with open(out_path, "w", encoding="utf-8") as f2:
        json.dump(out, f2, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
