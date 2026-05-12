"""Strict-EXACT roadmap audit for A_s, m_tau, m_e.

Three observables currently closed at PRECISE/FACTOR2 tier
under the canonical-physics regime; this audit catalogues
each gap, tests the candidate framework-natural higher-order
correction(s), and reports which (if any) reach
strict-EXACT (<= 1% relative residual against PDG/Planck).

  A_s     observed 2.105e-9 (Planck 2018);
          framework slow-roll + instanton modulation under
          reduced-Planck-mass convention gives factor ~932
          OPEN. Cascade-instanton chain (parent corpus,
          memory line on hidden-closures search) reduces to
          factor 0.90 = PRECISE 10%. Strict-EXACT requires
          either an additional suppression mechanism or a
          convention bridge.

  m_tau   observed 1.777 GeV; framework cost-mode-dressed
          3.04 GeV (ratio 1.71, FACTOR2). Bare ratio 3.37,
          so cost-mode dressing reduces overshoot by factor
          2.0. Strict-EXACT (ratio <= 1.01) requires an
          additional dressing layer.

  m_e     observed 5.11e-4 GeV; framework cost-mode-dressed
          9.57e-4 GeV (ratio 1.87, FACTOR2). Bare ratio 7.33,
          so cost-mode dressing reduces overshoot by factor
          4.0. Strict-EXACT requires further suppression.

Output: outputs/verify_strict_exact_roadmap.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "outputs" / "verify_strict_exact_roadmap.json"

A_S_PLANCK = 2.105e-9
M_TAU_OBS = 1.777
M_E_OBS = 5.11e-4
M_MU_OBS = 0.10566

EXACT_TIER = 0.01    # 1%
PRECISE_TIER = 0.025  # 2.5%
FACTOR2_TIER = 1.0    # ratio 1-2x


def _ratio_to_tier(ratio):
    """Classify residual ratio into closure tier."""
    rel = abs(ratio - 1.0)
    if rel <= EXACT_TIER:
        return "EXACT"
    if rel <= PRECISE_TIER:
        return "PRECISE"
    if rel <= FACTOR2_TIER:
        return "FACTOR2"
    return "OPEN"


def audit_A_s():
    """Test cascade-instanton chain + finer-grained corrections."""
    M_Pl_red = 2.4354e18
    V_0 = 3.25e74
    eps = 0.0018125
    A_s_raw_red = V_0 / (24 * math.pi**2 * M_Pl_red**4 * eps)

    # Baseline single-instanton modulation
    eta_S = 3.013
    S_inst_single = (math.pi**2 / 2) * eta_S
    N_modes = 13.0
    A_s_single = A_s_raw_red * math.exp(-S_inst_single) / math.sqrt(N_modes)
    ratio_single = A_s_single / A_S_PLANCK

    # Cascade-instanton chain: N_barriers * <S> with N_barriers=2..3
    cascade_results = {}
    for N_barriers in (1, 2, 3, 4, 5):
        S_cascade = N_barriers * S_inst_single
        A_s_cascade = (A_s_raw_red * math.exp(-S_cascade)
                       / math.sqrt(N_modes))
        ratio = A_s_cascade / A_S_PLANCK
        cascade_results[f"N_barriers={N_barriers}"] = {
            "S_cascade": S_cascade,
            "A_s_predicted": A_s_cascade,
            "ratio_to_Planck": ratio,
            "rel_residual_pct": abs(ratio - 1.0) * 100,
            "tier": _ratio_to_tier(ratio),
        }

    # sinc^2 lattice form-factor at fine N (memory: closure
    # mechanism for charged-lepton additional suppression).
    # Approximate suppression: sinc^2(pi/N) -> 1/N^2 at large N
    sinc2_results = {}
    for N in (100, 200, 300, 500, 1000):
        sinc_factor = (math.sin(math.pi / N) / (math.pi / N))**2
        # combined cascade(N=2) + sinc^2 lattice form
        S_cascade_2 = 2 * S_inst_single
        A_s_combined = (A_s_raw_red * math.exp(-S_cascade_2)
                        / math.sqrt(N_modes) * sinc_factor)
        ratio = A_s_combined / A_S_PLANCK
        sinc2_results[f"N={N}"] = {
            "sinc2_factor": sinc_factor,
            "A_s_predicted": A_s_combined,
            "ratio_to_Planck": ratio,
            "rel_residual_pct": abs(ratio - 1.0) * 100,
            "tier": _ratio_to_tier(ratio),
        }

    # Find the best candidate
    all_candidates = []
    for tag, d in cascade_results.items():
        all_candidates.append(("cascade-" + tag, d["rel_residual_pct"],
                                d["tier"]))
    for tag, d in sinc2_results.items():
        all_candidates.append(("cascade-2 + sinc2-" + tag,
                                d["rel_residual_pct"], d["tier"]))
    all_candidates.sort(key=lambda x: x[1])
    best = all_candidates[0]
    return {
        "observable": "A_s_primordial_scalar_amplitude",
        "observed": A_S_PLANCK,
        "convention": "reduced-Planck-mass standard slow-roll",
        "A_s_raw_baseline": A_s_raw_red,
        "single_instanton": {
            "A_s_predicted": A_s_single,
            "ratio_to_Planck": ratio_single,
            "rel_residual_pct": abs(ratio_single - 1.0) * 100,
            "tier": _ratio_to_tier(ratio_single),
        },
        "cascade_instanton": cascade_results,
        "cascade_2_plus_sinc2_lattice": sinc2_results,
        "best_candidate": {
            "label": best[0],
            "rel_residual_pct": best[1],
            "tier": best[2],
        },
    }


def audit_lepton_masses():
    """Test sinc^2 fine-lattice + generation-specific residue."""
    bare_predictions = {
        "m_tau": 3.04, "m_mu": 0.150, "m_e": 9.57e-4,
    }
    obs = {"m_tau": M_TAU_OBS, "m_mu": M_MU_OBS, "m_e": M_E_OBS}

    results = {}
    for lepton, m_pred in bare_predictions.items():
        m_obs = obs[lepton]
        ratio_bare = m_pred / m_obs
        # sinc^2 lattice factor at fine N
        sinc2_layer = {}
        for N in (100, 200, 300, 500, 1000):
            f = (math.sin(math.pi / N) / (math.pi / N))**2
            m_corrected = m_pred * f
            ratio = m_corrected / m_obs
            sinc2_layer[f"N={N}"] = {
                "sinc2_factor": f,
                "m_predicted": m_corrected,
                "ratio_to_obs": ratio,
                "rel_residual_pct": abs(ratio - 1.0) * 100,
                "tier": _ratio_to_tier(ratio),
            }
        # Generation-specific residue: x ~ alpha_em / 4pi per generation
        # (3-loop QED running from Planck to mass scale, illustrative)
        alpha_em = 1 / 137.036
        gen_index = {"m_tau": 3, "m_mu": 2, "m_e": 1}[lepton]
        residue_factor = (1 - alpha_em / (4 * math.pi)) ** gen_index
        m_residue = m_pred * residue_factor
        ratio_res = m_residue / m_obs
        # Combined cost-mode + sinc2 + gen-residue
        combined = {}
        for N in (200, 500, 1000):
            f_sinc = (math.sin(math.pi / N) / (math.pi / N))**2
            m_full = m_pred * f_sinc * residue_factor
            ratio_full = m_full / m_obs
            combined[f"N={N}"] = {
                "m_predicted": m_full,
                "ratio_to_obs": ratio_full,
                "rel_residual_pct": abs(ratio_full - 1.0) * 100,
                "tier": _ratio_to_tier(ratio_full),
            }
        results[lepton] = {
            "observed": m_obs,
            "framework_dressed_baseline": m_pred,
            "ratio_baseline": ratio_bare,
            "tier_baseline": _ratio_to_tier(ratio_bare),
            "sinc2_lattice_layer": sinc2_layer,
            "generation_residue": {
                "factor": residue_factor,
                "m_predicted": m_residue,
                "ratio_to_obs": ratio_res,
                "rel_residual_pct": abs(ratio_res - 1.0) * 100,
                "tier": _ratio_to_tier(ratio_res),
            },
            "combined_sinc2_plus_residue": combined,
        }
    return results


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out = {
        "method": "Strict-EXACT roadmap audit for A_s + charged-lepton masses",
        "tier_thresholds": {
            "EXACT": EXACT_TIER, "PRECISE": PRECISE_TIER,
            "FACTOR2": FACTOR2_TIER,
        },
        "A_s": audit_A_s(),
        "charged_leptons": audit_lepton_masses(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("=== Strict-EXACT roadmap audit ===")
    print()
    print(f"A_s (observed = {A_S_PLANCK:.3e}):")
    a = out["A_s"]
    print(f"  single-instanton:        ratio={a['single_instanton']['ratio_to_Planck']:.3e}"
          f"  ({a['single_instanton']['tier']})")
    for tag, d in a["cascade_instanton"].items():
        print(f"  cascade {tag:>15s}: ratio={d['ratio_to_Planck']:.4f}"
              f"  rel={d['rel_residual_pct']:6.2f}%  ({d['tier']})")
    print(f"  Best A_s candidate: {a['best_candidate']['label']}"
          f" -> rel_residual = {a['best_candidate']['rel_residual_pct']:.2f}%"
          f" ({a['best_candidate']['tier']})")
    print()
    for lepton, d in out["charged_leptons"].items():
        print(f"{lepton}: obs={d['observed']:.4e}, "
              f"baseline ratio={d['ratio_baseline']:.3f} "
              f"({d['tier_baseline']})")
        gr = d["generation_residue"]
        print(f"  generation-residue alone: ratio={gr['ratio_to_obs']:.3f}"
              f" ({gr['tier']})")
        # show best of combined
        best_comb = min(
            d["combined_sinc2_plus_residue"].values(),
            key=lambda x: x["rel_residual_pct"])
        print(f"  best combined sinc2+residue: ratio="
              f"{best_comb['ratio_to_obs']:.3f}"
              f"  rel={best_comb['rel_residual_pct']:.2f}%"
              f"  ({best_comb['tier']})")
    print()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
