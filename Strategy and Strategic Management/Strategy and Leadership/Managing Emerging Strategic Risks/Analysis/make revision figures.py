"""Figures for the revised manuscript (300 dpi PNG and SVG in Figures and Tables/Revision).

All figures are drawn in shades of grey with line styles and markers that remain legible
when printed in black and white. Data figures read only from Results and Derived files.
"""
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

matplotlib.use("Agg")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
RES = PROJ / "Results"
REV = RES / "Revision"
DER = PROJ / "Datasets" / "Derived"
FIG = PROJ / "Figures and Tables" / "Revision"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Carlito", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#3a3a3a", "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "savefig.facecolor": "white", "axes.titlesize": 9.5})
K, D, M, L, XL = "#1a1a1a", "#4d4d4d", "#7f7f7f", "#b3b3b3", "#e6e6e6"
LABELS = {"geopolitical": "Geopolitical", "trade": "Trade policy", "regulatory": "Regulatory change",
          "cyber": "Cybersecurity", "technology": "AI and technology", "supply": "Supply chain",
          "climate": "Climate and environment", "macro": "Macro-financial", "pandemic": "Pandemic"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def box(ax, x, y, w, h, title, lines, fill="white", edge=D, lw=0.9, title_size=8.6, body_size=7.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fill, ec=edge, lw=lw))
    ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=title_size, fontweight="bold", color=K)
    ax.text(x + w / 2, y + h - 5.4, "\n".join(lines), ha="center", va="top", fontsize=body_size, color=K, linespacing=1.35)


ARROW = dict(arrowstyle="-|>", color=K, lw=0.9, mutation_scale=9)


def figure_model():
    """Figure 1: the three constructs, their link to sensing, seizing and reconfiguring, and the tests."""
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")
    box(ax, 1, 22, 28, 20, "Disclosed exposure", ["Item 1A category intensity", "Convergence breadth",
                                                   "Linkage and interaction", "(sensing as recorded)"], fill=XL)
    box(ax, 36, 22, 28, 20, "Documented response", ["Completed or ongoing actions", "tied to a disclosed threat",
                                                     "Items 1 and 7", "(seizing and reconfiguring)"], fill=XL)
    box(ax, 71, 22, 28, 20, "Realised sensitivity", ["Revenue and operating-", "margin change in shock",
                                                      "years and recovery", "(XBRL accounts)"], fill=XL)
    ax.annotate("", xy=(35.7, 32), xytext=(29.3, 32), arrowprops=dict(arrowstyle="-|>", color=M, lw=0.8, ls="--", mutation_scale=8))
    ax.text(32.5, 34.0, "coverage", ha="center", va="bottom", fontsize=6.8, style="italic", color=D)
    ax.annotate("", xy=(70.7, 32), xytext=(64.3, 32), arrowprops=ARROW)
    ax.text(67.5, 34.0, "H2", ha="center", va="bottom", fontsize=7.6, fontweight="bold", color=K)
    ax.annotate("", xy=(85, 42.6), xytext=(15, 42.6), arrowprops=dict(arrowstyle="-|>", color=K, lw=0.9, mutation_scale=9,
                                                                     connectionstyle="arc3,rad=-0.28"))
    ax.text(50, 57.0, "H1: breadth and later loss", ha="center", va="center", fontsize=7.6, fontweight="bold", color=K)
    ax.annotate("", xy=(50, 54.6), xytext=(50, 42.6), arrowprops=dict(arrowstyle="-|>", color=D, lw=0.8, ls="--", mutation_scale=8))
    ax.text(51.2, 47.5, "H3", ha="left", va="center", fontsize=7.6, fontweight="bold", color=K)
    ax.add_patch(Rectangle((40, 4), 59, 9.4, fc="white", ec=M, lw=0.8, ls="--"))
    ax.text(69.5, 10.0, "Shocks: pandemic (fiscal 2020); war, inflation, rates", ha="center", va="center", fontsize=7.3, color=K)
    ax.text(69.5, 7.0, "and supply pressure (fiscal 2022 to 2023); channel indices", ha="center", va="center", fontsize=7.3, color=K)
    ax.annotate("", xy=(85, 21.6), xytext=(85, 14.4), arrowprops=dict(arrowstyle="-|>", color=M, lw=0.8, mutation_scale=8))
    ax.text(86.2, 18, "exposure-by-shock\nchannel tests", ha="left", va="center", fontsize=6.8, style="italic", color=D)
    save(fig, "Figure One Constructs and Tests")


def figure_framework():
    """Executive diagnostic: Identify, Quantify, Respond, Validate."""
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(7, 64)
    ax.axis("off")
    stages = [
        ("1 Identify", "Which threats are\nspecific to us?",
         ["Separate firm-specific risk", "text from boilerplate", "Note new and dropped", "categories each year"],
         "Evidence: risk register,\nItem 1A changes"),
        ("2 Quantify", "Through which channel would\nit reach the accounts?",
         ["Revenue, cost and asset", "share exposed per channel", "Ability to pass costs", "into prices"],
         "Evidence: segment, supplier\nand contract data"),
        ("3 Respond", "What have we done, with\nwhat resources?",
         ["Completed actions tied to", "a named threat", "Resource commitment", "and owner"],
         "Evidence: action register,\ncapital and contracts"),
        ("4 Validate", "Did exposure behave as\nexpected in the last shock?",
         ["Compare realised revenue", "and margin change with", "the channel estimate", "Revise steps 1 to 3"],
         "Evidence: shock-year\nvariance analysis"),
    ]
    w, gap, x0, y0, h = 22.5, 2.5, 1, 18, 38
    for i, (title, q, lines, ev) in enumerate(stages):
        x = x0 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, y0), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                                    fc=[XL, "#d9d9d9", "#cccccc", "#bfbfbf"][i], ec=D, lw=0.9))
        ax.text(x + w / 2, y0 + h - 1.5, title, ha="center", va="top", fontsize=9.4, fontweight="bold", color=K)
        ax.text(x + w / 2, y0 + h - 6.0, q, ha="center", va="top", fontsize=7.5, style="italic", color=K, linespacing=1.25)
        ax.text(x + w / 2, y0 + h - 14.0, "\n".join(lines), ha="center", va="top", fontsize=7.3, color=K, linespacing=1.35)
        ax.add_patch(Rectangle((x + 1.2, y0 + 1.4), w - 2.4, 7.4, fc="white", ec=M, lw=0.6))
        ax.text(x + w / 2, y0 + 5.1, ev, ha="center", va="center", fontsize=6.9, color=D, linespacing=1.25)
        if i < 3:
            ax.annotate("", xy=(x + w + gap - 0.3, y0 + h / 2), xytext=(x + w + 0.3, y0 + h / 2), arrowprops=ARROW)
    ax.annotate("", xy=(x0 + w / 2, y0 - 0.6), xytext=(x0 + 3 * (w + gap) + w / 2, y0 - 0.6),
                arrowprops=dict(arrowstyle="-|>", color=M, lw=0.9, mutation_scale=9, connectionstyle="arc3,rad=-0.12"))
    ax.text(50, 10.2, "feedback after each shock or annual review", ha="center", va="center", fontsize=7.2, style="italic", color=D)
    caps = [("Sensing", 0, 1), ("Seizing", 2, 2), ("Reconfiguring and learning", 3, 3)]
    for lab, a, b in caps:
        xa, xb = x0 + a * (w + gap), x0 + b * (w + gap) + w
        ax.plot([xa + 0.5, xb - 0.5], [60.2, 60.2], color=K, lw=0.8)
        ax.text((xa + xb) / 2, 61.6, lab, ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=K)
    save(fig, "Figure Six Executive Diagnostic")


if __name__ == "__main__":
    figure_model()
    figure_framework()
    print("conceptual figures written")
