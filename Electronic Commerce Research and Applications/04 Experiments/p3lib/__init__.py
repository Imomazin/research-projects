"""P3 causal experiment library.

Reusable, deterministic building blocks for the P3 empirical programme:
- dgp: semi-synthetic data-generating process with known ground-truth ATE/CATE.
- estimators: cross-fitted nuisance models and ATE estimators (DIM, g-formula, IPW, AIPW) + T-learner HTE.
- metrics: recovery error, CI coverage, PEHE, uplift/Qini, policy value.
- heuristic: non-causal multi-touch attribution baselines (first/last/linear/time-decay/weighted).
- provenance: environment/config capture for reproducibility.

These mirror the Orbit `causal-core` product engine, but add the real nuisance
estimation and cross-fitting the TypeScript product code intentionally leaves to
an upstream research pipeline.
"""
__all__ = ["dgp", "estimators", "metrics", "heuristic", "provenance"]
