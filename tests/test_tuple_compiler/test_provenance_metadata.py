"""Provenance must hash-pin each extracted tuple to its YAML revision."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from tuple_compiler import SCHEMA_VERSION
from tuple_compiler.extract_topology_tuple import extract_one
from tuple_compiler.provenance import build_provenance, iso_now, yaml_sha256


ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def test_iso_now_format():
    assert ISO_RE.match(iso_now()), iso_now()


def test_yaml_sha256_matches_disk(yaml_dir: Path):
    """yaml_sha256 must match recomputing sha256 over the file's bytes."""
    yamls = list(yaml_dir.glob("*.yaml"))
    assert yamls, "Expected at least one YAML in observable_definitions/"
    for y in yamls:
        computed = yaml_sha256(y)
        expected = hashlib.sha256(y.read_bytes()).hexdigest()
        assert SHA256_RE.match(computed)
        assert computed == expected


def test_build_provenance_full_fields(repo_root: Path, yaml_dir: Path):
    y = next(yaml_dir.glob("*.yaml"))
    prov = build_provenance(y, repo_root, SCHEMA_VERSION)
    for k in ("yaml_sha256", "yaml_path", "extractor_commit",
              "schema_version", "extracted_at"):
        assert k in prov, f"Missing provenance field: {k}"
    assert SHA256_RE.match(prov["yaml_sha256"])
    assert prov["schema_version"] == SCHEMA_VERSION
    assert ISO_RE.match(prov["extracted_at"])


def test_extract_one_attaches_provenance(yaml_dir: Path):
    y = next(yaml_dir.glob("*.yaml"))
    result = extract_one(y)
    assert "provenance" in result
    assert result["provenance"]["schema_version"] == SCHEMA_VERSION
    assert SHA256_RE.match(result["provenance"]["yaml_sha256"])


def test_yaml_sha256_changes_with_content(tmp_path: Path):
    """Tampering with a YAML changes its sha256 (sanity)."""
    y = tmp_path / "x.yaml"
    y.write_text("id: A\n", encoding="utf-8")
    h1 = yaml_sha256(y)
    y.write_text("id: B\n", encoding="utf-8")
    h2 = yaml_sha256(y)
    assert h1 != h2
