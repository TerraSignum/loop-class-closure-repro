r"""
Compute the joint random-null probability of the Yukawa-Damping cluster
via Fisher's combined-p method.

Three observables of independent physical origin close on the same loop
class L_sigma = (1 + gamma/4) (Lemma 1, Yukawa-Damping):

  - alpha_dn (down-Yukawa exponent), post-loop residual ~ 0.0001 %
  - w_DE (dark-energy equation of state), post-loop residual ~ 0.050 %
  - H_0 (local Hubble constant), post-loop residual ~ 0.600 %

Under a uniform random null on the post-loop residual range
[0, PRECISE_2.5 %], the per-observable one-sided p-value of landing
at residual <= r_observed is

    p_per(r) = r / 2.5 %.

For the three cluster members we have

    p_alpha_dn = 0.0001 / 2.5 = 4.0e-5
    p_w_DE     = 0.050  / 2.5 = 0.020
    p_H_0      = 0.600  / 2.5 = 0.240.

These three p-values are statistically independent under the
hypothesis that the three observables are draws from independent
sectors. Fisher's method combines them as

    T = -2 (ln p_alpha_dn + ln p_w_DE + ln p_H_0)
      ~ chi^2 with 2k = 6 degrees of freedom under the null.

The combined p-value is the upper-tail probability of the
chi-square distribution evaluated at T.

The "three observables on the SAME loop class" coincidence is
treated as the structural prior; the trial-factor inflation is
already absorbed in the choice of the cluster's shared class
(1 + gamma/4) and the manuscript's promotion criterion.

Usage:
    python ./src/compute_yukawa_cluster_p.py
"""

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def per_observable_p(residual_pct, precise_band_pct=2.5):
    """One-sided p-value under uniform null on [0, precise_band_pct]."""
    return residual_pct / precise_band_pct


def fisher_combined_p(p_values):
    """Fisher's combined-p test. Returns (T, k, p_combined) where
    T = -2 sum(ln p_i) and p_combined = P(chi^2_{2k} >= T)."""
    k = len(p_values)
    T = -2.0 * sum(math.log(p) for p in p_values)
    p_comb = chi_square_survival(T, 2 * k)
    return T, k, p_comb


def chi_square_survival(x, df):
    """P(chi^2_df >= x) via the regularised upper incomplete gamma function
    Q(df/2, x/2). Uses a series + continued-fraction split."""
    if x <= 0:
        return 1.0
    a = df / 2.0
    z = x / 2.0
    if z < a + 1.0:
        # Series for the lower incomplete gamma -> P(z) = z^a e^{-z} sum
        ap = a
        s = 1.0 / a
        term = s
        for _ in range(2000):
            ap += 1.0
            term *= z / ap
            s += term
            if abs(term) < abs(s) * 1e-16:
                break
        gam_low_reg = s * math.exp(-z + a * math.log(z) - math.lgamma(a))
        return max(0.0, 1.0 - gam_low_reg)
    # Continued fraction for upper incomplete gamma directly.
    b = z + 1.0 - a
    c = 1.0e300
    d = 1.0 / b
    h = d
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return h * math.exp(-z + a * math.log(z) - math.lgamma(a))


def joint_null_probability(residual_threshold_pct, precise_band_pct=2.5,
                            n_observables=3):
    """Legacy: joint probability that n_observables independently land at
    residual <= residual_threshold_pct under a uniform null. Kept for
    sensitivity-sweep continuity; the load-bearing computation is now
    Fisher's combined-p test on each observable's actual residual."""
    p_per = residual_threshold_pct / precise_band_pct
    p_joint = p_per ** n_observables
    return p_per, p_joint


def sigma_from_p_two_sided(p):
    """Two-sided sigma equivalent of probability p (standard normal)."""
    if p <= 0.0:
        return float("inf")
    if p >= 1.0:
        return 0.0
    # erfcinv: scipy.special.erfcinv(2p) gives the one-sided sigma at level p.
    # For two-sided p: sigma = sqrt(2) * erfcinv(p).
    # Here we treat p as the one-sided p-value; sigma = sqrt(2) * erfinv(1 - 2p).
    # Use math.erf and a Newton iteration for inverse.
    def erfcinv(y):
        # Solve erfc(x) = y for x in [0, +inf); y in (0, 2).
        # Initial guess via the asymptotic series for small y.
        if y >= 1.0:
            x = 0.0
        else:
            x = math.sqrt(-math.log(y)) if y > 1e-15 else 8.0
        for _ in range(60):
            f = math.erfc(x) - y
            fp = -2.0 / math.sqrt(math.pi) * math.exp(-x * x)
            if fp == 0.0:
                break
            x_new = x - f / fp
            if abs(x_new - x) < 1e-15:
                x = x_new
                break
            x = x_new
        return x

    return math.sqrt(2.0) * erfcinv(2.0 * p)


def main():
    print("=" * 72)
    print("Yukawa-Damping cluster: joint random-null probability")
    print("=" * 72)
    print()

    # The three cluster members (post-loop residuals from registry).
    cluster = [
        ("alpha_dn", 0.0001),
        ("w_DE",      0.050),
        ("H_0",       0.600),
    ]
    print("  Cluster members on Lemma-1 class (1+gamma/4):")
    for name, r in cluster:
        print(f"    {name:<10} post-loop residual = {r:.4f} %")
    print()

    # Per-observable one-sided p-values under uniform null.
    p_values = [per_observable_p(r, 2.5) for (_n, r) in cluster]
    print("--- Per-observable p-values (uniform null on [0, 2.5%]) ---")
    for (name, r), p in zip(cluster, p_values):
        print(f"  p_{name:<10} = {r:.4f}% / 2.5% = {p:.4e}")
    print()

    T, k, p_combined = fisher_combined_p(p_values)
    print("--- Fisher's combined-p test ---")
    print(f"  T = -2 sum ln(p_i)            = {T:.4f}")
    print(f"  Degrees of freedom (2k)       = {2*k}")
    print(f"  p_combined = P(chi^2_{2*k} >= T) = {p_combined:.4e}")
    print()

    sigma = sigma_from_p_two_sided(p_combined)
    print(f"  Two-sided sigma equivalent:    ~{sigma:.2f} sigma")
    print()

    # Sensitivity sweep on the threshold-based legacy formula
    # (kept for traceability).
    print("--- Sensitivity (legacy threshold-based formula) ---")
    print(f"  {'threshold':>12} {'p_per':>10} {'p_joint':>14} {'sigma':>8}")
    print("  " + "-" * 50)
    for thr in (0.01, 0.05, 0.1, 0.2, 0.5, 1.0):
        pp, pj = joint_null_probability(thr, 2.5, 3)
        sg = sigma_from_p_two_sided(pj)
        print(f"  {thr:>10.3f} % {pp:>10.4f} {pj:>14.4e} {sg:>8.2f}")
    print()

    out = {
        "criterion": "Yukawa-Damping cluster joint random-null probability via Fisher's combined-p test",
        "cluster": [{"name": n, "residual_pct": r} for (n, r) in cluster],
        "shared_loop_class": "(1+gamma/4)",
        "shared_lemma": 1,
        "null_model": "uniform on [0, PRECISE_2.5%]",
        "n_observables": 3,
        "per_observable_p_values": [
            {"name": n, "residual_pct": r, "p_one_sided": p}
            for (n, r), p in zip(cluster, p_values)
        ],
        "primary_result": {
            "method": "Fisher's combined-p test",
            "T_statistic": T,
            "df": 2 * k,
            "p_combined": p_combined,
            "sigma_equivalent": sigma,
            "interpretation": (
                "Fisher's combined-p test on three independent "
                "per-observable p-values under a uniform null on "
                "[0, 2.5%]. The three observables (alpha_dn at "
                "0.0001%, w_DE at 0.05%, H_0 at 0.6%) yield individual "
                "p-values 4e-5, 0.02, 0.24; their Fisher-combined "
                "p_combined ~ 2.6e-5, corresponding to ~4.0 sigma "
                "(two-sided) significance."
            ),
        },
        "sensitivity_legacy": [
            {"threshold_pct": thr,
             "p_per": joint_null_probability(thr, 2.5, 3)[0],
             "p_joint": joint_null_probability(thr, 2.5, 3)[1]}
            for thr in (0.01, 0.05, 0.1, 0.2, 0.5, 1.0)
        ],
        "framing": (
            "The 'three observables on the SAME loop class (1+gamma/4)' "
            "coincidence is treated as the structural prior absorbed in "
            "the deterministic mapping algorithm; the present "
            "Fisher's-combined-p computation captures the "
            "per-observable residual-cut combinatoric, i.e. the joint "
            "probability that three uniform-null draws all land at "
            "their respective observed residuals."
        ),
    }
    out_path = OUTPUTS / "yukawa_cluster_joint_p.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
