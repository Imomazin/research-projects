# P3 Results Interpretation

Working notes for the writing agent **C** — not journal prose. Every number traces to a
committed result file in `04 Experiments/results/`. "What C may claim" / "must not claim" are
binding.

---

## P3-E2 — Semi-synthetic ATE/CATE recovery (100 seeds/condition; n=4000)

Source: `p3_e2_canonical_ate_summary.csv`, `_hte_summary.csv`.

| Condition | Estimator | Mean bias | RMSE | 95% coverage |
|---|---|---|---|---|
| linear, low confounding | difference-in-means | +0.580 | 0.583 | 0.00 |
| linear, low confounding | AIPW | +0.003 | 0.036 | 0.94 |
| linear, moderate | difference-in-means | +1.007 | 1.008 | 0.00 |
| linear, moderate | AIPW | +0.004 | 0.035 | 0.98 |
| linear, high | difference-in-means | +1.472 | 1.473 | 0.00 |
| linear, high | AIPW | +0.006 | 0.061 | 0.92 |
| nonlinear, linear learner | AIPW | +1.873 | 1.875 | 0.00 |
| nonlinear, GBM learner | AIPW | +0.352 | 0.356 | 0.00 |

- **Main result:** under correct specification, cross-fitted AIPW (and IPW, g-formula) recover
  the known ATE with near-nominal CI coverage, while the naive difference in means is biased by
  the full confounding gap (up to +1.47 against a true ATE of 1.0).
- **Failure region:** with a nonlinear confounder and a *linear* learner, **all** estimators —
  AIPW included — are badly biased (AIPW +1.87). Double robustness cannot rescue two wrong
  models. A flexible (GBM) learner cuts AIPW bias ~5× (to +0.35) but residual finite-sample
  bias remains and CI coverage is still 0.
- **Coverage nuance:** g-formula shows undercoverage (~0.42–0.46) even when nearly unbiased —
  its plug-in SE ignores nuisance-estimation error. AIPW's influence-function SE gives proper
  coverage. This is a methodological point worth stating.
- **CATE:** T-learner PEHE is small and rank correlation high under correct specification
  (see `_hte_summary.csv`); it degrades with nonlinearity — same failure region.
- **What C may claim:** the pipeline recovers known effects and correct CIs under stated
  assumptions; misspecification with inflexible learners is a documented failure region.
- **Must not claim:** that AIPW is unconditionally robust; that low bias implies valid CIs.

## P3-E6 — Assumption/sensitivity & failure mapping (60 seeds; AIPW)

Source: `p3_e6_canonical_summary.csv`.

- **Robust factors (AIPW stays ~unbiased, precision only):** confounding strength 0→3 (bias
  ≤0.006; RMSE 0.032→0.064; min propensity collapses to 0.01 — overlap, not bias, is the cost);
  outcome noise; HTE strength; treatment prevalence; sample size (RMSE 0.099 at n=500 → 0.028 at
  n=8000). Placebo permuted-treatment recovers ~0 (bias −0.002, coverage 0.92) — negative control passes.
- **Failure regions (identification breaks; graded dose-response):**
  - Unmeasured confounding — hiding weak confounder x4: bias +0.056; x3,x4: +0.162; x2,x3,x4:
    +0.328; hiding the strongest confounder x0: **+0.552**, coverage 0.
  - Covariate measurement error 0.25→2.0: bias +0.073 → **+0.836**, coverage → 0.
  - Collider selection (strength 2.0): bias **−0.191**, coverage 0.17.
- **What C may claim:** causal reliability is governed by identification (exchangeability,
  correct measurement, no selection), not by confounding magnitude per se; the method degrades
  gracefully and predictably, and overlap diagnostics flag the precision cost.
- **Must not claim:** that good overlap/balance implies no unmeasured confounding.

## P3-E1 — Heuristic attribution vs incremental causal contribution (n=60,000)

Source: `p3_e1_canonical_channels.csv`, `_ranking.csv`.

- Confounded **retargeting** (fires last, shown to already-interested users): true effect 0.010,
  AIPW 0.005, naive diff-in-means 0.122, **last-touch credit share 0.674**. **Display**: true
  effect 0.000, AIPW 0.001, last-touch credit 0.111.
- Ranking vs true-effect (Spearman): AIPW **+1.00**; first-touch +0.50; last-touch **−0.50**;
  time-decay **−0.80**; linear/weighted +0.10.
- **Main result:** heuristic credit diverges sharply from incremental contribution exactly where
  exposure is confounded with conversion; last-touch/time-decay are *anti-correlated* with true
  incrementality, while cross-fitted AIPW recovers the true causal ranking.
- **What C may claim (RQ1):** heuristic attribution answers a descriptive question and can invert
  the causal channel ranking under realistic confounding; causal adjustment corrects it.
- **Must not claim:** that AIPW here is randomized ground truth — it is observational under the
  stated DAG/adjustment set. AIPW estimates are mildly attenuated vs truth (e.g., search 0.048
  vs 0.060) with a binary outcome and a strong latent driver; report ranking, not exact magnitude,
  as the headline.

## P3-E5 — Matched-budget causal decision (300 seeds; budget 20 units)

Source: `p3_e5_canonical_summary.csv`.

| Strategy | Realised value | Regret vs oracle |
|---|---|---|
| oracle (knapsack on truth) | 235.85 | 0.00% |
| causal (knapsack on AIPW-style estimates) | 235.15 | **0.30%** |
| causal, conservative (LCB) | 235.15 | 0.30% |
| rule-based (∝ observed volume) | 190.26 | 19.33% |
| historical (∝ last-touch credit) | 151.95 | **35.57%** |

- **Main result:** under a matched budget, allocating on estimated incremental value achieves
  ~99.7% of the oracle's realised incremental value, whereas attribution-informed allocation
  leaves ~36% on the table and the rule-based baseline ~19%.
- **What C may claim (RQ4/RQ5):** the historical-vs-causal accounting distinction has direct,
  large decision value under realistic confounding.
- **Must not claim:** that 36% transfers to any specific real platform — it is the semi-synthetic
  gap under this DGP; the mechanism (over-funding confounded low-incrementality channels)
  generalises, the magnitude does not.

## P3-E3 — Randomized pipeline validation (schema fixture)

Source: `p3_e3_fixture/summary.json`.

- On a randomized, schema-exact fixture (treatment rate 0.85): visit AIPW **+0.0498**
  (95% CI [0.044, 0.055]) vs known truth 0.050 and randomized diff-in-means 0.0493; conversion
  AIPW **+0.0145** (CI [0.011, 0.018]) vs truth 0.015, diff-in-means 0.0142.
- **What C may claim:** the randomized-validation pipeline is implemented and correct — under
  randomization AIPW equals the randomized difference in means and recovers the known uplift.
- **Must not claim:** any Criteo result. The real Criteo/UCI runs are **blocked by the
  environment network policy** (see `03 Data/ACQUISITION_STATUS.md`); the fixture is synthetic
  and is never manuscript evidence.

## Null / negative findings (do not omit)

- No estimator (AIPW included) is unbiased under nonlinear misspecification with a linear learner.
- g-formula CIs undercover despite low bias.
- Confounding *strength* alone does not bias AIPW; it degrades overlap/precision.
- AIPW is mildly attenuated on the binary-outcome journey DGP (E1).
