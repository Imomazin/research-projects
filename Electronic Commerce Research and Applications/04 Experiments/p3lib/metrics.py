"""Evaluation metrics for causal estimation and decision quality.

Known-truth metrics (semi-synthetic): ATE bias/RMSE, CI coverage, PEHE, rank
correlation. Randomized-design metrics (no individual counterfactuals needed):
uplift-by-decile, Qini, doubly-robust policy value and regret.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np
from scipy import stats


def recovery_summary(estimates: Sequence[float], ci_low: Sequence[float],
                     ci_high: Sequence[float], ses: Sequence[float], truth: float) -> Dict[str, float]:
    est = np.asarray(estimates, float)
    lo = np.asarray(ci_low, float)
    hi = np.asarray(ci_high, float)
    se = np.asarray(ses, float)
    bias = est - truth
    coverage = np.mean((lo <= truth) & (truth <= hi))
    return {
        "truth": float(truth),
        "mean_estimate": float(est.mean()),
        "mean_bias": float(bias.mean()),
        "mean_abs_bias": float(np.abs(bias).mean()),
        "rmse": float(np.sqrt(np.mean(bias ** 2))),
        "empirical_sd": float(est.std(ddof=1)) if len(est) > 1 else 0.0,
        "mean_se": float(se.mean()),
        "ci_coverage_95": float(coverage),
        "n_reps": int(len(est)),
    }


def pehe(pred_tau: np.ndarray, true_tau: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred_tau - true_tau) ** 2)))


def cate_rank_corr(pred_tau: np.ndarray, true_tau: np.ndarray) -> float:
    if np.std(pred_tau) < 1e-12 or np.std(true_tau) < 1e-12:
        return 0.0
    return float(stats.spearmanr(pred_tau, true_tau).correlation)


def uplift_by_decile(pred_tau: np.ndarray, Y: np.ndarray, T: np.ndarray, n_bins: int = 10) -> List[Dict[str, float]]:
    order = np.argsort(-pred_tau)
    bins = np.array_split(order, n_bins)
    rows = []
    for i, idx in enumerate(bins):
        t = T[idx]
        y = Y[idx]
        yt = y[t == 1]
        yc = y[t == 0]
        obs = (yt.mean() - yc.mean()) if len(yt) and len(yc) else float("nan")
        rows.append({
            "decile": i + 1,
            "n": int(len(idx)),
            "mean_pred_uplift": float(pred_tau[idx].mean()),
            "observed_uplift": float(obs),
            "n_treated": int((t == 1).sum()),
            "n_control": int((t == 0).sum()),
        })
    return rows


def qini_coefficient(pred_tau: np.ndarray, Y: np.ndarray, T: np.ndarray) -> Dict[str, float]:
    """Qini coefficient for a binary-response randomized experiment.

    Returns the area between the Qini curve and the random-targeting diagonal,
    normalised by the number of observations.
    """
    order = np.argsort(-pred_tau)
    t = T[order].astype(float)
    y = Y[order].astype(float)
    n = len(t)
    nt1 = np.cumsum(t)
    nt0 = np.cumsum(1 - t)
    yt1 = np.cumsum(t * y)
    yt0 = np.cumsum((1 - t) * y)
    with np.errstate(divide="ignore", invalid="ignore"):
        qini = yt1 - yt0 * np.where(nt0 > 0, nt1 / np.maximum(nt0, 1), 0.0)
    total_treated = t.sum()
    total_lift = (yt1[-1] - yt0[-1] * (total_treated / max(n - total_treated, 1)))
    x = np.arange(1, n + 1) / n
    random_line = total_lift * x
    area = float(np.trapz(qini - random_line, x))
    return {"qini_coefficient": area / n, "cum_lift_at_100pct": float(total_lift)}


def dr_policy_value(policy: np.ndarray, Y: np.ndarray, T: np.ndarray,
                    e: np.ndarray, mu0: np.ndarray, mu1: np.ndarray) -> float:
    """Doubly-robust estimate of E[Y(policy(X))] for a binary policy in {0,1}."""
    mu_d = np.where(policy == 1, mu1, mu0)
    p_d = np.where(policy == 1, e, 1 - e)
    match = (T == policy).astype(float)
    dr = mu_d + match / p_d * (Y - mu_d)
    return float(dr.mean())


def policy_analysis(pred_tau: np.ndarray, Y: np.ndarray, T: np.ndarray,
                    e: np.ndarray, mu0: np.ndarray, mu1: np.ndarray,
                    true_tau: np.ndarray | None = None) -> Dict[str, float]:
    learned = (pred_tau > 0).astype(int)
    treat_all = np.ones_like(learned)
    treat_none = np.zeros_like(learned)
    out = {
        "value_learned_policy": dr_policy_value(learned, Y, T, e, mu0, mu1),
        "value_treat_all": dr_policy_value(treat_all, Y, T, e, mu0, mu1),
        "value_treat_none": dr_policy_value(treat_none, Y, T, e, mu0, mu1),
        "fraction_treated_by_policy": float(learned.mean()),
    }
    if true_tau is not None:
        oracle = (true_tau > 0).astype(int)
        out["value_oracle_policy"] = dr_policy_value(oracle, Y, T, e, mu0, mu1)
        out["regret_vs_oracle"] = out["value_oracle_policy"] - out["value_learned_policy"]
    return out
