"""Smallest calibration class count for which any automatic decision region can be certified.

The floor is reached when a zero noisy event count passes the binomial-Skellam test at the
lower count bound, with the first bin admitted. Values are exact computations, not experiments.
"""
import importlib.util
import json
import math
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("private_risk_control", HERE / "Private Risk Control Library.py")
L = importlib.util.module_from_spec(spec)
sys.modules["private_risk_control"] = L
spec.loader.exec_module(L)


def floor(alpha, mu, bins=26, delta_test=0.04, delta_count=0.01):
    for n in range(1, 5000):
        n_low = L.count_lower_bound(n, bins, mu, delta_count) if mu > 0 else n
        if L.binomial_skellam_pvalue(0, n_low, alpha, mu) <= delta_test:
            return n
    return float("nan")


rows = []
for target, alpha in [("miss rate 0.10", 0.10), ("false-alarm rate 0.05", 0.05), ("miss rate 0.20", 0.20)]:
    for eps in [None, 8, 4, 2, 1, 0.5]:
        mu = 0.0 if eps is None else L.calibrate_skellam_mu(float(eps), 1e-5)
        rows.append({"target": target, "epsilon_calibration": "non-private" if eps is None else eps,
                     "skellam_mu": mu, "minimum_class_count": floor(alpha, mu)})
df = pd.DataFrame(rows)
out = HERE / "Results" / "Analysis"
out.mkdir(parents=True, exist_ok=True)
df.to_csv(out / "Evidence Floor.csv", index=False)
print(df.to_string())
