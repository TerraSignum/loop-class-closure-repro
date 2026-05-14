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
| **Phase 3** | done (this commit) | 6 standard two-loop compounds (O11, O12, O23, O24, O25, O26) via `closure_kind: loop_compound` + compact `factors: [...]` array; 2 structural-only observables (O27 α_ξ²=81/100, O28 −γ²/2=−1/200) via `closure_kind: structural`. Cross-verification: every compound's factor string matches the registry's `loop_class` formula. |
| **Phase 4** | done (this commit) | Cross-consistency audit between the compiler and the broader corpus state. **Not** a YAML extension — the Phase-4 audit honestly revealed that (a) the `prospective_cluster_registry` contains stability-diagnostic tests, not loop-class closures, so the tuple compiler does not apply; (b) six registry observables (O09-O14) carry a `closure_form_2026_05_10` field documenting a **superseding** structural closure that the compiler is silent about; and (c) five companion-JSON entries (`neutrino_sector_closure`, `ckm_closure`) describe the same observables via different structural identities. The audit script surfaces all of these explicitly so corpus owners can resolve them. |

### Phase 4 honest scope statement

The naïve Phase-4 plan would have been "extend the compiler to the
prospective registry and to closures in companion JSONs". The audit
revealed this was the wrong move:

**Why the prospective registry is out of scope.** The 3 entries
(PROSP-01 gravitational coupling-scaling, PROSP-02 vortex-cosmological
gate, PROSP-03 Xi-reactivity ratio at g=1.42) are **multi-N stability
diagnostics**, not closure observables. Their "residuals" are scores
like `newton_like_badness` or `cosmo_compat`, not target-vs-predicted
percentages on a closed structural formula. Forcing them into the
loop-class tuple schema would be cheating — they have no `(n, g, s, w, r)`
classification because they aren't loop-class observables.

**Why the dual-closure state is out of scope.** Six registry entries
(O09 PMNS_θ₁₃, O10 PMNS_θ₁₂, O11 PMNS_θ₂₃, O12 PMNS_δ_CP, O13 CKM_V_us,
O14 CKM_V_cb) carry both:
- A `loop_class` field — what the tuple compiler reproduces (e.g.
  O09's `1 - γ²/4` = L2 single-loop).
- A `closure_form_2026_05_10` field — a System-R structural rational
  identity that supersedes the loop-class form (e.g. O09's
  `2 γ²(1+γ) = 11/500`).

The two forms can be numerically close (both within ~1% of anchor) but
they are **different closure mechanisms**. The compiler's job is to
reproduce the `loop_class` field, which it does correctly for all 29
entries. The audit surfaces the dual-state so corpus owners can
decide whether to (a) consolidate to a single canonical form, (b) keep
both as alternative closures, or (c) deprecate one. **The compiler does
not pick a side.**

**Why companion-JSON disagreements are out of scope.** The
`neutrino_sector_closure.json` describes PMNS_θ₁₃ as
`(1-γ)/(2 N_gen)` (tree-only structural identity), while the registry
says L2 dressed `1 - γ²/4`. Both round to ≈0.15 rad (the anchor is
0.149636). The companion form is the structural identity; the registry
form is the loop-class form. The audit lists these without picking
one.

The legacy `V_us = γ√5` and `V_cb = eps²√(2/N_gen)` in `ckm_closure.json`
are **already noted as superseded** in the registry's
`closure_form_2026_05_10` ("supersedes legacy gamma sqrt 5"). The
audit surfaces this for cleanup.

### Phase 4 deliverable

`src/tuple_compiler/cross_consistency_audit.py` produces
`outputs/cross_consistency_audit.json` listing:
- 6 dual-state registry observables with both forms side-by-side
- 5 companion-JSON disagreements
- A `note` field stating the audit picks no side

Tests (`tests/test_tuple_compiler/test_phase4_cross_consistency.py`)
**pin the exact set** of dual-state IDs and disagreement IDs. If a
new registry entry adds a `closure_form_2026_05_10` field, the test
fails and forces explicit acknowledgment — the audit's coverage
cannot silently drift.

| **Phase 5** | done (this commit) | Structural-identity evaluator (sympy-based, exact Fraction arithmetic) closes every Phase-4-surfaced dual-state gap. 6 new YAMLs (HK-09, HK-10, HK-11, HK-12, HJ-13, HQ-14) declare the registry's `closure_form_2026_05_10` forms; O27/O28 structural fields are activated. All 8 structural forms evaluate EXACTLY to their claimed rationals; no float fallback, no stub. Audit upgraded to v0.2 with `phase5_resolution` block per dual-state entry; all 6 RESOLVED. |
| **Phase 6** | done (this commit) | Branch-resolved P4 + Lemma B + β_π refined-vacuum structural identities. 12 new YAMLs cover both vacuum AND matter branches of T_00, G_00, Λ_t, λ_w; Lemma B's family-coupling, skeleton, Kahale, and 20/21 master-correction; and the β_π 143/144 refined-vacuum identity. Every form evaluates EXACTLY via sympy. |
| **Phase 7** | done (this commit) | Prospective-registry stability diagnostics. 3 new YAMLs (PROSP-01/02/03) with `closure_kind: stability_diagnostic`. The harness reads bundle JSON files from the broader Emergence corpus, extracts named diagnostic fields via dotted paths, and reports verdict status. SHA-256 hash-pinning per bundle catches silent upstream data drift. |

### Phase 7 honest scope statement

The prospective registry's 3 entries (PROSP-01 gravitational coupling
scaling, PROSP-02 vortex cosmological gate, PROSP-03 charged-current
Xi-reactivity ratio) are **multi-N stability diagnostics**, not
closures. They report scores like `newton_like_pass`,
`far_field_exponent`, `cosmo_compat`, `gate_gap`, `cw_net_corrected`
on lattice bundles produced by separate simulation pipelines. The
tuple compiler does NOT run those simulations; it **reproduces the
recorded outputs deterministically** from the JSON bundles.

Specifically the harness:

1. Resolves each declared bundle path relative to the Emergence root
   (the parent of loop-class-closure-repro).
2. Reads the bundle, extracts the named fields via dotted paths.
3. Computes the SHA-256 of each bundle so a silent upstream change
   fails the test.
4. Reports one of these status values:
   - `BUNDLE_MISSING` — a declared bundle file is absent on disk.
   - `EXTRACT_ERROR` — a declared field path is missing in the bundle.
   - `BASELINE_RECOVERED` — pre-T_0 baseline values extracted; no
     prospective prediction declared (the post-T_0 residual would
     require a new lattice run).
   - `PROSPECTIVE_CONFIRMED` — prediction declared and all extracted
     values within tolerance.
   - `PROSPECTIVE_FALSIFIED` — prediction declared and at least one
     extracted value outside tolerance.

For PROSP-01/02/03 the harness reports `BASELINE_RECOVERED`: the
pre-T_0 baseline values are deterministically extracted from
`results_c5_fix4/c5_p{0,1,2prime}.json`,
`outputs_theory_closure/pg_vtx02_cosmo_gate.json`, and
`outputs_cwbp_patch_cw/zmeq_b2_p2prime_core_patch_self_closure_audit.json`.
The post-T_0 prospective residuals (lattice-N extension, full re-run
at g=1.42) are NOT in the corpus at T_0 and the harness does not
fabricate them; running the corresponding simulations is a separate
task outside the tuple compiler.

### Honest "no fabrication" pinning

Phase-7 tests pin the SHA-256 prefix of each bundle PLUS the EXACT
extracted value of each field. This guards against three failure
modes simultaneously:

- **Silent data drift**: a bundle file changes upstream → SHA fails.
- **Schema drift**: a JSON field is renamed upstream → extract fails.
- **Logic drift**: the harness changes behaviour → value test fails.

No tolerance, no fallback, no default value. The harness reads what
is on disk; the tests pin what the harness must return.

### What stays out of scope (intentionally)

- **Running the lattice simulations**. The harness reproduces recorded
  outputs; it does not run new simulations. Computing the post-T_0
  prospective residuals (e.g. the g=1.42 re-run of PROSP-03) is a
  separate task — when those bundle files appear on disk, the
  corresponding YAMLs can be extended with the new bundle paths and
  the verdict status will upgrade from BASELINE_RECOVERED to
  PROSPECTIVE_CONFIRMED or PROSPECTIVE_FALSIFIED automatically.

| Phase 8 | open | Future work would build the lattice-simulation runner that produces the post-T_0 bundle files; the harness then automatically picks up the new data and upgrades the verdict. |

### Phase 6 honest scope statement

Phase 5 closed the P3 registry's dual-state gap (6 dual + O27/O28 = 8
structural). It left untouched the structural identities documented
in P4 outside the P3 registry:

- **P4 branch-resolved Eq.** `lambda_t_branch_resolved` (manuscript
  line 3083) splits T_00, G_00, Λ_t at θ_chir = π/4. Phase 5 only
  carried the matter-branch Λ_t = α_ξ² = 81/100 (via O27). Phase 6
  adds the vacuum-branch counterparts and the missing source-side
  components.
- **Lemma B Step 4a** identifies four structural rationals
  (family-coupling 7/6, skeleton 7/24, Kahale 9/7, master-correction
  20/21) plus the chain `3/8 = (7/24)·(9/7)`. None of these were in
  Phase 5.
- **β_π refined vacuum** 143/144 = (2^d·N_gen² − 1)/(2^d·N_gen²) —
  the (X−1)/X universal-pattern counterpart at X = 144.

Phase 6 adds all 12 as `closure_kind: structural` YAMLs evaluated
exactly:

| YAML id                 | structural formula                           | claimed rational |
|-------------------------|----------------------------------------------|------------------|
| P4-VAC-T00              | `α_ξ² + 3·γ²`                                | 84/100 = 21/25   |
| P4-MAT-T00              | `α_ξ²`                                       | 81/100           |
| P4-VAC-G00              | `3·γ²/2`                                     | 3/200            |
| P4-MAT-G00              | `γ²/3`                                       | 1/300            |
| P4-VAC-LAMBDA-T         | `α_ξ² + 3·γ²/2`                              | 33/40            |
| P4-VAC-LAMBDA-W         | `(d−1)/(2·d)`                                | 3/8              |
| P4-MAT-LAMBDA-W         | `(d−1)/(2·d) + 2·γ²`                         | 79/200           |
| LEMB-FAMILY             | `(d+N_gen)/(2·N_gen)`                        | 7/6              |
| LEMB-SKELETON           | `(d+N_gen)/(2·d·N_gen)`                      | 7/24             |
| LEMB-KAHALE             | `(d−1)·N_gen/(d+N_gen)`                      | 9/7              |
| LEMB-MASTER-CORRECTION  | `d·(d+1)/(N_gen·(d+N_gen))`                  | 20/21            |
| BPI-REFINED-VACUUM      | `(2^d·N_gen²−1)/(2^d·N_gen²)`                | 143/144          |

### Phase 6 algebraic identities verified by tests

- **Lemma B master identity**: `7/6 = α_ξ · Kahale + γ² · (20/21)`
  via direct sympy evaluation. Test `test_lemma_b_master_identity`
  asserts EXACT Fraction equality.
- **Spatial dilution**: `λ_skel = (1/d) · λ_family = 7/24`. Test
  `test_lemma_b_skeleton_via_spatial_dilution`.
- **λ_w chain**: `3/8 = (7/24)·(9/7) = (d−1)/(2·d)`. Test
  `test_lemma_b_lambda_w_chain`.
- **Matter-branch shift**: `λ_w^mat − λ_w^vac = 2·γ² = 1/50`. Test
  `test_branch_resolved_matter_shift_consistency`.
- **T_00 chirality-flip shift**: `T_00^vac − T_00^mat = 3·γ² = 3/100`.
  Test `test_t00_branch_difference_equals_3_gamma_squared`.
- **Universal (X−1)/X pattern**: at X=21 and X=144, both forms
  evaluate exactly. Test `test_x_minus_1_over_x_pattern_universal`.

### Phase 5 honest scope statement

The Phase-4 audit revealed 6 dual-state observables (O09-O14) where
the registry's `loop_class` field is reproduced by the loop-class
compiler but a superseding `closure_form_2026_05_10` field documents
a System-R rational identity that the loop-class compiler is silent
about. Phase 5 closes this gap by:

1. Building `src/tuple_compiler/structural_evaluator.py` — a
   sympy-based evaluator that parses each structural formula in the
   System-R rational namespace and computes its **exact** rational
   coefficient. There is no float-approximation fallback: an
   expression that does not reduce to either a pure rational or
   (rational × π) raises `StructuralEvaluationError`.

2. Declaring 6 new YAMLs in `data/observable_definitions/` with
   `closure_kind: structural`:

| YAML id  | observable                  | structural formula                       | claimed rational |
|----------|-----------------------------|------------------------------------------|------------------|
| HK-09    | sin²(θ₁₃)                   | `2·γ²·(1+γ)`                            | 11/500           |
| HK-10    | sin²(θ₁₂)                   | `1/4 + α_ξ/16`                           | 49/160           |
| HK-11    | sin²(θ₂₃)                   | `1/2 + α_ξ/12`                           | 23/40            |
| HK-12    | δ_CP (rad)                  | `π · (1+γ) · (1−γ²/4)`                   | 4389/4000 (×π)   |
| HJ-13    | V_us                        | `α_ξ · s_face` with s_face = 1/4         | 9/40             |
| HQ-14    | V_cb                        | `α_ξ / (2·(2·d+N_gen))`                  | 9/220            |

   The auxiliary `s_face = 1/4` is the BH-entropy face fraction
   documented in `data/closure_derivations/HJ_Vus_alpha_xi_quarter.json`
   (not fabricated for this phase).

3. Activating the previously-stub `closure_kind: structural` handler:
   O27 (Λ_t = α_ξ² = 81/100) and O28 (Λ_s = −γ²/2 = −1/200) now
   evaluate exactly.

4. Upgrading the cross-consistency audit to v0.2 with a
   `phase5_resolution` block per dual-state entry. The audit reports
   `RESOLVED` iff the Phase-5 alternative YAML evaluates EXACTLY against
   its claimed rational. All 6 dual-state observables now report
   `RESOLVED`.

5. Adding 22 Phase-5 tests (every structural form, every System-R
   constant in the symbol table, plus negative tests for unknown
   identifiers, float-claimed-rationals, mismatch-rejection, and
   unsupported irrationals). Audit tests upgraded to lock the
   `n_dual_state_resolved_by_phase5 == n_dual_state_observables`
   invariant.

### Symbol table (exact sympy expressions)

```
gamma     = 1/10
alpha_xi  = 9/10
beta_pi   = 15/16
eps_sync2 = 1/20
D_Omega   = 67/80
N_gen     = 3
d         = 4
s_face    = 1/4      (BH-entropy face fraction; corpus-documented)
pi        = sympy.pi (exact symbolic; supports rational × π closures)
```

No additional symbols are injected. Any structural_formula using a
name outside this table raises `StructuralEvaluationError` with the
exact unknown-identifier list.

### What stays out of scope (intentionally)

- **PROSP-01/02/03 stability diagnostics**: not loop-class, not
  structural-identity, but multi-N regression diagnostics. A future
  phase would build a separate harness; the tuple compiler does not
  apply.
- **Sign-rule derivation**: the L6/L7 mixed signs within a lemma class
  remain sector-determined. `parity.expected_sign` is still declared
  per YAML; a Phase-3 derivation pass would need prospective
  observables to expose a sub-pattern.
- **Companion-JSON LEGACY forms**: `ckm_closure.json`'s
  `V_us = γ√5` and `V_cb = eps_sync²·√(2/N_gen)` are explicitly
  marked superseded in the registry. The Phase-5 alternative YAMLs
  encode the CURRENT canonical structural form, not the legacy.

### Phase 3 closure_kind taxonomy (extended in Phase 7)

The audit of the 29-entry registry revealed four distinct closure
mechanisms at Phase 3; Phase 7 added a fifth (`stability_diagnostic`)
for the prospective registry's multi-N stability tests:

| `closure_kind` | Count | Mechanism |
|---|---:|---|
| `tree` | 3 | Tree formula alone reaches target; loop factor = 1. |
| `single_loop` | 18 | Tree formula × one loop-class factor = target. |
| `loop_compound` | 6 | Tree formula × product of two loop-class factors = target. |
| `structural` | 2 | Direct System-R algebraic identity (no tree × loop split); loop-class library is not the closure mechanism. |
| `stability_diagnostic` (Phase 7) | 3 | Multi-N stability scores (newton_like_pass, cosmo_compat, etc.) read deterministically from bundle JSONs; the YAML declares which fields to extract and the harness reports BASELINE_RECOVERED / PROSPECTIVE_CONFIRMED / PROSPECTIVE_FALSIFIED with SHA-256-pinned bundle provenance. PROSP-01/02/03. |

Two observables fall in the `structural` class:
- **O27 Lambda_t_cosm_tensor** = α_ξ² = 81/100 — matter-branch
  cosmological-constant tensor diagonal (P4 Eq. branch-resolved).
- **O28 Lambda_s_cosm_tensor** = −γ²/2 = −1/200 — spatial
  cosmological-constant tensor component, via the System-R identity
  eps_sync² = γ/2.

Their registry `lemma: "1+1"` and `lemma: "5+5"` labels are bookkeeping
of the *symbolic factor count*, not literal loop-class products. The
compiler treats them as structural identities and records the closed
form directly, without going through the loop-class matcher.

### Phase 3 schema extension (compact factors syntax)

For compounds, the YAML has an optional top-level `closure_kind` and a
`factors: [...]` array (length 2 in Phase 3), each entry a compact
record:

```yaml
closure_kind: loop_compound
factors:
  - {n: 1, g_support: sub_generation, g_symbol: "1/(2*N_gen)",
     s_channel: "0", w: false, r: false, sign: -1}
  - {n: 1, g_support: none, s_channel: "0", w: false, r: false, sign: -1}
```

For `structural`:

```yaml
closure_kind: structural
structural_formula: "alpha_xi^2"
structural_rational: "81/100"
```

For `tree` / `single_loop`, the existing flat schema is unchanged.
The validator branches on `closure_kind` (default `single_loop` for
backward compatibility with Phase-1/2 YAMLs).

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
