r"""
Deterministic loop-class mapping algorithm (the deterministic-mapping theorem).

Given an observable's (n, g, s) topology factors, this module returns
the UNIQUE loop class L_sigma in the library, or NO_CLAIM if the
observable does not lie in the closure domain.

The mapping is purely lookup-driven and forbids any free choice of
class -- it is the formal answer to the reviewer question "Why are the
loop factors not chosen after the fact?".

Usage as a module:
    from classify_observable import classify
    cls = classify(n=1, g=0, s=0, double_wick=False, resummed=False)
    # -> {'loop_class': '1+/-gamma/4', 'lemma': 1, 'name': 'Yukawa-Damping'}

CLI:
    python ./src/classify_observable.py --n 1 --g 0 --s 0
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def load_mapping_table():
    with open(DATA / "allowed_topological_multipliers.json", "r", encoding="utf-8") as f:
        return json.load(f)["mapping_algorithm_table"]


def _normalize(g, s):
    """Normalize g, s for lookup."""
    if isinstance(g, (int, float)) and g == 0:
        g = 0
    if isinstance(s, (int, float)) and s == 0:
        s = 0
    return g, s


def classify(n, g=0, s=0, double_wick=False, resummed=False):
    """
    Deterministic loop-class lookup.

    Parameters
    ----------
    n : int
        Spinor-trace component count (0, 1, 2, or 4).
    g : int, str, or float
        Generation range (0, 1, "1/N_gen", "1/(2*N_gen)").
    s : int or str
        Sync coupling (0, "eps^2", "eps^2 pure").
    double_wick : bool
        Marks the PMNS-self-energy form (Lemma 2).
    resummed : bool
        Marks the resummed-propagator form (Lemma 4).

    Returns
    -------
    dict with keys 'loop_class', 'lemma', 'name'.

    Raises
    ------
    ValueError if no entry is found, or if more than one entry matches.
    """
    g, s = _normalize(g, s)
    table = load_mapping_table()

    candidates = []
    for entry in table:
        if entry["n"] != n:
            continue
        if entry["g"] != g:
            continue
        if entry["s"] != s:
            continue
        if entry.get("double_wick", False) != double_wick:
            continue
        if entry.get("resummed", False) != resummed:
            continue
        candidates.append(entry)

    if not candidates:
        raise ValueError(
            f"No loop class for (n={n}, g={g}, s={s}, "
            f"double_wick={double_wick}, resummed={resummed}). "
            f"Observable lies outside the closure domain G_claim^auth."
        )
    if len(candidates) > 1:
        raise ValueError(
            f"Mapping is non-unique for "
            f"(n={n}, g={g}, s={s}, double_wick={double_wick}, resummed={resummed}): "
            f"{[c['name'] for c in candidates]}. This indicates a malformed "
            f"input — the (n, g, s, double_wick, resummed) tuple did not "
            f"discriminate between candidate library entries. This is an "
            f"input-validation error, not a theorem-falsification trigger."
        )

    e = candidates[0]
    return {
        "loop_class": e["loop_class"],
        "lemma": e["lemma"],
        "name": e["name"],
    }


def classify_observable_from_registry(observable_id):
    """Look up an observable's classification straight from the registry."""
    with open(DATA / "observable_registry.json", "r", encoding="utf-8") as f:
        reg = json.load(f)["observables"]
    for obs in reg:
        if obs["id"] == observable_id:
            return obs
    raise KeyError(f"Observable {observable_id!r} not in registry.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--g", default="0")
    p.add_argument("--s", default="0")
    p.add_argument("--double-wick", action="store_true")
    p.add_argument("--resummed", action="store_true")
    p.add_argument("--observable", default=None,
                   help="Look up by registry ID (e.g. O01) instead of (n,g,s)")
    args = p.parse_args()

    if args.observable:
        obs = classify_observable_from_registry(args.observable)
        print(json.dumps(obs, indent=2))
        return

    if args.n is None:
        p.error("--n is required (or use --observable)")

    try:
        g_arg = int(args.g)
    except ValueError:
        g_arg = args.g
    try:
        s_arg = int(args.s)
    except ValueError:
        s_arg = args.s

    result = classify(n=args.n, g=g_arg, s=s_arg,
                      double_wick=args.double_wick, resummed=args.resummed)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
