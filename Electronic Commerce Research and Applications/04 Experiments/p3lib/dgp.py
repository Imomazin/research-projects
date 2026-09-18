"""Semi-synthetic data-generating process with known causal ground truth.

Design (binary treatment T, continuous or binary outcome Y, covariates X in R^d):

  X            ~ N(0, I_d)
  logit e(X)   = intercept + confounding * (beta . X)          # confounder -> T
  T            ~ Bernoulli(e(X))
  mu0(X)       = base_intercept + (gamma . X)                  # confounder -> Y
  tau(X)       = ate + hte * X[:, 0]                           # heterogeneous effect
  mu1(X)       = mu0(X) + tau(X)
  Y_cont       = mu_T(X) + noise * N(0, 1)
  Y_bin        ~ Bernoulli(clip(mu_T(X), 0, 1))

Because beta and gamma both load on X, the naive difference in means is
confounded; adjusting for X removes the bias. Overlap degrades as `confounding`
grows (propensities pushed toward 0/1). The true sample ATE is mean(tau(X_i))
and the true individual effect tau(X_i) is retained for CATE/PEHE evaluation.

`unmeasured_index`: covariates with index >= this are HIDDEN from estimators
(returned separately) to simulate unmeasured confounding without changing truth.
`measurement_error`: Gaussian noise added to the OBSERVED covariates only.
`selection_bias`: if >0, rows are kept with probability depending on outcome and
treatment (a collider-style selection), biasing the observed sample.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class DGPConfig:
    n: int = 4000
    d: int = 5
    ate: float = 1.0
    hte: float = 0.7
    confounding: float = 1.0
    intercept: float = 0.0          # treatment-prevalence shift
    base_intercept: float = 0.0
    noise: float = 1.0
    binary_outcome: bool = False
    unmeasured_index: Optional[int] = None   # covariates >= idx are hidden
    hide_covariates: Optional[List[int]] = None   # specific covariate indices hidden from estimators
    measurement_error: float = 0.0
    selection_bias: float = 0.0
    nonlinear_strength: float = 0.0           # nonlinear/interaction terms in mu0 and e(X)
    beta: Optional[List[float]] = None        # confounder -> T loadings
    gamma: Optional[List[float]] = None       # confounder -> Y loadings


@dataclass
class DGPResult:
    X: np.ndarray            # observed covariates (post measurement error, unmeasured dropped)
    X_full: np.ndarray       # full latent covariates
    T: np.ndarray
    Y: np.ndarray
    propensity: np.ndarray   # true e(X_full)
    mu0: np.ndarray          # true E[Y|do(T=0),X]
    mu1: np.ndarray          # true E[Y|do(T=1),X]
    tau: np.ndarray          # true individual effect
    true_ate: float          # population ATE (= config.ate)
    true_sample_ate: float   # mean(tau_i) on generated sample
    covariate_names: List[str]


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def generate(config: DGPConfig, seed: int = 0) -> DGPResult:
    rng = np.random.default_rng(seed)
    d = config.d
    beta = np.array(config.beta) if config.beta is not None else np.linspace(1.0, 0.4, d)
    gamma = np.array(config.gamma) if config.gamma is not None else np.linspace(0.8, 0.3, d)
    beta = beta / np.linalg.norm(beta)
    gamma = gamma / np.linalg.norm(gamma)

    X_full = rng.standard_normal((config.n, d))
    nl = config.nonlinear_strength
    # Nonlinear/interaction terms shared by treatment and outcome (a nonlinear
    # confounder), so linear nuisance learners are misspecified while the true
    # treatment effect tau stays additive and known.
    nonlin = nl * ((X_full[:, 0] ** 2 - 1.0) + X_full[:, min(1, d - 1)] * X_full[:, min(2, d - 1)])
    logit_e = config.intercept + config.confounding * (X_full @ beta) + config.confounding * nonlin
    e = _sigmoid(logit_e)
    T = (rng.random(config.n) < e).astype(int)

    mu0 = config.base_intercept + (X_full @ gamma) + nonlin
    tau = config.ate + config.hte * X_full[:, 0]
    mu1 = mu0 + tau

    mu_t = np.where(T == 1, mu1, mu0)
    if config.binary_outcome:
        # Interpret mu as a probability after squashing to keep it in [0,1].
        p0 = np.clip(_sigmoid(mu0), 1e-4, 1 - 1e-4)
        p1 = np.clip(_sigmoid(mu1), 1e-4, 1 - 1e-4)
        mu0, mu1 = p0, p1
        tau = p1 - p0
        pt = np.where(T == 1, p1, p0)
        Y = (rng.random(config.n) < pt).astype(float)
    else:
        Y = mu_t + config.noise * rng.standard_normal(config.n)

    keep = np.ones(config.n, dtype=bool)
    if config.selection_bias > 0:
        # Collider-style selection on outcome and treatment.
        sel_logit = config.selection_bias * (Y - Y.mean()) / (Y.std() + 1e-9) + \
            config.selection_bias * (T - 0.5)
        sel_p = _sigmoid(sel_logit)
        keep = rng.random(config.n) < sel_p

    X_obs = X_full.copy()
    if config.measurement_error > 0:
        X_obs = X_obs + config.measurement_error * rng.standard_normal(X_obs.shape)
    keep_cols = list(range(d))
    if config.unmeasured_index is not None:
        keep_cols = list(range(config.unmeasured_index))
    if config.hide_covariates is not None:
        keep_cols = [i for i in keep_cols if i not in set(config.hide_covariates)]
    X_obs = X_obs[:, keep_cols]
    names = [f"x{i}" for i in keep_cols]

    idx = np.where(keep)[0]
    return DGPResult(
        X=X_obs[idx],
        X_full=X_full[idx],
        T=T[idx],
        Y=Y[idx],
        propensity=e[idx],
        mu0=mu0[idx],
        mu1=mu1[idx],
        tau=tau[idx],
        true_ate=float(config.ate) if not config.binary_outcome else float(np.mean(mu1 - mu0)),
        true_sample_ate=float(np.mean(tau[idx])),
        covariate_names=names,
    )
