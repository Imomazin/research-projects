#!/usr/bin/env python3
"""Generate a schema-exact synthetic fixture for the Criteo uplift benchmark.

This is NOT Criteo data and NEVER manuscript evidence. It reproduces the released
schema (f0..f11, treatment, conversion, visit, exposure) with RANDOMIZED treatment
(prevalence ~0.85, as in the public release) and a known positive uplift, so the
P3-E3 pipeline can be validated end-to-end: under randomization AIPW must agree
with the randomized difference in means, and observed uplift must increase with
predicted-uplift decile.
"""
from __future__ import annotations

import argparse
import gzip
import os

import numpy as np
import pandas as pd


def make(n: int, seed: int, treatment_rate: float = 0.85) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    d = 12
    X = rng.standard_normal((n, d))
    T = (rng.random(n) < treatment_rate).astype(int)     # randomized (independent of X)
    beta_v = np.linspace(0.3, -0.2, d)
    beta_c = np.linspace(0.2, -0.1, d)
    # Heterogeneous randomized uplift on visit and conversion.
    tau_visit = 0.05 + 0.04 * X[:, 0]
    tau_conv = 0.015 + 0.02 * X[:, 1]
    p_visit = 1 / (1 + np.exp(-(-1.0 + X @ beta_v))) + tau_visit * T
    p_conv = 1 / (1 + np.exp(-(-2.5 + X @ beta_c))) + tau_conv * T
    visit = (rng.random(n) < np.clip(p_visit, 0, 1)).astype(int)
    conversion = (rng.random(n) < np.clip(p_conv, 0, 1)).astype(int)
    exposure = T  # in the release exposure tracks treatment for treated users
    df = pd.DataFrame(X, columns=[f"f{i}" for i in range(d)])
    df["treatment"] = T
    df["conversion"] = conversion
    df["visit"] = visit
    df["exposure"] = exposure
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "results", "_fixtures", "criteo_uplift_fixture.csv.gz"))
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = make(args.n, args.seed)
    with gzip.open(args.out, "wt") as f:
        df.to_csv(f, index=False)
    print(f"wrote fixture {args.out} rows={len(df)} treat_rate={df.treatment.mean():.3f} "
          f"visit_rate={df.visit.mean():.3f} conv_rate={df.conversion.mean():.3f}")


if __name__ == "__main__":
    main()
