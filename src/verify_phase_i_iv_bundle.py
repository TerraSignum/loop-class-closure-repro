r"""
Verify the Phase I-IV bundle of cross-sector closures.

The bundled file `data/phase_i_iv_bundle.json` records 20 closures
across Phase I (Standard-Model anchors), Phase II (cosmology / RG /
baryogenesis), Phase III (vacuum-selection inputs), and Phase IV
(structural theorems and calibration). This script surfaces the
tier counts, the headline ratios, and the EXACT/PRECISE/STRUCTURAL
verdict per phase.

The aggregate is the cross-sector context within which the
deterministic loop-class mapping algorithm of this paper sits: each
of the 20 closures uses one of the loop classes from the library of
Section 3.

Usage:
    python ./src/verify_phase_i_iv_bundle.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def load_bundle():
    with open(DATA / "phase_i_iv_bundle.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    d = load_bundle()
    print("=" * 88)
    print("Phase I-IV cross-sector closures (Standard-Model + cosmology + structural)")
    print("=" * 88)
    print()

    n_total = 0
    n_by_tier = {"EXACT": 0, "PRECISE": 0, "STRUCTURAL_CLOSED": 0,
                 "STRUCTURAL_STATEMENT": 0, "STRUCTURAL_OPEN_CALIBRATION": 0,
                 "ORDER": 0}
    for phase_key in ("phase_i", "phase_ii", "phase_iii", "phase_iv"):
        phase = d[phase_key]
        print(f"--- {phase['name']} ---")
        for c in phase["closures"]:
            n_total += 1
            tier = c.get("tier", "?")
            if tier in n_by_tier:
                n_by_tier[tier] += 1
            ratio = c.get("ratio")
            ratio_str = f", ratio={ratio:.4f}" if ratio is not None else ""
            pred = c.get("predicted", c.get("claim", ""))[:60]
            print(f"  {c['id']:<5} {c['name']:<40} | tier={tier:<28}{ratio_str}")
            print(f"        {pred}")
        print()

    summ = d["summary_counts"]
    print("--- Aggregate ---")
    print(f"  Total closures:   {summ['total_closures']}")
    print(f"  EXACT:            {summ['EXACT']}")
    print(f"  PRECISE:          {summ['PRECISE']}")
    print(f"  STRUCTURAL closed/stated/open: "
          f"{summ['STRUCTURAL_CLOSED']}/{summ['STRUCTURAL_STATEMENT']}/"
          f"{summ['STRUCTURAL_OPEN_CALIBRATION']}")
    print(f"  OUT_OF_BAND:      {summ.get('OUT_OF_BAND', summ.get('ORDER', 0))}")
    print(f"  PRECISE-or-better: {summ['PRECISE_or_better']}/"
          f"{summ['total_closures']}")
    print(f"  By phase: I={summ['by_phase']['I']}, "
          f"II={summ['by_phase']['II']}, "
          f"III={summ['by_phase']['III']}, "
          f"IV={summ['by_phase']['IV']}")
    print()

    out = {
        "criterion": "Phase I-IV cross-sector closure aggregate",
        "tier_counts_recomputed": n_by_tier,
        "total_recomputed": n_total,
        "consistent_with_bundled": (
            n_total == summ["total_closures"]
            and n_by_tier["EXACT"] == summ["EXACT"]
            and n_by_tier["PRECISE"] == summ["PRECISE"]
        ),
        "headline_ratios_phase_i": {
            c["id"]: c.get("ratio") for c in d["phase_i"]["closures"]
            if c.get("ratio") is not None
        },
        "headline_ratios_phase_ii": {
            c["id"]: c.get("ratio") for c in d["phase_ii"]["closures"]
            if c.get("ratio") is not None
        },
        "headline_ratios_phase_iii": {
            c["id"]: c.get("ratio") for c in d["phase_iii"]["closures"]
            if c.get("ratio") is not None
        },
        "headline_ratios_phase_iv": {
            c["id"]: c.get("ratio_alpha", c.get("ratio"))
            for c in d["phase_iv"]["closures"]
            if c.get("ratio") is not None or c.get("ratio_alpha") is not None
        },
    }
    out_path = OUTPUTS / "phase_i_iv_recompute.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
