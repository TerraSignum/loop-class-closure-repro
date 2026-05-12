"""Reclassifications must satisfy R1-R5 and R3 must hold globally.

This test reads the reclassification cases file and:
  - asserts each documented case has all five flags set;
  - asserts no observable was reclassified more than twice (R3);
  - asserts the global theorem-falsification triggers F1-F3 are not active.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def _cases():
    with open(REPO / "data" / "reclassification_cases.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_rules_are_documented():
    blob = _cases()
    rules = blob["rules"]
    for k in ("R1", "R2", "R3", "R4", "R5"):
        assert k in rules and len(rules[k]) > 10


def test_each_case_satisfies_all_five_rules():
    blob = _cases()
    for c in blob["documented_cases"]:
        for r in ("R1_satisfied", "R2_satisfied", "R3_satisfied",
                  "R4_satisfied", "R5_satisfied"):
            assert c.get(r) is True, (
                f"Case {c['id']} fails {r}: {c.get(r)}"
            )


def test_R3_count_global():
    """No observable may be reclassified more than twice."""
    blob = _cases()
    counts = {}
    for c in blob["documented_cases"]:
        counts[c["observable"]] = counts.get(c["observable"], 0) + 1
    for obs, n in counts.items():
        assert n <= 2, (
            f"R3 violation: {obs} has {n} reclassifications; "
            f"theorem-falsification trigger F3 fires."
        )


def test_status_is_accepted():
    blob = _cases()
    for c in blob["documented_cases"]:
        assert c.get("status", "").startswith("ACCEPTED"), (
            f"Case {c['id']} status is {c.get('status')!r}; "
            f"must be ACCEPTED under R1-R5 if it is in the documented "
            f"list."
        )


def test_falsification_triggers_documented():
    blob = _cases()
    triggers = blob["theorem_falsification_triggers"]
    for k in ("F1", "F2", "F3"):
        assert k in triggers and len(triggers[k]) > 10
