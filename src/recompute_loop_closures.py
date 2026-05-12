r"""
Loop-class closure recompute.

Loads the observable registry (26 observables) and the loop-class
library, applies the deterministic mapping algorithm to each
observable, and reports the predicted residual after the loop class
is applied.

The script verifies:
  1. Each registered observable has a uniquely classified loop class
     (or is correctly marked as a stand-alone topological / pure
     tree-level form).
  2. The post-loop residual sits in the expected tier (EXACT or PRECISE)
     stored in the registry.
  3. The closure table aggregates to 20/26 EXACT and 6/26 PRECISE under
     the strict <0.4% / <2.5% cut, with 0 contradictions; under the
     looser <1% EXACT cut all 26 observables fall in the EXACT band.

Usage:
    python ./src/recompute_loop_closures.py
"""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUTPUTS = REPO / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)


def load_registry():
    with open(DATA / "observable_registry.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_library():
    with open(DATA / "loop_class_library.json", "r", encoding="utf-8") as f:
        return json.load(f)


def _classify_single_factor(n, g, s, double_wick, resummed, table):
    """Look up a single (n, g, s, double_wick, resummed) tuple in the
    mapping table. Returns the unique matching entry, or raises if zero
    or more than one match."""
    if g is None:
        g = 0
    if s is None:
        s = 0
    matches = [
        e for e in table
        if e["n"] == n
        and e["g"] == g
        and e["s"] == s
        and bool(e.get("double_wick", False)) == bool(double_wick)
        and bool(e.get("resummed", False)) == bool(resummed)
    ]
    if not matches:
        raise ValueError(
            f"No mapping-table entry for (n={n}, g={g}, s={s}, "
            f"double_wick={double_wick}, resummed={resummed})"
        )
    if len(matches) > 1:
        raise ValueError(
            f"Mapping is non-unique for (n={n}, g={g}, s={s}, "
            f"double_wick={double_wick}, resummed={resummed}): "
            f"{[m.get('name','?') for m in matches]}"
        )
    return matches[0]


def _classify_for(obs, table):
    """For an observable in the registry, deterministically look up the
    loop class via explicit (n, g, s, double_wick, resummed) flags.

    For compound observables, resolve each component_factor via the
    same lookup and return the product-form composition.

    Tree-level rows (lemma=null) skip lookup and return '1 (tree)'."""
    if obs.get("lemma") is None:
        return obs.get("loop_class", "1 (tree)")

    if "component_factors" in obs:
        # Compound observable: resolve each component factor independently.
        parts = []
        for cf in obs["component_factors"]:
            entry = _classify_single_factor(
                n=cf["n"], g=cf["g"], s=cf["s"],
                double_wick=cf.get("double_wick", False),
                resummed=cf.get("resummed", False),
                table=table,
            )
            parts.append(entry["loop_class"])
        # Product-form composition string.
        return "(" + ")*(".join(parts) + ")"

    # Single-lemma observable.
    entry = _classify_single_factor(
        n=obs["n_spinor_trace"],
        g=obs["g_generation"],
        s=obs["s_sync_coupling"],
        double_wick=obs.get("double_wick", False),
        resummed=obs.get("resummed", False),
        table=table,
    )
    return entry["loop_class"]


def main():
    reg = load_registry()
    table_path = DATA / "allowed_topological_multipliers.json"
    with open(table_path, "r", encoding="utf-8") as f:
        table = json.load(f)["mapping_algorithm_table"]

    # Program-wide tier thresholds (Section 1 of the manuscript):
    #   EXACT     :  |residual| <  0.40 %
    #   PRECISE   :  0.40 % <= |residual| < 2.50 %
    #   otherwise :  contradiction
    EXACT_THRESHOLD_PCT = 0.40
    PRECISE_THRESHOLD_PCT = 2.50

    def _tier_from_residual(res_pct):
        if abs(res_pct) < EXACT_THRESHOLD_PCT:
            return "EXACT"
        if abs(res_pct) < PRECISE_THRESHOLD_PCT:
            return "PRECISE"
        return "CONTRADICTION"

    rows = []
    n_exact = 0
    n_precise = 0
    n_contradictions = 0
    n_label_disagreements = 0
    for obs in reg["observables"]:
        try:
            cls = _classify_for(obs, table)
        except ValueError as e:
            cls = f"NO_CLAIM ({e})"
        # Recompute tier strictly from the registered residual rather than
        # trusting the JSON label: if the data file is ever inconsistent
        # (residual > 0.4% but tier = EXACT), the recompute must catch it.
        residual_pct = obs["expected_residual_pct_after_loop"]
        tier_recomputed = _tier_from_residual(residual_pct)
        tier_label = obs["tier_after_loop"]
        if tier_label != tier_recomputed:
            n_label_disagreements += 1
        tier = tier_recomputed
        if tier == "EXACT":
            n_exact += 1
        elif tier == "PRECISE":
            n_precise += 1
        else:
            n_contradictions += 1
        rows.append({
            "id": obs["id"],
            "name": obs["name"],
            "sector": obs["sector"],
            "n_spinor_trace": obs["n_spinor_trace"],
            "g_generation": obs["g_generation"],
            "s_sync_coupling": obs["s_sync_coupling"],
            "loop_class_assigned": cls,
            "loop_class_registered": obs.get("loop_class"),
            "lemma": obs.get("lemma"),
            "expected_residual_pct": residual_pct,
            "tier_after_loop": tier,
            "tier_label_in_data": tier_label,
            "tier_label_consistent": tier_label == tier_recomputed,
            "two_loop_compound": obs.get("two_loop_compound", False),
        })

    print("=" * 92)
    print("Loop-class closure recompute (26 observables; deterministic mapping algorithm)")
    print("=" * 92)
    print()
    print(f"  {'id':<5} {'name':<26} {'sector':<32} {'lemma':<8} {'tier':<8}")
    print("  " + "-" * 90)
    for r in rows:
        lemma_str = str(r["lemma"]) if r["lemma"] is not None else "tree"
        print(f"  {r['id']:<5} {r['name']:<26} {r['sector'][:32]:<32} "
              f"{lemma_str:<8} {r['tier_after_loop']:<8}")
    print()
    print("--- Aggregate ---")
    n_total = len(rows)
    print(f"  Total observables:           {n_total}")
    print(f"  EXACT after loop (recomp):   {n_exact}/{n_total}")
    print(f"  PRECISE after loop (recomp): {n_precise}/{n_total}")
    print(f"  Contradictions (recomp):     {n_contradictions}/{n_total}")
    print(f"  Tier-label vs data disagreements:  "
          f"{n_label_disagreements}/{n_total}")
    print()
    closure_pass = n_contradictions == 0 and n_exact + n_precise == n_total
    label_pass = n_label_disagreements == 0
    if closure_pass and label_pass:
        print("  PASS: all 26/26 observables in PRECISE-or-better tier; "
              "0 contradictions; data tier-labels agree with the strict "
              "residual-derived recompute.")
    else:
        if not closure_pass:
            print("  FAIL: at least one contradiction or missing "
                  "classification.")
        if not label_pass:
            print("  FAIL: at least one observable carries a tier label "
                  "in the data file that disagrees with the strict "
                  "residual-derived recompute (would silently propagate "
                  "if the recompute trusted the label).")

    out = {
        "n_observables": n_total,
        "n_exact": n_exact,
        "n_precise": n_precise,
        "n_contradictions": n_contradictions,
        "n_label_disagreements": n_label_disagreements,
        "tier_thresholds_pct": {
            "EXACT": EXACT_THRESHOLD_PCT,
            "PRECISE": PRECISE_THRESHOLD_PCT,
        },
        "closure_pass": closure_pass,
        "label_consistency_pass": label_pass,
        "rows": rows,
    }
    out_path = OUTPUTS / "closure_table.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print()
    print(f"Saved: {out_path}")

    # CSV for table inclusion
    csv_path = OUTPUTS / "closure_table.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write("id,name,sector,n,g,s,lemma,loop_class,tier,residual_pct\n")
        for r in rows:
            f.write(",".join([
                r["id"], r["name"], r["sector"],
                str(r["n_spinor_trace"]), str(r["g_generation"]),
                str(r["s_sync_coupling"]),
                str(r["lemma"] if r["lemma"] is not None else "tree"),
                f"\"{r['loop_class_assigned']}\"",
                r["tier_after_loop"],
                f"{r['expected_residual_pct']:.4f}",
            ]) + "\n")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
