"""Stability-diagnostic harness for prospective registry observables.

Phase 7 of the tuple compiler. PROSP-01/02/03 in
data/prospective_cluster_registry.json are multi-N stability
diagnostics, NOT loop-class closures and NOT structural identities --
they record diagnostic scores (newton_like_pass, far_field_exponent,
cosmo_compat, gate_gap, cw_net_corrected, ...) measured on lattice
bundle outputs scattered across the broader Emergence corpus.

This harness honestly reproduces a diagnostic by:

1. Resolving each declared bundle path relative to the Emergence root
   (the parent of loop-class-closure-repro).
2. Reading each bundle JSON deterministically.
3. Extracting the named fields via dotted paths
   (e.g. 'gap_analysis_p2p_s1_vs_p5_ref.cw_net_corrected').
4. Hash-pinning each bundle to its SHA-256 so silent data drift is
   detectable.
5. Comparing extracted values to the YAML's prediction window where
   declared.
6. Reporting one of: BASELINE_RECOVERED (pre-T_0 inputs verified),
   PROSPECTIVE_CONFIRMED (post-T_0 residual within window),
   PROSPECTIVE_FALSIFIED (post-T_0 residual outside window),
   BUNDLE_MISSING (a declared bundle file is not on disk).

No fabrication, no fallback to defaults, no float tolerance unless
explicitly declared in the YAML's prediction.tolerance field.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# Discover the Emergence root: the parent of the loop-class-closure-repro
# directory. The PROSP bundle paths are relative to this root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
EMERGENCE_ROOT = _REPO_ROOT.parent


def resolve_bundle_path(relative_path: str) -> Optional[Path]:
    """Resolve a bundle path relative to the Emergence root.

    Returns the absolute Path if the file exists, None otherwise.
    The harness intentionally does NOT raise -- a missing bundle is
    reported as BUNDLE_MISSING by the verdict logic, so the user can
    distinguish 'file not there' from 'file present but value wrong'.
    """
    candidates = [
        EMERGENCE_ROOT / relative_path,
        _REPO_ROOT / relative_path,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def bundle_sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def extract_dotted(payload: Dict[str, Any], field: str) -> Any:
    """Extract a dotted-path field from a nested JSON mapping.

    Raises KeyError if any intermediate key is missing -- no silent
    None return.
    """
    cur: Any = payload
    for part in field.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"field path '{field}' missing at '{part}'")
        cur = cur[part]
    return cur


def _check_prediction(extracted: Dict[str, Any],
                       prediction: Optional[Dict[str, Any]]
                       ) -> Dict[str, Any]:
    """Compare extracted values to a YAML-declared prediction window."""
    if prediction is None:
        return {"checked": False, "reason": "no prediction declared"}
    expected = prediction.get("expected", {})
    tol      = prediction.get("tolerance")
    if not isinstance(expected, dict) or not isinstance(tol, (int, float)):
        return {"checked": False,
                "reason": "prediction.expected (dict) and prediction.tolerance "
                          "(number) both required"}
    results: List[Dict[str, Any]] = []
    all_pass = True
    for field, target in expected.items():
        if field not in extracted:
            results.append({"field": field, "status": "MISSING",
                            "expected": target, "actual": None})
            all_pass = False
            continue
        # Per-regime list-of-dicts: check that EVERY regime is within
        # tolerance, since the diagnostic asserts ladder-wide stability.
        actuals = extracted[field]
        if not isinstance(actuals, list):
            actuals = [actuals]
        max_dev = max(abs(float(a) - float(target)) for a in actuals)
        ok = max_dev <= tol
        results.append({
            "field":      field,
            "expected":   target,
            "max_abs_deviation_across_ladder": max_dev,
            "tolerance":  tol,
            "status":     "PASS" if ok else "FAIL",
        })
        if not ok:
            all_pass = False
    return {
        "checked":   True,
        "all_pass":  all_pass,
        "per_field": results,
    }


def evaluate_diagnostic(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Run one stability-diagnostic YAML end-to-end and return verdict.

    The verdict status is one of:
    - BUNDLE_MISSING        : at least one declared bundle file absent
    - EXTRACT_ERROR         : a declared field is missing in a bundle
    - BASELINE_RECOVERED    : pre-T_0 baseline values successfully
                              extracted; no prediction declared OR
                              prediction.checked is False
    - PROSPECTIVE_CONFIRMED : prediction declared and all extracted
                              values within tolerance
    - PROSPECTIVE_FALSIFIED : prediction declared and at least one
                              extracted value outside tolerance
    """
    diag = obs["diagnostic"]
    bundles_decl = diag["bundle_files"]
    extract_decl = diag["extract"]
    prediction   = diag.get("prediction")

    bundles_resolved: List[Dict[str, Any]] = []
    missing_paths: List[str] = []
    for b in bundles_decl:
        path = resolve_bundle_path(b["path"])
        if path is None:
            missing_paths.append(b["path"])
            bundles_resolved.append({**b, "resolved_path": None,
                                      "sha256": None})
            continue
        bundles_resolved.append({
            **b,
            "resolved_path":          str(path),
            "resolved_path_relative": str(path.relative_to(EMERGENCE_ROOT)),
            "sha256":                 bundle_sha256(path),
        })

    if missing_paths:
        return {
            "id":              obs["id"],
            "name":            obs["name"],
            "status":          "BUNDLE_MISSING",
            "missing_paths":   missing_paths,
            "bundles":         bundles_resolved,
        }

    # Extract: aggregate every field over all bundles into a list.
    extracted: Dict[str, List[Any]] = {e["field"]: [] for e in extract_decl}
    extract_per_bundle: List[Dict[str, Any]] = []
    extract_errors: List[Dict[str, Any]] = []

    for b in bundles_resolved:
        with Path(b["resolved_path"]).open("r", encoding="utf-8") as f:
            payload = json.load(f)
        per_bundle: Dict[str, Any] = {
            "path":   b["resolved_path_relative"],
            "regime": b.get("regime"),
            "sha256": b["sha256"],
        }
        for e in extract_decl:
            field = e["field"]
            try:
                value = extract_dotted(payload, field)
            except KeyError as exc:
                extract_errors.append({
                    "path":  b["resolved_path_relative"],
                    "field": field,
                    "error": str(exc),
                })
                per_bundle[field] = None
                continue
            per_bundle[field] = value
            extracted[field].append(value)
        extract_per_bundle.append(per_bundle)

    if extract_errors:
        return {
            "id":              obs["id"],
            "name":            obs["name"],
            "status":          "EXTRACT_ERROR",
            "extract_errors":  extract_errors,
            "bundles":         bundles_resolved,
        }

    pred_result = _check_prediction(extracted, prediction)
    if not pred_result["checked"]:
        status = "BASELINE_RECOVERED"
    elif pred_result["all_pass"]:
        status = "PROSPECTIVE_CONFIRMED"
    else:
        status = "PROSPECTIVE_FALSIFIED"

    return {
        "id":                  obs["id"],
        "name":                obs["name"],
        "sector":              obs.get("sector"),
        "status":              status,
        "bundles":             bundles_resolved,
        "extract_per_bundle":  extract_per_bundle,
        "extract_aggregated":  extracted,
        "prediction_check":    pred_result,
    }
