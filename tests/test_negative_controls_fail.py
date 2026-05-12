"""Negative controls must NOT receive a closing loop class.

Falsification of the algorithm: if any negative-control observable is
assigned a class in the loop library and predicts a value within the
PRECISE_2.5 cut of its experimental target, the algorithm falls.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def _negative_controls():
    with open(REPO / "data" / "negative_controls.json", "r", encoding="utf-8") as f:
        return json.load(f)["controls"]


def _registry_names():
    with open(REPO / "data" / "observable_registry.json", "r", encoding="utf-8") as f:
        return {o["name"] for o in json.load(f)["observables"]}


def test_negative_controls_not_in_registry():
    nc = _negative_controls()
    reg_names = _registry_names()
    for c in nc:
        assert c["name"] not in reg_names, (
            f"Negative control {c['name']} appears in the closure "
            f"registry; this falsifies the negative-control framework."
        )


def test_at_least_seven_negative_controls():
    nc = _negative_controls()
    assert len(nc) >= 7


def test_each_negative_control_has_rationale():
    """Each control must justify its rejection (rejection_reason + outcome)."""
    nc = _negative_controls()
    for c in nc:
        assert c.get("rejection_reason"), (
            f"{c['id']} has no rejection_reason: {c}"
        )
        assert c.get("expected_outcome") == "NO_CLAIM", c


def test_negative_control_categories():
    """Sanity-check that we cover all the major category types."""
    nc = _negative_controls()
    cats = {c["category"] for c in nc}
    expected_categories = {
        "Quark/lepton mass ratio",
        "Coefficient value",
        "Quantum-gravity",
        "Beyond-program",
        "Neutrino mass",
    }
    overlap = cats.intersection(expected_categories)
    assert len(overlap) >= 4, f"only got categories {cats}"


def test_subclass_partition_delegated_vs_genuine_out():
    """Each control must declare a subclass: DELEGATED or GENUINE_OUT.

    DELEGATED = predicted by a companion sector outside L; the algorithm
    delegates by returning NO_CLAIM.
    GENUINE_OUT = outside the program's claim domain G_claim^auth.
    Both must reject in the algorithm; the partition documents WHY.
    """
    nc = _negative_controls()
    valid = {"DELEGATED", "GENUINE_OUT"}
    for c in nc:
        sc = c.get("subclass")
        assert sc in valid, (
            f"{c['id']} has subclass {sc!r}, must be one of {valid}"
        )
    # At least one of each, otherwise the partition is vacuous.
    delegated = [c for c in nc if c.get("subclass") == "DELEGATED"]
    genuine = [c for c in nc if c.get("subclass") == "GENUINE_OUT"]
    assert len(delegated) >= 1, "no DELEGATED controls registered"
    assert len(genuine) >= 1, "no GENUINE_OUT controls registered"


def test_delegated_controls_name_companion_sector():
    """DELEGATED controls must point to the sector that does close them."""
    nc = _negative_controls()
    for c in nc:
        if c.get("subclass") == "DELEGATED":
            assert c.get("delegated_to"), (
                f"{c['id']} is DELEGATED but missing 'delegated_to' field"
            )
            assert c.get("delegated_status"), (
                f"{c['id']} is DELEGATED but missing 'delegated_status' field"
            )
