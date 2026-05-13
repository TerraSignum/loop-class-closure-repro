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

REQUIRED_TOP_LEVEL = ("id", "name", "sector", "operator", "generation",
                      "sync", "parity", "anchors", "schema_version")


class SchemaError(ValueError):
    """Raised when an observable YAML violates the schema."""


def _validate_top_level(obs: Dict[str, Any], oid: str) -> None:
    for field in REQUIRED_TOP_LEVEL:
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


def validate(obs: Dict[str, Any]) -> None:
    """Raise SchemaError if obs does not conform.

    Validates:
    - all required top-level fields present
    - anchors.target_value_allowed is False
    - anchors.external_target_used_in_tuple is False
    - operator.spinor_trace_count is in N_DOMAIN
    - operator.double_wick / resummed / loop_dressed are booleans
    - generation.support is in G_DOMAIN_SUPPORT and matches symbol
    - sync.channel is in S_DOMAIN_CHANNEL
    - parity.expected_sign is the integer +1 or -1
    """
    oid = obs.get("id", "<unknown>")
    _validate_top_level(obs, oid)
    _validate_anchors(obs["anchors"], oid)
    _validate_operator(obs["operator"], oid)
    _validate_generation(obs["generation"], oid)
    _validate_sync(obs["sync"], oid)
    _validate_parity(obs["parity"], oid)


def g_symbol_from_support(support: str) -> str:
    """Map a generation.support enum value to its symbolic factor."""
    return G_SYMBOL_BY_SUPPORT[support]
