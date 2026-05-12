# loop-class-closure-repro

**Deterministic loop-class mapping for cross-sector observable corrections.**

[![CI: reproduce](https://github.com/TerraSignum/loop-class-closure-repro/actions/workflows/reproduce.yml/badge.svg)](https://github.com/TerraSignum/loop-class-closure-repro/actions/workflows/reproduce.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This repository reproduces the deterministic loop-class mapping algorithm
and the closure of 26 cross-sector observables under a finite, parameter-free
loop-factor library (Lemmas 1-8 plus a pure-sync class).

## Result in one line

```
Deterministic loop-class mapping algorithm closes 26/26 observables.
Strict <0.4% / <2.5% post-loop cut: 20 EXACT + 6 PRECISE; 0 contradictions.
Looser <1% EXACT cut: all 26 observables fall in EXACT (max residual 0.84%).
Negative controls correctly return NO_CLAIM.
Reclassifications bounded by the protocol of Section 6
(at most two per observable; further requirements falsify the theorem).
```

## Scope

This package answers the reviewer question

> *Why are the loop factors not chosen after the fact?*

by giving an explicit, deterministic, lookup-only mapping
algorithm that returns a unique loop class for every observable as a
function of three topology factors `(n, g, s)`:
* **n**: spinor-trace component count (0, 1, 2, or 4)
* **g**: generation range (0, 1/N_gen, or 1/(2*N_gen))
* **s**: sync coupling (0, eps^2, or pure eps^2)

Plus a `+/-` sign from the CP/T eigenparity (T-parity source axiom
on the defect field, fixing the bounce negative mode to be T-odd).

## What this is **not**

- Not a complete Standard-Model derivation
- Not a complete Quantum-Gravity theory
- Not a free-parameter fit
- Not a claim outside the canonical variation regime

## Installation (Windows PowerShell)

```powershell
git clone https://github.com/TerraSignum/loop-class-closure-repro.git
cd loop-class-closure-repro

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Reproduce the result

```powershell
python .\src\classify_observable.py --observable O01
python .\src\recompute_loop_closures.py
python .\src\run_negative_controls.py
python .\src\validate_reclassification.py
pytest
```

## Repository structure

```
loop-class-closure-repro/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── pyproject.toml
├── data/
│   ├── loop_class_library.json
│   ├── allowed_topological_multipliers.json
│   ├── observable_registry.json
│   ├── negative_controls.json
│   └── reclassification_cases.json
├── src/
│   ├── classify_observable.py
│   ├── recompute_loop_closures.py
│   ├── run_negative_controls.py
│   ├── validate_reclassification.py
│   ├── compute_yukawa_cluster_p.py
│   ├── verify_phase_i_iv_bundle.py
│   ├── verify_lambda_qcd_alpha_s.py
│   └── make_figures.py
├── tests/
│   ├── test_mapping_determinism.py
│   ├── test_closure_results.py
│   ├── test_no_free_class_selection.py
│   ├── test_negative_controls_fail.py
│   ├── test_reclassification_rules.py
│   ├── test_falsification.py
│   ├── test_yukawa_cluster_p.py
│   ├── test_phase_i_iv_bundle.py
│   └── test_lambda_qcd_alpha_s.py
├── outputs/
│   ├── expected_output.txt
│   ├── closure_table.json
│   ├── closure_table.csv
│   ├── negative_control_results.json
│   └── reclassification_report.json
├── paper/
│   ├── manuscript.tex
│   ├── manuscript.pdf
│   └── figures/
└── .github/workflows/
    └── reproduce.yml
```

## The loop-factor library (Lemmas 1-8)

| Lemma | Class | Topology factor | Physics                                            |
|-------|------:|-----------------|----------------------------------------------------|
| 1 | Yukawa-Damping       | `gamma/4`             | d=4 spinor-trace normalization                  |
| 2 | PMNS-Self-Energy     | `gamma^2/4`           | Double-Wick contraction                         |
| 3 | Pure-Self-Energy     | `gamma^2`             | Spinor-trace-less vertex                        |
| 4 | Resummed-Propagator  | `2*gamma^2`           | Resummation across two chiralities              |
| 5 | Generation           | `gamma/N_gen`         | Generation-summed self-energy                   |
| 6 | Sub-Generation       | `gamma/(2*N_gen)`     | SU(2)_L doublet/singlet splitting               |
| 7 | EW-Mixed             | `gamma*eps_sync^2`    | Bosonic Lemma-1 with Goldstone vertex factor    |
| 8 | Cosmological-Density | `gamma/2`             | Chirality restriction (matter-only)             |

## Falsification

The closure mechanism fails if any of (matching the manuscript):

1. **F1**: An observable in `G_claim^auth` cannot be assigned to any
   library class (after at most two reclassifications). The
   reclassification cap is enforced inside this trigger; a third
   required reclassification is therefore an F1 falsification, not
   a separate trigger.
2. **F2**: The algorithm predicts a closing loop class for a
   negative-control observable that should return `NO_CLAIM`
   (quark mass ratios, supersymmetric-partner masses, QG-UV
   cutoffs, etc.). This is the scope-discipline trigger.
3. **F3**: An observable cannot be classified consistently across
   the QFT and gravitational/cosmological sectors of the wider
   program — i.e., the same `(n, g, s, w, r)` tuple returns
   different loop-class predictions in two sectors. This is the
   cross-sector consistency trigger.

A non-uniqueness on `(n, g, s)` alone is an input-validation
condition (the disambiguating flags `w` and `r` exist for the
two double-occupancy cells `(1, 0, 0)` and `(4, 0, 0)`); it is
not a separate falsification trigger.

## Citation

```bibtex
@misc{bucciarelli2026loopclass,
  author    = {Bucciarelli, Sandro},
  title     = {Deterministic loop-class mapping for cross-sector observable corrections},
  year      = {2026},
  version   = {0.1.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX}
}
```

## License

MIT License. See [LICENSE](LICENSE).
