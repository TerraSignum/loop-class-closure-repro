# Tuple-compiler design memo

**Date:** 2026-05-13
**Scope:** P3 (loop-class-closure-repro)
**Goal:** Replace the current "registered mapping protocol" with a
**deterministic observable compiler**:

```
YAML observable definition  →  rule-based tuple extraction  →
unique loop-class match  →  prediction
```

This memo audits the existing P3 schema, reconciles it with the
proposed extractor design, and fixes the design choices that the
implementation will respect.

---

## 1. Existing P3 schema audit

### 1.1 The tuple is 5-component, not 6

P3's `data/observable_registry.json` (29 entries) uses

```
(n_spinor_trace, g_generation, s_sync_coupling, double_wick, resummed)
```

abbreviated `(n, g, s, w, r)`. **There is no `η` component.**
Signs (e.g. the `+` in `1+γ/4` vs the `−` in `1−γ/4`) are
determined sector-by-sector by the physical observable (whether
it dresses up or down), not by a tuple component. Adding `η` to
the tuple would be a strict extension that breaks 29 existing
entries for no closure benefit. **Decision: keep the tuple at
five components.**

### 1.2 Component domains are discrete, not integer-scored

| Field | Domain |
|---|---|
| `n` | `int ∈ {0, 1, 2, 4}` (n=3 does not appear in the library) |
| `g` | `str ∈ {"0", "1/N_gen", "1/(2*N_gen)"}` (generation-suppression factor as symbolic) |
| `s` | `str ∈ {"0", "eps^2", "eps^2 pure", "eps^2 * gamma"}` (sync-coupling channel as symbolic) |
| `w` | `bool` (double-Wick contraction yes/no) |
| `r` | `bool` (resummed propagator yes/no) |

The user's proposal scored `s` as `sum(bool) ∈ {0,1,2,3,4}`. That is
semantically richer than the 4-class library covers, and would
re-classify all 21 single-loop entries. **Decision: keep `s` as
symbolic class — the existing 4-class enum already exhausts every
loop-class lemma in the library.** If new observables require
multi-channel sync, the enum can be extended later.

### 1.3 Two-loop compounds are products of single-loop tuples

8 of the 29 P3 entries carry `two_loop_compound: true` and a
`component_factors: [...]` array of length 2, each entry itself a
single-loop tuple. The 21 remaining entries are single-loop. The
compiler must support both via a uniform `factors: [...]` list
(of length 1 for single-loop).

### 1.4 The library has 10 lemma classes

| Lemma | (n, g, s, w, r) | loop-classes |
|---:|---|---|
| L1 Yukawa-Damping     | (1, 0,         0,             F, F) | `1 ± γ/4` |
| L2 PMNS-Self-Energy   | (1, 0,         0,             T, F) | `1 ± γ²/4` |
| L3 Pure-Self-Energy   | (4, 0,         0,             F, F) | `1 ± γ²` |
| L4 Resummed-Propagator| (4, 0,         0,             F, T) | `1 ± 2γ²`, `1/(1±2γ²)` |
| L5 Generation         | (2, 1/N_gen,   0,             F, F) | `1 ± γ/N_gen` |
| L6 Sub-Generation     | (1, 1/(2N_g),  0,             F, F) | `1 ± γ/(2N_gen)` |
| L7 EW-Mixed           | (1, 0,         eps^2,         F, F) | `1 ± γ·eps_sync²` |
| L8 Matter-Core        | (2, 0,         0,             F, F) | `1 ± γ/2` |
| L_pure_eps2           | (0, 0,         eps^2 pure,    F, F) | `1 ± eps_sync²` |
| L10                   | (0, 0,         eps^2 · gamma, F, F) | `± γ²/2` |

Each lemma maps **bijectively** to a tuple — the loop-class map
JSON can be built directly from the library and is keyed by tuple.

---

## 2. The `target_value_allowed: false` lock

The decisive methodological upgrade is the YAML constraint

```yaml
anchors:
  target_value_allowed: false
  external_target_used_in_tuple: false
```

The extractor refuses to operate on any YAML where these are not
both `false`. This makes "tuple-first before target comparison"
**machine-checkable**, not just disciplinary.

The current `observable_registry.json` mixes tuple + target in one
record (carrying `target`, `expected_residual_pct_after_loop`,
`tier_after_loop`). The new compiler does **not** read these
fields — they live in a separate `data/observable_targets.json`
file that the **predictor** (not the extractor) loads after the
tuple has already been written to the immutable
`outputs/extracted_topology_tuples.json`.

**Hash-pinning protocol:**

```yaml
provenance:
  yaml_sha256: <hash of this YAML at extraction time>
  extractor_commit: <git hash>
  extracted_at: <ISO 8601 timestamp>
```

This is recorded in the extractor output so that years later a
reader can verify the tuple was extracted from a specific YAML
revision, before any target comparison.

---

## 3. Migration audit of the 29 P3 tuples

| Class | Count | New-schema status |
|---|---:|---|
| Single-loop with `(n, g, s, w, r)` populated | 19 | direct migration |
| Single-loop with `g_generation = "1/(2*N_gen)"` symbolic | 4 | direct (g already symbolic) |
| Single-loop with `s_sync_coupling = "eps^2"` symbolic | 1 | direct |
| Single-loop with `lemma: null` (tree-only) | 1 | maps to `{lemma_id: "TREE"}` class |
| Two-loop compounds | 8 | `factors: [...]` of length 2, both single-loop |
| Two-loop with sum-form `lemma: "pure-eps2 + 7"` | 1 | sum-of-products, needs ladder |

The "sum-form" entry (`Lambda_QCD`) is the only entry that requires
a **sum** of loop-class products, not a single product. Phase 1
covers the single-loop case; the sum-form is deferred to Phase 3.

---

## 4. Sign / `η` handling (deliberately outside the tuple)

The tuple does not encode signs. Each loop-class lemma has a
twofold sign choice (e.g. L1 gives `1+γ/4` or `1−γ/4`). The sign
is determined by:

1. **Sector**: dressing direction (mass enhancement vs.
   suppression for the observable in question).
2. **CP / T parity**: T-parity of the defect field $\Xi$
   (P1 source axiom).
3. **Chirality flip**: the $\theta_{\rm chir}=\pi/4$ flip flips
   the sign for matter-branch vs vacuum-branch.

Signs are recorded **in the predictor output**, not in the
extracted tuple. The extractor's job is purely structural
identification; the sign comes from the physics of the
observable, which is read from a separate `sign_rules.yaml`
(Phase 2).

For Phase 1 (this commit), the sign is read from a single
`expected_sign` field in the YAML (`+1` or `-1`), which the
extractor passes through to the predictor but **does not** use
in tuple identification.

---

## 5. Phase plan

| Phase | Status | Scope |
|---|---|---|
| **Phase 1** | done (commit 5a6c528) | 3 YAMLs covering TREE + L1 + L6. End-to-end extractor + predictor + 61 tests. |
| **Phase 2** | done (this commit) | All 21 single-loop observables in the existing P3 registry. L4 inverse-form extension (`operator.resummation_inverse` flag). Cross-verification: 45 Phase-2 tests pin every compiler factor + lemma assignment against `data/observable_registry.json` without registry access during extraction. |
| Phase 3 | open | Two-loop compounds via `factors: [...]`. Lambda_QCD sum-form handler. |
| Phase 4 | open | Prospective-registry observables (not yet closed); the compiler outputs `OPEN` for unmatched tuples. |

### Phase 2 sign-rules note

Within the 21 single-loop observables, signs distribute as follows:

| Lemma | Count | Signs |
|---|---:|---|
| L1 Yukawa-Damping     | 5 | all `+` |
| L2 PMNS-Self-Energy   | 2 | all `-` |
| L6 Sub-Generation     | 5 | 2 `+`, 3 `-` (mixed within lemma class) |
| L7 EW-Mixed           | 5 | 4 `+`, 1 `-` (mixed within lemma class) |
| L4 Resummed (inverse) | 1 | `-` (T_RH) |
| TREE                  | 3 | sign meaningless (factor = 1) |

L6 and L7 carry **mixed signs within the same structural lemma class**.
The sign therefore cannot be derived from the lemma class alone — it
is sector-determined by the physical observable. The decision in this
phase is: keep `parity.expected_sign` as an explicit per-YAML field
(declarative), and defer a sign-rules layer to a later phase only if
prospective observables expose a derivable sub-pattern within a lemma.

---

## 6. Decisions vs. the user's original proposal

| User proposal | This memo |
|---|---|
| Tuple = `(n, g, s, w, r, η)` 6-component | Tuple = `(n, g, s, w, r)` 5-component; η as separate `expected_sign` field |
| `s` = integer 0..4 from boolean sum | `s` = symbolic class enum (matches existing library) |
| `g` = integer (count) | `g` = symbolic class enum (matches existing library) |
| `match_loop_class` raises if not exactly one match | Three-status: `MATCHED` / `OPEN` (no match) / `ERROR` (multiple). `OPEN` is not a failure. |
| η-sign as multiplicative XOR | Sign deferred to Phase 2 with proper CP-T algebra |
| `n` derived from `spinor_trace_count + clifford_frame + γ5 + mixes_lr` | `n` is declared directly as the spinor-trace integer (matches existing library exactly) |
| Phase 1 = 5 observables | Phase 1 = 3 observables covering tree + sub-gen + Yukawa, all distinct lemmas |

---

## 7. The claim the compiler enables

**Before this work** (P3, §2):

> Given a registered tuple, the loop-class assignment is unique.

The "registered tuple" was a JSON record that a human filled in.

**After this work** (P3, §2 + appendix):

> Given a formal YAML definition of the observable that does not
> reference its target value, the tuple is deterministically
> extracted by `extract_topology_tuple.py`; given the tuple, the
> loop-class assignment is unique via `loop_class_predictor.py`.
> Both steps are hash-pinned to the YAML revision and the
> extractor/predictor commit.

This upgrades the "registered mapping protocol" of P3 to an
**observable compiler** with machine-checkable target-isolation.

---

## 8. File layout

```
loop-class-closure-repro/
  data/
    observable_definitions/
      O07_BH_entropy_quarter.yaml
      O13_CKM_V_us.yaml
      O01_alpha_dn_yukawa_exponent.yaml
    loop_class_map.json
  src/
    tuple_compiler/
      __init__.py
      schema.py
      tuple_rules.py
      extract_topology_tuple.py
      loop_class_predictor.py
      provenance.py
  outputs/
    extracted_topology_tuples.json
    loop_class_predictions.json
  tests/
    tuple_compiler/
      test_no_target_value_access.py
      test_known_tuples_phase1.py
      test_provenance_metadata.py
      test_schema_validation.py
      test_unique_match.py
```

The compiler lives in `src/tuple_compiler/` (a Python package),
not flat in `src/`, so future phases can extend cleanly.

---

## 9. Reproducer

```bash
# Extract tuples (refuses if any YAML has target_value_allowed: true)
python -m tuple_compiler.extract_topology_tuple

# Predict loop-class (refuses to read target file if tuples not yet written)
python -m tuple_compiler.loop_class_predictor

# Run all compiler tests
pytest tests/tuple_compiler/ -v
```
