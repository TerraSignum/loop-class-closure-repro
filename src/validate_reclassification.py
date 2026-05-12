r"""
Validate documented reclassification cases against rules R1-R5.

Rules R1-R5 (Section 3.5 of the paper):
  R1: Falsification trigger
  R2: Algorithm consistency under explicit (n, g, s) re-identification
  R3: At most TWO reclassifications per observable
  R4: Cross-sector pre-specification of the new class
  R5: New class must define its own falsification bound

If any rule is violated, the case is rejected. If more than two
reclassifications occur for one observable, theorem-falsification
trigger F3 fires and the entire the loop-class completeness theorem falls.

Usage:
    python ./src/validate_reclassification.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

RULES = ("R1_satisfied", "R2_satisfied", "R3_satisfied",
         "R4_satisfied", "R5_satisfied")


def main():
    with open(DATA / "reclassification_cases.json", "r", encoding="utf-8") as f:
        blob = json.load(f)
    cases = blob["documented_cases"]

    print("=" * 78)
    print("Reclassification case validation under rules R1-R5")
    print("=" * 78)
    print()
    print(blob["rules"]["R1"])
    print(blob["rules"]["R2"])
    print(blob["rules"]["R3"])
    print(blob["rules"]["R4"])
    print(blob["rules"]["R5"])
    print()
    print("--- Cases ---")
    print(f"  {'id':<6} {'observable':<30} {'count':<6} R1 R2 R3 R4 R5  status")
    print("  " + "-" * 75)

    # Count reclassifications per observable.
    counts = {}
    for c in cases:
        counts[c["observable"]] = counts.get(c["observable"], 0) + 1

    n_pass = 0
    n_fail = 0
    n_theorem_fall = 0
    for c in cases:
        flags = []
        for r in RULES:
            flags.append("Y" if c.get(r, False) else "N")
        all_ok = all(c.get(r, False) for r in RULES)
        observable_count = counts[c["observable"]]
        r3_global_ok = observable_count <= 2
        status = "PASS" if (all_ok and r3_global_ok) else "FAIL"
        if not r3_global_ok:
            status = "THEOREM_FALL_F3"
            n_theorem_fall += 1
        if status == "PASS":
            n_pass += 1
        elif status == "FAIL":
            n_fail += 1
        print(f"  {c['id']:<6} {c['observable']:<30} {observable_count:<6} "
              f"{flags[0]:<2} {flags[1]:<2} {flags[2]:<2} {flags[3]:<2} {flags[4]:<2} "
              f"{status}")

    print()
    print("--- Verdict ---")
    print(f"  Total cases: {len(cases)}")
    print(f"  PASS:        {n_pass}")
    print(f"  FAIL:        {n_fail}")
    print(f"  THEOREM_FALL_F3: {n_theorem_fall}")
    if n_fail == 0 and n_theorem_fall == 0:
        print("  Overall: PASS (all reclassifications consistent with R1-R5).")
    else:
        print("  Overall: FAIL.")

    out = {
        "total_cases": len(cases),
        "pass": n_pass,
        "fail": n_fail,
        "theorem_fall_F3": n_theorem_fall,
        "per_observable_count": counts,
    }
    out_path = OUTPUTS / "reclassification_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
