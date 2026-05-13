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


def _predict_flat(r: Dict[str, Any], classes: List[Dict[str, Any]],
                  tree_class: Dict[str, Any]) -> Dict[str, Any]:
    """Predict for a tree or single_loop record (Phase-1/2 flat shape)."""
    entry: Dict[str, Any] = {
        "id":                  r["id"],
        "name":                r["name"],
        "sector":              r["sector"],
        "closure_kind":        r.get("closure_kind", "single_loop"),
        "tuple":               r["tuple"],
        "expected_sign":       r["expected_sign"],
        "loop_dressed":        r["loop_dressed"],
        "resummation_inverse": r.get("resummation_inverse", False),
        "provenance":          r["provenance"],
    }
    if not r["loop_dressed"]:
        entry["status"] = "MATCHED"
        entry["prediction"] = {
            "lemma_id": tree_class["lemma_id"],
            "name":     tree_class["name"],
            "factor":   tree_class["factor_plus"],
        }
        return entry

    status, matches = match_one(r["tuple"], classes)
    entry["status"] = status
    if status == "MATCHED":
        cls = matches[0]
        entry["prediction"] = {
            "lemma_id": cls["lemma_id"],
            "name":     cls["name"],
            "factor":   _select_factor(
                cls, sign=r["expected_sign"],
                inverse=entry["resummation_inverse"],
            ),
        }
    else:
        entry["candidate_lemma_ids"] = [m["lemma_id"] for m in matches]
    return entry


def _predict_compound(r: Dict[str, Any], classes: List[Dict[str, Any]]
                      ) -> Dict[str, Any]:
    """Predict for a loop_compound: match each factor, compose product."""
    entry: Dict[str, Any] = {
        "id":           r["id"],
        "name":         r["name"],
        "sector":       r["sector"],
        "closure_kind": "loop_compound",
        "factors":      r["factors"],
        "provenance":   r["provenance"],
    }
    factor_strings = []
    factor_lemmas = []
    for idx, f in enumerate(r["factors"]):
        status, matches = match_one(f["tuple"], classes)
        if status != "MATCHED":
            entry["status"] = status
            entry["error_at_factor"] = idx
            entry["candidate_lemma_ids"] = [m["lemma_id"] for m in matches]
            return entry
        cls = matches[0]
        factor_strings.append(_select_factor(
            cls, sign=f["expected_sign"],
            inverse=f.get("resummation_inverse", False),
        ))
        factor_lemmas.append(cls["lemma_id"])
    entry["status"] = "MATCHED"
    entry["prediction"] = {
        "lemma_id": "+".join(factor_lemmas),
        "name":     " x ".join(factor_lemmas),
        "factor":   "*".join(f"({s})" for s in factor_strings),
    }
    return entry


def _predict_structural(r: Dict[str, Any]) -> Dict[str, Any]:
    """Predict for a structural observable: actually evaluate the
    formula in the System-R rationals and assert it matches the claimed
    rational EXACTLY. No fallback, no approximation."""
    from .structural_evaluator import verify_structural_match
    match = verify_structural_match(
        r["structural_formula"], r["structural_rational"]
    )
    return {
        "id":            r["id"],
        "name":          r["name"],
        "sector":        r["sector"],
        "closure_kind":  "structural",
        "status":        "MATCHED",
        "provenance":    r["provenance"],
        "prediction": {
            "lemma_id": "STRUCTURAL",
            "name":     "Structural identity (no loop class)",
            "factor":   r["structural_formula"],
            "rational": r["structural_rational"],
            "evaluation": match,
        },
    }


def _predict_diagnostic(r: Dict[str, Any]) -> Dict[str, Any]:
    """Predict for a stability-diagnostic: read bundles, extract fields,
    compare to YAML prediction window. No fabrication."""
    from .stability_diagnostic import evaluate_diagnostic
    verdict = evaluate_diagnostic(r)
    # Status is one of BUNDLE_MISSING, EXTRACT_ERROR, BASELINE_RECOVERED,
    # PROSPECTIVE_CONFIRMED, PROSPECTIVE_FALSIFIED.
    base_status = verdict["status"]
    matched_statuses = {"BASELINE_RECOVERED", "PROSPECTIVE_CONFIRMED"}
    return {
        "id":            r["id"],
        "name":          r["name"],
        "sector":        r["sector"],
        "closure_kind":  "stability_diagnostic",
        "status":        "MATCHED" if base_status in matched_statuses else "OPEN",
        "diagnostic_status": base_status,
        "provenance":    r.get("provenance"),
        "prediction": {
            "lemma_id": "STABILITY_DIAGNOSTIC",
            "name":     verdict["name"],
            "verdict":  verdict,
        },
    }


def _predict_one(r: Dict[str, Any], classes: List[Dict[str, Any]],
                 tree_class: Dict[str, Any]) -> Dict[str, Any]:
    kind = r.get("closure_kind", "single_loop")
    if kind in ("tree", "single_loop"):
        return _predict_flat(r, classes, tree_class)
    if kind == "loop_compound":
        return _predict_compound(r, classes)
    if kind == "structural":
        return _predict_structural(r)
    if kind == "stability_diagnostic":
        return _predict_diagnostic(r)
    raise RuntimeError(f"{r['id']}: unhandled closure_kind={kind!r}")


def _select_factor(cls: Dict[str, Any], *, sign: int, inverse: bool) -> str:
    """Pick the (sign, direct/inverse) variant from a matched lemma class.

    The inverse fields exist only for L4 (Resummed-Propagator); for all
    other lemma classes the inverse variant is structurally undefined.
    Raises if the YAML requests an inverse form on a non-resummed class.
    """
    if inverse:
        key = "factor_plus_inverse" if sign > 0 else "factor_minus_inverse"
        if key not in cls:
            raise RuntimeError(
                f"Lemma {cls['lemma_id']} has no '{key}' (inverse form is "
                f"defined for L4 only; check the YAML's "
                f"operator.resummation_inverse flag)."
            )
        return cls[key]
    return cls["factor_plus"] if sign > 0 else cls["factor_minus"]


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
        entry = _predict_one(r, classes, tree_class)
        counts[entry["status"]] += 1
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
