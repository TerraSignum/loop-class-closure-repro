"""Hash-pinning provenance for the tuple compiler.

Each extracted tuple records:
- yaml_sha256: SHA-256 of the YAML file's bytes at extraction time
- extractor_commit: git HEAD commit of the repository
- schema_version: enum-locked schema identifier
- extracted_at: ISO-8601 timestamp

Together these let a reader years later verify that the tuple was
extracted from a specific YAML revision, before any target
comparison was performed.
"""
from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def yaml_sha256(path: Path) -> str:
    """Hex SHA-256 of the YAML file's bytes."""
    with path.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def git_commit(repo_root: Path) -> str:
    """Current git HEAD commit hash, or 'NO_GIT' if not available."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "NO_GIT"
    if out.returncode != 0:
        return "NO_GIT"
    return out.stdout.strip()


def iso_now() -> str:
    """UTC timestamp in ISO-8601 with seconds precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_provenance(
    yaml_path: Path, repo_root: Path, schema_version: str
) -> Dict[str, str]:
    return {
        "yaml_sha256":      yaml_sha256(yaml_path),
        "yaml_path":        str(yaml_path.relative_to(repo_root)),
        "extractor_commit": git_commit(repo_root),
        "schema_version":   schema_version,
        "extracted_at":     iso_now(),
    }
