"""Sensitivity analysis of the Yukawa-Damping cluster Fisher's-combined p-value
under alternative null distributions.

The closed-form claim (Section "Yukawa cluster") combines three observables on
the Lemma-1 (1+gamma/4) loop class via Fisher's method under a uniform null on
the PRECISE band [0, 2.5%]. This sensitivity scan tests robustness under:

  null_uniform_1.5   - uniform on [0, 1.5%]
  null_uniform_5.0   - uniform on [0, 5.0%]
  null_truncnorm_0_5 - truncated normal sigma=0.5%, [0, 2.5%]
  null_truncnorm_1_0 - truncated normal sigma=1.0%, [0, 2.5%]
  null_exponential_2 - exponential rate lambda=2 on [0, infty)

For each null, computes per-observable one-sided p-value, Fisher's T,
combined p, and equivalent two-sided sigma.

Output: outputs/yukawa_cluster_p_sensitivity.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

REPO = Path(__file__).resolve().parents[1]


CLUSTER_OBSERVABLES = {
    "alpha_dn": 0.0001,
    "w_DE": 0.05,
    "H_0": 0.6,
}


def p_uniform(residual_pct, upper_pct):
    """Uniform on [0, upper_pct]: P(X <= r) = r / upper."""
    return min(residual_pct / upper_pct, 1.0)


def p_truncnorm(residual_pct, sigma_pct, upper_pct):
    """Truncated normal on [0, upper_pct] with mean=0, std=sigma_pct."""
    a, b = 0.0, upper_pct / sigma_pct
    return float(stats.truncnorm.cdf(residual_pct / sigma_pct, a, b))


def p_exponential(residual_pct, rate):
    """Exponential with rate lambda."""
    return float(1.0 - np.exp(-rate * residual_pct))


def fisher_combined(p_values):
    """Fisher's method: T = -2 sum log(p_i), chi2 with 2k df under independent null."""
    T = -2.0 * sum(np.log(max(p, 1e-15)) for p in p_values)
    df = 2 * len(p_values)
    p_combined = float(stats.chi2.sf(T, df))
    sigma = float(stats.norm.isf(p_combined / 2.0))
    return T, p_combined, sigma


def main() -> int:
    out: dict = {
        "method": "yukawa_cluster_fisher_sensitivity_scan",
        "stand": "2026-05-05",
        "cluster_observables": CLUSTER_OBSERVABLES,
        "nulls": {},
    }

    nulls = {
        "null_uniform_2.5": ("uniform", {"upper_pct": 2.5}, p_uniform),
        "null_uniform_1.5": ("uniform", {"upper_pct": 1.5}, p_uniform),
        "null_uniform_5.0": ("uniform", {"upper_pct": 5.0}, p_uniform),
        "null_truncnorm_0_5": ("truncnorm",
                                {"sigma_pct": 0.5, "upper_pct": 2.5},
                                p_truncnorm),
        "null_truncnorm_1_0": ("truncnorm",
                                {"sigma_pct": 1.0, "upper_pct": 2.5},
                                p_truncnorm),
        "null_exponential_2": ("exponential", {"rate": 2.0}, p_exponential),
    }

    for name, (kind, params, fn) in nulls.items():
        per_obs = {}
        ps = []
        for obs, r in CLUSTER_OBSERVABLES.items():
            if kind == "uniform":
                p = fn(r, params["upper_pct"])
            elif kind == "truncnorm":
                p = fn(r, params["sigma_pct"], params["upper_pct"])
            else:
                p = fn(r, params["rate"])
            per_obs[obs] = p
            ps.append(p)
        T, p_combined, sigma = fisher_combined(ps)
        out["nulls"][name] = {
            "kind": kind,
            "params": params,
            "per_observable_p": per_obs,
            "fisher_T": float(T),
            "p_combined": p_combined,
            "sigma_two_sided": sigma,
        }

    # Headline summary
    out["headline"] = {
        "primary_null": "null_uniform_2.5",
        "primary_p_combined": out["nulls"]["null_uniform_2.5"]["p_combined"],
        "primary_sigma": out["nulls"]["null_uniform_2.5"]["sigma_two_sided"],
        "robust_under_5_alternative_nulls": (
            all(out["nulls"][k]["p_combined"] < 0.01
                for k in nulls if k != "null_uniform_2.5")
        ),
    }

    out_path = REPO / "outputs" / "yukawa_cluster_p_sensitivity.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved {out_path}")
    print(f"Primary null (uniform [0, 2.5%]): p={out['headline']['primary_p_combined']:.3e}, "
          f"sigma={out['headline']['primary_sigma']:.2f}")
    print(f"Robust across 5 alternative nulls: {out['headline']['robust_under_5_alternative_nulls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
