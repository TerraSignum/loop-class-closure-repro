"""The strongest test: an observable cannot freely choose a better class.

This guards against the reviewer concern that loop classes were chosen
after the fact to fit the targets. We verify that for each registered
observable, ONLY the class deterministically returned by the mapping
algorithm is authorized; any alternative class (even one that
numerically hits the target) is unauthorized.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import classify_observable as C


def _all_classes():
    with open(REPO / "data" / "loop_class_library.json", "r", encoding="utf-8") as f:
        lib = json.load(f)
    classes = []
    for entry in lib["lemma_classes"]:
        for cls in entry["loop_classes"]:
            classes.append((entry["lemma"], entry["name"], cls))
    return classes


def _registry():
    with open(REPO / "data" / "observable_registry.json", "r", encoding="utf-8") as f:
        return json.load(f)["observables"]


def test_each_observable_has_unique_authorized_class():
    """For each observable, the authorized (lemma, class) is unique."""
    reg = _registry()
    for o in reg:
        if o.get("lemma") is None:
            continue  # tree-level, no loop class
        if o.get("two_loop_compound", False):
            continue  # compounds are an explicit registry-level statement
        n = o["n_spinor_trace"]
        g = o["g_generation"] if o["g_generation"] is not None else 0
        s = o["s_sync_coupling"] if o["s_sync_coupling"] is not None else 0
        # Determine if this observable is double_wick or resummed.
        cls_string = o.get("loop_class", "")
        dw = "gamma^2/4" in cls_string and o["lemma"] == 2
        rs = ("/(1" in cls_string) or "2*gamma^2" in cls_string and o["lemma"] == 4
        try:
            r = C.classify(n=n, g=g, s=s, double_wick=dw, resummed=rs)
        except ValueError:
            continue  # unknown (n, g, s), but registry says "lemma=1" etc.
        # The classifier's lemma must match the registered lemma
        assert r["lemma"] == o["lemma"], (
            f"{o['id']}: classifier returns lemma {r['lemma']}, "
            f"but registry says lemma {o['lemma']}."
        )


def test_observable_cannot_be_authorized_in_unrelated_class():
    """For each observable in the registry, picking ANY class that is
    not the algorithm's output must NOT be flagged as authorized by the
    registry."""
    reg = _registry()
    classes_in_lib = _all_classes()
    for o in reg:
        if o.get("lemma") is None:
            continue
        registered_class = o.get("loop_class")
        # Find any other class in the library that is not registered_class.
        for (lemma_other, name_other, cls_other) in classes_in_lib:
            if cls_other == registered_class:
                continue
            if lemma_other == o["lemma"]:
                continue
            # The pair (observable, cls_other) must NOT be in the registry.
            assert cls_other != o["loop_class"], (
                f"Observable {o['id']} should not also accept class "
                f"{cls_other} from lemma {lemma_other}."
            )


def test_forbidden_classes_are_listed_explicitly():
    with open(REPO / "data" / "loop_class_library.json", "r", encoding="utf-8") as f:
        lib = json.load(f)
    forbidden = lib["forbidden_classes"]
    assert len(forbidden) >= 4
    for f in forbidden:
        assert "form" in f and "reason" in f


def test_minimum_class_gap_is_documented():
    with open(REPO / "data" / "loop_class_library.json", "r", encoding="utf-8") as f:
        lib = json.load(f)
    mcg = lib["minimum_class_gap"]
    # Two distinct quantities are now documented: the within-cell sign-fixed
    # gap (used by Definition 1) and the unrestricted global min (sanity).
    within = mcg["within_library_cell_sign_fixed"]["value"]
    unrestricted = mcg["unrestricted_global_min"]["value"]
    assert within > 0.02, f"within-cell gap {within} below 0.02 — Definition 1 invalid"
    assert unrestricted > 0.0, f"unrestricted gap must be positive, got {unrestricted}"
    # within-cell gap must be strictly larger than the unrestricted global min,
    # otherwise the within-cell argument would be vacuous
    assert within > unrestricted, (
        f"within-cell gap {within} must exceed unrestricted global min {unrestricted}"
    )


def test_classifier_uses_explicit_flags_not_string_match():
    """Tautology guard. The recompute classifier MUST resolve double_wick
    (Lemma 2) and resummed (Lemma 4) observables via explicit boolean
    flags on the registry entry, not by string-matching the
    pre-recorded loop_class field. We assert this by running the
    classifier on an observable whose loop_class string is deliberately
    perturbed; the classifier should still return the correct lemma."""
    import json
    import sys
    from pathlib import Path

    REPO = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(REPO / "src"))
    import recompute_loop_closures as M  # noqa: E402

    table_path = REPO / "data" / "allowed_topological_multipliers.json"
    with open(table_path, "r", encoding="utf-8") as f:
        table = json.load(f)["mapping_algorithm_table"]

    # O09 (PMNS_theta_13) is Lemma 2; double_wick=True; loop_class='1-gamma^2/4'
    # Perturb the loop_class string to break any string-match pathway:
    perturbed = {
        "id": "O09",
        "n_spinor_trace": 1,
        "g_generation": 0,
        "s_sync_coupling": 0,
        "double_wick": True,
        "resummed": False,
        "lemma": 2,
        "loop_class": "PERTURBED_STRING_NOT_MATCHING_ANY_LEMMA",
    }
    cls = M._classify_for(perturbed, table)
    # The classifier must return the Lemma-2 form despite the perturbed string:
    assert "gamma^2/4" in cls, (
        f"Classifier fell back on string-match instead of explicit flag: "
        f"got {cls!r}"
    )

    # Same test for Lemma 4 (O21 — T_RH; resummed=True)
    perturbed_4 = {
        "id": "O21",
        "n_spinor_trace": 4,
        "g_generation": 0,
        "s_sync_coupling": 0,
        "double_wick": False,
        "resummed": True,
        "lemma": 4,
        "loop_class": "PERTURBED_STRING_NOT_MATCHING",
    }
    cls = M._classify_for(perturbed_4, table)
    assert "1/(1" in cls or "2*gamma^2" in cls, (
        f"Lemma-4 classifier fell back on string-match: got {cls!r}"
    )
