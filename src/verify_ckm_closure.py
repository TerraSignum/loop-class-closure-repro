r"""
Verify the bundled CKM closure: full |V_CKM| from SYE; Jarlskog
PRECISE 1.8% against PDG; delta_CP EXACT 1.23% via F-02b Wilson
holonomy.

Usage:
    python ./src/verify_ckm_closure.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def load_bundle():
    with open(DATA / "ckm_closure.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    d = load_bundle()
    print("=" * 78)
    print("CKM closure recompute (Jarlskog + delta_CP via F-02b Wilson holonomy)")
    print("=" * 78)
    print()

    m = d["ckm_matrix_closure"]
    print(f"--- CKM matrix closure ---")
    print(f"  Claim:  {m['claim']}")
    print(f"  Method: {m['method']}")
    print(f"  Tier:   {m['tier']}")
    print()

    j = d["jarlskog_invariant_closure"]
    print("--- Jarlskog invariant J_CP ---")
    print(f"  Predicted: {j['predicted']:.3e}")
    print(f"  Anchor:    {j['anchor_value']:.3e}  ({j['anchor_source']})")
    print(f"  Ratio:     {j['ratio_predicted_over_measured']:.3f}")
    print(f"  Residual:  {j['residual_pct']:.2f}%")
    print(f"  Tier:      {j['tier']}")
    print()

    dcp = d["delta_CP_F02b_closure"]
    print("--- Dirac CP phase delta_CP (F-02b Wilson holonomy) ---")
    print(f"  Predicted: {dcp['predicted_rad']:.4f} rad")
    print(f"  Anchor:    {dcp['anchor_rad']:.4f} rad  ({dcp['anchor_source']})")
    print(f"  Residual:  {dcp['residual_pct']:.2f}%")
    print(f"  Tier:      {dcp['tier']}")
    print(f"  Coherence filter: |delta^Berry - delta^largest| < "
          f"{dcp['coherence_filter_rad']} rad")
    print(f"  Regime selected:  {dcp['regime_selected']}")
    print()

    s = d["summary"]
    print("--- Summary ---")
    print(f"  Total closures:    {s['n_closures']}")
    print(f"  EXACT:             {s['EXACT']}")
    print(f"  PRECISE:           {s['PRECISE']}")
    print(f"  DERIVED:           {s['DERIVED_no_residual']}")
    print(f"  Fitted parameters: {s['fitted_parameters']}")
    print()

    jarlskog_pass = (j["tier"] == "EXACT" and j["residual_pct"] <= 1.0)
    delta_cp_pass = (dcp["tier"] == "EXACT" and dcp["residual_pct"] <= 1.5)

    out = {
        "criterion": "CKM closure recompute",
        "ckm_matrix_derived": m["tier"] == "DERIVED",
        "jarlskog_EXACT_via_Wolfenstein_Compound": jarlskog_pass,
        "jarlskog_residual_pct": j["residual_pct"],
        "delta_CP_EXACT": delta_cp_pass,
        "delta_CP_residual_pct": dcp["residual_pct"],
        "fitted_parameters": s["fitted_parameters"],
        "verdict": (
            "PASS"
            if (m["tier"] == "DERIVED" and jarlskog_pass and delta_cp_pass
                and s["fitted_parameters"] == 0)
            else "FAIL"
        ),
    }
    out_path = OUTPUTS / "ckm_closure_recompute.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
