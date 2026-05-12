r"""m_tau Path D: TIME_FEED_NORMALIZATION-corrected closure
combining cost-dressed m_tau with the GFS04-direct vs Y5-biunitary
arm-normalization structure documented in
outputs_flavor_cp_spinor_emt_deepening_v2/pg_tcp1_time_asymmetry_to_cp_quantitative_link.json.

The deepening modules (PG-TCP1, PG-JTS2, PG-SPN3) localize the
remaining flavor/CP gap as a TIME_FEED_NORMALIZATION_MISMATCH
between the direct GFS04 arm (eta_B transport ratio 0.534, health
0.786) and the bi-unitary Y5 arm (transport ratio 89242, health
0.168). The Y5 arm strongly overshoots while the GFS04 arm
under-shoots by a structurally-meaningful factor.

This Path D test asks: if the GFS04-vs-Y5 normalization mismatch
that fixes eta_B applies analogously to m_tau (since both are
charged-lepton-mediated CP/mass observables), what does the
GFS04-corrected m_tau look like?

Audited m_tau arms:
- Y3 raw (charged-lepton spectral Yukawa eigenvalue): outputs_theory_closure/yukawa_y1_y5.json
- cost-dressed (gfs08 5-layer cascade): outputs_gap_closure_fermion/gap_closure_fermion_dressed_predictions.csv
- F-05 GJ-textur-null bi-unitary: outputs_theory_closure/f05_gj_textur_null_impl.json
- F-05 lattice-N extension: outputs_theory_closure/f05_gj_textur_null_p5n_extension.json

Normalization corrections probed:
- direct_gfs04_eta_transport_ratio = 0.533684 (PG-TCP1, P1)
- biunitary_y5_health = 0.168051 (PG-TCP1)
- direct_gfs04_time_feed_health = 0.785721 (PG-TCP1)

Output: outputs/verify_m_tau_path_D_normalization.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

PDG_M_TAU_GEV = 1.77686

PG_TCP1_PATH = Path(
    "c:/Users/user/Desktop/Emergence/outputs_flavor_cp_spinor_emt_deepening_v2/"
    "pg_tcp1_time_asymmetry_to_cp_quantitative_link.json"
)


def load_framework_m_tau_arms() -> dict:
    """Collect m_tau predictions across all bundled framework arms."""
    arms: dict = {}

    yk = json.load(open(
        "c:/Users/user/Desktop/Emergence/outputs_theory_closure/yukawa_y1_y5.json",
        encoding="utf-8"))
    y3_preds = yk.get("y3", {}).get("predictions", [])
    for p in y3_preds:
        if p.get("particle") == "tau":
            arms[f"Y3_raw_{p['regime']}"] = p["predicted_GeV"]

    p1_dressed = 3.040719
    p2prime_dressed = 16.935417
    arms["gfs08_cost_dressed_p1"] = p1_dressed
    arms["gfs08_cost_dressed_p2prime"] = p2prime_dressed

    f05_impl = json.load(open(
        "c:/Users/user/Desktop/Emergence/outputs_theory_closure/f05_gj_textur_null_impl.json",
        encoding="utf-8"))
    for i, row in enumerate(f05_impl.get("per_regime_table", [])):
        v = row.get("m_tau_GeV")
        if isinstance(v, (int, float)):
            arms[f"F05_GJ_textur_null_row{i}"] = v

    f05_p5n = json.load(open(
        "c:/Users/user/Desktop/Emergence/outputs_theory_closure/f05_gj_textur_null_p5n_extension.json",
        encoding="utf-8"))
    for row in f05_p5n.get("per_regime_table_extension", []):
        v = row.get("m_tau_GeV")
        if isinstance(v, (int, float)):
            arms[f"F05_GJ_textur_null_extension_{row.get('regime')}"] = v

    return arms


def load_pg_tcp1_normalizations() -> dict:
    if not PG_TCP1_PATH.exists():
        return {}
    d = json.load(open(PG_TCP1_PATH, encoding="utf-8"))
    return {
        "direct_gfs04_eta_transport_ratio_p1":
            _get_nested(d, "direct_gfs04_eta_transport_ratio_p1"),
        "biunitary_y5_eta_transport_ratio_p1":
            _get_nested(d, "biunitary_y5_eta_transport_ratio_p1"),
        "direct_gfs04_time_feed_health":
            _get_nested(d, "direct_gfs04_time_feed_health"),
        "biunitary_y5_time_feed_health":
            _get_nested(d, "biunitary_y5_time_feed_health"),
        "first_time_to_cp_quantitative_loss":
            _get_nested(d, "first_time_to_cp_quantitative_loss"),
    }


def _get_nested(obj, target_key):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == target_key:
                return v
            r = _get_nested(v, target_key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for it in obj:
            r = _get_nested(it, target_key)
            if r is not None:
                return r
    return None


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


def main():
    arms = load_framework_m_tau_arms()
    norms = load_pg_tcp1_normalizations()

    print("=" * 78)
    print("m_tau Path D: TIME_FEED_NORMALIZATION-corrected closure")
    print("=" * 78)
    print()
    print("BUNDLED PG-TCP1 normalizations:")
    for k, v in norms.items():
        print(f"  {k}: {v}")
    print()
    print("Framework m_tau arms (raw):")
    print(f"  {'arm':<40s} {'pred_GeV':>10s} {'ratio_PDG':>10s} {'residual%':>10s}  tier")
    print("-" * 78)
    arm_rows = []
    for label, pred in sorted(arms.items()):
        r = residual_pct(pred, PDG_M_TAU_GEV)
        ratio = pred / PDG_M_TAU_GEV
        arm_rows.append({"arm": label, "pred_GeV": pred,
                          "ratio_to_PDG": ratio,
                          "residual_pct": r, "tier": tier_of(r)})
        print(f"  {label:<40s} {pred:>10.4f} {ratio:>10.3f} {r:>10.2f}%  {tier_of(r)}")

    # Path D normalization corrections
    eta_transport = norms.get("direct_gfs04_eta_transport_ratio_p1")
    health = norms.get("direct_gfs04_time_feed_health")
    print()
    print("=" * 78)
    print("PATH D corrections applied to gfs08 cost-dressed m_tau (3.0407 GeV at P1)")
    print("=" * 78)
    print(f"  {'correction':<60s} {'corr_pred':>10s} {'res%':>8s}  tier")
    print("-" * 90)

    base = arms.get("gfs08_cost_dressed_p1", 3.040719)
    corrections = {}

    if eta_transport is not None:
        # (i) GFS04 eta_B transport ratio applied as direct normalization
        corr = base * eta_transport
        corrections["base * eta_B_transport_GFS04"] = {
            "value": corr, "residual_pct": residual_pct(corr, PDG_M_TAU_GEV),
            "tier": tier_of(residual_pct(corr, PDG_M_TAU_GEV)),
            "note": "Hypothesis: time-feed normalization mismatch on the GFS04 arm "
                    "is the same factor that closes eta_B; applied to m_tau gives "
                    f"{corr:.4f} GeV vs PDG {PDG_M_TAU_GEV} GeV.",
        }
        print(f"  {'base * eta_B_transport_GFS04 (=0.534)':<60s} "
              f"{corr:>10.4f} {residual_pct(corr, PDG_M_TAU_GEV):>7.2f}%  "
              f"{tier_of(residual_pct(corr, PDG_M_TAU_GEV))}")

    if health is not None:
        corr = base * health
        corrections["base * gfs04_time_feed_health"] = {
            "value": corr, "residual_pct": residual_pct(corr, PDG_M_TAU_GEV),
            "tier": tier_of(residual_pct(corr, PDG_M_TAU_GEV)),
        }
        print(f"  {'base * gfs04_time_feed_health (=0.786)':<60s} "
              f"{corr:>10.4f} {residual_pct(corr, PDG_M_TAU_GEV):>7.2f}%  "
              f"{tier_of(residual_pct(corr, PDG_M_TAU_GEV))}")

    if eta_transport is not None and health is not None:
        joint = base * eta_transport * health
        corrections["base * eta * health"] = {
            "value": joint, "residual_pct": residual_pct(joint, PDG_M_TAU_GEV),
            "tier": tier_of(residual_pct(joint, PDG_M_TAU_GEV)),
        }
        print(f"  {'base * eta_B * health (joint)':<60s} "
              f"{joint:>10.4f} {residual_pct(joint, PDG_M_TAU_GEV):>7.2f}%  "
              f"{tier_of(residual_pct(joint, PDG_M_TAU_GEV))}")

        sqrt_eta = math.sqrt(eta_transport)
        corr = base * sqrt_eta
        corrections["base * sqrt(eta_B_transport)"] = {
            "value": corr, "residual_pct": residual_pct(corr, PDG_M_TAU_GEV),
            "tier": tier_of(residual_pct(corr, PDG_M_TAU_GEV)),
        }
        print(f"  {'base * sqrt(eta_B) [single-flavour mediated]':<60s} "
              f"{corr:>10.4f} {residual_pct(corr, PDG_M_TAU_GEV):>7.2f}%  "
              f"{tier_of(residual_pct(corr, PDG_M_TAU_GEV))}")

    out = {
        "method": "m_tau Path D — TIME_FEED_NORMALIZATION-corrected closure using PG-TCP1 GFS04-vs-Y5 normalization mismatch",
        "stand": "2026-05-05",
        "PDG_target_GeV": PDG_M_TAU_GEV,
        "framework_arms": arm_rows,
        "PG_TCP1_normalizations": norms,
        "path_D_corrections_on_gfs08_p1_base": corrections,
        "verdict": (
            "PATH D HYPOTHETICAL: applying the GFS04-arm eta_B transport ratio "
            "0.534 (PG-TCP1, baryogenesis-credible) as a multiplicative "
            "correction to the gfs08 cost-dressed m_tau prediction (3.04 GeV) "
            "yields 1.624 GeV vs PDG 1.777 GeV (~8.6% FACTOR2 residual, much "
            "tighter than the bare 71% residual). This is a structural "
            "hypothesis: it requires an independent argument that the same "
            "TIME_FEED_NORMALIZATION_MISMATCH that closes baryogenesis on "
            "the GFS04 arm also applies to the charged-lepton mass scale. "
            "If accepted, m_tau closes at FACTOR2 8.6%; without that "
            "argument, the correction is target-aware and inadmissible. "
            "Independent route: compute m_tau directly from the GFS04 arm "
            "(currently bundled outputs only carry GFS04-derived eta_B / "
            "Jarlskog, not m_tau)."
        ),
    }

    out_path = OUTPUTS / "verify_m_tau_path_D_normalization.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
