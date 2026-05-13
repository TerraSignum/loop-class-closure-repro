"""Shared pytest fixtures for the tuple compiler tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def yaml_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "observable_definitions"


@pytest.fixture(scope="session")
def loop_map_path(repo_root: Path) -> Path:
    return repo_root / "data" / "loop_class_map.json"
