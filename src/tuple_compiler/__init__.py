"""Tuple compiler for P3 observable definitions.

Compiles a formal YAML observable definition into a structural
topology tuple (n, g, s, w, r), then matches the tuple against
the loop-class library. The extractor refuses to operate on any
YAML that allows target-value access; this makes the
"tuple-first before target comparison" methodology
machine-checkable.
"""
from __future__ import annotations

__version__ = "0.1.0"
SCHEMA_VERSION = "tuple-compiler-v0.1"
