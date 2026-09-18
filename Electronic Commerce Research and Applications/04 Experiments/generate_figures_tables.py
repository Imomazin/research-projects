#!/usr/bin/env python3
"""Generate P3 publication figures and tables from canonical result files.

Every figure/table is produced directly from the stored CSV/JSON results in
04 Experiments/results/ (no re-simulation), so they trace to the committed
provenance. Colourblind-safe Okabe-Ito palette; PNGs at 300 dpi.
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
BASE = os.path.abspath(os.path.join(HERE, "..", "05 Manuscript"))
FIG = os.path.join(BASE, "figures")
TAB = os.path.join(BASE, "tables")
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

OI = {"black": "#000000", "orange": "#E69F00", "skyblue": "#56B4E9", "green": "#009E73",
      "yellow": "#F0E442", "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7"}
EST_COLOR = {"difference-in-means": OI["vermillion"], "outcome-regression": OI["orange"],
             "ipw": OI["skyblue"], "aipw": OI["blue"]}
plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 300, "font.size": 10,
                     "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True})


def _csv(name):
    p = os.path.join(RES, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("figure:", os.path.relpath(path, BASE))


def md_table(df, path, floatfmt=4):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(f"{v:.{floatfmt}f}" if isinstance(v, (int, float, np.floating)) and not isinstance(v, bool) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("table:", os.path.relpath(path, BASE))


# ---- F1: heuristic vs causal (E1) ----
def fig_e1():
    ch = _csv("p3_e1_canonical_channels.csv")
    if ch is None:
        return
    ch = ch.set_index("channel")
    order = ["search", "email", "social", "retargeting", "display"]
    ch = ch.loc[[c for c in order if c in ch.index]]
    x = np.arange(len(ch))
    w = 0.25
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.bar(x - w, ch["true_effect"], w, label="True causal effect", color=OI["black"])
    ax.bar(x, ch["aipw_effect"], w, label="AIPW estimate (observational)", color=OI["blue"])
    ax.bar(x + w, ch["heuristic_last-touch"], w, label="Last-touch credit share", color=OI["vermillion"])
    ax.set_xticks(x); ax.set_xticklabels(ch.index)
    ax.set_ylabel("effect (per-exposure) / credit share")
    ax.set_title("P3-E1: heuristic credit vs incremental causal contribution")
    ax.legend(fontsize=8)
    save(fig, "fig_e1_heuristic_vs_causal.png")


# ---- F2/F3: E2 recovery bias & coverage ----
def fig_e2():
    s = _csv("p3_e2_canonical_ate_summary.csv")
    if s is None:
        return
    conds = list(dict.fromkeys(s["condition"]))
    ests = ["difference-in-means", "outcome-regression", "ipw", "aipw"]
    x = np.arange(len(conds)); w = 0.2
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for i, e in enumerate(ests):
        sub = s[s["estimator"] == e].set_index("condition").reindex(conds)
        ax.bar(x + (i - 1.5) * w, sub["mean_bias"], w, yerr=sub["rmse"], capsize=2,
               label=e, color=EST_COLOR[e])
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("mean bias (bars) ± RMSE")
    ax.set_title("P3-E2: ATE recovery bias by estimator and condition")
    ax.legend(fontsize=8)
    save(fig, "fig_e2_ate_bias.png")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i, e in enumerate(ests):
        sub = s[s["estimator"] == e].set_index("condition").reindex(conds)
        ax.bar(x + (i - 1.5) * w, sub["ci_coverage_95"], w, label=e, color=EST_COLOR[e])
    ax.axhline(0.95, color="k", lw=0.8, ls="--", label="nominal 0.95")
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("95% CI coverage"); ax.set_ylim(0, 1.05)
    ax.set_title("P3-E2: confidence-interval coverage by estimator and condition")
    ax.legend(fontsize=8)
    save(fig, "fig_e2_ci_coverage.png")


# ---- F4: E6 confounding + overlap ----
def fig_e6_confounding():
    s = _csv("p3_e6_canonical_summary.csv")
    if s is None:
        return
    g = s[(s["sweep"] == "confounding_strength") & (s["estimator"] == "aipw")].copy()
    g["value"] = g["value"].astype(float); g = g.sort_values("value")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(g["value"], g["mean_bias"], "o-", color=OI["blue"], label="AIPW mean bias")
    ax.plot(g["value"], g["rmse"], "s--", color=OI["orange"], label="AIPW RMSE")
    ax.set_xlabel("confounding strength"); ax.set_ylabel("bias / RMSE")
    ax2 = ax.twinx()
    ax2.plot(g["value"], g["mean_min_propensity"], "^:", color=OI["green"], label="min propensity (overlap)")
    ax2.set_ylabel("min propensity"); ax2.grid(False)
    ax.set_title("P3-E6: AIPW error and overlap vs confounding strength")
    l1, la1 = ax.get_legend_handles_labels(); l2, la2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, la1 + la2, fontsize=8, loc="upper left")
    save(fig, "fig_e6_confounding_overlap.png")


# ---- F5: E6 unmeasured confounding & measurement error / selection ----
def fig_e6_failure():
    s = _csv("p3_e6_canonical_summary.csv")
    if s is None:
        return
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    um = s[(s["sweep"] == "unmeasured_confounding") & (s["estimator"] == "aipw")]
    order = ["none", "x4", "x3,x4", "x2,x3,x4", "x0"]
    um = um.set_index("value").reindex([o for o in order if o in set(um["value"])])
    axes[0].bar(range(len(um)), um["mean_bias"], color=OI["vermillion"])
    axes[0].set_xticks(range(len(um))); axes[0].set_xticklabels(um.index, rotation=20, fontsize=8)
    axes[0].set_ylabel("AIPW mean bias"); axes[0].set_title("Unmeasured confounding (hidden covariates)")

    for sweep, color, marker in [("measurement_error", OI["purple"], "o"), ("selection_bias", OI["green"], "s")]:
        g = s[(s["sweep"] == sweep) & (s["estimator"] == "aipw")].copy()
        g["value"] = g["value"].astype(float); g = g.sort_values("value")
        axes[1].plot(g["value"], g["mean_bias"], marker + "-", color=color, label=sweep)
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_xlabel("stress level"); axes[1].set_ylabel("AIPW mean bias")
    axes[1].set_title("Measurement error & collider selection"); axes[1].legend(fontsize=8)
    fig.suptitle("P3-E6: identification-assumption failure regions")
    save(fig, "fig_e6_failure_regions.png")


# ---- F7: E5 matched-budget ----
def fig_e5():
    s = _csv("p3_e5_canonical_summary.csv")
    if s is None:
        return
    order = ["oracle", "causal", "causal_lcb", "rule_based", "historical"]
    s = s.set_index("strategy").reindex([o for o in order if o in set(s.index)])
    colors = [OI["black"], OI["blue"], OI["skyblue"], OI["orange"], OI["vermillion"]]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.bar(range(len(s)), s["mean_realised_value"], color=colors[:len(s)])
    for i, (v, r) in enumerate(zip(s["mean_realised_value"], s["mean_regret_pct"])):
        ax.text(i, v, f"{r:.1f}% regret", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(range(len(s))); ax.set_xticklabels(s.index, rotation=15, fontsize=9)
    ax.set_ylabel("realised incremental value")
    ax.set_title("P3-E5: matched-budget realised value & regret vs oracle")
    save(fig, "fig_e5_matched_budget.png")


# ---- F8: E3 fixture uplift deciles (pipeline illustration) ----
def fig_e3_deciles():
    for outcome in ["visit", "conversion"]:
        p = os.path.join(RES, "p3_e3_fixture", f"uplift_deciles_{outcome}.csv")
        if not os.path.exists(p):
            continue
        d = pd.read_csv(p)
        fig, ax = plt.subplots(figsize=(6.5, 4))
        ax.plot(d["decile"], d["mean_predicted_uplift"], "o-", color=OI["blue"], label="predicted uplift")
        ax.plot(d["decile"], d["randomized_observed_uplift"], "s--", color=OI["vermillion"], label="randomized observed uplift")
        ax.set_xlabel("predicted-uplift decile (1=highest)"); ax.set_ylabel("uplift")
        ax.set_title(f"P3-E3 (fixture): {outcome} uplift by predicted decile")
        ax.legend(fontsize=8)
        save(fig, f"fig_e3_fixture_uplift_deciles_{outcome}.png")


# ---- Architecture figure ----
def fig_architecture():
    stages = ["journeys /\ndata", "causal spec\n+ DAG", "identification\n(backdoor)",
              "nuisance +\ncross-fitting", "effect est.\n(DIM/g/IPW/AIPW)", "diagnostics\n(overlap/balance)",
              "counterfactual\nattribution", "HTE / uplift", "budget\nallocation", "decision +\nabstention"]
    fig, ax = plt.subplots(figsize=(12, 3.2)); ax.axis("off")
    n = len(stages); w = 1.0 / n
    for i, s in enumerate(stages):
        x = i * w
        ax.add_patch(plt.Rectangle((x + 0.005, 0.35), w - 0.01, 0.3, fc=OI["skyblue"], ec="k", alpha=0.85))
        ax.text(x + w / 2, 0.5, s, ha="center", va="center", fontsize=7.5)
        if i < n - 1:
            ax.annotate("", xy=(x + w, 0.5), xytext=(x + w - 0.004, 0.5),
                        arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.text(0.5, 0.9, "Orbit P3 causal research architecture (evidence & assumption layer throughout)",
            ha="center", fontsize=10, weight="bold")
    ax.text(0.5, 0.12, "evidence label: SEMI-SYNTHETIC · RANDOMIZED · OBSERVATIONAL · DEMONSTRATION   |   research gates block live recommendation until evidence quality is met",
            ha="center", fontsize=7.5, style="italic")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    save(fig, "fig_architecture.png")


# ---- Tables ----
def tables():
    s = _csv("p3_e2_canonical_ate_summary.csv")
    if s is not None:
        t = s[["condition", "estimator", "truth", "mean_bias", "rmse", "empirical_sd",
                "mean_se", "ci_coverage_95", "n_reps"]].copy()
        t.to_csv(os.path.join(TAB, "table_e2_recovery.csv"), index=False)
        md_table(t, os.path.join(TAB, "table_e2_recovery.md"))
    s6 = _csv("p3_e6_canonical_summary.csv")
    if s6 is not None:
        t = s6[s6["estimator"] == "aipw"][["sweep", "value", "mean_bias", "rmse",
                                            "ci_coverage_95", "mean_min_propensity"]].copy()
        t.to_csv(os.path.join(TAB, "table_e6_sensitivity_aipw.csv"), index=False)
        md_table(t, os.path.join(TAB, "table_e6_sensitivity_aipw.md"))
    ch = _csv("p3_e1_canonical_channels.csv")
    if ch is not None:
        keep = ["channel", "true_effect", "aipw_effect", "aipw_ci_low", "aipw_ci_high",
                "naive_diff_in_means", "heuristic_first-touch", "heuristic_last-touch",
                "heuristic_linear", "heuristic_time-decay", "heuristic_weighted"]
        ch[keep].to_csv(os.path.join(TAB, "table_e1_channels.csv"), index=False)
        md_table(ch[keep], os.path.join(TAB, "table_e1_channels.md"))
    rk = _csv("p3_e1_canonical_ranking.csv")
    if rk is not None:
        rk.to_csv(os.path.join(TAB, "table_e1_ranking.csv"), index=False)
        md_table(rk, os.path.join(TAB, "table_e1_ranking.md"), floatfmt=2)
    e5 = _csv("p3_e5_canonical_summary.csv")
    if e5 is not None:
        e5.to_csv(os.path.join(TAB, "table_e5_allocation.csv"), index=False)
        md_table(e5, os.path.join(TAB, "table_e5_allocation.md"), floatfmt=2)


def main():
    fig_e1(); fig_e2(); fig_e6_confounding(); fig_e6_failure(); fig_e5()
    fig_e3_deciles(); fig_architecture(); tables()
    print("done.")


if __name__ == "__main__":
    main()
