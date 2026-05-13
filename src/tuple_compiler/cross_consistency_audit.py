"""Cross-consistency audit: compiler prediction vs corpus closure state.

The tuple compiler reproduces each observable_registry entry's
`loop_class` field by extracting a YAML and matching it against the
loop-class library. But the registry has *evolved*: six entries now
carry a `closure_form_2026_05_10` field (or `stand_alone_form: true`)
that documents a different closure identity than the original
`loop_class`. The compiler is **silent** about this evolution; it
just reproduces the `loop_class` field.

This audit surfaces the dual-closure state and, where possible,
numerically evaluates both forms to report which matches the anchor.
It is the honest follow-up to Phases 1-3:

- It does NOT pick a side or silently update the registry.
- It does NOT shoehorn structural identities into loop-class YAMLs.
- It DOES enumerate the gap explicitly so corpus owners can resolve it.

It also checks that companion JSONs (neutrino_sector_closure,
ckm_closure, ...) describing the same observables agree with the
registry; disagreements are recorded.

Output: outputs/cross_consistency_audit.json

Usage:
    python -m tuple_compiler.cross_consistency_audit
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "data" / "observable_registry.json"
PREDICTIONS_PATH = REPO_ROOT / "outputs" / "loop_class_predictions.json"
OUTPUT_PATH = REPO_ROOT / "outputs" / "cross_consistency_audit.json"


# Numerical values of the System-R rationals (frozen at the corpus' canonical values).
SYSTEM_R = {
    "gamma":          0.1,
    "alpha_xi":       0.9,
    "beta_pi":        0.9375,
    "eps_sync2":      0.05,
    "eps_sync^2":     0.05,
    "D_Omega":        0.8375,
    "N_gen":          3.0,
    "d":              4.0,
    "pi":             3.141592653589793,
}


def _safe_eval(expr: str) -> Optional[float]:
    """Numerically evaluate a System-R rational expression.

    Refuses to eval anything that isn't a sanitised arithmetic
    expression in the known symbol set. Returns None if the
    expression doesn't fit the safe subset.
    """
    # Strip leading/trailing whitespace and any anchor/comment after a space-paren
    cleaned = expr.strip()
    # Remove anchor-comment style "= value (note)" suffixes
    cleaned = re.split(r"\s+\(", cleaned, maxsplit=1)[0]
    cleaned = cleaned.replace("**", "**").replace("^", "**")
    # Only allow alnum, underscore, ./+-*()/whitespace
    if not re.fullmatch(r"[A-Za-z0-9_\.\+\-\*/\(\)\s]+", cleaned):
        return None
    try:
        return float(eval(cleaned, {"__builtins__": {}}, SYSTEM_R))
    except (NameError, SyntaxError, ZeroDivisionError, TypeError):
        return None


def _rel_err_pct(predicted: float, anchor: float) -> Optional[float]:
    if anchor == 0:
        return None
    return abs(predicted - anchor) / abs(anchor) * 100.0


def _load_registry() -> Dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_predictions() -> Dict[str, Dict[str, Any]]:
    if not PREDICTIONS_PATH.exists():
        return {}
    bundle = json.loads(PREDICTIONS_PATH.read_text(encoding="utf-8"))
    return {p["id"]: p for p in bundle.get("predictions", [])}


def _audit_dual_closure(o: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """If observable o has both loop_class and an alternative closure form,
    record the gap. Returns None if there's no dual state."""
    has_dual = ("closure_form_2026_05_10" in o
                or o.get("stand_alone_form") is True)
    if not has_dual:
        return None
    return {
        "id":   o["id"],
        "name": o["name"],
        "loop_class":                o.get("loop_class"),
        "tree_formula":              o.get("tree_formula"),
        "closure_form_2026_05_10":   o.get("closure_form_2026_05_10"),
        "stand_alone_form":          bool(o.get("stand_alone_form", False)),
        "rational_form":             o.get("rational_form"),
        "target":                    o.get("target"),
        "target_units":              o.get("target_units"),
        "tier_after_loop":           o.get("tier_after_loop"),
        "structural_origin":         o.get("structural_origin"),
    }


def _evaluate_alternative_form(expr: str, anchor: Optional[float]
                                ) -> Dict[str, Any]:
    """Try to numerically eval an alternative closure form string."""
    out: Dict[str, Any] = {"expression": expr}
    val = _safe_eval(expr)
    out["numerical_value"]   = val
    out["evaluation_status"] = "evaluated" if val is not None else "non_evaluatable"
    if val is not None and anchor is not None:
        try:
            anchor_f = float(anchor)
            out["anchor"]              = anchor_f
            out["abs_diff_vs_anchor"]  = abs(val - anchor_f)
            err = _rel_err_pct(val, anchor_f)
            out["rel_err_pct_vs_anchor"] = err
        except (TypeError, ValueError):
            pass
    return out


def _try_extract_rational_value(rational: str) -> Optional[float]:
    """Parse a string like '49/160' or '11/500' or '23/40' or '-1/200'."""
    if rational is None:
        return None
    m = re.fullmatch(r"\s*(-?\d+)\s*/\s*(\d+)\s*", rational)
    if m:
        return float(m.group(1)) / float(m.group(2))
    return _safe_eval(rational)


def _audit_companion_disagreement(o: Dict[str, Any],
                                  companion: Dict[str, Any]
                                  ) -> Optional[Dict[str, Any]]:
    """If a companion JSON describes the same observable with a different
    structural identity, record the disagreement."""
    if not companion:
        return None
    reg_loop = o.get("loop_class")
    comp_form = (companion.get("structural_identity")
                 or companion.get("loop_class"))
    if comp_form is None or reg_loop is None:
        return None
    # The simple heuristic: if the companion's structural identity does not
    # contain the registry's loop_class substring (after whitespace strip),
    # we record a candidate disagreement. This is intentionally imprecise --
    # the audit's job is to surface candidates, not to adjudicate.
    a = "".join(reg_loop.split())
    b = "".join(comp_form.split())
    if a in b or b in a:
        return None  # The companion includes the loop_class as a substring.
    return {
        "registry_loop_class":       reg_loop,
        "companion_form":            comp_form,
        "companion_source":          companion.get("_source"),
    }


def _load_companion_observables() -> Dict[str, Dict[str, Any]]:
    """Pull observable entries from companion closure JSONs."""
    by_canonical_name: Dict[str, Dict[str, Any]] = {}

    # neutrino_sector_closure.json
    p = REPO_ROOT / "data" / "neutrino_sector_closure.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d.get("closures", []):
            cid = c.get("id")
            if cid:
                c2 = dict(c)
                c2["_source"] = "neutrino_sector_closure.json"
                by_canonical_name[cid] = c2

    # ckm_closure.json
    p = REPO_ROOT / "data" / "ckm_closure.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        mags = d.get("ckm_magnitudes_closure", {})
        for k, v in mags.items():
            if isinstance(v, dict) and "structural_identity" in v:
                v2 = dict(v)
                v2["_source"] = "ckm_closure.json.ckm_magnitudes_closure"
                v2.setdefault("id", f"CKM_{k}")
                by_canonical_name[v2["id"]] = v2

    return by_canonical_name


# Map observable_registry IDs to companion JSON IDs.
COMPANION_ID_MAP = {
    "O09": "PMNS_theta_13",
    "O10": "PMNS_theta_12",
    "O11": "PMNS_theta_23",
    "O13": "CKM_V_us",
    "O14": "CKM_V_cb",
}

# Phase-5: explicit alternative-form YAML ID per dual-state registry entry.
# When a Phase-5 YAML evaluates the closure_form_2026_05_10 form to its
# exact rational, the audit records that pairing so the dual state is
# *resolved* in the sense that both forms are now machine-verifiable.
ALT_FORM_YAML_BY_REGISTRY_ID = {
    "O09": "HK-09",
    "O10": "HK-10",
    "O11": "HK-11",
    "O12": "HK-12",
    "O13": "HJ-13",
    "O14": "HQ-14",
}


def _attach_alt_form_evaluation(o: Dict[str, Any],
                                 dual: Dict[str, Any]) -> None:
    """Numeric + sympy evaluation of the closure_form_2026_05_10 form."""
    alt = o.get("closure_form_2026_05_10", "")
    evaluation = _evaluate_alternative_form(alt, o.get("target"))
    rat = o.get("rational_form")
    if rat:
        evaluation["rational_form_numerical"] = _try_extract_rational_value(rat)
    dual["alternative_form_evaluation"] = evaluation


def _attach_compiler_prediction(o: Dict[str, Any],
                                 predictions: Dict[str, Dict[str, Any]],
                                 dual: Dict[str, Any]) -> None:
    """Record what the loop-class compiler currently emits for this id."""
    pred = predictions.get(o["id"])
    if pred and "prediction" in pred:
        dual["compiler_prediction"] = {
            "lemma_id":     pred["prediction"]["lemma_id"],
            "factor":       pred["prediction"]["factor"],
            "closure_kind": pred.get("closure_kind"),
        }


def _attach_phase5_resolution(o: Dict[str, Any],
                               predictions: Dict[str, Dict[str, Any]],
                               dual: Dict[str, Any]) -> None:
    """If a Phase-5 alternative YAML exists and evaluates EXACTLY, the
    dual state is resolved: both forms are machine-verifiable."""
    alt_yaml_id = ALT_FORM_YAML_BY_REGISTRY_ID.get(o["id"])
    if alt_yaml_id is None:
        dual["phase5_resolution"] = {"status": "NO_ALTERNATIVE_YAML"}
        return

    alt_pred = predictions.get(alt_yaml_id)
    if alt_pred is None:
        dual["phase5_resolution"] = {
            "status":            "ALT_YAML_DECLARED_BUT_NOT_EXTRACTED",
            "expected_yaml_id":  alt_yaml_id,
        }
        return

    evaluation = alt_pred.get("prediction", {}).get("evaluation")
    if not evaluation or not evaluation.get("exact_match"):
        dual["phase5_resolution"] = {
            "status":            "ALT_YAML_DID_NOT_EVALUATE_EXACTLY",
            "yaml_id":           alt_yaml_id,
        }
        return

    dual["phase5_resolution"] = {
        "status":               "RESOLVED",
        "yaml_id":              alt_yaml_id,
        "structural_formula":   evaluation["formula"],
        "structural_rational":  evaluation["claimed_rational"],
        "is_pure_rational":     evaluation["is_pure_rational"],
    }


def _audit_dual_state_for(o: Dict[str, Any],
                           predictions: Dict[str, Dict[str, Any]]
                           ) -> Optional[Dict[str, Any]]:
    """Build the full dual-state record for one registry observable."""
    dual = _audit_dual_closure(o)
    if dual is None:
        return None
    _attach_alt_form_evaluation(o, dual)
    _attach_compiler_prediction(o, predictions, dual)
    _attach_phase5_resolution(o, predictions, dual)
    return dual


def _audit_disagreement_for(o: Dict[str, Any],
                             companions: Dict[str, Dict[str, Any]]
                             ) -> Optional[Dict[str, Any]]:
    """Build the disagreement record for one registry observable, if any."""
    comp_id = COMPANION_ID_MAP.get(o["id"])
    if comp_id is None or comp_id not in companions:
        return None
    disagreement = _audit_companion_disagreement(o, companions[comp_id])
    if disagreement is None:
        return None
    disagreement["observable_id"]   = o["id"]
    disagreement["observable_name"] = o["name"]
    return disagreement


def run_audit() -> Dict[str, Any]:
    registry    = _load_registry()
    predictions = _load_predictions()
    companions  = _load_companion_observables()

    dual_state_observables: List[Dict[str, Any]] = []
    companion_disagreements: List[Dict[str, Any]] = []

    for o in registry["observables"]:
        dual = _audit_dual_state_for(o, predictions)
        if dual is not None:
            dual_state_observables.append(dual)
        disagreement = _audit_disagreement_for(o, companions)
        if disagreement is not None:
            companion_disagreements.append(disagreement)

    n_resolved = sum(
        1 for d in dual_state_observables
        if d.get("phase5_resolution", {}).get("status") == "RESOLVED"
    )

    return {
        "schema_version":            "cross-consistency-audit-v0.2",
        "registry_size":             len(registry["observables"]),
        "n_dual_state_observables":  len(dual_state_observables),
        "n_dual_state_resolved_by_phase5": n_resolved,
        "n_companion_disagreements": len(companion_disagreements),
        "dual_state_observables":    dual_state_observables,
        "companion_disagreements":   companion_disagreements,
        "note": (
            "Honest gap report: each dual-state entry shows the original "
            "loop_class field (which the loop-class compiler reproduces) "
            "alongside the closure_form_2026_05_10 alternative. The "
            "Phase-5 structural evaluator (sympy-based, exact Fraction "
            "arithmetic in the System-R rationals) is applied to each "
            "alternative form whose YAML has been declared in "
            "data/observable_definitions/. 'RESOLVED' means the "
            "alternative form was evaluated EXACTLY against its claimed "
            "rational and matched without tolerance. Companion-"
            "disagreements list cases where a companion closure JSON "
            "describes the same observable with a structural identity "
            "that does not embed the registry's loop_class as a "
            "substring. The audit does NOT pick a canonical form; it "
            "verifies that BOTH forms are machine-checkable and surfaces "
            "the dual state for explicit corpus consolidation."
        ),
    }


def main() -> int:
    bundle = run_audit()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(
        f"Cross-consistency audit: "
        f"{bundle['n_dual_state_observables']} dual-state, "
        f"{bundle['n_companion_disagreements']} companion-disagreements "
        f"-> {OUTPUT_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
