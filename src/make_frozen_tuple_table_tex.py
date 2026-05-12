"""Frozen topology-tuple sheet for the loop-class manuscript.

Reads the canonical source of truth `data/observable_registry.json`
and emits a LaTeX table that lists, for every observable in the
closure domain, the full deterministic topology tuple
$(n, g, s, w, r)$ together with the lemma cell and a one-line
structural justification keyed to the diagram type. This is the
reproducibility certificate behind Theorem~\\ref{thm:determinism}:
it is a transcription of the registry, not a re-derivation.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "observable_registry.json"
OUT = REPO / "paper" / "tables" / "tab_frozen_tuples.tex"
OUT.parent.mkdir(parents=True, exist_ok=True)

JUSTIFICATIONS = {
    "O01": "single Yukawa vertex, one spinor-trace closure",
    "O02": "$\\Omega_{\\rm DM}h^{2}$: gen-summed Yukawa-driven density (Lemma~6 sub-gen)",
    "O03": "$w_{\\rm DE}$: $-1$ shifted by single Yukawa-loop correction",
    "O04": "QCD running with gen-summed quark loops, $g=1/(2\\Ngen)$",
    "O05": "charged-lepton Yukawa-exponent ratio, sub-gen lepton splitting",
    "O06": "EW mixing tree value, no loop dressing",
    "O07": "horizon-area tree quarter, no loop dressing",
    "O08": "Einstein-gap tree $2/3$, no loop dressing",
    "O09": "PMNS reactor angle: double-Wick $\\langle\\Xi\\Xi^{\\dagger}\\Xi\\Xi^{\\dagger}\\rangle$",
    "O10": "PMNS solar angle: double-Wick on the same family",
    "O11": "PMNS atmospheric angle: 2-loop sub-gen $\\times$ pure-Yukawa",
    "O12": "PMNS Dirac CP-phase: stand-alone $\\pi$ basis-scale, 2-loop compound",
    "O13": "CKM $V_{us}$: gen-summed sub-generation mixing",
    "O14": "CKM $V_{cb}$: gen-summed sub-generation mixing (heavy-light)",
    "O15": "Higgs mass: single Yukawa-driven mass-counterterm",
    "O16": "$m_{W}$: EW-mixed loop with Goldstone vertex, $s=\\esync$",
    "O17": "$m_{Z}$: EW-mixed loop with Goldstone vertex, $s=\\esync$",
    "O18": "$\\Gamma_{W}$: EW-mixed decay-width, $s=\\esync$",
    "O19": "$\\Gamma_{Z}$: EW-mixed decay-width, $s=\\esync$",
    "O20": "$H_{0}$: cosmological Yukawa-class running, single trace",
    "O21": "$T_{\\rm RH}$: resummed inflaton-decay propagator, $r=1$",
    "O22": "$n_{s}$: EW-precision tilt with Goldstone, $s=\\esync$",
    "O23": "$\\sigma_{8}$: 2-loop Yukawa $\\times$ generation",
    "O24": "$\\eta_{B}$: 2-loop Yukawa $\\times$ generation (asymmetry)",
    "O25": "$\\Lambda_{\\rm QCD}$: 2-loop pure-$\\esync$ $\\times$ EW-mixed",
    "O26": "$\\omega_{b}h^{2}$: 2-loop pure-self-energy $\\times$ Yukawa-density",
    "O27": "$\\Lambda_{t}$: time-time cosmological tensor, $\\axi^{2}$",
    "O28": "$\\Lambda_{s}$: spatial-isotropic cosmological tensor, $-\\gamma^{2}/2$",
    "O29": "$Y_{p}$: BBN refinement pipeline; sector-Yukawa class",
}


def fmt_n(v):
    if isinstance(v, str):
        return f"${v}$"
    return f"{v}"


def fmt_g(v):
    if v in (0, "0"):
        return "0"
    if v == "1/(2*N_gen)":
        return r"$1/(2\Ngen)$"
    if v == "1/N_gen":
        return r"$1/\Ngen$"
    s = str(v).replace("*", r"\,").replace("N_gen", r"\Ngen")
    return f"${s}$"


def fmt_s(v):
    if v in (0, "0"):
        return "0"
    if isinstance(v, str):
        s = (v.replace("eps_sync2", r"\esync")
             .replace("eps^2", r"\esync")
             .replace("gamma", r"\gamma")
             .replace("*", r"\,"))
        return f"${s}$"
    return f"${v}$"


def fmt_w(d):
    if "two_loop_compound" in d and d["two_loop_compound"]:
        comps = d.get("component_factors", [])
        flags = [c.get("double_wick", False) for c in comps]
        return "1" if any(flags) else "0"
    return "1" if d.get("double_wick", False) else "0"


def fmt_r(d):
    if "two_loop_compound" in d and d["two_loop_compound"]:
        comps = d.get("component_factors", [])
        flags = [c.get("resummed", False) for c in comps]
        return "1" if any(flags) else "0"
    return "1" if d.get("resummed", False) else "0"


def fmt_lemma(v):
    if v is None:
        return "tree"
    s = str(v).replace("pure-eps2", r"pure-$\esync$")
    return s


def fmt_obs_name(name):
    return name.replace("_", r"\_")


def main():
    reg = json.loads(SRC.read_text(encoding="utf-8"))
    rows = reg["observables"]
    lines = []
    A = lines.append
    A(r"\begin{tabular}{@{}l p{0.21\textwidth} c c c c c l "
      r"p{0.30\textwidth}@{}}")
    A(r"\toprule")
    A(r"ID & Observable & $n$ & $g$ & $s$ & $w$ & $r$ & "
      r"Lemma & Structural justification \\")
    A(r"\midrule")
    for d in rows:
        oid = d["id"]
        name = fmt_obs_name(d["name"])
        n = fmt_n(d["n_spinor_trace"])
        g = fmt_g(d["g_generation"])
        s = fmt_s(d["s_sync_coupling"])
        w = fmt_w(d)
        r = fmt_r(d)
        lemma = fmt_lemma(d.get("lemma"))
        just = JUSTIFICATIONS.get(oid, d.get("sector", ""))
        A(f"{oid} & \\texttt{{{name}}} & {n} & {g} & {s} & "
          f"{w} & {r} & {lemma} & {just} \\\\")
    A(r"\bottomrule")
    A(r"\end{tabular}")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}  ({len(rows)} observables)")


if __name__ == "__main__":
    main()
