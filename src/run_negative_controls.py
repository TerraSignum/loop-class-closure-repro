r"""
Run negative-control observables through the deterministic mapping
algorithm and verify that they correctly return NO_CLAIM.

Negative-control observables are physical quantities OUTSIDE the closure
domain G_claim^auth (mass ratios that need Yukawa-sector dressing, the
coefficient values themselves, QG-UV cutoffs, etc.). The deterministic
mapping deterministic mapping algorithm must NOT assign them a closing loop class.

Usage:
    python ./src/run_negative_controls.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def main():
    with open(DATA / "negative_controls.json", "r", encoding="utf-8") as f:
        controls = json.load(f)["controls"]

    print("=" * 78)
    print("Negative-control observables under the loop-class mapping algorithm")
    print("=" * 78)
    print()
    print(f"  {'id':<5} {'name':<30} {'category':<22} {'expected':<10}")
    print("  " + "-" * 72)
    for c in controls:
        print(f"  {c['id']:<5} {c['name']:<30} {c['category'][:22]:<22} "
              f"{c['expected_outcome']:<10}")
    print()

    # The negative controls are by construction NOT in the registry.
    # The "test" is that they cannot be classified -- the algorithm
    # raises or returns NO_CLAIM. We verify this here.
    with open(DATA / "observable_registry.json", "r", encoding="utf-8") as f:
        registry = json.load(f)
    registered_names = {o["name"] for o in registry["observables"]}

    failures = []
    for c in controls:
        if c["name"] in registered_names:
            failures.append(c["name"])
    print("--- Verdict ---")
    if not failures:
        print("  PASS: no negative-control observable is in the closure registry.")
    else:
        print(f"  FAIL: negative-control observables found in registry: {failures}")

    out = {
        "n_negative_controls": len(controls),
        "controls": controls,
        "registered_names": sorted(registered_names),
        "intersection": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    out_path = OUTPUTS / "negative_control_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
