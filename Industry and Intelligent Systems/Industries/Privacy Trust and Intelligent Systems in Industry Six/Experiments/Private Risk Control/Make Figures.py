"""Draw the manuscript figures from the analysis tables and run outputs.

Diagrams (Figures 1 and 2) are drawn from the implemented protocol; all other figures read
Results/Analysis CSV files or run JSON files. Output: SVG and 300 dpi PNG in Figures.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RES = HERE / "Results"
AN = RES / "Analysis"
FIG = HERE.parents[1] / "Figures"
FIG.mkdir(exist_ok=True)

for f in font_manager.findSystemFonts():
    if "Inter" in Path(f).name and "Display" not in Path(f).name:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Inter", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
                     "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#4A4A4A", "axes.linewidth": 0.7,
                     "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
                     "svg.fonttype": "none"})
INK, GREY, LIGHT = "#2B2B2B", "#8C8C8C", "#E9E9E9"
BLUE, TEAL, GOLD = "#3A6EA5", "#2A9D8F", "#B8862B"
TASK_LABEL = {("maintenance", "simulated"): "AI4I maintenance", ("semiconductor", "simulated"): "SECOM yield",
              ("steel", "simulated"): "Steel plate defects", ("power", "simulated"): "Power plant output",
              ("gas", "simulated"): "Gas turbine NOx", ("iot", "simulated"): "RT-IoT intrusion",
              ("bosch", "machines"): "Bosch CNC, machines", ("bosch", "time holdout"): "Bosch CNC, early periods",
              ("bosch", "machine holdout"): "Bosch CNC, two machines", ("hai", "sessions"): "HAI control sessions"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fitted_text(ax, x, y, w, h, text, size=7.0, weight="normal", colour=INK, ha="center", pad=0.06):
    """Place text centred in a box and shrink the font until it fits inside with padding."""
    fig = ax.figure
    renderer = fig.canvas.get_renderer()
    tx = x + w / 2 if ha == "center" else x + pad * w
    t = ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=size, color=colour, weight=weight,
                linespacing=1.3)
    inv = ax.transData.inverted()
    while size > 4.5:
        bb = t.get_window_extent(renderer)
        (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]])
        if (x1 - x0) <= w * (1 - 2 * pad) and (y1 - y0) <= h * (1 - 2 * pad):
            break
        size -= 0.2
        t.set_fontsize(size)
    return t


def box(ax, x, y, w, h, text, colour, fill="white", size=7.0, weight="normal", lw=1.0, style="-", ha="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.8", fc=fill, ec=colour,
                                lw=lw, ls=style))
    if text:
        fitted_text(ax, x, y, w, h, text, size, weight, ha=ha)


def arrow(ax, a, b, colour=INK, style="-", lw=1.0, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=8, color=colour, lw=lw, ls=style,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))


def canvas(width_in, height_units):
    fig, ax = plt.subplots(figsize=(width_in, width_in * height_units / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, height_units)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.subplots_adjust(0, 0, 1, 1)
    fig.canvas.draw()
    return fig, ax


def figure_framework():
    fig, ax = canvas(7.2, 40)
    w, h, y = 14.5, 11, 20
    xs = [0.5, 17.4, 34.3, 51.2, 68.1, 85.0]
    labels = ["Industrial data\nheld by sites", "Privacy-preserving\ncollaboration\n(DP-SGD, secure sum)",
              "Distributed\nintelligence\n(federated model)", "Reliability and\ntrust assessment\n(certified risk)",
              "Decision support\n(pass, alarm,\nescalate)", "Resilient\noperational\noutcomes"]
    colours = [GREY, BLUE, BLUE, TEAL, TEAL, GREY]
    for x, t, c in zip(xs, labels, colours):
        box(ax, x, y, w, h, t, c, size=7.0)
    tested = [True, True, True, True, False]
    for i in range(5):
        arrow(ax, (xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2), INK if tested[i] else GREY,
              "-" if tested[i] else "--")
    box(ax, 30, 2, 40, 8.5, "Human oversight and governance\n(escalation queue, recalibration, audit trail)", GOLD, size=7.0)
    arrow(ax, (xs[4] + w / 2, y), (62, 10.5), GOLD)
    arrow(ax, (45, 10.5), (xs[3] + w / 2 - 2, y), GOLD, "--")
    arrow(ax, (30, 6), (xs[1] + w / 2, y), GREY, "--", rad=-0.25)
    ax.plot([1, 5], [37, 37], color=INK, lw=1)
    ax.text(6, 37, "relationship measured in this study", va="center", fontsize=6.8, color=INK)
    ax.plot([42, 46], [37, 37], color=GREY, lw=1, ls="--")
    ax.text(47, 37, "relationship proposed, not measured", va="center", fontsize=6.8, color=INK)
    save(fig, "Research Framework")


def client_panel(ax, y0, name):
    ax.add_patch(FancyBboxPatch((0.5, y0), 40, 18, boxstyle="round,pad=0,rounding_size=0.8", fc="#F7F7F7",
                                ec=GREY, lw=0.7))
    ax.text(1.8, y0 + 16.3, name, fontsize=7.0, weight="bold", color=INK, va="center")
    box(ax, 1.8, y0 + 8.0, 11.5, 6.0, "Training\nrecords", GREY)
    box(ax, 16.0, y0 + 8.0, 23.5, 6.0, "DP-SGD: clip C, noise σC,\nPoisson sampling rate q", BLUE)
    box(ax, 1.8, y0 + 1.0, 11.5, 6.0, "Calibration\nrecords", GREY)
    box(ax, 16.0, y0 + 1.0, 23.5, 6.0, "Score histogram plus\nSkellam(μ/K) noise per bin", TEAL)
    arrow(ax, (13.3, y0 + 11.0), (16.0, y0 + 11.0))
    arrow(ax, (13.3, y0 + 4.0), (16.0, y0 + 4.0))


def figure_architecture():
    fig, ax = canvas(7.2, 72)
    client_panel(ax, 49, "Client 1 (site or machine)")
    client_panel(ax, 27, "Client K")
    ax.text(20.5, 46.6, "· · ·", fontsize=9, ha="center", va="center", color=GREY)
    box(ax, 45, 27, 17, 40, "Pairwise-mask\nsecure summation\n\nX25519 key agreement\nHKDF and ChaCha20\nmasks, sum mod 2³²\n\nserver sees\nonly the sums", INK)
    for y0 in (49, 27):
        arrow(ax, (39.5, y0 + 11.0), (45, y0 + 11.0), BLUE)
        arrow(ax, (39.5, y0 + 4.0), (45, y0 + 4.0), TEAL)
    box(ax, 66.5, 55, 33, 12, "Server model update\nsize-weighted average of masked local\nmodels, broadcast every round", BLUE)
    box(ax, 66.5, 27, 33, 24, "Certification from noisy sums\n\nbins j = 1, 2, … in order of rising risk\np_j = P(Bin(n⁻, α) + Skellam(jμ) ≤ m̃_j)\nadmit bin j while p_j ≤ δ_test\nn⁻: noisy total minus Skellam quantile", TEAL)
    arrow(ax, (62, 60), (66.5, 60), BLUE)
    arrow(ax, (62, 38), (66.5, 38), TEAL)
    arrow(ax, (83, 67), (20.5, 67.2), BLUE, "--", rad=0.18)
    ax.text(52, 71.0, "global model returned to every client", fontsize=6.6, color=BLUE, ha="center", va="center")
    ax.add_patch(FancyBboxPatch((0.5, 0.5), 99, 22, boxstyle="round,pad=0,rounding_size=0.8", fc="white",
                                ec=GREY, lw=0.7))
    ax.text(1.8, 20.6, "Operation at each site with the certified thresholds", fontsize=7.0, weight="bold",
            color=INK, va="center")
    box(ax, 2, 6.5, 13, 8, "New record x\nscore s(x)", GREY)
    box(ax, 20, 13.5, 24, 4.6, "s < t_low: automatic pass", BLUE)
    box(ax, 20, 7.6, 24, 4.6, "t_low ≤ s < t_high: escalate", GOLD)
    box(ax, 20, 1.7, 24, 4.6, "s ≥ t_high: automatic alarm", TEAL)
    for yy in (15.8, 9.9, 4.0):
        arrow(ax, (15, 10.5), (20, yy), GREY)
    box(ax, 50, 1.7, 48, 16.5, "With probability ≥ 0.90 over calibration data and noise:\nmiss rate of automatic passes ≤ α_miss\nfalse-alarm rate of automatic alarms ≤ α_fa\nfor exchangeable future records\n\nrecord-level privacy: (ε, δ) = max(training, calibration)", INK)
    arrow(ax, (83, 27), (83, 18.2), TEAL)
    save(fig, "Architecture and Protocol")


def primary(df, kind):
    return {"binary": "pr_auc", "multiclass": "macro_f1", "regression": "rmse"}[kind]


def figure_privacy_utility():
    u = pd.read_csv(AN / "Utility Summary.csv")
    kinds = pd.read_csv(AN / "Utility.csv")[["dataset", "design", "kind"]].drop_duplicates()
    tasks = [t for t in TASK_LABEL if ((kinds.dataset == t[0]) & (kinds.design == t[1])).any()]
    n = len(tasks)
    cols = 5
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(7.4, 1.75 * rows + 0.3), squeeze=False)
    for ax, (ds, design) in zip(axes.flat, tasks):
        kind = kinds[(kinds.dataset == ds) & (kinds.design == design)].kind.iloc[0]
        m = primary(u, kind)
        g = u[(u.dataset == ds) & (u.design == design) & (u.test_set == "test") & (u.metric == m)]
        eps = [1, 2, 4, 8]
        y = [g[g.model == f"dp eps {e}"]["mean"].iloc[0] for e in eps]
        lo = [g[g.model == f"dp eps {e}"]["ci_low"].iloc[0] for e in eps]
        hi = [g[g.model == f"dp eps {e}"]["ci_high"].iloc[0] for e in eps]
        x = np.arange(len(eps))
        ax.fill_between(x, lo, hi, color=BLUE, alpha=0.18, lw=0)
        ax.plot(x, y, "o-", color=BLUE, ms=3, lw=1.2, label="DP-FedAvg")
        for name, col, ls in [("fedavg", INK, "--"), ("central", GREY, ":")]:
            v = g[g.model == name]["mean"]
            if len(v):
                ax.axhline(v.iloc[0], color=col, ls=ls, lw=0.9, label={"fedavg": "FedAvg", "central": "pooled"}[name])
        ax.set_xticks(x, [str(e) for e in eps])
        ax.set_title(TASK_LABEL[(ds, design)], fontsize=7.6)
        ax.set_ylabel({"pr_auc": "PR-AUC", "macro_f1": "macro F1", "rmse": "RMSE"}[m], fontsize=7)
        ax.set_xlabel("ε (δ = 10⁻⁵)", fontsize=7)
    for ax in list(axes.flat)[n:]:
        ax.axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False)
    save(fig, "Privacy Utility")


def load_runs(folder):
    return [json.loads(f.read_text()) for f in sorted((RES / folder).glob("*/*.json"))]


def figure_models():
    u = pd.read_csv(AN / "Utility Summary.csv")
    kinds = pd.read_csv(AN / "Utility.csv")[["dataset", "design", "kind"]].drop_duplicates()
    order = ["reference", "linear", "central", "fedavg", "fedprox", "scaffold", "trimmed", "median",
             "dp eps 8", "dp eps 4", "dp eps 2", "dp eps 1"]
    names = {"reference": "reference", "linear": "linear", "central": "pooled MLP", "fedavg": "FedAvg",
             "fedprox": "FedProx", "scaffold": "SCAFFOLD", "trimmed": "trimmed mean", "median": "median",
             "dp eps 8": "DP ε=8", "dp eps 4": "DP ε=4", "dp eps 2": "DP ε=2", "dp eps 1": "DP ε=1"}
    tasks = [t for t in TASK_LABEL if ((kinds.dataset == t[0]) & (kinds.design == t[1])).any()]
    fig, axes = plt.subplots(2, 5, figsize=(7.4, 4.6), sharey=True, squeeze=False)
    for ax, (ds, design) in zip(axes.flat, tasks):
        kind = kinds[(kinds.dataset == ds) & (kinds.design == design)].kind.iloc[0]
        m = primary(u, kind)
        g = u[(u.dataset == ds) & (u.design == design) & (u.test_set == "test") & (u.metric == m)].set_index("model")
        for i, name in enumerate(order):
            if name not in g.index:
                continue
            row = g.loc[name]
            col = BLUE if name.startswith("dp") else (TEAL if name in ("fedavg", "fedprox", "scaffold", "trimmed", "median") else GREY)
            ax.errorbar(row["mean"], i, xerr=[[row["mean"] - row["ci_low"]], [row["ci_high"] - row["mean"]]],
                        fmt="o", ms=3, color=col, elinewidth=0.8, capsize=0)
        ax.set_yticks(range(len(order)), [names[o] for o in order])
        ax.invert_yaxis()
        ax.set_title(TASK_LABEL[(ds, design)], fontsize=7.4)
        ax.set_xlabel({"pr_auc": "PR-AUC", "macro_f1": "macro F1", "rmse": "RMSE (lower is better)"}[m], fontsize=7)
        ax.grid(axis="x", color=LIGHT, lw=0.6)
    for ax in list(axes.flat)[len(tasks):]:
        ax.axis("off")
    fig.tight_layout()
    save(fig, "Model Comparison")


def figure_ablation():
    r = pd.read_csv(AN / "Risk Control.csv")
    methods = ["default", "nonprivate_plugin", "nonprivate_ltt", "plugin", "ucb_without_noise", "proposed"]
    labels = ["default 0.5", "plug-in, exact", "Learn-then-Test, exact", "plug-in, private",
              "binomial test, private,\nno noise correction", "PARC"]
    sub = r[(r.test_set == "test") & (r.kind == "binary") & (r.model == "fedavg")]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), sharey=True)
    for ax, metric, title, target in [(axes[0], "miss_rate", "realised miss rate", 0.10),
                                      (axes[1], "false_alarm_rate", "realised false-alarm rate", 0.05),
                                      (axes[2], "escalation_rate", "share escalated", None)]:
        for i, m in enumerate(methods):
            v = sub[(sub.method == m) & (sub.metric == metric)]["value"].dropna().to_numpy()
            if not len(v):
                continue
            jitter = (np.random.default_rng(i).random(len(v)) - 0.5) * 0.35
            ax.scatter(v, i + jitter, s=5, color=TEAL if m == "proposed" else GREY, alpha=0.55, lw=0)
            ax.plot([v.mean()] * 2, [i - 0.3, i + 0.3], color=INK, lw=1.4)
            if target is not None:
                ax.text(1.0, i, f"{np.mean(v > target):.0%}", transform=ax.get_yaxis_transform(), fontsize=6.5,
                        va="center", ha="left", color=INK)
        if target is not None:
            ax.axvline(target, color=GOLD, lw=1, ls="--")
        ax.set_title(title, fontsize=8)
        ax.set_yticks(range(len(methods)), labels)
        ax.invert_yaxis()
        ax.set_xlim(left=0)
    fig.text(0.99, 0.01, "Percentages: share of runs above the target. Model: FedAvg; calibration ε = 4.",
             ha="right", fontsize=6.5, color=GREY)
    fig.tight_layout()
    save(fig, "Ablation of Certification Rules")


def figure_shift():
    d = pd.read_csv(AN / "Shift Differences.csv")
    r = pd.read_csv(AN / "Risk Control.csv")
    rows = []
    specs = [("gas", "simulated", "exceedance", ["test", "year 2014", "year 2015"]),
             ("bosch", "time holdout", "miss_rate", ["test", "later periods"]),
             ("bosch", "machine holdout", "miss_rate", ["test", "unseen"]),
             ("hai", "sessions", "miss_rate", ["test", "later sessions"])]
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.4))
    for ax, (ds, design, metric, sets) in zip(axes, specs):
        g = r[(r.dataset == ds) & (r.design == design) & (r.method == "proposed") & (r.metric == metric)
              & (r.model == "fedavg")]
        for i, ts in enumerate(sets):
            v = g[g.test_set.str.startswith("unseen machine")]["value"] if ts == "unseen" else g[g.test_set == ts]["value"]
            v = v.dropna().to_numpy()
            if len(v):
                ax.scatter(np.full(len(v), i) + (np.random.default_rng(i).random(len(v)) - 0.5) * 0.3, v, s=6,
                           color=TEAL if i == 0 else GOLD, alpha=0.7, lw=0)
                ax.plot([i - 0.25, i + 0.25], [v.mean()] * 2, color=INK, lw=1.4)
        ax.axhline(0.10, color=GREY, ls="--", lw=0.9)
        ax.set_xticks(range(len(sets)), [("in period" if s == "test" else s.replace("year ", "")) for s in sets], fontsize=6.6)
        ax.set_title(TASK_LABEL[(ds, design)], fontsize=7.4)
        ax.set_ylabel("interval exceedance" if metric == "exceedance" else "realised miss rate", fontsize=7)
    fig.tight_layout()
    save(fig, "Shift and Unseen Machines")


def figure_reliability():
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.5))
    mc = json.loads((RES / "Guarantee Validation" / "Monte Carlo Validation.json").read_text()) \
        if (RES / "Guarantee Validation" / "Monte Carlo Validation.json").exists() else None
    if mc:
        df = pd.DataFrame(mc["rows"])
        ax = axes[0]
        for m, col, lab in [("proposed", TEAL, "PARC"), ("plugin", GREY, "private plug-in"),
                            ("ucb_without_noise", GOLD, "no noise correction")]:
            g = df[(df.method == m)]
            g = g.groupby("epsilon")["miss_violation_rate"].max()
            ax.plot(range(len(g)), g.values, "o-", ms=3, color=col, label=lab)
            ax.set_xticks(range(len(g)), [f"{e:g}" for e in g.index])
        ax.axhline(0.05, color=INK, ls="--", lw=0.8)
        ax.set_xlabel("calibration ε", fontsize=7)
        ax.set_ylabel("worst violation rate\nacross conditions", fontsize=7)
        ax.set_title("Monte Carlo validity (H1)", fontsize=8)
        ax.legend(frameon=False, fontsize=6.3)
    ef = pd.read_csv(AN / "Evidence Floor.csv")
    ax = axes[1]
    for tgt, col in [("miss rate 0.10", TEAL), ("false-alarm rate 0.05", BLUE), ("miss rate 0.20", GREY)]:
        g = ef[ef.target == tgt]
        ax.plot(range(len(g)), g["minimum_class_count"], "o-", ms=3, color=col, label=tgt)
    ax.set_xticks(range(len(g)), [str(e) for e in g["epsilon_calibration"]], fontsize=6.5)
    ax.set_xlabel("calibration ε", fontsize=7)
    ax.set_ylabel("minimum calibration events", fontsize=7)
    ax.set_yscale("log")
    ax.set_yticks([20, 50, 100, 200, 400], ["20", "50", "100", "200", "400"])
    ax.minorticks_off()
    ax.set_title("Evidence floor", fontsize=8)
    ax.legend(frameon=False, fontsize=6.3)
    sw = AN / "Calibration Sweep.csv"
    ax = axes[2]
    if sw.exists():
        d = pd.read_csv(sw)
        for ds, col, lab in [("maintenance", TEAL, "AI4I"), ("bosch", BLUE, "Bosch"), ("hai", GOLD, "HAI")]:
            g = d[(d.dataset == ds) & (d.method == "proposed")].groupby("epsilon")["automation_rate"].mean()
            if len(g):
                ax.plot(range(len(g)), g.values, "o-", ms=3, color=col, label=lab)
            ax.set_xticks(range(len(g)), [f"{e:g}" for e in g.index])
        ax.set_xlabel("calibration ε", fontsize=7)
        ax.set_ylabel("share automated (PARC)", fontsize=7)
        ax.set_title("Price of private calibration", fontsize=8)
        ax.legend(frameon=False, fontsize=6.3)
    fig.tight_layout()
    save(fig, "Guarantee Validity and Evidence Floor")


def figure_robustness():
    sens = pd.read_csv(AN / "Sensitivity Summary.csv")
    util = pd.read_csv(AN / "Utility Summary.csv")
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.6))
    axes = axes.ravel()
    series = [("maintenance", "simulated", TEAL, "AI4I"), ("bosch", "machines", BLUE, "Bosch machines"),
              ("hai", "sessions", GOLD, "HAI")]

    def sv(ds, var, model, metric, method=np.nan, test="test"):
        g = sens[(sens.dataset == ds) & (sens.variant == var) & (sens.model == model) & (sens.metric == metric)
                 & (sens.test_set == test)]
        g = g[g.method.isna()] if isinstance(method, float) else g[g.method == method]
        return float(g["mean"].iloc[0]) if len(g) else np.nan

    def base(ds, design, model, metric="pr_auc"):
        g = util[(util.dataset == ds) & (util.design == design) & (util.model == model) & (util.metric == metric) & (util.test_set == "test")]
        return float(g["mean"].iloc[0]) if len(g) else np.nan
    ax = axes[0]
    for model, col, lab in [("fedavg", TEAL, "FedAvg"), ("dp eps 4", TEAL, "DP ε=4")]:
        y = [sv("maintenance", "alpha 0.1", model, "pr_auc"), base("maintenance", "simulated", model), sv("maintenance", "alpha 2.0", model, "pr_auc")]
        ax.plot([0, 1, 2], y, "o-" if model == "fedavg" else "o--", color=col, ms=3)
        ax.annotate(lab, (2, y[2]), xytext=(4, 0), textcoords="offset points", fontsize=6.5, va="center", color=INK)
    ax.set_xticks([0, 1, 2], ["0.1", "0.5", "2.0"])
    ax.set_xlim(-0.2, 2.6)
    ax.set_xlabel("Dirichlet concentration (lower = more skew)", fontsize=7)
    ax.set_ylabel("PR-AUC, AI4I", fontsize=7)
    ax.set_title("a. Label skew across clients", fontsize=8, loc="left")
    ax = axes[1]
    models = ["fedavg", "trimmed", "median", "dp eps 4"]
    x = np.arange(4)
    for k, (ds, design, col, lab) in enumerate(series):
        clean = [base(ds, design, m) for m in models]
        pois = [sv(ds, "poison", m, "pr_auc") for m in models]
        xx = x + (k - 1) * 0.22
        ax.vlines(xx, pois, clean, color=col, lw=0.8)
        ax.scatter(xx, clean, marker="o", s=12, color=col)
        ax.scatter(xx, pois, marker="o", s=12, facecolor="white", edgecolor=col, lw=0.9)
    ax.set_xticks(x, ["FedAvg", "Trimmed\nmean", "Median", "DP ε=4"], fontsize=6.5)
    ax.set_ylabel("PR-AUC (filled clean, open poisoned)", fontsize=7)
    ax.set_title("b. One malicious client", fontsize=8, loc="left")
    ax = axes[2]
    lv = ["0.25", "0.5", "1", "2"]
    for ds, design, col, lab in series:
        y = [sv(ds, "histogram poison", "dp eps 4", "miss_rate", f"proposed, fake faults {l} x n1") for l in lv]
        ax.plot(range(4), y, "o-", ms=3, color=col)
    ax.axhline(0.10, color=GREY, ls="--", lw=0.8)
    ax.text(3.45, 0.103, "target", fontsize=6.3, va="bottom", ha="right", color=GREY)
    ax.text(1.5, 0.004, "Bosch and HAI: 0 (all faults escalated)", fontsize=6.3, va="bottom", ha="center", color=INK)
    ax.set_xticks(range(4), [f"{l}×" for l in lv])
    ax.set_xlim(-0.2, 3.5)
    ax.set_xlabel("fabricated faults relative to true calibration faults", fontsize=7)
    ax.set_ylabel("realised miss rate, PARC", fontsize=7)
    ax.set_title("c. Calibration poisoning at DP ε=4", fontsize=8, loc="left")
    ax = axes[3]
    sets = ["test", "gaussian 0.5", "gaussian 1", "missing 0.2", "missing 0.4"]
    for ds, design, col, lab in series:
        y = [base(ds, design, "fedavg") if t == "test" else sv(ds, "corruption", "fedavg", "pr_auc", test=t) for t in sets]
        ax.plot(range(5), y, "o-", ms=3, color=col)
    ax.set_xticks(range(5), ["none", "noise\n0.5 sd", "noise\n1 sd", "20%\nmissing", "40%\nmissing"], fontsize=6.5)
    ax.set_ylabel("PR-AUC, FedAvg", fontsize=7)
    ax.set_title("d. Test-time sensor corruption", fontsize=8, loc="left")
    handles = [plt.Line2D([], [], color=c, marker="o", ms=3, label=l) for _, _, c, l in series]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=7)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "Robustness Under Attack and Corruption")


if __name__ == "__main__":
    figure_framework()
    figure_architecture()
    if (AN / "Utility Summary.csv").exists():
        figure_privacy_utility()
        figure_models()
        figure_ablation()
        figure_shift()
        figure_reliability()
        if (AN / "Sensitivity Summary.csv").exists():
            figure_robustness()
