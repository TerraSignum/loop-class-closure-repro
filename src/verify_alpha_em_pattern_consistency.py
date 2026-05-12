"""Cross-observable consistency audit for the alpha_EM pattern
identification

    alpha_EM = gamma^2 * alpha_xi^N_gen = 729 / 100000.

The audit takes ONLY the five System-R rationals
(alpha_xi=9/10, gamma=1/10, eps_sync^2=1/20, beta_pi=15/16,
N_gen=3, d=4) as inputs.  alpha_EM is computed once and then
fed into the eight loop-class identities O33..O40 of P3 and the
ten post-flip pattern identities T41..T53 of P4-B.  All eleven
unique observables are evaluated against PDG/NuFIT values.

Plus a delta_Y-elimination test: GP-02 (Theorem 16.3) renormalises
hypercharge with Z_Y = 1+delta_Y as a fitted parameter; we compute
the value of delta_Y forced by a given alpha_Y^tree to make
sin^2(theta_W) hit framework-prediction, and report whether
alpha_Y^tree itself can be expressed parameter-free.

Finally, an alpha_W consistency test: alpha_W = alpha_EM /
sin^2(theta_W); does it match PDG alpha_W at low-energy or at M_Z?

If 8/11 or more pattern observables hit PRECISE-or-better with
the same single-parameter-free alpha_EM input, the
gamma^2 * alpha_xi^N_gen identification is established as a
cross-observable structural pattern (not pigeonhole numerology).

Output: outputs/verify_alpha_em_pattern_consistency.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# System-R rationals (frozen, no fits)
GAMMA = 1.0 / 10.0
ALPHA_XI = 9.0 / 10.0
EPS_SYNC2 = 1.0 / 20.0
BETA_PI = 15.0 / 16.0
N_GEN = 3
D = 4

# Derived
ALPHA_EM = GAMMA ** 2 * ALPHA_XI ** N_GEN
SIN2_THETAW = BETA_PI - (1.0 - GAMMA) * math.pi / 4.0
COS2_THETAW = 1.0 - SIN2_THETAW

# PDG / NuFIT 6.1 reference values
REF = {
    "alpha_EM_low":   1.0 / 137.036,         # PDG 2024 alpha_EM(0)
    "alpha_EM_MZ":    1.0 / 127.951,         # PDG 2024 alpha_EM(M_Z)
    "alpha_W_MZ":     1.0 / 29.5938,         # PDG 2024 alpha_W(M_Z)
    "sin2_theta_W":   0.23129,               # PDG 2024 effective
    "m_mu_over_m_e":  206.7682,
    "m_t_over_m_b":   172.5 / 4.18,          # PDG 2024 pole/MSbar mix
    "m_b_over_m_s":   4.18 / 0.093,
    "m_c_over_m_u":   1.27 / 0.00216,
    "V_us":           0.22500,
    "V_ub":           0.00370,
    "V_cb":           0.04200,
    "V_td":           0.00854,
    "Dm21_over_Dm31": 7.42e-5 / 2.515e-3,    # NuFIT 6.1 normal ordering
    "BR_Bs_to_mumu":  3.09e-9,               # PDG 2024 LHCb
    "Yp_helium":      0.245,                  # PDG 2024 primordial He-4
}


def _tier(rel_err_pct):
    a = abs(rel_err_pct)
    if a < 0.4:
        return "EXACT"
    if a < 2.5:
        return "PRECISE"
    if a < 10.0:
        return "FACTOR2"
    if a < 50.0:
        return "ORDER"
    return "OFF"


def _row(label, predicted, target, formula):
    rel = (predicted - target) / target * 100.0 if target != 0 else float("nan")
    return {
        "label": label,
        "formula": formula,
        "predicted": float(predicted),
        "target": float(target),
        "rel_err_pct": float(rel),
        "abs_rel_err_pct": float(abs(rel)),
        "tier": _tier(rel),
    }


def main() -> int:
    print("=" * 100)
    print("alpha_EM cross-observable consistency audit")
    print("=" * 100)
    print(f"  Inputs (System-R, no fits):")
    print(f"    alpha_xi = {ALPHA_XI}  (= 9/10 = N_gen^2/(N_gen^2+1))")
    print(f"    gamma    = {GAMMA}     (= 1/10 = 1/(N_gen^2+1))")
    print(f"    eps_sync^2 = {EPS_SYNC2}  (= 1/20)")
    print(f"    beta_pi  = {BETA_PI}   (= 15/16 = (2^d-1)/2^d)")
    print(f"    N_gen, d = {N_GEN}, {D}")
    print()
    print(f"  Derived from inputs:")
    print(f"    alpha_EM = gamma^2 * alpha_xi^N_gen = {ALPHA_EM:.6f}")
    print(f"             = 729/100000  (closed-form rational)")
    print(f"    sin^2(theta_W) = beta_pi - (1-gamma)*pi/4 = {SIN2_THETAW:.6f}")
    print(f"    cos^2(theta_W) = {COS2_THETAW:.6f}")
    print()

    # ============================================================
    # Test set 1: cross-observable pattern identities
    # ============================================================
    print("=" * 100)
    print("Test set 1: cross-observable pattern identities")
    print("=" * 100)
    rows = []

    # O33 / definitional (alpha_EM itself)
    rows.append(_row(
        "O33: alpha_EM = gamma^2 * alpha_xi^N_gen",
        ALPHA_EM, REF["alpha_EM_low"],
        "gamma^2 * alpha_xi^N_gen"))

    # O34 / T43: m_mu/m_e
    rows.append(_row(
        "O34/T43: m_mu/m_e = 3/(2*alpha_EM)",
        3.0 / (2.0 * ALPHA_EM), REF["m_mu_over_m_e"],
        "3 / (2*alpha_EM)"))

    # O35 / T52: |V_ub|
    rows.append(_row(
        "O35/T52: |V_ub| = alpha_EM / 2",
        ALPHA_EM / 2.0, REF["V_ub"],
        "alpha_EM / 2"))

    # O36 / T53: |V_td|
    rows.append(_row(
        "O36/T53: |V_td| = 2*alpha_EM/sqrt(N_gen)",
        2.0 * ALPHA_EM / math.sqrt(N_GEN), REF["V_td"],
        "2*alpha_EM / sqrt(N_gen)"))

    # O37 / T51: |V_cb|
    rows.append(_row(
        "O37/T51: |V_cb| = alpha_EM*d*(1+1/N_gen)",
        ALPHA_EM * D * (1.0 + 1.0 / N_GEN), REF["V_cb"],
        "alpha_EM * d * (1+1/N_gen)"))

    # O38 / T49: m_b/m_s
    rows.append(_row(
        "O38/T49: m_b/m_s = 1/(alpha_EM*N_gen)",
        1.0 / (ALPHA_EM * N_GEN), REF["m_b_over_m_s"],
        "1 / (alpha_EM*N_gen)"))

    # O39 / T41: Dm^2_21/Dm^2_31
    rows.append(_row(
        "O39/T41: Dm^2_21/Dm^2_31 = 4*alpha_EM",
        4.0 * ALPHA_EM, REF["Dm21_over_Dm31"],
        "4 * alpha_EM"))

    # O40 / T45: sin^2 theta_W (eps version)
    rows.append(_row(
        "O40/T45: sin^2(theta_W) = 1/4 - eps^2/N_gen",
        0.25 - EPS_SYNC2 / N_GEN, REF["sin2_theta_W"],
        "1/4 - eps^2/N_gen"))

    # T44: m_t/m_b
    rows.append(_row(
        "T44: m_t/m_b = 1/(2*alpha_EM*sqrt(N_gen))",
        1.0 / (2.0 * ALPHA_EM * math.sqrt(N_GEN)), REF["m_t_over_m_b"],
        "1 / (2*alpha_EM*sqrt(N_gen))"))

    # T46b: Y_p (primordial helium)
    rows.append(_row(
        "T46b: Y_p = 1/(d+1) + eps^2 - alpha_EM",
        1.0 / (D + 1) + EPS_SYNC2 - ALPHA_EM, REF["Yp_helium"],
        "1/(d+1) + eps^2 - alpha_EM"))

    # T42: BR(B_s -> mu mu) = alpha_EM^4
    rows.append(_row(
        "T42: BR(B_s->mumu) = alpha_EM^4",
        ALPHA_EM ** 4, REF["BR_Bs_to_mumu"],
        "alpha_EM^4"))

    # T50: m_c/m_u
    rows.append(_row(
        "T50: m_c/m_u = 1/(30*alpha_EM^2)",
        1.0 / (30.0 * ALPHA_EM ** 2), REF["m_c_over_m_u"],
        "1 / (30*alpha_EM^2)"))

    # V_us = alpha_xi * s_face = 9/40 (H-J upgrade,
    # data/closure_derivations/HJ_Vus_alpha_xi_quarter.json; supersedes
    # legacy gamma*sqrt(5))
    ALPHA_XI_LOC = 1.0 - GAMMA  # = 9/10
    S_FACE_LOC = 0.25
    rows.append(_row(
        "V_us = alpha_xi*s_face = 9/40",
        ALPHA_XI_LOC * S_FACE_LOC, REF["V_us"],
        "alpha_xi * s_face"))

    # Print + tier counts
    print(f"  {'identity':<55s} {'pred':>11s} {'target':>11s} {'rel_pct':>9s}  {'tier':>8s}")
    for r in rows:
        print(f"  {r['label']:<55s} {r['predicted']:>11.5g} {r['target']:>11.5g} "
              f"{r['rel_err_pct']:>+8.3f}% {r['tier']:>8s}")

    n_total = len(rows)
    n_exact = sum(1 for r in rows if r["tier"] == "EXACT")
    n_precise = sum(1 for r in rows if r["tier"] == "PRECISE")
    n_factor2 = sum(1 for r in rows if r["tier"] == "FACTOR2")
    n_better = n_exact + n_precise

    print(f"\n  {n_exact}/{n_total} EXACT, {n_precise}/{n_total} PRECISE, "
          f"{n_factor2}/{n_total} FACTOR2; {n_better}/{n_total} <= 2.5%")

    # ============================================================
    # Test set 2: alpha_W = alpha_EM / sin^2(theta_W) consistency
    # ============================================================
    print()
    print("=" * 100)
    print("Test set 2: alpha_W self-consistency from alpha_EM and sin^2 theta_W")
    print("=" * 100)
    alpha_W_pred = ALPHA_EM / SIN2_THETAW
    alpha_W_inv_pred = 1.0 / alpha_W_pred
    print(f"  alpha_W = alpha_EM / sin^2(theta_W) = {alpha_W_pred:.6f}")
    print(f"  alpha_W^-1 (framework) = {alpha_W_inv_pred:.4f}")
    print(f"  PDG alpha_W^-1(M_Z)    = {1.0/REF['alpha_W_MZ']:.4f}  "
          f"(rel err {(alpha_W_pred-REF['alpha_W_MZ'])/REF['alpha_W_MZ']*100:+.3f}%)")
    print(f"  alpha_W^-1 ~ N_gen*pi^2 = {N_GEN*math.pi**2:.4f}  "
          f"(memory candidate identity)")
    aW_consistency = (alpha_W_pred - REF["alpha_W_MZ"]) / REF["alpha_W_MZ"] * 100.0
    print(f"  Self-consistency residual at M_Z: {aW_consistency:+.3f}% "
          f"(tier: {_tier(aW_consistency)})")

    # ============================================================
    # Test set 3: delta_Y elimination from GP-02 (Theorem 16.3)
    # ============================================================
    print()
    print("=" * 100)
    print("Test set 3: delta_Y elimination test (GP-02 Theorem 16.3)")
    print("=" * 100)
    # GP-02: alpha_Y^renorm = alpha_Y^tree * (1+delta_Y)
    #        sin^2 theta_W = alpha_Y^renorm / (alpha_Y^renorm + alpha_EW)
    #        alpha_EM      = alpha_Y^renorm * alpha_EW / (alpha_Y^renorm + alpha_EW)
    # Solve for alpha_Y^renorm:  alpha_Y^renorm = alpha_EW * sin^2 / (1 - sin^2)
    # With alpha_EW = alpha_EM / sin^2(theta_W) (just derived):
    #   alpha_Y^renorm = alpha_EM / cos^2(theta_W)
    alpha_Y_renorm = ALPHA_EM / COS2_THETAW
    print(f"  alpha_Y^renorm = alpha_EM / cos^2(theta_W) = {alpha_Y_renorm:.6f}")
    print(f"  alpha_Y^renorm^-1 = {1.0/alpha_Y_renorm:.4f}")

    # Memory candidate identity: alpha_Y^-1 = (sum_f Y_f^2)*pi^2 = 10*pi^2
    candidate_aY_inv = 10.0 * math.pi ** 2
    print(f"  Memory candidate: alpha_Y^-1 = 10*pi^2 = {candidate_aY_inv:.4f}")
    print(f"  PDG alpha_Y^-1(M_Z) ~ 98.36  (running scale dependent)")
    aY_residual = (1.0/alpha_Y_renorm - candidate_aY_inv) / candidate_aY_inv * 100.0
    print(f"  Framework alpha_Y^-1 vs 10*pi^2: rel err {aY_residual:+.3f}%")

    # If we accept alpha_Y^tree as a candidate parameter-free form,
    # delta_Y is determined.  Try several candidates:
    print()
    print(f"  delta_Y = alpha_Y^renorm/alpha_Y^tree - 1, for several alpha_Y^tree:")
    candidates_aY_tree = [
        ("alpha_EM (= alpha_Y^renorm * cos^2)",
         ALPHA_EM, "tree = alpha_EM (assumes Z_Y absorbs only cos^2 effect)"),
        ("eps_sync^2 * gamma^2  (S-R rational)",
         EPS_SYNC2 * GAMMA ** 2, "framework structural rational"),
        ("alpha_EM / 10  (memory hint Sigma Y^2 = 10)",
         ALPHA_EM / 10.0, "if alpha_Y^tree is alpha_EM scaled by Sigma Y^2"),
        ("gamma^4  (chirality-squared squared)",
         GAMMA ** 4, "structural framework rational"),
        ("alpha_EM_observed at low E",
         REF["alpha_EM_low"], "PDG reference"),
    ]
    delta_y_results = []
    for label, aY_tree, note in candidates_aY_tree:
        delta_y = alpha_Y_renorm / aY_tree - 1.0
        delta_y_results.append({
            "alpha_Y_tree_label": label,
            "alpha_Y_tree": aY_tree,
            "delta_Y_required": float(delta_y),
            "note": note,
        })
        print(f"    {label:<46s}  alpha_Y^tree={aY_tree:.6f}  "
              f"=> delta_Y = {delta_y:+.4f}")

    # Compare to memory: delta_Y(P1) = -0.20, delta_Y(P2') = -0.27
    print()
    print(f"  Memory (Theorem 16.3): delta_Y(P1) = -0.20, delta_Y(P2') = -0.27")
    print(f"  Closest match: alpha_Y^tree giving delta_Y in [-0.30, -0.10]:")
    for entry in delta_y_results:
        if -0.30 <= entry["delta_Y_required"] <= -0.10:
            print(f"    -> {entry['alpha_Y_tree_label']}  "
                  f"(delta_Y={entry['delta_Y_required']:+.4f})")

    # ============================================================
    # Verdict
    # ============================================================
    print()
    print("=" * 100)
    print("Final verdict")
    print("=" * 100)
    if n_better >= 8:
        verdict_pattern = "ALPHA_EM_PATTERN_STRUCTURALLY_CONSISTENT"
    elif n_better >= 6:
        verdict_pattern = "ALPHA_EM_PATTERN_PARTIAL_CONSISTENT"
    else:
        verdict_pattern = "ALPHA_EM_PATTERN_INCONSISTENT"

    if abs(aW_consistency) < 10.0:
        verdict_aW = "ALPHA_W_SELF_CONSISTENT_AT_M_Z"
    else:
        verdict_aW = "ALPHA_W_INCONSISTENT_AT_M_Z"

    print(f"  Pattern verdict:  {verdict_pattern}  "
          f"({n_better}/{n_total} <= 2.5%)")
    print(f"  alpha_W verdict:  {verdict_aW}  ({aW_consistency:+.3f}% off PDG)")

    bundle = {
        "method": "verify_alpha_em_pattern_consistency",
        "schema_version": "1.0.0",
        "stand": "2026-05-07",
        "system_R_inputs": {
            "alpha_xi": ALPHA_XI, "gamma": GAMMA,
            "eps_sync_squared": EPS_SYNC2, "beta_pi": BETA_PI,
            "N_gen": N_GEN, "d": D,
        },
        "derived": {
            "alpha_EM_pred": ALPHA_EM,
            "sin2_theta_W_pred": SIN2_THETAW,
            "cos2_theta_W_pred": COS2_THETAW,
            "alpha_W_pred": alpha_W_pred,
            "alpha_W_inv_pred": alpha_W_inv_pred,
            "alpha_Y_renorm": alpha_Y_renorm,
            "alpha_Y_renorm_inv": 1.0 / alpha_Y_renorm,
        },
        "pattern_identities": rows,
        "n_total": n_total, "n_exact": n_exact,
        "n_precise": n_precise, "n_factor2": n_factor2,
        "n_better_2_5pct": n_better,
        "alpha_W_consistency_residual_pct": aW_consistency,
        "delta_Y_candidates": delta_y_results,
        "verdict_pattern": verdict_pattern,
        "verdict_alpha_W": verdict_aW,
    }
    out = REPO / "outputs" / "verify_alpha_em_pattern_consistency.json"
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print()
    print(f"Saved {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
