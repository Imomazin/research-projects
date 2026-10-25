"""Generate the manuscript figures from the Results and Derived files (300 dpi PNG and SVG)."""
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

matplotlib.use("Agg")
HERE = Path(__file__).resolve().parent
RES = HERE.parent / "Results"
DER = HERE.parent / "Datasets" / "Derived"
FIG = HERE.parent / "Figures and Tables"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "Carlito", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#4a4a4a", "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "axes.titlesize": 9.5, "axes.titleweight": "bold",
                     "savefig.facecolor": "white"})
CHAR, BLUE, TEAL, GREY, LIGHT = "#2b2d33", "#3c6e9f", "#2f8f83", "#8a8f98", "#d9dce1"
LABELS = {"geopolitical": "Geopolitical", "trade": "Trade policy", "regulatory": "Regulatory change",
          "cyber": "Cybersecurity", "technology": "AI and technology", "supply": "Supply chain",
          "climate": "Climate and environment", "macro": "Macro-financial", "pandemic": "Pandemic"}
SOURCE = "Source: SEC EDGAR 10-K filings, fiscal years 2017 to 2025; 787 sampled US non-financial firms; author's analysis."


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


# Figure 1: research model
fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.set_xlim(0, 100)
ax.set_ylim(0, 50)
ax.axis("off")


def box(x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc="white", ec=color, lw=1.1))
    ax.text(x + w / 2, y + h - 2.4, title, ha="center", va="top", fontsize=8.6, fontweight="bold", color=color)
    ax.text(x + w / 2, y + h - 6.6, body, ha="center", va="top", fontsize=7.4, color=CHAR, linespacing=1.35)


box(1, 25, 33, 18, "Disclosed exposure (Item 1A)", "Intensity in nine categories\nConvergence breadth\nLinkage density\nUpdating", BLUE)
box(1, 1, 33, 18, "Documented response (Items 1, 7)", "Action sentences by category\nResponse coverage\nProfile alignment\nResource reconfiguration", TEAL)
box(37, 37, 30, 12, "Systemic shocks", "Pandemic, fiscal 2020\nWar, inflation and supply pressure, 2022", GREY)
box(71, 12, 28, 19, "Organisational resilience", "Severity: revenue and\noperating-margin fall\nRecovery: revenue regained\nPanel growth, adverse years", CHAR)
arrow = dict(arrowstyle="-|>", color=CHAR, lw=0.9, mutation_scale=9)
ax.annotate("", xy=(70.4, 26), xytext=(34.6, 33), arrowprops=arrow)
ax.annotate("", xy=(70.4, 17), xytext=(34.6, 10), arrowprops=arrow)
ax.annotate("", xy=(52, 22.2), xytext=(52, 36.4), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.9, ls="--", mutation_scale=9))
ax.annotate("", xy=(16.5, 19.6), xytext=(16.5, 24.4), arrowprops=dict(arrowstyle="<|-|>", color=GREY, lw=0.8, mutation_scale=8))
ax.text(38, 33.4, "H1: breadth", fontsize=7.6, color=BLUE, style="italic")
ax.text(38, 8.6, "H2: coverage", fontsize=7.6, color=TEAL, style="italic")
ax.text(18, 22, "H3: moderation", fontsize=7.4, color=GREY, style="italic", va="center")
ax.text(53, 23.0, "shock context", fontsize=7.2, color=GREY, style="italic", ha="left")
save(fig, "Figure One Research Model")

# Figure 2: share of firms with each category material
tr = pd.read_csv(RES / "Disclosure Trends.csv", index_col=0)
fig, axes = plt.subplots(3, 3, figsize=(7.2, 5.4), sharex=True, sharey=True)
for ax, (c, lab) in zip(axes.flat, LABELS.items()):
    ax.plot(tr.index, tr[f"share_material_{c}"] * 100, color=BLUE, lw=1.6, marker="o", ms=2.5)
    ax.set_title(lab, loc="left")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", color=LIGHT, lw=0.5)
    ax.set_xticks([2017, 2019, 2021, 2023, 2025])
fig.supylabel("Firms with category material (%)", fontsize=9)
for ax in axes[-1, :]:
    ax.set_xlabel("Fiscal year")
fig.tight_layout()
save(fig, "Figure Two Category Prevalence")

# Figure 3: convergence and homogenisation
disp = pd.read_csv(RES / "Breadth Dispersion.csv", index_col=0)
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(7.2, 2.6))
a1.plot(disp.index, disp["mean"], color=BLUE, lw=1.8, marker="o", ms=3, label="All firms")
a1.plot(disp.index, disp["breadth_mean_balanced"], color=TEAL, lw=1.2, ls="--", label="Firms present every year")
a1.set_title("Mean convergence breadth", loc="left")
a1.set_ylabel("Material categories (0 to 9)")
a1.legend(frameon=False, fontsize=7, loc="lower right")
a2.plot(disp.index, disp["cv"], color=CHAR, lw=1.8, marker="o", ms=3)
a2.set_title("Dispersion across firms", loc="left")
a2.set_ylabel("Coefficient of variation of breadth")
a3.plot(disp.index, disp["linkage_mean"] * 100, color=TEAL, lw=1.8, marker="o", ms=3)
a3.set_title("Linked risk sentences", loc="left")
a3.set_ylabel("Share of Item 1A sentences (%)")
for a in (a1, a2, a3):
    a.set_xticks([2017, 2019, 2021, 2023, 2025])
    a.grid(axis="y", color=LIGHT, lw=0.5)
    a.set_xlabel("Fiscal year")
fig.tight_layout()
save(fig, "Figure Three Convergence and Homogenisation")

# Figure 4: breadth by division
div = pd.read_csv(RES / "Breadth by Division.csv", index_col=0)
counts = pd.read_csv(DER / "Research Panel.csv", usecols=["division", "fiscal_year", "cik"])
n = counts[counts["fiscal_year"] == 2018].groupby("division")["cik"].nunique()
div = div[[c for c in div.columns if c.isdigit() and 2017 <= int(c) <= 2025]]
div = div.loc[[d for d in div.index if n.get(d, 0) >= 15]]
fig, ax = plt.subplots(figsize=(7.2, 2.9))
im = ax.imshow(div.values, aspect="auto", cmap="Blues", vmin=4, vmax=9)
ax.set_xticks(range(div.shape[1]), div.columns)
ax.set_yticks(range(div.shape[0]), [f"{d} (n={n[d]})" for d in div.index])
for i in range(div.shape[0]):
    for j in range(div.shape[1]):
        v = div.values[i, j]
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7, color="white" if v > 7 else CHAR)
ax.spines[:].set_visible(False)
ax.set_xlabel("Fiscal year")
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("Mean breadth")
ax.set_title("Mean convergence breadth by SIC division", loc="left")
save(fig, "Figure Four Breadth by Division")

# Figure 5: coefficient plot of the hypothesis tests
e = pd.read_csv(RES / "Episode Models.csv")
rows = [("A|H1|severity", "breadth_z", "Pandemic: revenue fall, FY2020 vs FY2019"),
        ("A|H1|margin_change", "breadth_z", "Pandemic: operating-margin change"),
        ("A|H1|recovery", "breadth_z", "Pandemic: revenue recovery to FY2022"),
        ("B|H1|margin_change", "breadth_z", "2022 shock: margin change, FY2022 vs FY2021"),
        ("B|H1|severity", "breadth_z", "2022 shock: revenue change, FY2023 vs FY2021"),
        ("A|H2|severity", "coverage_z", "Pandemic: revenue fall, FY2020 vs FY2019"),
        ("A|H2|recovery", "coverage_z", "Pandemic: revenue recovery to FY2022"),
        ("B|H2|margin_change", "coverage_z", "2022 shock: margin change, FY2022 vs FY2021"),
        ("A|H3|severity", "breadth_z:coverage_z", "Pandemic: revenue fall, FY2020 vs FY2019"),
        ("A|H3|recovery", "breadth_z:coverage_z", "Pandemic: revenue recovery to FY2022")]
fig, ax = plt.subplots(figsize=(7.2, 3.9))
for i, (m, t, lab) in enumerate(rows):
    r = e[(e["model"] == m) & (e["term"] == t)].iloc[0]
    col = {"breadth_z": BLUE, "coverage_z": TEAL}.get(t, CHAR)
    y = len(rows) - 1 - i
    ax.plot([r["ci_low"], r["ci_high"]], [y, y], color=col, lw=1.4)
    ax.plot(r["coef"], y, "o", color=col, ms=4.5)
ax.axvline(0, color=GREY, lw=0.7, ls=":")
names = {"breadth_z": "Breadth (H1): ", "coverage_z": "Coverage (H2): ", "breadth_z:coverage_z": "Breadth x coverage (H3): "}
ax.set_yticks(range(len(rows)), [names[t] + lab for _, t, lab in rows][::-1])
ax.set_xlabel("Coefficient per standard deviation, with 95% confidence interval (log revenue or margin units)")
ax.grid(axis="x", color=LIGHT, lw=0.5)
save(fig, "Figure Five Hypothesis Estimates")
print("figures written")
