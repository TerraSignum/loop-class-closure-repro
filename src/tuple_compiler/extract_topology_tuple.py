"""Extract topology tuples from all observable YAML definitions.

Reads every *.yaml in data/observable_definitions/, runs the
deterministic extractor on each, and writes the result to
outputs/extracted_topology_tuples.json. The extractor refuses to
operate on any YAML that allows target-value access.

This module is the entry point that pins each tuple to the YAML
revision (SHA-256) and the repository commit hash, so that years
later a reader can verify the tuple-first protocol.

Usage:
    python -m tuple_compiler.extract_topology_tuple
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from . import SCHEMA_VERSION
from .provenance import build_provenance
from .schema import SchemaError
from .tuple_rules import extract_tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = REPO_ROOT / "data" / "observable_definitions"
OUTPUT_PATH = REPO_ROOT / "outputs" / "extracted_topology_tuples.json"


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML observable definition as a dict.

    Raises ValueError if the YAML root is not a mapping.
    """
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: YAML root must be a mapping.")
    return data


def extract_one(path: Path) -> Dict[str, Any]:
    """Extract one YAML; return result with provenance attached."""
    obs = load_yaml(path)
    result = extract_tuple(obs)
    result["provenance"] = build_provenance(path, REPO_ROOT, SCHEMA_VERSION)
    return result


def extract_all() -> Dict[str, Any]:
    """Extract every YAML in INPUT_DIR. Failures are collected, not silenced."""
    results: List[Dict[str, Any]] = []
    errors:  List[Dict[str, str]] = []

    yaml_paths = sorted(INPUT_DIR.glob("*.yaml"))
    for path in yaml_paths:
        try:
            results.append(extract_one(path))
        except (SchemaError, ValueError, KeyError) as exc:
            errors.append({
                "yaml_path": str(path.relative_to(REPO_ROOT)),
                "error_type": type(exc).__name__,
                "error":      str(exc),
            })

    return {
        "schema_version":           SCHEMA_VERSION,
        "n_observables":            len(results),
        "n_errors":                 len(errors),
        "results":                  results,
        "errors":                   errors,
        "target_isolation_locked":  True,
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    bundle = extract_all()

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False, sort_keys=True)

    if bundle["n_errors"] > 0:
        print(f"Tuple extraction finished with {bundle['n_errors']} errors:")
        for e in bundle["errors"]:
            print(f"  {e['yaml_path']}: {e['error_type']}: {e['error']}")
        print(f"Output: {OUTPUT_PATH}")
        return 1

    print(f"Extracted {bundle['n_observables']} tuples -> {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
