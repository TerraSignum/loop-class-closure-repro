"""Quick orphan-label audit for the P4 manuscript."""
import re
from pathlib import Path

P4 = Path("c:/Users/user/Desktop/Emergence/emergent-gr-closure-repro/paper/manuscript.tex")
text = P4.read_text(encoding="utf-8")

labels = set(re.findall(r"\\label\{([^}]+)\}", text))
refs = set()
for pat in [r"\\ref\{([^}]+)\}", r"\\eqref\{([^}]+)\}", r"\\autoref\{([^}]+)\}"]:
    refs.update(re.findall(pat, text))

orphans = labels - refs
print(f"Total labels: {len(labels)}")
print(f"Total refs:   {len(refs)}")
print(f"Orphan labels: {len(orphans)}")
print()


def cat(o):
    if o.startswith("sec:"):
        return "sec"
    if o.startswith("fig:"):
        return "fig"
    if o.startswith("eq:"):
        return "eq"
    if o.startswith(("thm:", "lem:", "cor:", "def:", "prop:", "rmk:", "remark:", "axiom:")):
        return "thm/lem/cor/def"
    if o.startswith("tab:"):
        return "tab"
    return "other"


by_cat = {}
for o in sorted(orphans):
    by_cat.setdefault(cat(o), []).append(o)

for c, items in by_cat.items():
    print(f"  {c}: {len(items)}")
    for it in items:
        print(f"    {it}")
