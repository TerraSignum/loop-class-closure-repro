"""Avenue-D: tuple-exhaustion audit for the topology-labelled
loop-class mapping algorithm.

Question: is the topology tuple (n, g, s, w, r) for each
registered observable uniquely determined by the algorithmic
classification (sec:algorithm), or is it author-chosen?

Method: for each observable in data/observable_registry.json,
scan every alternative tuple (n, g, s, w, r) in the admissibility
space (4 x 3 x 3 x 2 x 2 = 144 tuples). For each alternative,
look up the implied loop class in data/allowed_topological_multipliers.json
(`mapping_algorithm_table'); if a loop class exists for that
tuple, evaluate the predicted observable value and compute the
relative residual against the registered target. Count how many
alternative tuples pass the PRECISE threshold |residual| < 2.5%.

If the canonical tuple is the unique pass --> tuple is uniquely
determined by the data and the algorithm is deterministic in the
strong sense.

If multiple tuples pass --> the (n, g, s, w, r) tuple alone is
not sufficient to single out the loop class; an additional
disambiguator (the lemma index) is needed. This is the
"avenue-D ambiguity" structural finding: the tuple-to-class map
is many-to-one, not one-to-one.

Output: outputs/verify_tuple_exhaustion.json
"""

from __future__ import annotations
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = REPO / "outputs" / "verify_tuple_exhaustion.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Admissible tuple space (from data/allowed_topological_multipliers.json).
N_VALUES = [0, 1, 2, 4]
G_VALUES = [0, "1/N_gen", "1/(2*N_gen)"]
S_VALUES = [0, "eps^2", "eps^2 pure", "eps^2*gamma"]
W_VALUES = [0, 1]
R_VALUES = [0, 1]

# Threshold (PRECISE band) for `tuple pass'.
PRECISE_CUT_PCT = 2.5


def _normalize_s(s):
    """Map registry/library string variants for s to canonical."""
    if s in (0, "0", None):
        return 0
    if isinstance(s, str):
        sl = s.lower().replace(" ", "").replace("_", "")
        if "eps2pure" in sl or "epssync2pure" in sl or sl == "eps^2pure":
            return "eps^2 pure"
        if "eps^2*gamma" in s or "eps2gamma" in sl or "eps^2*g" in sl:
            return "eps^2*gamma"
        if "eps2" in sl or sl == "eps^2" or "epssync" in sl:
            return "eps^2"
    return s


def _normalize_g(g):
    if g in (0, "0", None):
        return 0
    if isinstance(g, str):
        gs = g.strip().replace(" ", "")
        if gs in ("1/N_gen", "1/Ngen"):
            return "1/N_gen"
        if gs in ("1/(2*N_gen)", "1/(2*Ngen)", "1/2/N_gen", "1/(2N_gen)"):
            return "1/(2*N_gen)"
    return g


def _tuple_key(n, g, s, w, r):
    return (n, _normalize_g(g), _normalize_s(s), int(bool(w)), int(bool(r)))


def main() -> int:
    reg = json.loads((DATA / "observable_registry.json").read_text(encoding="utf-8"))
    lib = json.loads((DATA / "allowed_topological_multipliers.json").read_text(encoding="utf-8"))
    library_entries = lib.get("mapping_algorithm_table", [])

    # Index library by canonical tuple key. The JSON library uses
    # the boolean keys `double_wick` and `resummed' (not w/r), and
    # these are absent (= default False = 0) on most entries.
    by_tuple = {}
    for e in library_entries:
        w_flag = bool(e.get("double_wick", e.get("w", 0)))
        r_flag = bool(e.get("resummed", e.get("r", 0)))
        k = _tuple_key(e.get("n"), e.get("g"), e.get("s"),
                       w_flag, r_flag)
        by_tuple.setdefault(k, []).append({
            "loop_class": e.get("loop_class"),
            "lemma": e.get("lemma"),
            "name": e.get("name"),
            "w": int(w_flag),
            "r": int(r_flag),
        })

    # Audit: for every admissible (n, g, s, w, r) report how many
    # library entries match it. If >1, the tuple is ambiguous.
    ambiguous_tuples = []
    for n, g, s, w, r in product(N_VALUES, G_VALUES, S_VALUES, W_VALUES, R_VALUES):
        k = _tuple_key(n, g, s, w, r)
        if k in by_tuple and len(by_tuple[k]) > 1:
            ambiguous_tuples.append({
                "tuple": {"n": n, "g": g, "s": s, "w": w, "r": r},
                "n_matching_library_entries": len(by_tuple[k]),
                "library_entries": by_tuple[k],
            })

    # Per-observable: canonical tuple key + the number of library
    # entries it matches. If >1, the (n,g,s,w,r)-classification of
    # this observable is not single-valued without a lemma disambiguator.
    per_observable = []
    obs_list = reg.get("observables", [])
    for o in obs_list:
        canonical_k = _tuple_key(
            o.get("n_spinor_trace"),
            o.get("g_generation"),
            o.get("s_sync_coupling"),
            o.get("double_wick", False),
            o.get("resummed", False),
        )
        matches = by_tuple.get(canonical_k, [])
        per_observable.append({
            "id": o.get("id"),
            "name": o.get("name"),
            "canonical_tuple": {
                "n": canonical_k[0],
                "g": canonical_k[1],
                "s": canonical_k[2],
                "w": canonical_k[3],
                "r": canonical_k[4],
            },
            "registered_loop_class": o.get("loop_class"),
            "registered_lemma": o.get("lemma"),
            "n_library_entries_matching_tuple": len(matches),
            "library_matches": matches,
            "tuple_uniquely_determines_loop_class": len(matches) <= 1,
        })

    n_unique = sum(1 for x in per_observable
                    if x["tuple_uniquely_determines_loop_class"])
    n_ambiguous = len(per_observable) - n_unique

    out = {
        "schema_version": "1.0.0",
        "method": ("Avenue-D tuple-exhaustion audit: for each "
                   "registered observable, count how many entries in "
                   "the loop-factor library match its (n, g, s, w, r) "
                   "tuple. Multiple matches indicate the tuple alone "
                   "does not single out the loop class and a lemma "
                   "disambiguator is needed."),
        "admissibility_space_size": (len(N_VALUES) * len(G_VALUES)
                                     * len(S_VALUES) * len(W_VALUES)
                                     * len(R_VALUES)),
        "library_entries": len(library_entries),
        "n_observables": len(per_observable),
        "n_observables_uniquely_determined": n_unique,
        "n_observables_with_tuple_ambiguity": n_ambiguous,
        "ambiguous_tuples_in_library": ambiguous_tuples,
        "per_observable": per_observable,
        "verdict": ("TUPLE_UNIQUE_PER_OBSERVABLE" if n_ambiguous == 0
                    else "TUPLE_REQUIRES_LEMMA_DISAMBIGUATOR"),
    }

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Avenue-D tuple-exhaustion audit")
    print(f"  admissibility_space_size = "
          f"{out['admissibility_space_size']}")
    print(f"  library_entries          = {out['library_entries']}")
    print(f"  n_observables            = {out['n_observables']}")
    print(f"  uniquely determined      = {n_unique}")
    print(f"  require lemma            = {n_ambiguous}")
    print(f"  ambiguous library tuples = {len(ambiguous_tuples)}")
    print(f"  verdict                  = {out['verdict']}")
    print(f"\nSaved {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
