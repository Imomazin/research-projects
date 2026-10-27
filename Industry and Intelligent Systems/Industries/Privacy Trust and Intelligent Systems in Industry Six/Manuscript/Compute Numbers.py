"""Collect every number quoted in the manuscript from the analysis tables into one JSON file."""
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
AN = HERE.parent / "Experiments" / "Private Risk Control" / "Results" / "Analysis"
RES = AN.parent
N = {}


def f(x, d=3):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)


u = pd.read_csv(AN / "Utility Summary.csv")
r = pd.read_csv(AN / "Risk Control Summary.csv")
runs = pd.read_csv(AN / "Utility.csv")[["dataset", "design", "seed"]].drop_duplicates()
N["main_runs"] = int(len(runs))
N["n_units"] = 10000 + 1567 + 1941 + 9568 + 36733 + 123117 + 1702 + 13400
prim = {"maintenance": "pr_auc", "semiconductor": "pr_auc", "iot": "pr_auc", "bosch": "pr_auc", "hai": "pr_auc",
        "steel": "macro_f1", "power": "rmse", "gas": "rmse"}


def util(ds, design, model, metric=None, test="test", stat="mean"):
    metric = metric or prim[ds]
    g = u[(u.dataset == ds) & (u.design == design) & (u.model == model) & (u.metric == metric) & (u.test_set == test)]
    return f(g[stat].iloc[0]) if len(g) else None


def risk(ds, design, model, method, metric, test="test", stat="mean"):
    g = r[(r.dataset == ds) & (r.design == design) & (r.model == model) & (r.method == method) & (r.metric == metric)
          & (r.test_set == test)]
    return f(g[stat].iloc[0]) if len(g) else None


tasks = [("maintenance", "simulated"), ("semiconductor", "simulated"), ("steel", "simulated"), ("power", "simulated"),
         ("gas", "simulated"), ("iot", "simulated"), ("bosch", "machines"), ("bosch", "time holdout"),
         ("bosch", "machine holdout"), ("hai", "sessions")]
models = ["reference", "linear", "central", "fedavg", "fedprox", "scaffold", "trimmed", "median",
          "dp eps 8", "dp eps 4", "dp eps 2", "dp eps 1"]
N["utility"] = {f"{ds}|{de}": {m: [util(ds, de, m), util(ds, de, m, stat="ci_low"), util(ds, de, m, stat="ci_high")]
                                for m in models} for ds, de in tasks}
for ds, de in tasks:
    fa = util(ds, de, "fedavg")
    for e in (8, 4, 1):
        d = util(ds, de, f"dp eps {e}")
        N[f"ratio_dp{e}_{ds}|{de}"] = f(d / fa) if fa and d is not None else None

methods = ["default", "nonprivate_plugin", "nonprivate_ltt", "plugin", "ucb_without_noise", "proposed"]
N["decisions"] = {}
for ds, de in tasks:
    for model in ["fedavg", "dp eps 8", "dp eps 4", "dp eps 1"]:
        for m in methods:
            for metric in ["miss_rate", "false_alarm_rate", "escalation_rate", "joint_error", "coverage", "half_width"]:
                v = risk(ds, de, model, m, metric)
                if v is not None:
                    N["decisions"][f"{ds}|{de}|{model}|{m}|{metric}"] = v
hyp = json.loads((AN / "Hypotheses.json").read_text())
N["hyp"] = hyp
# exceedance shares across runs by method (FedAvg and DP models, binary in-distribution)
rc = pd.read_csv(AN / "Risk Control.csv")
sub = rc[(rc.metric == "miss_rate") & (rc.test_set == "test") & (rc.kind == "binary")]
N["exceed_share"] = {m: f(np.mean(sub[sub.method == m]["value"].dropna() > 0.10)) for m in methods}
fa = rc[(rc.metric == "false_alarm_rate") & (rc.test_set == "test") & (rc.kind == "binary")]
N["fa_exceed_share"] = {m: f(np.mean(fa[fa.method == m]["value"].dropna() > 0.05)) for m in methods}
N["binary_policy_runs"] = int(len(sub[sub.method == "proposed"]))
mem = pd.read_csv(AN / "Membership Summary.csv")
N["mia"] = {f"{a}|{b}|{c}|{d}": f(v) for a, b, c, d, v in
            mem[["dataset", "design", "model", "metric", "mean"]].itertuples(index=False)}
N["mia_auc_range"] = [f(mem[mem.metric == "auc"]["mean"].min()), f(mem[mem.metric == "auc"]["mean"].max())]
ev = pd.read_csv(AN / "HAI Events Summary.csv")
N["hai"] = {f"{a}|{b}|{c}": f(v) for a, b, c, v in ev[["model", "method", "metric", "mean"]].itertuples(index=False)}
gr = pd.read_csv(AN / "Gas Recalibration Summary.csv")
N["gas_recal"] = {f"{a}|{b}|{c}": f(v) for a, b, c, v in gr[["model", "method", "metric", "mean"]].itertuples(index=False)}
pa = pd.read_csv(AN / "Privacy Accounting.csv")
N["privacy"] = {m: {c: [f(g[c].min()), f(g[c].max())] for c in pa.columns if c.startswith(("epsilon", "skellam"))}
                for m, g in pa.groupby("model")}
ef = pd.read_csv(AN / "Evidence Floor.csv")
N["floor"] = {f"{a}|{b}": int(c) for a, b, c in ef[["target", "epsilon_calibration", "minimum_class_count"]].itertuples(index=False)}
# calibration positives available per task (mean over runs)
cal = []
for p in sorted((RES / "Main").glob("*/*.json")):
    d = json.loads(p.read_text())
    if d["kind"] == "binary":
        cal.append({"task": f"{d['dataset']}|{d['design']}",
                    "cal_pos": sum(c["calibration_positive"] for c in d["clients"]),
                    "cal_neg": sum(c["calibration"] - c["calibration_positive"] for c in d["clients"])})
cal = pd.DataFrame(cal).groupby("task").mean()
N["cal_pos"] = {k: f(v, 1) for k, v in cal["cal_pos"].items()}
N["cal_neg"] = {k: f(v, 1) for k, v in cal["cal_neg"].items()}
cost = pd.read_csv(AN / "Cost Summary.csv")
N["cost"] = {f"{a}|{b}|{c}|{d}": f(v, 4) for a, b, c, d, v in cost[["dataset", "design", "model", "item", "mean"]].itertuples(index=False)}
mc = RES / "Guarantee Validation" / "Monte Carlo Validation.json"
if mc.exists():
    df = pd.DataFrame(json.loads(mc.read_text())["rows"])
    N["mc_rows"] = len(df)
    for m in ["proposed", "plugin", "ucb_without_noise", "nonprivate_ltt", "nonprivate_plugin"]:
        g = df[df.method == m]
        N[f"mc_{m}_max_miss_violation"] = f(g["miss_violation_rate"].max())
        N[f"mc_{m}_max_fa_violation"] = f(g["false_alarm_violation_rate"].max())
        N[f"mc_{m}_mean_miss_violation"] = f(g["miss_violation_rate"].mean())
    N["mc"] = df.to_dict("records")
for name in ("Sensitivity Summary", "Calibration Sweep", "Reconstruction"):
    p = AN / f"{name}.csv"
    if p.exists():
        N[name] = pd.read_csv(p).to_dict("records")
import numpy, scipy, sklearn, cryptography
N.update({"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pd.__version__,
          "scipy": scipy.__version__, "sklearn": sklearn.__version__, "cryptography": cryptography.__version__})
(HERE / "Manuscript Numbers.json").write_text(json.dumps(N, indent=1, default=str))
print("numbers", len(N))
