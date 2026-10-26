"""Monte Carlo check of the finite-sample guarantee of private aggregate risk control.

Calibration scores are drawn from known Beta distributions, so the population miss rate and
false-alarm rate of any certified threshold are computed exactly from the Beta CDF. For each
condition the script records how often the certified threshold violates the target (the
guarantee bounds this by delta_test + delta_count = 0.05 per side) and the population share of
decisions that are automated.
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("private_risk_control", HERE / "Private Risk Control Library.py")
L = importlib.util.module_from_spec(spec)
sys.modules["private_risk_control"] = L
spec.loader.exec_module(L)

SCENARIOS = {"separated": {"pos": (6, 2), "neg": (2, 8)}, "overlapping": {"pos": (3, 2), "neg": (2, 3)}}
REPLICATIONS = 1000
POSITIVES = [30, 100, 400]
EPSILONS = [1.0, 2.0, 4.0, 8.0]
NEG_RATIO = 10
CLIENTS = 4


def population(pol, sc):
    a1, b1 = SCENARIOS[sc]["pos"]
    a0, b0 = SCENARIOS[sc]["neg"]
    tl, th = pol["t_low"], pol["t_high"]
    miss = stats.beta.cdf(tl, a1, b1) if np.isfinite(tl) else (1.0 if tl > 0 else 0.0)
    th_eff = max(th, tl) if np.isfinite(th) else th
    fa = stats.beta.sf(th_eff, a0, b0) if np.isfinite(th_eff) else 0.0
    auto_pos = miss + (stats.beta.sf(th_eff, a1, b1) if np.isfinite(th_eff) else 0.0)
    auto_neg = (stats.beta.cdf(tl, a0, b0) if np.isfinite(tl) else 0.0) + fa
    return float(miss), float(fa), float(auto_pos), float(auto_neg)


def main():
    policy = L.RiskPolicy()
    rng = np.random.default_rng(20261026)
    rows = []
    start = time.time()
    for sc in SCENARIOS:
        a1, b1 = SCENARIOS[sc]["pos"]
        a0, b0 = SCENARIOS[sc]["neg"]
        for n1 in POSITIVES:
            conditions = [("nonprivate_ltt", None), ("nonprivate_plugin", None)]
            conditions += [(m, e) for e in EPSILONS for m in ("proposed", "ucb_without_noise", "plugin")]
            for method, eps in conditions:
                mu = L.calibrate_skellam_mu(eps, 1e-5) if eps else 0.0
                stats_rep = []
                for _ in range(REPLICATIONS):
                    sp = rng.beta(a1, b1, n1)
                    sn = rng.beta(a0, b0, n1 * NEG_RATIO)
                    cp = np.array_split(sp, CLIENTS)
                    cn = np.array_split(sn, CLIENTS)
                    scores = [np.concatenate([p, q]) for p, q in zip(cp, cn)]
                    labels = [np.r_[np.ones(len(p), int), np.zeros(len(q), int)] for p, q in zip(cp, cn)]
                    pol = L.binary_policy(scores, labels, mu, policy, method, rng)
                    stats_rep.append(population(pol, sc))
                arr = np.array(stats_rep)
                rows.append({"scenario": sc, "positives": n1, "negatives": n1 * NEG_RATIO,
                             "method": method, "epsilon": eps if eps else "none", "mu": mu,
                             "replications": REPLICATIONS,
                             "miss_violation_rate": float(np.mean(arr[:, 0] > policy.alpha_miss)),
                             "false_alarm_violation_rate": float(np.mean(arr[:, 1] > policy.alpha_false_alarm)),
                             "mean_population_miss": float(arr[:, 0].mean()),
                             "mean_population_false_alarm": float(arr[:, 1].mean()),
                             "mean_automation_faults": float(arr[:, 2].mean()),
                             "mean_automation_normal": float(arr[:, 3].mean())})
                print(sc, n1, method, eps, rows[-1]["miss_violation_rate"], rows[-1]["false_alarm_violation_rate"],
                      round(rows[-1]["mean_automation_normal"], 3), f"{time.time() - start:.0f}s", flush=True)
    out = HERE / "Results" / "Guarantee Validation"
    out.mkdir(parents=True, exist_ok=True)
    (out / "Monte Carlo Validation.json").write_text(json.dumps({
        "targets": {"alpha_miss": policy.alpha_miss, "alpha_false_alarm": policy.alpha_false_alarm,
                    "delta_per_side": policy.delta_test + policy.delta_count},
        "scenarios": SCENARIOS, "rows": rows}, indent=1) + "\n")


if __name__ == "__main__":
    main()
