"""Collect run outputs into tidy tables and compute the pre-specified statistics.

Writes CSV tables and a hypotheses file to Results/Analysis. Every number in the manuscript
is read from these tables, which are rebuilt only from the per-run JSON files.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
RES = HERE / "Results"
OUT = RES / "Analysis"
BOOT = 10000
RNG = np.random.default_rng(20261026)
MAIN_POLICY = "proposed"


def load(folder):
    rows = []
    for f in sorted((RES / folder).glob("*/*.json")):
        rows.append(json.loads(f.read_text()))
    return rows


def num(v):
    if isinstance(v, str):
        return float(v)
    return float(v) if v is not None else float("nan")


def boot_ci(x, stat=np.mean):
    x = np.asarray([v for v in x if np.isfinite(v)], dtype=float)
    if len(x) == 0:
        return (float("nan"),) * 3
    if len(x) == 1:
        return float(x[0]), float("nan"), float("nan")
    idx = RNG.integers(0, len(x), (BOOT, len(x)))
    b = stat(x[idx], axis=1)
    return float(stat(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def bh(pvals):
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    adj = np.empty_like(p)
    prev = 1.0
    for rank in range(n - 1, -1, -1):
        i = order[rank]
        prev = min(prev, p[i] * n / (rank + 1))
        adj[i] = prev
    return adj.tolist()


def tidy_main(runs):
    util, risk, priv, mia, cost, events, recal = [], [], [], [], [], [], []
    for r in runs:
        key = {"dataset": r["dataset"], "design": r["design"], "seed": r["seed"], "kind": r["kind"]}
        for model, res in r["metrics"].items():
            if model == "local":
                for k, c in enumerate(res["clients"]):
                    for metric, v in c["global_test"].items():
                        util.append({**key, "model": "local", "client": k, "test_set": "test", "metric": metric,
                                     "value": num(v)})
                continue
            for test_set, m in res.items():
                if test_set == "client_tests":
                    for k, c in enumerate(m):
                        if c:
                            for metric, v in c.items():
                                util.append({**key, "model": model, "client": k, "test_set": "own client test",
                                             "metric": metric, "value": num(v)})
                    continue
                if test_set == "corrupted":
                    continue
                for metric, v in m.items():
                    util.append({**key, "model": model, "client": None, "test_set": test_set, "metric": metric,
                                 "value": num(v)})
        for model, block in r["risk_control"].items():
            for method, entry in block.items():
                if method == "secure_aggregation":
                    cost.append({**key, "model": model, "item": "calibration secure aggregation bytes",
                                 "value": entry["bytes"]})
                    cost.append({**key, "model": model, "item": "calibration secure aggregation seconds",
                                 "value": entry["seconds"]})
                    continue
                pol = entry.get("policy", {})
                for test_set, m in entry.items():
                    if test_set in ("policy", "seconds"):
                        continue
                    for metric, v in m.items():
                        risk.append({**key, "model": model, "method": method, "test_set": test_set,
                                     "metric": metric, "value": num(v)})
                for k2 in ("t_low", "t_high", "n1_lower", "n0_lower", "threshold", "half_width_scaled", "n_lower"):
                    if k2 in pol:
                        risk.append({**key, "model": model, "method": method, "test_set": "policy",
                                     "metric": k2, "value": num(pol[k2])})
        for model, p in r.get("privacy", {}).items():
            priv.append({**key, "model": model, **{k: num(v) for k, v in p.items()}})
        for model, m in r.get("membership_inference", {}).items():
            for metric, v in m.items():
                mia.append({**key, "model": model, "metric": metric, "value": num(v)})
        for model, log in r["training_logs"].items():
            if isinstance(log, dict):
                for item in ("train_seconds", "parameter_bytes_up", "parameter_bytes_down",
                             "secure_aggregation_bytes", "secure_aggregation_seconds", "parameter_count"):
                    if item in log:
                        cost.append({**key, "model": model, "item": item, "value": num(log[item])})
            elif isinstance(log, (int, float)):
                cost.append({**key, "model": model.replace("_seconds", ""), "item": "train_seconds",
                             "value": num(log)})
        for model, ev in (r.get("hai_events") or {}).items():
            if not ev:
                continue
            for method, e in ev.items():
                delays = [x["alarm_delay_seconds"] for x in e["events"] if x["alarm_delay_seconds"] is not None]
                flags = [x["flag_delay_seconds"] for x in e["events"] if x["flag_delay_seconds"] is not None]
                events.append({**key, "model": model, "method": method, "events": len(e["events"]),
                               "detected_by_alarm": e["detected_by_alarm"], "detected_by_flag": e["detected_by_flag"],
                               "median_alarm_delay_seconds": float(np.median(delays)) if delays else float("nan"),
                               "median_flag_delay_seconds": float(np.median(flags)) if flags else float("nan"),
                               "normal_windows_alarmed": e["normal_windows_alarmed"],
                               "normal_windows_flagged": e["normal_windows_flagged"]})
        for model, block in (r.get("recalibration") or {}).items():
            for method, e in block.items():
                recal.append({**key, "model": model, "method": method,
                              "coverage_2015": e["year 2015"]["coverage"],
                              "half_width_2015": num(e["year 2015"]["half_width"])})
    return (pd.DataFrame(util), pd.DataFrame(risk), pd.DataFrame(priv), pd.DataFrame(mia),
            pd.DataFrame(cost), pd.DataFrame(events), pd.DataFrame(recal))


def summarise(df, by, value="value"):
    rows = []
    for k, g in df.groupby(by, dropna=False):
        m, lo, hi = boot_ci(g[value].to_numpy())
        rows.append({**dict(zip(by, k if isinstance(k, tuple) else (k,))), "mean": m, "ci_low": lo, "ci_high": hi,
                     "sd": float(np.nanstd(g[value].to_numpy(), ddof=1)) if len(g) > 1 else float("nan"),
                     "runs": int(g[value].notna().sum())})
    return pd.DataFrame(rows)


def paired(df, index, a, b, col):
    w = df.pivot_table(index=index, columns=col, values="value")
    if a not in w or b not in w:
        return None
    d = (w[a] - w[b]).dropna()
    if len(d) == 0:
        return None
    m, lo, hi = boot_ci(d.to_numpy())
    try:
        p = float(stats.wilcoxon(d.to_numpy()).pvalue) if np.any(d.to_numpy() != 0) else 1.0
    except ValueError:
        p = float("nan")
    return {"mean_difference": m, "ci_low": lo, "ci_high": hi, "pairs": int(len(d)), "wilcoxon_p": p}


BINARY_IN_DIST = [("maintenance", "simulated"), ("semiconductor", "simulated"), ("iot", "simulated"),
                  ("bosch", "machines"), ("hai", "sessions"), ("bosch", "time holdout"),
                  ("bosch", "machine holdout")]
SHIFT_TESTS = {("gas", "simulated"): ["year 2014", "year 2015"], ("bosch", "time holdout"): ["later periods"],
               ("bosch", "machine holdout"): [None], ("hai", "sessions"): ["later sessions"]}


def hypotheses(risk):
    out = {}
    # H2: exceedance of alpha_miss on in-distribution tests, PARC versus private plug-in (paired runs)
    alpha = 0.10
    sub = risk[(risk.metric == "miss_rate") & (risk.test_set == "test") & risk.model.str.startswith(("dp eps", "fedavg"))]
    sub = sub[sub.apply(lambda r: (r.dataset, r.design) in BINARY_IN_DIST, axis=1)]
    w = sub.pivot_table(index=["dataset", "design", "seed", "model"], columns="method", values="value")
    b = int(((w["plugin"] > alpha) & ~(w["proposed"] > alpha)).sum())
    c = int(((w["proposed"] > alpha) & ~(w["plugin"] > alpha)).sum())
    p_h2 = float(stats.binom.cdf(c, b + c, 0.5)) if b + c > 0 else 1.0
    out["H2"] = {"runs": int(len(w)), "plugin_exceedances": int((w["plugin"] > alpha).sum()),
                 "proposed_exceedances": int((w["proposed"] > alpha).sum()),
                 "nonprivate_plugin_exceedances": int((w["nonprivate_plugin"] > alpha).sum()),
                 "nonprivate_ltt_exceedances": int((w["nonprivate_ltt"] > alpha).sum()),
                 "discordant_plugin_only": b, "discordant_proposed_only": c, "p_one_sided_exact_mcnemar": p_h2}
    # H3: escalation difference at epsilon 4, PARC minus non-private LTT on the same DP model
    e = risk[(risk.metric == "escalation_rate") & (risk.test_set == "test") & (risk.model == "dp eps 4")]
    w3 = e.pivot_table(index=["dataset", "design", "seed"], columns="method", values="value")
    d = (w3["proposed"] - w3["nonprivate_ltt"]).dropna().to_numpy()
    m, lo, hi = boot_ci(d)
    p_h3 = float(np.mean(RNG.choice(d, (BOOT, len(d))).mean(axis=1) >= 0.05)) if len(d) else float("nan")
    out["H3"] = {"runs": int(len(d)), "mean_difference": m, "ci_low": lo, "ci_high": hi,
                 "margin": 0.05, "bootstrap_p_difference_at_or_above_margin": p_h3}
    # H4: shifted versus in-distribution realised risk under PARC (paired by run and model)
    diffs = []
    for (ds, design), shifted in SHIFT_TESTS.items():
        metric = "exceedance" if ds == "gas" else "miss_rate"
        g = risk[(risk.dataset == ds) & (risk.design == design) & (risk.method == "proposed") & (risk.metric == metric)]
        for (seed, model), gg in g.groupby(["seed", "model"]):
            base = gg[gg.test_set == "test"]["value"]
            for s in shifted:
                sh = (gg[gg.test_set.str.startswith("unseen machine")] if s is None else gg[gg.test_set == s])["value"]
                if len(base) and len(sh) and np.isfinite(base.iloc[0]) and np.isfinite(sh.iloc[0]):
                    diffs.append({"dataset": ds, "design": design, "seed": seed, "model": model,
                                  "shift": s or "unseen machine", "difference": float(sh.iloc[0] - base.iloc[0])})
    dd = pd.DataFrame(diffs)
    if len(dd):
        x = dd["difference"].to_numpy()
        m, lo, hi = boot_ci(x)
        p_h4 = float(stats.wilcoxon(x, alternative="greater").pvalue) if np.any(x != 0) else 1.0
        out["H4"] = {"pairs": int(len(x)), "mean_difference": m, "ci_low": lo, "ci_high": hi,
                     "wilcoxon_p_one_sided": p_h4,
                     "by_shift": dd.groupby(["dataset", "design", "shift"])["difference"].agg(["mean", "count"]).reset_index().to_dict("records")}
    else:
        p_h4 = float("nan")
    adj = holm([p_h2, p_h3, p_h4])
    # Secondary checks (not part of the frozen protocol): treat each dataset-design-seed run as one cluster,
    # because run-model combinations within a run share data partitions.
    ex = (w["plugin"] > alpha).astype(int) - (w["proposed"] > alpha).astype(int)
    cl = ex.groupby(level=["dataset", "design", "seed"]).sum()
    pos, neg = int((cl > 0).sum()), int((cl < 0).sum())
    out["clustered_checks"] = {"H2_clusters": int(len(cl)), "H2_clusters_plugin_worse": pos, "H2_clusters_parc_worse": neg,
                               "H2_cluster_sign_test_p": float(stats.binom.cdf(neg, pos + neg, 0.5)) if pos + neg else 1.0}
    if len(dd):
        cm = dd.groupby(["dataset", "design", "seed"])["difference"].mean()
        out["clustered_checks"].update({"H4_clusters": int(len(cm)), "H4_cluster_mean": float(cm.mean()),
                                        "H4_cluster_wilcoxon_p": float(stats.wilcoxon(cm, alternative="greater").pvalue) if np.any(cm != 0) else 1.0})
        ng = dd[dd.dataset != "gas"]["difference"].to_numpy()
        out["clustered_checks"].update({"H4_without_gas_pairs": int(len(ng)), "H4_without_gas_mean": float(ng.mean()) if len(ng) else float("nan")})
    out["holm_adjusted"] = {"H2": adj[0], "H3": adj[1], "H4": adj[2]}
    return out, dd


def tidy_sensitivity():
    rows, sweep = [], []
    for r in load("Sensitivity"):
        key = {"dataset": r["dataset"], "design": r["design"], "variant": r["variant"], "seed": r["seed"]}
        for model, res in r["metrics"].items():
            for test_set, m in res.items():
                if test_set == "client_tests" or not isinstance(m, dict):
                    continue
                if test_set == "corrupted":
                    for cset, mm in m.items():
                        for metric, v in mm.items():
                            rows.append({**key, "model": model, "method": "", "test_set": cset, "metric": metric, "value": num(v)})
                    continue
                for metric, v in m.items():
                    rows.append({**key, "model": model, "method": "", "test_set": test_set, "metric": metric, "value": num(v)})
        for model, block in r.get("risk_control", {}).items():
            for method, entry in block.items():
                if method == "secure_aggregation":
                    continue
                for test_set, m in entry.items():
                    if test_set in ("policy", "seconds"):
                        continue
                    for metric, v in m.items():
                        rows.append({**key, "model": model, "method": method, "test_set": test_set, "metric": metric, "value": num(v)})
        for lvl, block in (r.get("histogram_poison") or {}).items():
            for test_set, m in block["proposed"].items():
                if test_set in ("policy", "seconds"):
                    continue
                for metric, v in m.items():
                    rows.append({**key, "model": "dp eps 4", "method": f"proposed, fake faults {lvl} x n1",
                                 "test_set": test_set, "metric": metric, "value": num(v)})
        for eps, block in (r.get("calibration_sweep") or {}).items():
            for method, entry in block.items():
                if method in ("secure_aggregation", "mu"):
                    continue
                m = entry.get("test", {})
                sweep.append({"dataset": r["dataset"], "design": r["design"], "seed": r["seed"], "epsilon": float(eps),
                              "method": method, **{k: num(v) for k, v in m.items()}})
    return pd.DataFrame(rows), pd.DataFrame(sweep)


def tidy_reconstruction():
    rows = []
    for f in sorted((RES / "Reconstruction").glob("*.json")):
        r = json.loads(f.read_text())
        for setting, v in r["reconstruction"].items():
            rows.append({"dataset": r["dataset"], "seed": r["seed"], "setting": setting, **v})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runs = load("Main")
    util, risk, priv, mia, cost, events, recal = tidy_main(runs)
    for name, df in [("Utility", util), ("Risk Control", risk), ("Privacy Accounting", priv),
                     ("Membership Inference", mia), ("Costs", cost), ("HAI Events", events),
                     ("Gas Recalibration", recal)]:
        df.to_csv(OUT / f"{name}.csv", index=False)
    summarise(util[util.client.isna()], ["dataset", "design", "model", "test_set", "metric"]).to_csv(
        OUT / "Utility Summary.csv", index=False)
    summarise(risk, ["dataset", "design", "model", "method", "test_set", "metric"]).to_csv(
        OUT / "Risk Control Summary.csv", index=False)
    summarise(mia, ["dataset", "design", "model", "metric"]).to_csv(OUT / "Membership Summary.csv", index=False)
    summarise(cost, ["dataset", "design", "model", "item"]).to_csv(OUT / "Cost Summary.csv", index=False)
    if len(events):
        ev = events.melt(id_vars=["dataset", "design", "seed", "kind", "model", "method"], var_name="metric")
        summarise(ev, ["model", "method", "metric"]).to_csv(OUT / "HAI Events Summary.csv", index=False)
    if len(recal):
        rr = recal.melt(id_vars=["dataset", "design", "seed", "kind", "model", "method"], var_name="metric")
        summarise(rr, ["model", "method", "metric"]).to_csv(OUT / "Gas Recalibration Summary.csv", index=False)
    if len(priv):
        pm = priv.melt(id_vars=["dataset", "design", "seed", "kind", "model"], var_name="metric")
        summarise(pm, ["dataset", "design", "model", "metric"]).to_csv(OUT / "Privacy Summary.csv", index=False)
    for df in (util, risk, mia):
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
    hyp, shifts = hypotheses(risk)
    shifts.to_csv(OUT / "Shift Differences.csv", index=False)
    # Secondary paired comparisons: utility of each method against FedAvg, BH within dataset-design
    sec = []
    prim = {"binary": "pr_auc", "multiclass": "macro_f1", "regression": "rmse"}
    for (ds, design, kind), g in util[(util.client.isna()) & (util.test_set == "test")].groupby(["dataset", "design", "kind"]):
        g = g[g.metric == prim[kind]]
        block = []
        for m in sorted(set(g.model) - {"fedavg"}):
            r = paired(g[g.model.isin([m, "fedavg"])], ["seed"], m, "fedavg", "model")
            if r:
                block.append({"dataset": ds, "design": design, "metric": prim[kind], "model": m,
                              "versus": "fedavg", **r})
        if block:
            adj = bh([b["wilcoxon_p"] if np.isfinite(b["wilcoxon_p"]) else 1.0 for b in block])
            for b, a in zip(block, adj):
                b["bh_adjusted_p"] = a
            sec += block
    pd.DataFrame(sec).to_csv(OUT / "Paired Utility Comparisons.csv", index=False)
    sens, sweep = tidy_sensitivity() if (RES / "Sensitivity").exists() else (pd.DataFrame(), pd.DataFrame())
    if len(sens):
        sens.to_csv(OUT / "Sensitivity.csv", index=False)
        summarise(sens, ["dataset", "design", "variant", "model", "method", "test_set", "metric"]).to_csv(
            OUT / "Sensitivity Summary.csv", index=False)
    if len(sweep):
        sweep.to_csv(OUT / "Calibration Sweep.csv", index=False)
    if (RES / "Reconstruction").exists():
        tidy_reconstruction().to_csv(OUT / "Reconstruction.csv", index=False)
    (OUT / "Hypotheses.json").write_text(json.dumps(hyp, indent=1, default=float) + "\n")
    print(json.dumps(hyp, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
