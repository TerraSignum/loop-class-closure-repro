"""LaTeX table generator for P3 reclassification audit cases."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
JSON = REPO / "data" / "reclassification_cases.json"
OUT = REPO / "paper" / "tables" / "tab_reclassification_audit.tex"
OUT.parent.mkdir(parents=True, exist_ok=True)

d = json.loads(JSON.read_text())
cases = d["documented_cases"]

lines = []
A = lines.append
A(r"\begin{tabular}{l p{0.18\textwidth} p{0.16\textwidth} p{0.16\textwidth}"
  r" c c c c c c}")
A(r"\toprule")
A(r"ID & Observable & $\sigma_{\rm alt}$ (orig.) & "
  r"$\sigma_{\rm new}$ (post) & R1 & R2 & R3 & R4 & R5 & Status \\")
A(r"\midrule")
for c in cases:
    obs = c["observable"].replace("_", r"\_")
    alt = f"L{c['sigma_alt']['lemma']}"
    new = f"L{c['sigma_new']['lemma']}"
    r1 = r"\checkmark" if c["R1_satisfied"] else r"$\times$"
    r2 = r"\checkmark" if c["R2_satisfied"] else r"$\times$"
    r3 = r"\checkmark" if c["R3_satisfied"] else r"$\times$"
    r4 = r"\checkmark" if c["R4_satisfied"] else r"$\times$"
    r5 = r"\checkmark" if c["R5_satisfied"] else r"$\times$"
    status = c["status"].replace("_", r"\_")[:18]
    A(f"{c['id']} & {obs} & {alt} & {new} & {r1} & {r2} & {r3} & "
      f"{r4} & {r5} & {status} \\\\")
A(r"\bottomrule")
A(r"\end{tabular}")
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT}")
