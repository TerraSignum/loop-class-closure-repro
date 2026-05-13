"""Match extracted tuples against the loop-class library.

Reads outputs/extracted_topology_tuples.json (immutable input from
the extractor) and data/loop_class_map.json (bijective tuple ->
lemma map), and produces outputs/loop_class_predictions.json with
three status values per observable:

    MATCHED  -- exactly one lemma matches; loop-class assigned
    OPEN     -- zero lemmas match; the tuple is not in the library
    ERROR    -- two or more lemmas match; map has a duplicate

Refuses to read the loop-class map if the tuples bundle has any
extraction errors, so a partial/inconsistent extraction cannot
silently produce predictions.

Usage:
    python -m tuple_compiler.loop_class_predictor
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
TUPLES_PATH = REPO_ROOT / "outputs" / "extracted_topology_tuples.json"
LOOP_MAP_PATH = REPO_ROOT / "data" / "loop_class_map.json"
OUTPUT_PATH = REPO_ROOT / "outputs" / "loop_class_predictions.json"


def match_one(tup: Dict[str, Any], classes: List[Dict[str, Any]]
              ) -> Tuple[str, List[Dict[str, Any]]]:
    """Return (status, matches) for a single (loop-dressed) tuple."""
    matches: List[Dict[str, Any]] = []
    for cls in classes:
        if all(tup.get(k) == v for k, v in cls["match"].items()):
            matches.append(cls)
    if len(matches) == 1:
        return "MATCHED", matches
    if len(matches) == 0:
        return "OPEN", matches
    return "ERROR", matches


def predict_all() -> Dict[str, Any]:
    """Run the predictor on the current extracted tuples."""
    if not TUPLES_PATH.exists():
        raise RuntimeError(
            f"{TUPLES_PATH} not found. Run extract_topology_tuple first."
        )
    bundle = json.loads(TUPLES_PATH.read_text(encoding="utf-8"))
    if bundle["n_errors"] > 0:
        raise RuntimeError(
            f"Tuples bundle has {bundle['n_errors']} extraction errors; "
            f"refusing to predict on a partial/inconsistent input."
        )

    loop_map = json.loads(LOOP_MAP_PATH.read_text(encoding="utf-8"))
    classes = loop_map["classes"]
    tree_class = loop_map["tree_class"]

    predictions: List[Dict[str, Any]] = []
    counts = {"MATCHED": 0, "OPEN": 0, "ERROR": 0}

    for r in bundle["results"]:
        entry: Dict[str, Any] = {
            "id":            r["id"],
            "name":          r["name"],
            "sector":        r["sector"],
            "tuple":         r["tuple"],
            "expected_sign": r["expected_sign"],
            "loop_dressed":  r["loop_dressed"],
            "provenance":    r["provenance"],
        }

        if not r["loop_dressed"]:
            # Tree-level: assign the TREE class directly; the structural
            # tuple identifies the operator signature but the dressing
            # axiom puts this observable at tree-level with factor=1.
            entry["status"]     = "MATCHED"
            entry["prediction"] = {
                "lemma_id": tree_class["lemma_id"],
                "name":     tree_class["name"],
                "factor":   tree_class["factor_plus"],
            }
            counts["MATCHED"] += 1
        else:
            status, matches = match_one(r["tuple"], classes)
            counts[status] += 1
            entry["status"] = status
            if status == "MATCHED":
                cls = matches[0]
                sign = r["expected_sign"]
                factor = cls["factor_plus"] if sign > 0 else cls["factor_minus"]
                entry["prediction"] = {
                    "lemma_id": cls["lemma_id"],
                    "name":     cls["name"],
                    "factor":   factor,
                }
            else:
                entry["candidate_lemma_ids"] = [m["lemma_id"] for m in matches]

        predictions.append(entry)

    return {
        "schema_version":     bundle["schema_version"],
        "loop_map_version":   loop_map["schema_version"],
        "n_observables":      len(predictions),
        "counts":             counts,
        "predictions":        predictions,
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bundle = predict_all()

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False, sort_keys=True)

    print(
        f"Predictions: MATCHED={bundle['counts']['MATCHED']}, "
        f"OPEN={bundle['counts']['OPEN']}, "
        f"ERROR={bundle['counts']['ERROR']} -> {OUTPUT_PATH}"
    )
    return 0 if bundle["counts"]["ERROR"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
