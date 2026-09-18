#!/usr/bin/env python3
"""P3-E6 — Assumption violations and sensitivity analysis.

Research question (RQ3): how do causal estimates and decisions degrade as key
identification assumptions are stressed? One factor is varied at a time from a
baseline; recovery error, CI coverage and overlap diagnostics are recorded.

Sweeps: confounding strength, treatment prevalence/imbalance, unmeasured
confounding (hiding the strongest confounder), sample size, outcome noise,
covariate measurement error, collider selection bias, and HTE strength. A placebo
check permutes the treatment label (true effect = 0).

Development: --smoke / --max-seeds. Canonical: no overrides.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3lib import dgp, estimators as est, metrics as m, io_utils as io  # noqa: E402
from p3lib.provenance import Provenance  # noqa: E402

RESULTS = os.path.join(HERE, "results")

BASELINE = dict(n=4000, d=5, ate=1.0, hte=0.7, noise=1.0, confounding=1.0)

SWEEPS = {
    "confounding_strength": ("confounding", [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]),
    "treatment_intercept": ("intercept", [-2.5, -1.5, 0.0, 1.5, 2.5]),
    "sample_size": ("n", [500, 1000, 2000, 4000, 8000]),
    "outcome_noise": ("noise", [0.25, 0.5, 1.0, 2.0, 4.0]),
    "measurement_error": ("measurement_error", [0.0, 0.25, 0.5, 1.0, 2.0]),
    "selection_bias": ("selection_bias", [0.0, 0.5, 1.0, 2.0]),
    "hte_strength": ("hte", [0.0, 0.5, 1.0, 2.0]),
}


def _run_cell(cfg_kwargs, learner, n_folds, floor, seed, placebo=False):
    cfg = dgp.DGPConfig(**cfg_kwargs)
    data = dgp.generate(cfg, seed=seed)
    T = data.T
    truth = data.true_ate
    if placebo:
        rng = np.random.default_rng(10_000 + seed)
        T = rng.permutation(data.T)
        truth = 0.0
    nu = est.crossfit_nuisances(data.X, T, data.Y, learner=learner,
                                n_folds=n_folds, propensity_floor=floor, seed=seed)
    ests = est.all_ate_estimates(data.Y, T, nu)
    return data, nu, ests, truth


def run(config, out_prefix, max_seeds=None):
    n_seeds = config["n_seeds"] if max_seeds is None else min(config["n_seeds"], max_seeds)
    learner = config["learner"]
    n_folds = config["n_folds"]
    floor = config["propensity_floor"]
    rows = []

    def record(sweep, value, seed, data, nu, ests, truth, unmeasured=False):
        for name, e in ests.items():
            rows.append({
                "sweep": sweep, "value": value, "seed": seed, "estimator": name,
                "estimate": e.estimate, "se": e.se, "ci_low": e.ci_low, "ci_high": e.ci_high,
                "truth": truth, "min_propensity": float(nu.e.min()),
                "max_propensity": float(nu.e.max()), "clipped_fraction": nu.clipped_fraction,
                "treatment_rate": float(data.T.mean()), "unmeasured": unmeasured,
            })

    for sweep, (param, values) in SWEEPS.items():
        for value in values:
            for seed in range(n_seeds):
                kwargs = {**BASELINE, param: value}
                data, nu, ests, truth = _run_cell(kwargs, learner, n_folds, floor, seed)
                record(sweep, value, seed, data, nu, ests, truth)

    # Unmeasured confounding: hide the strongest confounder(s) x0..
    for hide in [[], [4], [3, 4], [2, 3, 4], [0]]:
        label = "none" if not hide else ",".join(f"x{i}" for i in hide)
        for seed in range(n_seeds):
            kwargs = {**BASELINE, "hide_covariates": hide}
            data, nu, ests, truth = _run_cell(kwargs, learner, n_folds, floor, seed)
            record("unmeasured_confounding", label, seed, data, nu, ests, truth, unmeasured=bool(hide))

    # Placebo: permuted treatment, true effect 0.
    for seed in range(n_seeds):
        data, nu, ests, truth = _run_cell({**BASELINE}, learner, n_folds, floor, seed, placebo=True)
        record("placebo_permuted_treatment", "permuted", seed, data, nu, ests, truth)

    df = pd.DataFrame(rows)
    io.write_table(rows, out_prefix + "_runs")

    summary = []
    for (sweep, value, estimator), g in df.groupby(["sweep", "value", "estimator"]):
        s = m.recovery_summary(g["estimate"], g["ci_low"], g["ci_high"], g["se"], g["truth"].iloc[0])
        s.update({"sweep": sweep, "value": value, "estimator": estimator,
                  "mean_min_propensity": float(g["min_propensity"].mean()),
                  "mean_treatment_rate": float(g["treatment_rate"].mean())})
        summary.append(s)
    io.write_table(summary, out_prefix + "_summary")
    return {"summary": summary}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "configs/p3_e6_canonical.json"))
    ap.add_argument("--max-seeds", type=int, default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    max_seeds = 2 if args.smoke else args.max_seeds
    tag = "smoke" if args.smoke else "canonical"
    out_prefix = os.path.join(RESULTS, f"p3_e6_{tag}")
    prov = Provenance(experiment_id="P3-E6", config={**config, "baseline": BASELINE,
                                                     "sweeps": {k: v[1] for k, v in SWEEPS.items()},
                                                     "tag": tag, "max_seeds": max_seeds})
    result = run(config, out_prefix, max_seeds=max_seeds)
    io.write_json({"provenance": prov.to_dict(), **result}, out_prefix + "_summary.json")
    print(f"[P3-E6:{tag}] wrote {out_prefix}_*")
    aipw = [r for r in result["summary"] if r["estimator"] == "aipw"]
    for r in sorted(aipw, key=lambda x: (x["sweep"], str(x["value"]))):
        print(f"  {r['sweep']:26s} {str(r['value']):>10s} aipw bias={r['mean_bias']:+.3f} "
              f"rmse={r['rmse']:.3f} cover={r['ci_coverage_95']:.2f} minP={r['mean_min_propensity']:.3f}")


if __name__ == "__main__":
    main()
