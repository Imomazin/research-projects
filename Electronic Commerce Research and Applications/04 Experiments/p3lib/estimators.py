"""Cross-fitted nuisance estimation and ATE/HTE estimators.

The AIPW point estimate and influence-function SE match the Orbit `causal-core`
TypeScript estimator exactly; here the nuisances (propensity, mu0, mu1) are
learned by real models with K-fold cross-fitting so that no observation's
nuisance is predicted by a model trained on that same observation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import StratifiedKFold


@dataclass
class Estimate:
    estimator: str
    estimate: float
    se: float
    ci_low: float
    ci_high: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "estimator": self.estimator,
            "estimate": self.estimate,
            "se": self.se,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
        }


@dataclass
class Nuisances:
    e: np.ndarray            # cross-fitted propensity P(T=1|X)
    mu0: np.ndarray          # cross-fitted E[Y|T=0,X]
    mu1: np.ndarray          # cross-fitted E[Y|T=1,X]
    clipped_fraction: float
    n_folds: int
    learner: str


def _make_models(learner: str, binary_outcome: bool):
    if learner == "linear":
        prop = LogisticRegression(max_iter=1000, C=1.0)
        if binary_outcome:
            out0 = LogisticRegression(max_iter=1000, C=1.0)
            out1 = LogisticRegression(max_iter=1000, C=1.0)
        else:
            out0 = LinearRegression()
            out1 = LinearRegression()
    elif learner == "gbm":
        prop = GradientBoostingClassifier(random_state=0)
        if binary_outcome:
            out0 = GradientBoostingClassifier(random_state=0)
            out1 = GradientBoostingClassifier(random_state=0)
        else:
            out0 = GradientBoostingRegressor(random_state=0)
            out1 = GradientBoostingRegressor(random_state=0)
    else:
        raise ValueError(f"unknown learner {learner!r}")
    return prop, out0, out1


def _predict_outcome(model, X, binary_outcome: bool) -> np.ndarray:
    if binary_outcome:
        return model.predict_proba(X)[:, 1]
    return model.predict(X)


def crossfit_nuisances(
    X: np.ndarray,
    T: np.ndarray,
    Y: np.ndarray,
    *,
    learner: str = "linear",
    binary_outcome: bool = False,
    n_folds: int = 5,
    propensity_floor: float = 0.01,
    seed: int = 0,
) -> Nuisances:
    n = len(T)
    e = np.full(n, np.nan)
    mu0 = np.full(n, np.nan)
    mu1 = np.full(n, np.nan)

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    for train_idx, test_idx in skf.split(X, T):
        Xtr, Ttr, Ytr = X[train_idx], T[train_idx], Y[train_idx]
        prop, out0, out1 = _make_models(learner, binary_outcome)

        # Propensity on all training rows.
        prop.fit(Xtr, Ttr)
        e[test_idx] = prop.predict_proba(X[test_idx])[:, 1]

        # Outcome models on treated / control training rows (T-learner).
        ctrl = Ttr == 0
        trt = Ttr == 1
        out0.fit(Xtr[ctrl], Ytr[ctrl])
        out1.fit(Xtr[trt], Ytr[trt])
        mu0[test_idx] = _predict_outcome(out0, X[test_idx], binary_outcome)
        mu1[test_idx] = _predict_outcome(out1, X[test_idx], binary_outcome)

    raw = e.copy()
    e = np.clip(e, propensity_floor, 1 - propensity_floor)
    clipped_fraction = float(np.mean(raw != e))
    return Nuisances(e=e, mu0=mu0, mu1=mu1, clipped_fraction=clipped_fraction,
                     n_folds=n_folds, learner=learner)


def _ci(est: float, se: float, z: float = 1.96) -> Tuple[float, float]:
    return est - z * se, est + z * se


def difference_in_means(Y: np.ndarray, T: np.ndarray) -> Estimate:
    y1, y0 = Y[T == 1], Y[T == 0]
    est = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
    lo, hi = _ci(est, se)
    return Estimate("difference-in-means", float(est), float(se), float(lo), float(hi))


def outcome_regression(mu0: np.ndarray, mu1: np.ndarray) -> Estimate:
    contrast = mu1 - mu0
    est = contrast.mean()
    se = np.sqrt(contrast.var(ddof=1) / len(contrast))
    lo, hi = _ci(est, se)
    return Estimate("outcome-regression", float(est), float(se), float(lo), float(hi))


def ipw(Y: np.ndarray, T: np.ndarray, e: np.ndarray) -> Estimate:
    n = len(T)
    w1 = T / e
    w0 = (1 - T) / (1 - e)
    mu1 = np.sum(w1 * Y) / np.sum(w1)
    mu0 = np.sum(w0 * Y) / np.sum(w0)
    est = mu1 - mu0
    wbar1, wbar0 = w1.mean(), w0.mean()
    inf = (w1 * (Y - mu1)) / wbar1 - (w0 * (Y - mu0)) / wbar0
    se = np.sqrt(np.sum(inf ** 2) / (n * n))
    lo, hi = _ci(est, se)
    return Estimate("ipw", float(est), float(se), float(lo), float(hi))


def aipw(Y: np.ndarray, T: np.ndarray, e: np.ndarray, mu0: np.ndarray, mu1: np.ndarray) -> Estimate:
    n = len(T)
    score = mu1 - mu0 + T * (Y - mu1) / e - (1 - T) * (Y - mu0) / (1 - e)
    est = score.mean()
    se = np.sqrt(score.var(ddof=1) / n)
    lo, hi = _ci(est, se)
    return Estimate("aipw", float(est), float(se), float(lo), float(hi))


def all_ate_estimates(Y, T, nuis: Nuisances) -> Dict[str, Estimate]:
    return {
        "difference-in-means": difference_in_means(Y, T),
        "outcome-regression": outcome_regression(nuis.mu0, nuis.mu1),
        "ipw": ipw(Y, T, nuis.e),
        "aipw": aipw(Y, T, nuis.e, nuis.mu0, nuis.mu1),
    }


def tlearner_cate(nuis: Nuisances) -> np.ndarray:
    """Cross-fitted T-learner CATE prediction."""
    return nuis.mu1 - nuis.mu0
