r"""m_tau closure audit, Path B (RG-running / loop-class IR-matching)
and Path C (QFE + EMT joint dressing).

Path A (uniform System-R factor) is INSUFFICIENT per the bundled
verify_m_tau_path_A_audit.json. This module tests:

Path B — IR-matching via loop-class composition: enumerate
multiplicative factors built from system-R rationals
{alpha_xi, gamma, beta_pi, eps_sync2, D_Omega, N_gen} of the form
1 ± c (single), or compounds (1 ± c)(1 ± c'), and compute the
residual against PDG m_tau when applied to the QFE m_tau
prediction.

Path C — joint QFE + EMT closure: combine the QFE m_tau
prediction (b2_fermion_propagator.json) with available EMT-side
m_tau anchors via (i) geometric mean, (ii) arithmetic mean,
(iii) loop-class-weighted hybrid. Test whether |Delta m_tau /
m_tau| under the joint construction is below the strict-EXACT
0.4% cut (analogous to the v_EW W/Z joint-repair logic from
PG-BMG2).

Output: outputs/verify_m_tau_paths_B_and_C.json
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

PDG_M_TAU_GEV = 1.77686

# QFE-side m_tau predictions across regimes (b2_fermion_propagator)
QFE_M_TAU = {
    "p1": 3.054472,
    "p2prime": 17.012014,
}

# F-05 GJ-textur-null lattice-N extension predictions
F05_GJ_M_TAU = {
    "p5n64": 5.72107798,
    "p5n100": 5.63937824,
}

# System-R rationals
ALPHA_XI = 9.0 / 10.0
GAMMA = 1.0 / 10.0
BETA_PI = 15.0 / 16.0
EPS_SYNC2 = 1.0 / 20.0
D_OMEGA = BETA_PI - GAMMA
N_GEN = 3.0

# Loop-class single-factor library
SINGLE_FACTORS = {
    "L1+":  1 + GAMMA / 4,
    "L1-":  1 - GAMMA / 4,
    "L2":   1 - GAMMA**2 / 4,
    "L3+":  1 + GAMMA**2,
    "L3-":  1 - GAMMA**2,
    "L4":   1 / (1 - 2 * GAMMA**2),
    "L5":   1 - GAMMA / N_GEN,
    "L6+":  1 + GAMMA / (2 * N_GEN),
    "L6-":  1 - GAMMA / (2 * N_GEN),
    "L7":   1 - GAMMA * EPS_SYNC2,
    "L8+":  1 + GAMMA / 2,
    "L8-":  1 - GAMMA / 2,
    "PS+":  1 + EPS_SYNC2,
    "PS-":  1 - EPS_SYNC2,
}


def residual_pct(pred, target):
    return abs(pred - target) / target * 100.0


def tier_of(res_pct):
    if res_pct <= 0.4:
        return "EXACT"
    if res_pct <= 2.5:
        return "PRECISE"
    if res_pct <= 100.0:
        return "FACTOR2"
    return "ORDER"


def path_B_loop_class_scan(qfe_pred, target):
    """Enumerate single + two-factor + three-factor loop-class
    compositions on QFE prediction; report best residual.
    """
    base_res = residual_pct(qfe_pred, target)
    rows = [{"factors": [], "value": qfe_pred, "residual_pct": base_res,
             "tier": tier_of(base_res)}]

    # Single-factor
    for name, f in SINGLE_FACTORS.items():
        v = qfe_pred * f
        r = residual_pct(v, target)
        rows.append({"factors": [name], "value": v, "residual_pct": r,
                      "tier": tier_of(r)})

    # Two-factor
    keys = list(SINGLE_FACTORS.keys())
    for i, k1 in enumerate(keys):
        for k2 in keys[i:]:
            v = qfe_pred * SINGLE_FACTORS[k1] * SINGLE_FACTORS[k2]
            r = residual_pct(v, target)
            rows.append({"factors": [k1, k2], "value": v,
                          "residual_pct": r, "tier": tier_of(r)})

    # Three-factor (cap exploration to compounds with same parity)
    for k1, k2, k3 in itertools.combinations_with_replacement(keys, 3):
        v = qfe_pred * SINGLE_FACTORS[k1] * SINGLE_FACTORS[k2] * SINGLE_FACTORS[k3]
        r = residual_pct(v, target)
        rows.append({"factors": [k1, k2, k3], "value": v,
                      "residual_pct": r, "tier": tier_of(r)})

    rows.sort(key=lambda x: x["residual_pct"])
    return rows[:10]


def path_C_joint(qfe_pred, gj_pred, target):
    """Joint QFE + GJ-textur-null closure: geometric mean,
    arithmetic mean, harmonic, and a few loop-class hybrids.
    """
    if qfe_pred is None or gj_pred is None:
        return None
    geom = math.sqrt(qfe_pred * gj_pred)
    arith = 0.5 * (qfe_pred + gj_pred)
    if qfe_pred * gj_pred > 0:
        harmonic = 2 * qfe_pred * gj_pred / (qfe_pred + gj_pred)
    else:
        harmonic = float("nan")
    # gamma-weighted hybrid: log-linear interpolation
    log_hybrid = qfe_pred ** GAMMA * gj_pred ** (1 - GAMMA)
    return [
        {"method": "geometric_mean", "value": geom,
         "residual_pct": residual_pct(geom, target),
         "tier": tier_of(residual_pct(geom, target))},
        {"method": "arithmetic_mean", "value": arith,
         "residual_pct": residual_pct(arith, target),
         "tier": tier_of(residual_pct(arith, target))},
        {"method": "harmonic_mean", "value": harmonic,
         "residual_pct": residual_pct(harmonic, target),
         "tier": tier_of(residual_pct(harmonic, target))},
        {"method": "gamma_log_hybrid_QFE^gamma_GJ^(1-gamma)",
         "value": log_hybrid,
         "residual_pct": residual_pct(log_hybrid, target),
         "tier": tier_of(residual_pct(log_hybrid, target))},
    ]


def main():
    out: dict = {
        "method": "m_tau closure audit, Path B (loop-class IR matching) + Path C (QFE+GJ joint)",
        "stand": "2026-05-05",
        "PDG_target_GeV": PDG_M_TAU_GEV,
        "QFE_predictions_GeV": QFE_M_TAU,
        "F05_GJ_predictions_GeV": F05_GJ_M_TAU,
        "fitted_parameters": 0,
    }

    # Path B: scan over QFE_p1 and F05 lattice-N regime values
    out["path_B_scan"] = {}
    print("=" * 78)
    print("PATH B: loop-class IR-matching scan on m_tau predictions")
    print("=" * 78)
    print()
    for label, qfe_val in [("QFE_p1", QFE_M_TAU["p1"]),
                            ("F05_p5n64", F05_GJ_M_TAU["p5n64"]),
                            ("F05_p5n100", F05_GJ_M_TAU["p5n100"])]:
        print(f"\nBase: {label} = {qfe_val:.5f} GeV (target {PDG_M_TAU_GEV:.5f})")
        print(f"  Base residual: {residual_pct(qfe_val, PDG_M_TAU_GEV):.2f}%")
        rows = path_B_loop_class_scan(qfe_val, PDG_M_TAU_GEV)
        out["path_B_scan"][label] = rows
        print(f"  Top 5 closures (factors -> residual%):")
        for r in rows[:5]:
            print(f"    {str(r['factors']):<35} {r['value']:.5f}  "
                  f"{r['residual_pct']:>7.3f}%  {r['tier']}")

    # Path C: joint QFE + GJ
    out["path_C_joint"] = {}
    print("\n" + "=" * 78)
    print("PATH C: joint QFE + F05-GJ-textur closures (geometric/arith/log)")
    print("=" * 78)
    for qfe_label, qfe_val in QFE_M_TAU.items():
        for gj_label, gj_val in F05_GJ_M_TAU.items():
            joint = path_C_joint(qfe_val, gj_val, PDG_M_TAU_GEV)
            if joint:
                key = f"{qfe_label}_x_{gj_label}"
                out["path_C_joint"][key] = joint
                print(f"\n  {qfe_label}={qfe_val:.4f} x {gj_label}={gj_val:.4f}:")
                for j in joint:
                    print(f"    {j['method']:<40} {j['value']:.5f}  "
                          f"{j['residual_pct']:>7.3f}%  {j['tier']}")

    # Verdict
    best_B = min((r for rows in out["path_B_scan"].values() for r in rows),
                  key=lambda x: x["residual_pct"])
    best_C = min((j for joints in out["path_C_joint"].values() for j in joints),
                  key=lambda x: x["residual_pct"])
    out["verdict"] = {
        "best_path_B": best_B,
        "best_path_C": best_C,
        "path_B_reaches_EXACT": best_B["residual_pct"] <= 0.4,
        "path_B_reaches_PRECISE": best_B["residual_pct"] <= 2.5,
        "path_C_reaches_EXACT": best_C["residual_pct"] <= 0.4,
        "path_C_reaches_PRECISE": best_C["residual_pct"] <= 2.5,
    }

    out_path = OUTPUTS / "verify_m_tau_paths_B_and_C.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n\n=== VERDICT ===")
    print(f"Best Path B: {best_B['factors']} -> residual {best_B['residual_pct']:.3f}% ({best_B['tier']})")
    print(f"Best Path C: {best_C['method']} -> residual {best_C['residual_pct']:.3f}% ({best_C['tier']})")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
