#!/usr/bin/env python3
"""P3-E2 — Semi-synthetic causal truth recovery.

Research question (RQ2/RQ3): under known ground truth, do cross-fitted causal
estimators recover the ATE and CATE, and how does recovery depend on confounding
strength and nuisance-model (mis)specification?

Design: for each condition and seed, generate a semi-synthetic dataset with known
ATE/CATE, cross-fit nuisances, and compute difference-in-means, outcome-regression
(g-formula), IPW and AIPW, plus a T-learner CATE. Aggregate recovery error, CI
coverage, PEHE and policy value across seeds.

Development runs use --max-seeds / --smoke; the frozen canonical run reads
configs/p3_e2_canonical.json with no overrides.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3lib import dgp, estimators as est, metrics as m, io_utils as io  # noqa: E402
from p3lib.provenance import Provenance  # noqa: E402

RESULTS = os.path.join(HERE, "results")
ATE_ESTIMATORS = ["difference-in-means", "outcome-regression", "ipw", "aipw"]


def run(config: dict, out_prefix: str, max_seeds: int | None = None) -> dict:
    per_run_rows = []
    hte_rows = []
    default_seeds = config["n_seeds"]

    for cond in config["conditions"]:
        n_seeds = cond.get("n_seeds", default_seeds)
        if max_seeds is not None:
            n_seeds = min(n_seeds, max_seeds)
        learner = cond["learner"]
        for seed in range(n_seeds):
            cfg = dgp.DGPConfig(
                n=config["n"], d=config["d"], ate=config["ate"], hte=config["hte"],
                noise=config["noise"], confounding=cond["confounding"],
                nonlinear_strength=cond.get("nonlinear_strength", 0.0),
            )
            data = dgp.generate(cfg, seed=seed)
            nu = est.crossfit_nuisances(
                data.X, data.T, data.Y, learner=learner,
                n_folds=config["n_folds"], propensity_floor=config["propensity_floor"], seed=seed,
            )
            ests = est.all_ate_estimates(data.Y, data.T, nu)
            for name, e in ests.items():
                per_run_rows.append({
                    "condition": cond["name"], "learner": learner, "seed": seed,
                    "estimator": name, "estimate": e.estimate, "se": e.se,
                    "ci_low": e.ci_low, "ci_high": e.ci_high,
                    "true_ate": data.true_ate, "true_sample_ate": data.true_sample_ate,
                    "treatment_rate": float(data.T.mean()),
                    "min_propensity": float(nu.e.min()), "max_propensity": float(nu.e.max()),
                    "clipped_fraction": nu.clipped_fraction,
                })
            tau = est.tlearner_cate(nu)
            pol = m.policy_analysis(tau, data.Y, data.T, nu.e, nu.mu0, nu.mu1, data.tau)
            hte_rows.append({
                "condition": cond["name"], "learner": learner, "seed": seed,
                "pehe": m.pehe(tau, data.tau), "cate_rank_corr": m.cate_rank_corr(tau, data.tau),
                **{k: v for k, v in pol.items()},
            })

    io.write_table(per_run_rows, out_prefix + "_runs")
    io.write_table(hte_rows, out_prefix + "_hte_runs")

    # Aggregate ATE recovery per (condition, estimator).
    summary = []
    import pandas as pd
    runs = pd.DataFrame(per_run_rows)
    for (cond, estimator), g in runs.groupby(["condition", "estimator"]):
        truth = g["true_ate"].iloc[0]
        s = m.recovery_summary(g["estimate"], g["ci_low"], g["ci_high"], g["se"], truth)
        s.update({"condition": cond, "estimator": estimator,
                  "mean_treatment_rate": float(g["treatment_rate"].mean()),
                  "mean_min_propensity": float(g["min_propensity"].mean())})
        summary.append(s)
    io.write_table(summary, out_prefix + "_ate_summary")

    hte = pd.DataFrame(hte_rows)
    hte_summary = []
    for cond, g in hte.groupby("condition"):
        hte_summary.append({
            "condition": cond,
            "mean_pehe": float(g["pehe"].mean()), "sd_pehe": float(g["pehe"].std()),
            "mean_rank_corr": float(g["cate_rank_corr"].mean()),
            "mean_regret_vs_oracle": float(g["regret_vs_oracle"].mean()),
            "mean_value_learned": float(g["value_learned_policy"].mean()),
            "mean_value_oracle": float(g["value_oracle_policy"].mean()),
            "mean_value_treat_all": float(g["value_treat_all"].mean()),
        })
    io.write_table(hte_summary, out_prefix + "_hte_summary")
    return {"ate_summary": summary, "hte_summary": hte_summary}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "configs/p3_e2_canonical.json"))
    ap.add_argument("--max-seeds", type=int, default=None, help="cap seeds for development runs")
    ap.add_argument("--smoke", action="store_true", help="tiny development run")
    ap.add_argument("--tag", default="canonical")
    args = ap.parse_args()

    with open(args.config) as f:
        config = json.load(f)
    max_seeds = 3 if args.smoke else args.max_seeds
    tag = "smoke" if args.smoke else args.tag

    out_prefix = os.path.join(RESULTS, f"p3_e2_{tag}")
    prov = Provenance(experiment_id="P3-E2", config={**config, "tag": tag, "max_seeds": max_seeds})
    result = run(config, out_prefix, max_seeds=max_seeds)
    io.write_json({"provenance": prov.to_dict(), **result}, out_prefix + "_summary.json")
    print(f"[P3-E2:{tag}] wrote {out_prefix}_*.{{csv,parquet,json}}")
    for r in result["ate_summary"]:
        print(f"  {r['condition']:28s} {r['estimator']:20s} "
              f"bias={r['mean_bias']:+.3f} rmse={r['rmse']:.3f} cover={r['ci_coverage_95']:.2f}")


if __name__ == "__main__":
    main()
