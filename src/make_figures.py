r"""
Generate the four figures of the Paper 3 manuscript.

  Figure 1 - Loop-class library tree (Lemmas 1-8).
  Figure 2 - Deterministic mapping decision tree (n, g, s).
  Figure 3 - Closure residuals across the 26 observables.
  Figure 4 - Negative-control vs registered observables.

Usage:
    python ./src/make_figures.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

FIG_DIR = REPO / "paper" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})


def save_both(fig, stem):
    pdf = FIG_DIR / f"{stem}.pdf"
    png = FIG_DIR / f"{stem}.png"
    fig.savefig(pdf, format="pdf")
    fig.savefig(png, format="png")
    print(f"  Saved: {pdf.relative_to(REPO)} + .png")


def figure_1_lemma_tree():
    """Loop-class library: 8 Lemmas + Pure-Sync class.

    Layout: tall figure with 9 rows of 1 column each (one row per lemma);
    each row has the lemma title on the left, topology factor in the
    middle, and a short physics descriptor on the right. This avoids
    the cross-cell text overlap of an n-column grid layout.
    """
    fig, ax = plt.subplots(figsize=(11.5, 8.5))
    ax.set_axis_off()

    ax.text(0.5, 0.97, r"Loop-factor library $\mathcal{L}$",
            ha="center", fontsize=15, fontweight="bold")
    ax.text(0.5, 0.93,
            r"Each row is one parameter-free class of the form $1 \pm c_\sigma$, "
            r"derived from a Lattice-Defect-FT spinor-trace lemma.",
            ha="center", fontsize=10, style="italic", color="#444")

    rows_data = [
        ("1", "Yukawa-Damping",       r"$1 \pm \gamma/4$",
         r"$d=4$ spinor-trace normalization",                  "#cfe2f3"),
        ("2", "PMNS-Self-Energy",     r"$1 \pm \gamma^{2}/4$",
         "double-Wick contraction",                            "#fce5cd"),
        ("3", "Pure-Self-Energy",     r"$1 \pm \gamma^{2}$",
         "spinor-trace-less vertex",                           "#d9ead3"),
        ("4", "Resummed-Propagator",  r"$1/(1 \pm 2\gamma^{2})$",
         "resummation across two chiralities",                 "#f4cccc"),
        ("5", "Generation",           r"$1 \pm \gamma/N_{\mathrm{gen}}$",
         "generation-summed self-energy",                      "#ead1dc"),
        ("6", "Sub-Generation",       r"$1 \pm \gamma/(2N_{\mathrm{gen}})$",
         r"SU(2)$_L$ doublet/singlet splitting",               "#d0e0e3"),
        ("7", "EW-Mixed",             r"$1 \pm \gamma\,\varepsilon^{2}_{\mathrm{sync}}$",
         "bosonic Lemma-1 with Goldstone vertex",              "#fff2cc"),
        ("8", "Cosmological-Density", r"$1 \pm \gamma/2$",
         "chirality restriction (matter-only)",                "#d9d2e9"),
        ("--", "Pure-Sync",            r"$1 \pm \varepsilon^{2}_{\mathrm{sync}}$",
         "pure Goldstone-vertex bosonic class",                "#e6e6e6"),
    ]
    n_rows = len(rows_data)
    y_top = 0.87
    y_bottom = 0.05
    row_h = (y_top - y_bottom) / n_rows
    box_x = 0.04
    box_w = 0.92

    # Column boundaries inside each row
    x_lemma = 0.06
    x_name = 0.13
    x_class = 0.42
    x_physics = 0.66

    for i, (lemma, name, cls, physics, color) in enumerate(rows_data):
        y = y_top - (i + 1) * row_h
        rect = plt.Rectangle((box_x, y), box_w, row_h * 0.92,
                             facecolor=color, edgecolor="black", lw=1.0)
        ax.add_patch(rect)
        y_mid = y + row_h * 0.46
        ax.text(x_lemma, y_mid, f"{lemma}",
                ha="center", va="center", fontsize=11, fontweight="bold",
                color="#222")
        ax.text(x_name, y_mid, name,
                ha="left", va="center", fontsize=11, fontweight="bold")
        ax.text(x_class, y_mid, cls,
                ha="left", va="center", fontsize=12)
        ax.text(x_physics, y_mid, physics,
                ha="left", va="center", fontsize=10, style="italic",
                color="#444")

    # Header row labels
    y_header = y_top + 0.005
    ax.text(x_lemma, y_header, "Lemma",
            ha="center", va="bottom", fontsize=10, color="#666",
            fontweight="bold")
    ax.text(x_name, y_header, "Class name",
            ha="left", va="bottom", fontsize=10, color="#666",
            fontweight="bold")
    ax.text(x_class, y_header, r"Loop class $L_\sigma$",
            ha="left", va="bottom", fontsize=10, color="#666",
            fontweight="bold")
    ax.text(x_physics, y_header, "Physical origin",
            ha="left", va="bottom", fontsize=10, color="#666",
            fontweight="bold")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save_both(fig, "fig1_lemma_tree")
    plt.close(fig)


def figure_2_decision_tree():
    """Deterministic (n, g, s) decision tree."""
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_axis_off()

    ax.text(0.5, 0.97, "Deterministic loop-class mapping algorithm",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(0.5, 0.93,
            "Input: physical observable; outputs are uniquely determined by topology factors $(n, g, s)$.",
            ha="center", fontsize=10, style="italic", color="#444")

    ax.text(0.5, 0.85, "Spinor-trace component $n \\in \\{0, 1, 2, 4\\}$",
            ha="center", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="#cfe2f3", edgecolor="black"))
    ax.text(0.5, 0.74, "Generation range $g \\in \\{0,\\,1/N_\\mathrm{gen},\\,1/(2N_\\mathrm{gen})\\}$",
            ha="center", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="#fce5cd", edgecolor="black"))
    ax.text(0.5, 0.63, "Sync coupling $s \\in \\{0,\\,\\varepsilon^{2},\\,\\varepsilon^{2}\\text{ pure}\\}$",
            ha="center", fontsize=11, fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="#d9ead3", edgecolor="black"))

    leaves = [
        (0.10, 0.40, "Lemma 1\n$1 \\pm \\gamma/4$",         "#fff2cc"),
        (0.30, 0.40, "Lemma 2\n$1 \\pm \\gamma^{2}/4$",     "#fff2cc"),
        (0.50, 0.40, "Lemma 3\n$1 \\pm \\gamma^{2}$",       "#fff2cc"),
        (0.70, 0.40, "Lemma 4\n$1/(1 \\pm 2\\gamma^{2})$",  "#fff2cc"),
        (0.90, 0.40, "Lemma 5\n$1 \\pm \\gamma/N$",         "#fff2cc"),
        (0.10, 0.20, "Lemma 6\n$1 \\pm \\gamma/(2N)$",      "#fff2cc"),
        (0.30, 0.20, "Lemma 7\n$1 \\pm \\gamma\\varepsilon^{2}$", "#fff2cc"),
        (0.50, 0.20, "Lemma 8\n$1 \\pm \\gamma/2$",         "#fff2cc"),
        (0.70, 0.20, "Pure-sync\n$1 \\pm \\varepsilon^{2}$",       "#fff2cc"),
    ]
    for (x, y, txt, c) in leaves:
        ax.text(x, y, txt, ha="center", va="center", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.4",
                          facecolor=c, edgecolor="black", lw=1.0))

    ax.text(0.5, 0.05,
            "Sign $+$ for CP-/T-even, $-$ for CP-/T-odd "
            "(T-parity source axiom on the defect field)",
            ha="center", fontsize=9, color="#444", style="italic")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save_both(fig, "fig2_decision_tree")
    plt.close(fig)


def figure_3_closure_residuals():
    """Residuals across the 26 observables with tier coloring.

    Tier counts and threshold annotations are derived from the
    registry, not hardcoded; the strict program-wide thresholds
    are EXACT < 0.40 % and PRECISE < 2.50 %.
    """
    EXACT_THRESHOLD_PCT = 0.40
    PRECISE_THRESHOLD_PCT = 2.50

    with open(REPO / "data" / "observable_registry.json",
              "r", encoding="utf-8") as f:
        reg = json.load(f)
    obs = reg["observables"]
    ids = [o["id"] for o in obs]
    res = [o["expected_residual_pct_after_loop"] for o in obs]

    # Recompute tier strictly from residual rather than trust the
    # registry's tier_after_loop label.
    def _tier(r):
        if abs(r) < EXACT_THRESHOLD_PCT:
            return "EXACT"
        if abs(r) < PRECISE_THRESHOLD_PCT:
            return "PRECISE"
        return "OUT_OF_TIER"

    tiers = [_tier(r) for r in res]
    n_exact = sum(1 for t in tiers if t == "EXACT")
    n_precise = sum(1 for t in tiers if t == "PRECISE")
    n_total = len(tiers)
    n_contradict = n_total - n_exact - n_precise
    color = ["#1f7a1f" if t == "EXACT" else "#1f77b4" for t in tiers]

    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.bar(ids, res, color=color, edgecolor="black", lw=0.8)
    ax.axhline(PRECISE_THRESHOLD_PCT, color="#888", linestyle=":", lw=1,
               label=f"PRECISE cut ({PRECISE_THRESHOLD_PCT}%)")
    ax.axhline(EXACT_THRESHOLD_PCT, color="#888", linestyle="-.", lw=1,
               label=f"EXACT cut ({EXACT_THRESHOLD_PCT}%)")
    ax.set_yscale("log")
    ax.set_ylim(1e-4, 5)
    ax.set_ylabel("|residual| (%, log scale)")
    ax.set_xlabel("Observable ID")
    ax.set_title(
        f"Closure-table residuals across {n_total} observables "
        f"({n_exact} EXACT + {n_precise} PRECISE; "
        f"{n_contradict} contradictions)",
        pad=10)
    ax.legend(loc="upper right", framealpha=0.9)
    plt.xticks(rotation=45, ha="right")
    save_both(fig, "fig3_closure_residuals")
    plt.close(fig)


def figure_4_negative_controls():
    """Negative-controls vs registered observables visualization."""
    with open(REPO / "data" / "negative_controls.json", "r", encoding="utf-8") as f:
        nc = json.load(f)
    with open(REPO / "data" / "observable_registry.json", "r", encoding="utf-8") as f:
        reg = json.load(f)

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_axis_off()
    ax.text(0.5, 0.96, "Closure domain $G_{\\mathrm{claim}}^{\\mathrm{auth}}$ and its complement",
            ha="center", fontsize=13, fontweight="bold")

    n_reg = len(reg["observables"])
    n_nc = len(nc["controls"])
    EXACT_THRESHOLD_PCT = 0.40
    PRECISE_THRESHOLD_PCT = 2.50
    n_exact = sum(1 for o in reg["observables"]
                  if abs(o["expected_residual_pct_after_loop"])
                     < EXACT_THRESHOLD_PCT)
    n_precise = sum(1 for o in reg["observables"]
                    if EXACT_THRESHOLD_PCT
                       <= abs(o["expected_residual_pct_after_loop"])
                       < PRECISE_THRESHOLD_PCT)
    n_contradict = n_reg - n_exact - n_precise

    in_box = plt.Rectangle((0.04, 0.20), 0.46, 0.65,
                           facecolor="#d9ead3", edgecolor="black", lw=1.4)
    ax.add_patch(in_box)
    ax.text(0.27, 0.82, "Inside $G_{\\mathrm{claim}}^{\\mathrm{auth}}$",
            ha="center", va="top", fontsize=11, fontweight="bold")
    ax.text(0.27, 0.76,
            f"{n_reg} observables; deterministic mapping closes\n"
            f"to PRECISE-or-better tier under Lemmas 1-8.\n"
            f"{n_exact} EXACT + {n_precise} PRECISE; "
            f"{n_contradict} contradictions.",
            ha="center", va="top", fontsize=9.5)

    out_box = plt.Rectangle((0.52, 0.20), 0.44, 0.65,
                            facecolor="#f4cccc", edgecolor="black", lw=1.4)
    ax.add_patch(out_box)
    ax.text(0.74, 0.82, "Negative controls $\\overline{G_{\\mathrm{claim}}^{\\mathrm{auth}}}$",
            ha="center", va="top", fontsize=11, fontweight="bold")
    txt = ""
    for c in nc["controls"]:
        txt += f"NC{c['id'][-2:]}  {c['name']}\n"
    ax.text(0.74, 0.76, txt,
            ha="center", va="top", fontsize=8.5, family="monospace")
    ax.text(0.74, 0.27,
            f"Algorithm must return\nNO_CLAIM for all {n_nc} controls.",
            ha="center", va="top", fontsize=9, style="italic", color="#555")

    ax.text(0.5, 0.10,
            "Falsification: if the algorithm assigns any negative control to a closing class, the algorithm falls.",
            ha="center", fontsize=9.5, color="#440000")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    save_both(fig, "fig4_negative_controls")
    plt.close(fig)


def main():
    print("Generating Paper 3 figures into paper/figures/")
    print()
    figure_1_lemma_tree()
    figure_2_decision_tree()
    figure_3_closure_residuals()
    figure_4_negative_controls()
    print()
    print("All four figures generated.")


if __name__ == "__main__":
    main()
