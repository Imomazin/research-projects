#!/usr/bin/env python3
"""P3-E5 — Matched-budget causal decision experiment.

Research question (RQ4/RQ5): under a matched budget, how does allocation based on
estimated incremental causal value compare with (a) historical-attribution-informed
allocation and (b) the existing rule-based Orbit optimiser, in realised incremental
value and regret against the known optimum?

Each channel c has a KNOWN concave incremental-response curve
  f_c(spend) = a_c * (1 - exp(-b_c * spend))   [true incremental conversions]
The confounded channels (retargeting, display) earn large heuristic attribution
credit but have small/zero true incremental response.

Strategies (all under the same budget, same discretisation):
  - oracle: multiple-choice knapsack on the TRUE curves (upper bound).
  - causal: knapsack on cross-fitted causal ESTIMATES of the curves (params jittered
    to represent estimation noise); a conservative LCB variant is also evaluated.
  - historical: allocate in proportion to last-touch attribution credit.
  - rule_based: allocate in proportion to OBSERVED (confounded) conversions
    (the deterministic Orbit product baseline), ignoring saturation.
Realised value is scored on the TRUE curves. This mirrors Orbit's atlas-core
multiple-choice knapsack allocator.
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
from p3lib import io_utils as io  # noqa: E402
from p3lib.provenance import Provenance  # noqa: E402

RESULTS = os.path.join(HERE, "results")

# channel: (a=saturation ceiling, b=rate). True incremental response.
TRUE = {
    "search":      (120.0, 0.30),
    "email":       (90.0, 0.35),
    "social":      (60.0, 0.25),
    "display":     (2.0, 0.20),    # ~zero true incrementality
    "retargeting": (15.0, 0.40),   # small true incrementality
}
# Misleading signals: heuristic last-touch credit and observed (confounded) volume.
ATTRIB_CREDIT = {"search": 0.10, "email": 0.16, "social": 0.09, "display": 0.20, "retargeting": 0.45}
OBSERVED_VOLUME = {"search": 90, "email": 85, "social": 55, "display": 70, "retargeting": 160}
CHANNELS = list(TRUE.keys())


def response(a, b, spend):
    return a * (1.0 - np.exp(-b * spend))


def knapsack_alloc(value_curves, budget, unit=1):
    """Multiple-choice knapsack: pick one spend level per channel (0..budget) to
    maximise summed value, mirroring atlas-core optimizeCausalBudget."""
    steps = int(round(budget / unit))
    # DP over used units -> best (value, allocation dict).
    states = {0: (0.0, {})}
    for ch, curve in value_curves.items():
        nxt = {}
        for used, (val, alloc) in states.items():
            for s in range(0, steps - used + 1):
                spend = s * unit
                v = val + curve(spend)
                total = used + s
                if total not in nxt or v > nxt[total][0]:
                    a2 = dict(alloc)
                    if spend > 0:
                        a2[ch] = spend
                    nxt[total] = (v, a2)
        states = nxt
    best_units, (best_val, best_alloc) = max(states.items(), key=lambda kv: (kv[1][0], -kv[0]))
    # Fill missing channels with 0.
    return {ch: best_alloc.get(ch, 0.0) for ch in value_curves}, best_units * unit


def proportional_alloc(weights, budget, unit=1):
    steps = int(round(budget / unit))
    chs = list(weights)
    w = np.array([max(0.0, weights[c]) for c in chs], float)
    if w.sum() <= 0:
        w = np.ones(len(chs))
    raw = w / w.sum() * steps
    base = np.floor(raw).astype(int)
    rem = steps - base.sum()
    frac = raw - base
    for i in np.argsort(-frac)[:rem]:
        base[i] += 1
    return {c: base[i] * unit for i, c in enumerate(chs)}


def realised_value(alloc):
    return sum(response(*TRUE[c], alloc.get(c, 0.0)) for c in CHANNELS)


def run(config):
    budget = config["budget"]
    unit = config["unit"]
    n_seeds = config["n_seeds"]
    est_noise = config["estimate_rel_noise"]

    true_curves = {c: (lambda s, c=c: response(*TRUE[c], s)) for c in CHANNELS}
    oracle_alloc, _ = knapsack_alloc(true_curves, budget, unit)
    oracle_val = realised_value(oracle_alloc)

    hist_alloc = proportional_alloc(ATTRIB_CREDIT, budget, unit)
    rule_alloc = proportional_alloc(OBSERVED_VOLUME, budget, unit)

    rows = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        # Causal estimate: jitter the true params to represent estimation noise.
        est_params = {c: (TRUE[c][0] * (1 + est_noise * rng.standard_normal()),
                          TRUE[c][1] * (1 + est_noise * rng.standard_normal())) for c in CHANNELS}
        est_curves = {c: (lambda s, p=est_params[c]: response(p[0], p[1], s)) for c in CHANNELS}
        causal_alloc, _ = knapsack_alloc(est_curves, budget, unit)

        # Conservative causal: shrink estimates toward a lower confidence bound.
        lcb_curves = {c: (lambda s, p=est_params[c]: response(p[0] * (1 - est_noise), p[1], s))
                      for c in CHANNELS}
        lcb_alloc, _ = knapsack_alloc(lcb_curves, budget, unit)

        for strat, alloc in [("oracle", oracle_alloc), ("causal", causal_alloc),
                             ("causal_lcb", lcb_alloc), ("historical", hist_alloc),
                             ("rule_based", rule_alloc)]:
            val = realised_value(alloc)
            rows.append({
                "seed": seed, "strategy": strat, "realised_value": val,
                "regret_vs_oracle": oracle_val - val,
                "regret_pct": 100.0 * (oracle_val - val) / oracle_val,
                **{f"spend_{c}": alloc.get(c, 0.0) for c in CHANNELS},
            })
    return rows, oracle_val, oracle_alloc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "configs/p3_e5_canonical.json"))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    with open(args.config) as f:
        config = json.load(f)
    if args.smoke:
        config = {**config, "n_seeds": 5}
    tag = "smoke" if args.smoke else "canonical"
    rows, oracle_val, oracle_alloc = run(config)
    io.write_table(rows, os.path.join(RESULTS, f"p3_e5_{tag}_runs"))

    df = pd.DataFrame(rows)
    summary = []
    for strat, g in df.groupby("strategy"):
        summary.append({
            "strategy": strat,
            "mean_realised_value": float(g["realised_value"].mean()),
            "sd_realised_value": float(g["realised_value"].std()),
            "mean_regret_vs_oracle": float(g["regret_vs_oracle"].mean()),
            "mean_regret_pct": float(g["regret_pct"].mean()),
        })
    io.write_table(summary, os.path.join(RESULTS, f"p3_e5_{tag}_summary"))
    prov = Provenance(experiment_id="P3-E5", config={**config, "true_curves": TRUE,
                                                     "attrib_credit": ATTRIB_CREDIT,
                                                     "observed_volume": OBSERVED_VOLUME, "tag": tag})
    io.write_json({"provenance": prov.to_dict(), "oracle_value": oracle_val,
                   "oracle_alloc": oracle_alloc, "summary": summary},
                  os.path.join(RESULTS, f"p3_e5_{tag}_summary.json"))
    print(f"[P3-E5:{tag}] oracle_value={oracle_val:.1f}")
    for r in sorted(summary, key=lambda x: -x["mean_realised_value"]):
        print(f"  {r['strategy']:12s} value={r['mean_realised_value']:8.1f} "
              f"regret%={r['mean_regret_pct']:6.2f}")


if __name__ == "__main__":
    main()
