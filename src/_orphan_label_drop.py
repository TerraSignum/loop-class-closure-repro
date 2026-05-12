"""Drop orphan \label{} from non-cited equations/figures/tables in P4."""
import re
from pathlib import Path

P4 = Path("c:/Users/user/Desktop/Emergence/emergent-gr-closure-repro/paper/manuscript.tex")
text = P4.read_text(encoding="utf-8")

# Compute orphans
labels = set(re.findall(r"\\label\{([^}]+)\}", text))
refs = set()
for pat in [r"\\ref\{([^}]+)\}", r"\\eqref\{([^}]+)\}", r"\\autoref\{([^}]+)\}"]:
    refs.update(re.findall(pat, text))
orphans = labels - refs

# Whitelist load-bearing theorems/corollaries — keep their labels even if
# not yet cited (they are theorems by name, intentional references).
keep_orphan = {"thm:cbi", "cor:einstein-triviality", "def:M123",
                "rmk:sketch_four_rationals",
                "sec:falsif", "sec:limitations",
                "tab:conservation_dictionary"}
drop = orphans - keep_orphan

print(f"Total orphans: {len(orphans)}")
print(f"Keeping (load-bearing): {len(keep_orphan & orphans)}")
print(f"Dropping: {len(drop)}")

new_text = text
n_dropped = 0
for orphan in drop:
    # Drop \label{...} occurrences (handle preceding whitespace)
    pattern = r"[\t ]*\\label\{" + re.escape(orphan) + r"\}\n?"
    matches = re.findall(pattern, new_text)
    if matches:
        new_text = re.sub(pattern, "", new_text)
        n_dropped += 1
    else:
        # Try inline removal without trailing newline
        pattern2 = r"\\label\{" + re.escape(orphan) + r"\}"
        if pattern2 in new_text:
            new_text = new_text.replace(pattern2, "")
            n_dropped += 1

print(f"Successfully dropped: {n_dropped}")
P4.write_text(new_text, encoding="utf-8")
print("Wrote P4 manuscript.tex")
