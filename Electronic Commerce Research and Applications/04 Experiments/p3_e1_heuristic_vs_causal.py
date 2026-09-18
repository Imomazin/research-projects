#!/usr/bin/env python3
"""P3-E1 — Heuristic attribution vs incremental causal contribution.

Research question (RQ1): where and why does heuristic multi-touch attribution
diverge from incremental causal contribution, and does it matter for channel
ranking / decisions?

Journey DGP (known causal effects per channel):
  - latent interest z drives conversion AND retargeting exposure (a confounder).
  - `retargeting` fires last and is shown to already-interested users -> it earns
    large last-touch credit but has a small true causal effect.
  - `display` appears in many journeys but has ZERO true causal effect.
  - `search`, `email`, `social` carry the real incremental effect.

We compute the five heuristic attribution shares and, for the same sample, an
OBSERVATIONAL causal incremental effect per channel via cross-fitted AIPW
(treatment = exposed to channel c; adjustment = observed pre-exposure covariates,
including z). Heuristic shares are DESCRIPTIVE credit; AIPW effects are causal
estimates UNDER STATED ASSUMPTIONS -- never randomized ground truth.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p3lib import estimators as est, heuristic as h, io_utils as io  # noqa: E402
from p3lib.provenance import Provenance  # noqa: E402

RESULTS = os.path.join(HERE, "results")

CHANNELS = ["search", "social", "display", "email", "retargeting"]
TRUE_EFFECT = {"search": 0.06, "social": 0.04, "display": 0.00, "email": 0.05, "retargeting": 0.01}
BASE_EXPOSURE = {"search": 0.55, "social": 0.45, "display": 0.60, "email": 0.35}
# Nominal recency (days before conversion): retargeting last, search earliest.
RECENCY = {"search": 12.0, "social": 8.0, "display": 6.0, "email": 4.0, "retargeting": 1.0}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def generate_journeys(n, seed):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)                 # latent interest (observed covariate)
    ctx = rng.standard_normal((n, 3))          # additional observed covariates
    exposure = {}
    for ch in ["search", "social", "display", "email"]:
        p = np.clip(BASE_EXPOSURE[ch] + 0.05 * z, 0.02, 0.98)
        exposure[ch] = (rng.random(n) < p).astype(int)
    # Retargeting is confounded by z (shown to interested users).
    p_ret = _sigmoid(-0.2 + 1.2 * z)
    exposure["retargeting"] = (rng.random(n) < p_ret).astype(int)

    base = 0.05
    conv_p = np.full(n, base) + 0.15 * z
    for ch in CHANNELS:
        conv_p = conv_p + TRUE_EFFECT[ch] * exposure[ch]
    conv_p = np.clip(conv_p, 0.001, 0.999)
    converted = (rng.random(n) < conv_p).astype(int)

    # Build journeys as ordered touchpoint lists with small timing jitter.
    journeys = []
    for i in range(n):
        tps = []
        for ch in CHANNELS:
            if exposure[ch][i] == 1:
                t = max(0.1, RECENCY[ch] + rng.normal(0, 0.5))
                tps.append((ch, t))
        journeys.append(tps)

    X = np.column_stack([z, ctx])
    return dict(z=z, X=X, exposure=exposure, converted=converted, journeys=journeys,
                covariate_names=["z", "c0", "c1", "c2"])


def run(config, out_prefix):
    n = config["n"]
    seed = config["seed"]
    data = generate_journeys(n, seed)
    converted = data["converted"]
    journeys = data["journeys"]

    # Heuristic shares.
    heur_shares = {model: h.attribution_shares(journeys, converted, model) for model in h.MODELS}

    # Observational causal incremental effect per channel via cross-fitted AIPW.
    rows = []
    n_conv = int(converted.sum())
    for ch in CHANNELS:
        Tc = data["exposure"][ch]
        # Adjust for observed pre-exposure covariates. Do NOT adjust for other
        # channels (potential colliders/mediators via z).
        nu = est.crossfit_nuisances(data["X"], Tc, converted.astype(float),
                                    learner="linear", binary_outcome=True,
                                    n_folds=config["n_folds"],
                                    propensity_floor=config["propensity_floor"], seed=seed)
        aipw = est.aipw(converted.astype(float), Tc, nu.e, nu.mu0, nu.mu1)
        dim = est.difference_in_means(converted.astype(float), Tc)
        incr_conversions = aipw.estimate * int(Tc.sum())   # exposed * per-unit effect
        row = {
            "channel": ch,
            "true_effect": TRUE_EFFECT[ch],
            "exposed": int(Tc.sum()),
            "naive_diff_in_means": dim.estimate,
            "aipw_effect": aipw.estimate,
            "aipw_se": aipw.se,
            "aipw_ci_low": aipw.ci_low,
            "aipw_ci_high": aipw.ci_high,
            "incremental_conversions_est": incr_conversions,
        }
        for model in h.MODELS:
            row[f"heuristic_{model}"] = heur_shares[model].get(ch, 0.0)
        rows.append(row)

    df = pd.DataFrame(rows)
    io.write_table(rows, out_prefix + "_channels")

    # Ranking divergence: correlate each heuristic share ranking with true-effect ranking
    # and with the AIPW ranking.
    true_rank = df["true_effect"].values
    aipw_rank = df["aipw_effect"].values
    rank_rows = []
    for model in h.MODELS:
        hv = df[f"heuristic_{model}"].values
        rank_rows.append({
            "heuristic_model": model,
            "spearman_vs_true_effect": float(stats.spearmanr(hv, true_rank).correlation),
            "spearman_vs_aipw": float(stats.spearmanr(hv, aipw_rank).correlation),
            "top_channel_heuristic": CHANNELS[int(np.argmax(hv))],
        })
    rank_rows.append({
        "heuristic_model": "aipw_causal",
        "spearman_vs_true_effect": float(stats.spearmanr(aipw_rank, true_rank).correlation),
        "spearman_vs_aipw": 1.0,
        "top_channel_heuristic": CHANNELS[int(np.argmax(aipw_rank))],
    })
    io.write_table(rank_rows, out_prefix + "_ranking")
    return {"channels": rows, "ranking": rank_rows, "n_conversions": n_conv}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "configs/p3_e1_canonical.json"))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    if args.smoke:
        config = {**config, "n": 5000}
    tag = "smoke" if args.smoke else "canonical"
    out_prefix = os.path.join(RESULTS, f"p3_e1_{tag}")
    prov = Provenance(experiment_id="P3-E1", config={**config, "true_effect": TRUE_EFFECT, "tag": tag})
    result = run(config, out_prefix)
    io.write_json({"provenance": prov.to_dict(), **result}, out_prefix + "_summary.json")
    print(f"[P3-E1:{tag}] conversions={result['n_conversions']}; wrote {out_prefix}_*")
    for r in result["channels"]:
        print(f"  {r['channel']:12s} true={r['true_effect']:.3f} aipw={r['aipw_effect']:+.3f}"
              f" naive={r['naive_diff_in_means']:+.3f} lasttouch={r['heuristic_last-touch']:.3f}")
    for r in result["ranking"]:
        print(f"  rank {r['heuristic_model']:14s} top={r['top_channel_heuristic']:12s}"
              f" rho_true={r['spearman_vs_true_effect']:+.2f}")


if __name__ == "__main__":
    main()
