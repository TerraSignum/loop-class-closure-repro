"""Strict-EXACT roadmap, second pass: alpha_xi + omega_world combinations.

Tests structurally-motivated correction factors built from the
parent paper's framework rationals
   alpha_xi = 9/10  (carrier-defect coupling)
   gamma    = 1/10
   eps2     = 1/20
   beta_pi  = 15/16
   N_gen    = 3
combined with the world-spectral weighted gradient density
   omega_world = <omega_a>_node, taken in a regime-stable
                  median-flavoured form (avoids 1/d^2 outliers
                  at near-unity Xi-edges)
on the four PRECISE/FACTOR2 residuals
   A_s, m_tau, m_mu, m_e.

Structural candidates tested:
   F1: alpha_xi^k                 for k in {1..7}
   F2: (alpha_xi^2)^k             (Lambda_t-power)
   F3: alpha_xi^{N_gen}           (generation-power: 9/10, 81/100, 729/1000)
   F4: alpha_xi^{2 N_gen}         (Lambda_t-generation-power)
   F5: 1 - gamma^k                (defect-suppression, equivalent to F1)
   F6: 2/(2 N_gen + 1)            (triangle-winding-class fraction)
   F7: beta_pi^k = (15/16)^k
   F8: alpha_xi^{N_gen} * (1 + gamma^2 * <omega>_med / <omega>_world)
                                  (omega-modulated suppression)
   F9: combined alpha_xi * beta_pi^N_gen
   F10: alpha_xi^2 * (1 - gamma^2)
   F11: ((2 N_gen)+1) / ((2 N_gen)+3)  - F12: (2 N_gen)/(2 N_gen + 1)
   F13: alpha_xi / beta_pi
   F14: (1/2) * (alpha_xi^N_gen + beta_pi^N_gen)
   F15: alpha_xi^N_gen * beta_pi
   F16: alpha_xi^{N_gen+1} = (9/10)^{N_gen+1}
   F17: alpha_xi^{2 N_gen - 1}

A correction f closes residual R = m_pred / m_obs to strict-EXACT
if |R*f - 1| < 0.01.

Output: outputs/verify_strict_exact_alpha_xi_omega.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "outputs" / "verify_strict_exact_alpha_xi_omega.json"

N_GEN = 3
# C4 (parent paper): tan^2(theta) = 1/N_gen^2 -> alpha_xi = cos^2(theta) =
#                    N_gen^2 / (N_gen^2 + 1), gamma = sin^2(theta) =
#                    1 / (N_gen^2 + 1). Geometric: one dissipation
#                    channel orthogonal to N_gen reaction channels.
ALPHA_XI = (N_GEN * N_GEN) / (N_GEN * N_GEN + 1.0)   # 9/10
GAMMA    = 1.0 / (N_GEN * N_GEN + 1.0)               # 1/10
EPS2     = GAMMA / 2.0                                # 1/20 (eps_sync^2)
# C5 (parent paper): beta_pi = (2^d - 1)/2^d for Cl(1, d-1) common-mode
#                    projector; in 4D, 2^4 = 16, beta_pi = 15/16.
CL_DIM = 4
BETA_PI = (2.0**CL_DIM - 1.0) / 2.0**CL_DIM           # 15/16
# Framework derived: D_Omega = beta_pi - gamma  (projection - dissipation
#                    = diffusion). Numerical: 67/80 = 0.8375.
D_OMEGA = BETA_PI - GAMMA

OBS = {
    "A_s_planck": 2.105e-9,
    "m_tau_GeV": 1.777,
    "m_mu_GeV": 0.10566,
    "m_e_GeV": 5.11e-4,
}
PRED_BASELINE = {
    "A_s_planck": 3.36e-9,    # framework full-Planck single-instanton
    "m_tau_GeV": 3.04,
    "m_mu_GeV": 0.150,
    "m_e_GeV": 9.57e-4,
}

# omega_world median over canonical regimes (computed separately)
# from regime-stable lattice data; representative value:
OMEGA_WORLD_REPRESENTATIVE = 5.5    # median across canonical-physics ladder
OMEGA_WORLD_MIN = 3.0; OMEGA_WORLD_MAX = 9.0

EXACT_TIER = 0.01
PRECISE_TIER = 0.025

# Generation index per observable (relevant for some candidates).
GEN_INDEX = {"m_tau_GeV": 3, "m_mu_GeV": 2, "m_e_GeV": 1, "A_s_planck": 0}


def tier_of(rel):
    a = abs(rel)
    if a <= EXACT_TIER:
        return "EXACT"
    if a <= PRECISE_TIER:
        return "PRECISE"
    if a <= 1.0:
        return "FACTOR2"
    return "OPEN"


def candidates(n_g, omega_world):
    """Return ordered list of (label, factor) candidates."""
    out = [
        ("alpha_xi^1",                  ALPHA_XI),
        ("alpha_xi^2",                  ALPHA_XI**2),
        ("alpha_xi^3",                  ALPHA_XI**3),
        ("alpha_xi^4",                  ALPHA_XI**4),
        ("alpha_xi^5",                  ALPHA_XI**5),
        ("alpha_xi^6",                  ALPHA_XI**6),
        ("alpha_xi^7",                  ALPHA_XI**7),
        # D_Omega = beta_pi - gamma (diffusion identity)
        ("D_Omega^1",                   D_OMEGA),
        ("D_Omega^2",                   D_OMEGA**2),
        ("D_Omega^3",                   D_OMEGA**3),
        ("D_Omega^4",                   D_OMEGA**4),
        ("D_Omega^Ngen",                D_OMEGA**N_GEN),
        (f"D_Omega^{n_g}",              D_OMEGA**max(n_g, 1)),
        (f"D_Omega^{n_g+1}",            D_OMEGA**max(n_g + 1, 1)),
        (f"D_Omega^{2*n_g}",            D_OMEGA**max(2 * n_g, 1)),
        ("D_Omega^Ngen*alpha_xi",       D_OMEGA**N_GEN * ALPHA_XI),
        ("D_Omega^Ngen*beta_pi",        D_OMEGA**N_GEN * BETA_PI),
        ("D_Omega^Ngen*(1-eps2)",       D_OMEGA**N_GEN * (1 - EPS2)),
        ("D_Omega^Ngen/(1-eps2)",       D_OMEGA**N_GEN / (1 - EPS2)),
        # N_gen-explicit second-order corrections (matches alphabet
        # {1/2, 1/3, 1/4, 1/N_gen^2, gamma^2} from corpus inventory)
        ("D_Omega^Ngen*(1+gamma^2)/(1-eps2)",
            D_OMEGA**N_GEN * (1 + GAMMA**2) / (1 - EPS2)),
        ("D_Omega^Ngen*(1+gamma^2/2)/(1-eps2)",
            D_OMEGA**N_GEN * (1 + GAMMA**2 / 2) / (1 - EPS2)),
        ("D_Omega^Ngen*(1+1/(N_gen^2*(2*N_gen+1)))/(1-eps2)",
            D_OMEGA**N_GEN * (1 + 1 / (N_GEN**2 * (2 * N_GEN + 1))) / (1 - EPS2)),
        ("D_Omega^Ngen*(2*N_gen+1)/(2*N_gen)",
            D_OMEGA**N_GEN * (2 * N_GEN + 1) / (2 * N_GEN)),
        ("D_Omega^Ngen*(N_gen+1)/N_gen",
            D_OMEGA**N_GEN * (N_GEN + 1) / N_GEN),
        ("D_Omega^Ngen*N_gen/(N_gen-gamma)",
            D_OMEGA**N_GEN * N_GEN / (N_GEN - GAMMA)),
        ("D_Omega^Ngen*(1+gamma)/(1-gamma)",
            D_OMEGA**N_GEN * (1 + GAMMA) / (1 - GAMMA)),
        (f"alpha_xi^{n_g}",             ALPHA_XI**max(n_g, 1)),
        (f"alpha_xi^{2*n_g}",           ALPHA_XI**max(2 * n_g, 1)),
        (f"alpha_xi^{n_g+1}",           ALPHA_XI**max(n_g + 1, 1)),
        (f"alpha_xi^{2*n_g-1}",         ALPHA_XI**max(2 * n_g - 1, 1)),
        (f"beta_pi^{n_g}",              BETA_PI**max(n_g, 1)),
        (f"beta_pi^{2*n_g}",            BETA_PI**max(2 * n_g, 1)),
        ("alpha_xi*beta_pi^Ngen",       ALPHA_XI * BETA_PI**N_GEN),
        (f"alpha_xi^{n_g}*beta_pi",     ALPHA_XI**max(n_g, 1) * BETA_PI),
        ("alpha_xi^Ngen*(1-gamma^2)",   ALPHA_XI**N_GEN * (1 - GAMMA**2)),
        ("(2*Ngen)/(2*Ngen+1)",         (2 * N_GEN) / (2 * N_GEN + 1)),
        ("(2*Ngen+1)/(2*Ngen+3)",       (2 * N_GEN + 1) / (2 * N_GEN + 3)),
        ("2/(2*Ngen+1)",                2.0 / (2 * N_GEN + 1)),
        ("alpha_xi/beta_pi",            ALPHA_XI / BETA_PI),
        ("(alpha_xi+beta_pi)/2",        (ALPHA_XI + BETA_PI) / 2),
        ("(alpha_xi*beta_pi)^(Ngen/2)", (ALPHA_XI * BETA_PI)**(N_GEN / 2)),
        # omega-modulated:
        ("alpha_xi^Ngen*(1+gamma^2/omega)",
            ALPHA_XI**N_GEN * (1 + GAMMA**2 / omega_world)),
        ("alpha_xi^Ngen*(1-gamma^2/omega)",
            ALPHA_XI**N_GEN * (1 - GAMMA**2 / omega_world)),
        ("(1-gamma^2*omega)*alpha_xi^Ngen",
            (1 - GAMMA**2 * omega_world) * ALPHA_XI**N_GEN
            if (1 - GAMMA**2 * omega_world) > 0 else float("nan")),
        ("alpha_xi^{2*Ngen}*omega^{-1/Ngen}",
            ALPHA_XI**(2 * N_GEN) / omega_world**(1 / max(n_g, 1))),
        # half-integer powers:
        ("alpha_xi^{Ngen+0.5}",         ALPHA_XI**(N_GEN + 0.5)),
        ("alpha_xi^{2*Ngen-0.5}",       ALPHA_XI**(2 * N_GEN - 0.5)),
    ]
    return out


def audit_one(label, R_baseline, n_g, omega_world):
    cands = candidates(n_g, omega_world)
    rows = []
    for cand_name, f in cands:
        if not math.isfinite(f) or f <= 0:
            rows.append({"candidate": cand_name, "factor": float("nan"),
                          "ratio_after": float("nan"), "rel_residual_pct": float("nan"),
                          "tier": "OPEN"})
            continue
        ratio = R_baseline * f
        rel = ratio - 1.0
        rows.append({
            "candidate": cand_name,
            "factor": float(f),
            "ratio_after": float(ratio),
            "rel_residual_pct": float(abs(rel) * 100),
            "tier": tier_of(rel),
        })
    rows.sort(key=lambda r: (r["rel_residual_pct"]
                              if math.isfinite(r["rel_residual_pct"])
                              else 1e9))
    best = rows[0]
    return {
        "observable": label,
        "R_baseline": R_baseline,
        "tier_baseline": tier_of(R_baseline - 1.0),
        "rel_residual_baseline_pct": abs(R_baseline - 1.0) * 100,
        "all_candidates": rows,
        "best_candidate": best,
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Compute baseline residuals
    out = {
        "method": "Strict-EXACT alpha_xi + omega_world structural-candidate audit",
        "framework_constants": {
            "alpha_xi": ALPHA_XI, "gamma": GAMMA,
            "eps_squared": EPS2, "beta_pi": BETA_PI, "N_gen": N_GEN,
        },
        "omega_world_used": OMEGA_WORLD_REPRESENTATIVE,
        "omega_world_range": [OMEGA_WORLD_MIN, OMEGA_WORLD_MAX],
        "tier_thresholds": {"EXACT": EXACT_TIER, "PRECISE": PRECISE_TIER},
        "per_observable": {},
    }
    for key in ("m_tau_GeV", "m_mu_GeV", "m_e_GeV", "A_s_planck"):
        R_baseline = PRED_BASELINE[key] / OBS[key]
        n_g = GEN_INDEX[key] if GEN_INDEX[key] > 0 else 1
        out["per_observable"][key] = audit_one(
            key, R_baseline, n_g, OMEGA_WORLD_REPRESENTATIVE)

    # Sensitivity to omega_world choice
    sensitivity = {}
    for omega_val in (OMEGA_WORLD_MIN, OMEGA_WORLD_REPRESENTATIVE,
                       OMEGA_WORLD_MAX):
        per_obs = {}
        for key in ("m_tau_GeV", "m_mu_GeV", "m_e_GeV"):
            R_baseline = PRED_BASELINE[key] / OBS[key]
            n_g = GEN_INDEX[key]
            r = audit_one(key, R_baseline, n_g, omega_val)
            per_obs[key] = {
                "best_candidate_label": r["best_candidate"]["candidate"],
                "best_rel_residual_pct": r["best_candidate"]["rel_residual_pct"],
                "best_tier": r["best_candidate"]["tier"],
            }
        sensitivity[f"omega_world_{omega_val}"] = per_obs
    out["omega_world_sensitivity"] = sensitivity

    # Verdict summary
    verdict = {}
    for key in ("m_tau_GeV", "m_mu_GeV", "m_e_GeV", "A_s_planck"):
        r = out["per_observable"][key]
        bc = r["best_candidate"]
        if bc["tier"] == "EXACT":
            v = f"CLOSED to EXACT via {bc['candidate']}"
        elif bc["tier"] == "PRECISE":
            v = (f"CLOSED to PRECISE only ({bc['rel_residual_pct']:.2f}%) "
                 f"via {bc['candidate']}")
        elif bc["tier"] == "FACTOR2":
            v = (f"REMAINS FACTOR2 (best {bc['rel_residual_pct']:.2f}%) "
                 f"via {bc['candidate']}")
        else:
            v = "REMAINS OPEN — no candidate closes"
        verdict[key] = v
    out["verdict"] = verdict

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("=== alpha_xi + omega_world structural-candidate audit ===")
    print()
    for key in ("m_tau_GeV", "m_mu_GeV", "m_e_GeV", "A_s_planck"):
        r = out["per_observable"][key]
        print(f"{key} (R_baseline = {r['R_baseline']:.4f}, "
              f"baseline tier {r['tier_baseline']}):")
        # show top-5 candidates
        for c in r["all_candidates"][:5]:
            f = c["factor"]
            ratio = c["ratio_after"]
            rel = c["rel_residual_pct"]
            print(f"  {c['candidate']:<32s} f={f:7.4f}  ratio={ratio:.4f}  "
                  f"rel={rel:6.2f}%  ({c['tier']})")
        print(f"  ===> {verdict[key]}")
        print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
