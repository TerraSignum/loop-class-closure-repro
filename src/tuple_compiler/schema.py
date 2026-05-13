"""Schema validation for observable YAML definitions.

The schema is intentionally narrow: every component of the tuple
(n, g, s, w, r) has a closed enum domain, and the YAML must
explicitly declare target-isolation via the anchors block. Any
deviation from the enum or any attempt to allow target access
raises an error -- there is no "best guess" path.
"""
from __future__ import annotations

from typing import Any, Dict


N_DOMAIN = {0, 1, 2, 4}
G_DOMAIN_SUPPORT = {"none", "full_generation", "sub_generation"}
G_SYMBOL_BY_SUPPORT = {
    "none":              "0",
    "full_generation":   "1/N_gen",
    "sub_generation":    "1/(2*N_gen)",
}
S_DOMAIN_CHANNEL = {"0", "eps^2", "eps^2 pure", "eps^2 * gamma"}
CLOSURE_KIND_DOMAIN = {"tree", "single_loop", "loop_compound", "structural"}

# Required for tree / single_loop closures.
REQUIRED_FLAT = ("id", "name", "sector", "operator", "generation",
                 "sync", "parity", "anchors", "schema_version")

# Required for loop_compound closures.
REQUIRED_COMPOUND = ("id", "name", "sector", "factors", "anchors",
                     "schema_version")

# Required for structural closures.
REQUIRED_STRUCTURAL = ("id", "name", "sector", "structural_formula",
                       "structural_rational", "anchors", "schema_version")


class SchemaError(ValueError):
    """Raised when an observable YAML violates the schema."""


def closure_kind_of(obs: Dict[str, Any]) -> str:
    """Return the closure_kind, defaulting to 'single_loop' for backward
    compatibility with Phase-1/2 YAMLs that omit the field."""
    kind = obs.get("closure_kind", "single_loop")
    if kind not in CLOSURE_KIND_DOMAIN:
        raise SchemaError(
            f"{obs.get('id', '<unknown>')}: closure_kind={kind!r} not in "
            f"{sorted(CLOSURE_KIND_DOMAIN)}."
        )
    return kind


def _validate_top_level(obs: Dict[str, Any], oid: str,
                        required: tuple) -> None:
    for field in required:
        if field not in obs:
            raise SchemaError(f"{oid}: missing required field '{field}'.")


def _validate_anchors(anchors: Dict[str, Any], oid: str) -> None:
    if anchors.get("target_value_allowed", True) is not False:
        raise SchemaError(
            f"{oid}: anchors.target_value_allowed must be literally false."
        )
    if anchors.get("external_target_used_in_tuple", True) is not False:
        raise SchemaError(
            f"{oid}: anchors.external_target_used_in_tuple must be literally false."
        )


def _validate_operator(op: Dict[str, Any], oid: str) -> None:
    n = op.get("spinor_trace_count")
    if n not in N_DOMAIN:
        raise SchemaError(
            f"{oid}: operator.spinor_trace_count={n} not in N_DOMAIN={sorted(N_DOMAIN)}."
        )
    for field, descr in (
        ("double_wick",  ""),
        ("resummed",     ""),
        ("loop_dressed", " (false for tree-level, true for loop-dressed)"),
    ):
        if not isinstance(op.get(field), bool):
            raise SchemaError(
                f"{oid}: operator.{field} must be a boolean{descr}."
            )
    # resummation_inverse is required iff resummed=True; otherwise it must
    # be absent or False (it only makes sense for the L4 inverse variants).
    res_inv = op.get("resummation_inverse", False)
    if not isinstance(res_inv, bool):
        raise SchemaError(
            f"{oid}: operator.resummation_inverse must be a boolean."
        )
    if res_inv and not op["resummed"]:
        raise SchemaError(
            f"{oid}: operator.resummation_inverse=true requires "
            f"operator.resummed=true."
        )


def _validate_generation(gen: Dict[str, Any], oid: str) -> None:
    support = gen.get("support")
    if support not in G_DOMAIN_SUPPORT:
        raise SchemaError(
            f"{oid}: generation.support={support!r} not in "
            f"{sorted(G_DOMAIN_SUPPORT)}."
        )
    if support == "none":
        return
    expected_symbol = G_SYMBOL_BY_SUPPORT[support]
    symbol = gen.get("symbol")
    if symbol != expected_symbol:
        raise SchemaError(
            f"{oid}: generation.symbol={symbol!r} does not match "
            f"support={support!r} (expected {expected_symbol!r})."
        )


def _validate_sync(sync: Dict[str, Any], oid: str) -> None:
    channel = sync.get("channel")
    if channel not in S_DOMAIN_CHANNEL:
        raise SchemaError(
            f"{oid}: sync.channel={channel!r} not in "
            f"{sorted(S_DOMAIN_CHANNEL)}."
        )


def _validate_parity(parity: Dict[str, Any], oid: str) -> None:
    sign = parity.get("expected_sign")
    # Reject booleans explicitly: True == 1 and False == 0 in Python.
    if isinstance(sign, bool) or sign not in (+1, -1):
        raise SchemaError(
            f"{oid}: parity.expected_sign={sign!r} must be the integer +1 or -1."
        )


def _validate_flat(obs: Dict[str, Any], oid: str) -> None:
    """Validate the tree / single_loop flat shape."""
    _validate_top_level(obs, oid, REQUIRED_FLAT)
    _validate_anchors(obs["anchors"], oid)
    _validate_operator(obs["operator"], oid)
    _validate_generation(obs["generation"], oid)
    _validate_sync(obs["sync"], oid)
    _validate_parity(obs["parity"], oid)


def _validate_factor(factor: Dict[str, Any], oid: str, idx: int) -> None:
    """Validate one entry of a compound's factors[] array.

    Each factor is a compact record with fields n, g_support, g_symbol
    (optional iff g_support='none'), s_channel, w, r, sign.
    """
    where = f"{oid}.factors[{idx}]"
    n = factor.get("n")
    if n not in N_DOMAIN:
        raise SchemaError(f"{where}.n={n} not in N_DOMAIN={sorted(N_DOMAIN)}.")
    for field in ("w", "r"):
        if not isinstance(factor.get(field), bool):
            raise SchemaError(f"{where}.{field} must be a boolean.")
    g_support = factor.get("g_support")
    if g_support not in G_DOMAIN_SUPPORT:
        raise SchemaError(
            f"{where}.g_support={g_support!r} not in "
            f"{sorted(G_DOMAIN_SUPPORT)}."
        )
    if g_support != "none":
        expected_symbol = G_SYMBOL_BY_SUPPORT[g_support]
        if factor.get("g_symbol") != expected_symbol:
            raise SchemaError(
                f"{where}.g_symbol does not match g_support={g_support!r} "
                f"(expected {expected_symbol!r})."
            )
    if factor.get("s_channel") not in S_DOMAIN_CHANNEL:
        raise SchemaError(
            f"{where}.s_channel={factor.get('s_channel')!r} not in "
            f"{sorted(S_DOMAIN_CHANNEL)}."
        )
    sign = factor.get("sign")
    if isinstance(sign, bool) or sign not in (+1, -1):
        raise SchemaError(
            f"{where}.sign={sign!r} must be the integer +1 or -1."
        )


def _validate_compound(obs: Dict[str, Any], oid: str) -> None:
    """Validate the loop_compound shape: factors[] of length >= 2."""
    _validate_top_level(obs, oid, REQUIRED_COMPOUND)
    _validate_anchors(obs["anchors"], oid)
    factors = obs["factors"]
    if not isinstance(factors, list) or len(factors) < 2:
        raise SchemaError(
            f"{oid}: factors must be a list of length >= 2 "
            f"(got {type(factors).__name__} of length "
            f"{len(factors) if isinstance(factors, list) else 'n/a'})."
        )
    for idx, factor in enumerate(factors):
        _validate_factor(factor, oid, idx)


def _validate_structural(obs: Dict[str, Any], oid: str) -> None:
    """Validate the structural shape: direct algebraic identity."""
    _validate_top_level(obs, oid, REQUIRED_STRUCTURAL)
    _validate_anchors(obs["anchors"], oid)
    if not isinstance(obs.get("structural_formula"), str):
        raise SchemaError(f"{oid}: structural_formula must be a string.")
    if not isinstance(obs.get("structural_rational"), str):
        raise SchemaError(f"{oid}: structural_rational must be a string.")


def validate(obs: Dict[str, Any]) -> None:
    """Raise SchemaError if obs does not conform.

    Dispatches on `closure_kind` (default 'single_loop' for backward
    compatibility with Phase-1/2 YAMLs):
    - 'tree' / 'single_loop' -> flat shape with operator/generation/sync/parity
    - 'loop_compound'        -> factors[] of length >= 2
    - 'structural'           -> structural_formula + structural_rational
    """
    oid = obs.get("id", "<unknown>")
    kind = closure_kind_of(obs)
    if kind in ("tree", "single_loop"):
        _validate_flat(obs, oid)
    elif kind == "loop_compound":
        _validate_compound(obs, oid)
    elif kind == "structural":
        _validate_structural(obs, oid)
    else:  # pragma: no cover -- closure_kind_of already enforces the domain
        raise SchemaError(f"{oid}: unhandled closure_kind={kind!r}.")


def g_symbol_from_support(support: str) -> str:
    """Map a generation.support enum value to its symbolic factor."""
    return G_SYMBOL_BY_SUPPORT[support]
