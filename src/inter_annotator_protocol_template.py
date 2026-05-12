"""Inter-annotator consistency study for the topology-labeled
mapping protocol (sec:algorithm).

This script implements a working pilot of the protocol:

1. Reads the observable registry data/observable_registry.json
   and extracts the bundled (n, g, s, w, r) tuple for each
   observable as the FIRST annotator's reading (the bundled
   classification, treated as annotator 'A1').

2. If additional annotator CSV files exist under
   data/inter_annotator_csv/<annotator_name>.csv, they are
   loaded as further annotators.

3. Computes per-coordinate Fleiss's kappa across annotators
   (and exact-tuple agreement rate when N_annotators >= 2).

4. With a single annotator (the bundled reading alone), the
   script reports the protocol setup and the bundled reading
   as the seed dataset for any future consistency run; Fleiss
   kappa is undefined for N=1 and is reported as NaN with the
   conditional message.

Output: outputs/inter_annotator_protocol.json
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CSV_DIR = DATA / "inter_annotator_csv"
OUT = REPO / "outputs" / "inter_annotator_protocol.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

TUPLE_FIELDS = (
    "n_spinor_trace",
    "g_generation",
    "s_sync_coupling",
    "loop_class",
    "lemma",
)


def _normalize(v):
    """Stringify primitives for cross-annotator comparison.
    Both the JSON-loaded annotator and the CSV-loaded annotator
    are normalised to the same string form so that equality
    compares semantic content rather than Python type.
    """
    if v is None:
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    return str(v).strip()


def _load_bundled_annotator() -> dict[str, dict]:
    """The bundled observable_registry.json is the A1 annotator
    (the manuscript's working classification).
    """
    with open(DATA / "observable_registry.json") as f:
        d = json.load(f)
    obs = d.get("observables", [])
    out: dict[str, dict] = {}
    for o in obs:
        out[o["id"]] = {f: _normalize(o.get(f)) for f in TUPLE_FIELDS}
    return out


def _load_additional_annotators() -> dict[str, dict[str, dict]]:
    """Load every <name>.csv file in data/inter_annotator_csv/.
    Each file is a CSV with header 'id,n_spinor_trace,...' giving
    one annotator's tuple per observable.
    """
    out: dict[str, dict[str, dict]] = {}
    if not CSV_DIR.exists():
        return out
    for csv_path in sorted(CSV_DIR.glob("*.csv")):
        name = csv_path.stem
        per_obs: dict[str, dict] = {}
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                oid = row.get("id")
                if not oid:
                    continue
                per_obs[oid] = {
                    f_: _normalize(row.get(f_)) for f_ in TUPLE_FIELDS}
        out[name] = per_obs
    return out


def _fleiss_kappa_per_coordinate(annotator_tables: list[dict[str, dict]],
                                  observable_ids: list[str],
                                  field: str) -> float:
    """Fleiss's kappa for one tuple coordinate across the
    annotator tables. annotator_tables is a list of dicts
    {obs_id: {field: value, ...}}.
    """
    n_annotators = len(annotator_tables)
    if n_annotators < 2:
        return float("nan")
    # Collect categorical values for this coordinate
    categories: list = []
    for table in annotator_tables:
        for oid in observable_ids:
            v = table.get(oid, {}).get(field)
            if v is not None and v not in categories:
                categories.append(v)
    if not categories:
        return float("nan")
    cat_index = {c: i for i, c in enumerate(categories)}
    K = len(categories)
    N = len(observable_ids)
    n_ij: list[list[int]] = [[0] * K for _ in range(N)]
    for table in annotator_tables:
        for i, oid in enumerate(observable_ids):
            v = table.get(oid, {}).get(field)
            if v is None:
                continue
            j = cat_index[v]
            n_ij[i][j] += 1
    P_i = []
    for i in range(N):
        row_sum_sq = sum(c * c for c in n_ij[i])
        denom = n_annotators * (n_annotators - 1)
        if denom <= 0:
            P_i.append(0.0)
        else:
            P_i.append((row_sum_sq - n_annotators) / denom)
    P_bar = sum(P_i) / N if N > 0 else 0.0
    p_j = []
    for j in range(K):
        total_j = sum(n_ij[i][j] for i in range(N))
        p_j.append(total_j / (N * n_annotators))
    P_e = sum(pj * pj for pj in p_j)
    if P_e >= 1.0:
        return 1.0
    kappa = (P_bar - P_e) / (1.0 - P_e)
    return float(kappa)


def _exact_tuple_agreement_rate(annotator_tables: list[dict[str, dict]],
                                 observable_ids: list[str]) -> float:
    if len(annotator_tables) < 2:
        return float("nan")
    n_obs = 0
    n_agree = 0
    for oid in observable_ids:
        tuples = []
        all_present = True
        for table in annotator_tables:
            entry = table.get(oid)
            if entry is None:
                all_present = False
                break
            tuples.append(tuple(entry.get(f_) for f_ in TUPLE_FIELDS))
        if not all_present:
            continue
        n_obs += 1
        if len(set(tuples)) == 1:
            n_agree += 1
    if n_obs == 0:
        return float("nan")
    return n_agree / n_obs


def main() -> None:
    a1 = _load_bundled_annotator()
    extra = _load_additional_annotators()
    annotator_tables = [a1] + [extra[name] for name in sorted(extra)]
    annotator_names = ["A1_bundled"] + sorted(extra)
    obs_ids = sorted(a1.keys())

    per_coord_kappa = {
        f_: _fleiss_kappa_per_coordinate(
            annotator_tables, obs_ids, f_)
        for f_ in TUPLE_FIELDS
    }
    exact_rate = _exact_tuple_agreement_rate(
        annotator_tables, obs_ids)
    n_annotators = len(annotator_tables)

    # Landis--Koch interpretation
    interp = {}
    for f_, k in per_coord_kappa.items():
        if math.isnan(k):
            interp[f_] = "undefined (need >= 2 annotators)"
        elif k >= 0.81:
            interp[f_] = "almost-perfect (>=0.81)"
        elif k >= 0.61:
            interp[f_] = "substantial (0.61-0.80)"
        elif k >= 0.41:
            interp[f_] = "moderate (0.41-0.60)"
        elif k >= 0.21:
            interp[f_] = "fair (0.21-0.40)"
        elif k >= 0.0:
            interp[f_] = "slight (0.0-0.20)"
        else:
            interp[f_] = "below chance"

    out = {
        "schema_version": "1.1.0",
        "release": "v0.2.0",
        "stand": "2026-05-10",
        "protocol": (
            "Inter-annotator consistency for the topology-labeled "
            "mapping protocol of sec:algorithm. Each annotator "
            "independently assigns the (n, g, s, w, r) tuple per "
            "observable using the rules of sec:algorithm. The "
            "bundled observable_registry.json is treated as the "
            "first annotator (A1_bundled, the manuscript's working "
            "classification). Additional annotators contribute "
            "CSV files in data/inter_annotator_csv/<name>.csv with "
            "columns id, n_spinor_trace, g_generation, "
            "s_sync_coupling, loop_class, lemma."),
        "tuple_fields": list(TUPLE_FIELDS),
        "n_observables": len(obs_ids),
        "n_annotators": n_annotators,
        "annotator_names": annotator_names,
        "fleiss_kappa_per_coordinate": per_coord_kappa,
        "fleiss_kappa_landis_koch_interpretation": interp,
        "exact_tuple_agreement_rate": exact_rate,
        "agreement_thresholds": {
            "almost_perfect_kappa_geq_0p81": True,
            "substantial_kappa_geq_0p61": True,
            "moderate_kappa_geq_0p41": True,
        },
        "current_state": (
            "PILOT_RUN: A1_bundled-only" if n_annotators == 1
            else f"MULTI_ANNOTATOR: {n_annotators} annotators"),
        "purpose": (
            "Hardens the topology-labeled mapping protocol from "
            "'reading-off rules' to 'measured inter-annotator "
            "consistency'. With a single annotator (A1_bundled), "
            "the script reports the bundled tuple as the seed "
            "dataset; Fleiss kappa is undefined for N=1 and the "
            "structural reading is acknowledged in sec:algorithm "
            "as conditional on the diagrammatic-structure reading "
            "of each observable. The protocol is operational and "
            "ready to consume additional annotators via the CSV "
            "drop-in mechanism."),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Inter-annotator protocol pilot run.")
    print(f"  N_annotators = {n_annotators}, "
          f"N_observables = {len(obs_ids)}")
    if n_annotators >= 2:
        print(f"  Exact-tuple agreement = {exact_rate:.3f}")
        for f_, k in per_coord_kappa.items():
            print(f"  Fleiss kappa({f_}) = {k:.3f}  [{interp[f_]}]")
    else:
        print("  PILOT: only A1_bundled present; "
              "Fleiss kappa undefined for N=1")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
