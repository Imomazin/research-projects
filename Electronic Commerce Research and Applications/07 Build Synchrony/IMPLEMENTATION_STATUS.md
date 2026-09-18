# P3 Orbit Causal Implementation Status

## Implemented on `research/p3-causal-orbit`

### Causal contracts

- causal DAG node/edge/version contracts
- treatment/outcome observation contract
- effect estimate and overlap diagnostic contracts
- counterfactual prediction contract
- channel incremental-effect attribution contract

### `packages/causal-core`

- DAG validation with cycle, forbidden-edge and temporal-order checks
- doubly robust AIPW average treatment-effect estimator
- deliberately naive observed difference-in-means baseline
- propensity-overlap diagnostics
- model-implied counterfactual prediction helper
- incremental channel-effect attribution summary
- deterministic semi-synthetic causal benchmark generator with known sample ATE

### Decision layer

- exact deterministic causal budget optimiser over discretised channel response options
- uplift-based treatment recommendation policy separating persuadable, likely-anyway, low-response and harmful cases
- expected incremental value check before treatment recommendation
- existing rule-based publish-time optimiser remains untouched as the non-causal product baseline

## Existing inherited Orbit baseline

- first-touch attribution
- last-touch attribution
- linear attribution
- time-decay attribution
- weighted multi-touch attribution
- journey, forecasting and recommendation product surfaces

## Not yet claimed as implemented

- nuisance-model training for propensity and potential outcomes
- channel-sequence causal discovery
- path-specific mediation engine
- CATE/uplift learner itself (the decision policy now exists but consumes externally estimated potential outcomes)
- Criteo data ingestion and validation
- production UI for causal diagnostics
- prospective SkillHubs validation

## Evidence discipline

These are causal computation primitives, not evidence that any historical Orbit campaign has a causal effect. Product-facing causal claims remain blocked until semi-synthetic and randomised-benchmark validation passes and identification assumptions are recorded.

---

## Final-stage update (2026-09-18, Orbit @ 559a262, research @ c022fba)

### Now implemented (previously "not yet claimed")
- **Nuisance-model training + cross-fitting**: real logistic/linear/GBM nuisances with K=5
  StratifiedKFold out-of-fold prediction (`04 Experiments/p3lib/estimators.py`).
- **Estimator suite in `causal-core`**: IPW (Hájek), outcome-regression, difference-in-means as
  full `EffectEstimate`, alongside AIPW; binary-treatment guard; propensity-clip reporting.
- **Backdoor identification engine** (`causal-core/identification.ts`): d-separation, refuses when
  not identified, rejects post-treatment adjustment; parents-of-treatment adjustment helper.
- **Diagnostics**: SMD balance (unadjusted + IPW-weighted), Kish ESS, extreme-weight fraction.
- **CATE/uplift learner**: cross-fitted T-learner + PEHE/rank/decile/Qini/policy-value evaluation.
- **Decision abstention**: evidence-quality and significance gates in `martech-core/uplift-recs.ts`.
- **Semi-synthetic generator**: covariates exposed, known individual effects, prevalence/overlap/
  nonlinearity/unmeasured-confounding/measurement-error/selection controls.
- **Criteo E3 pipeline**: validated end-to-end on a schema-exact randomized fixture.
- **32 unit tests** for the engine (`packages/causal-core/test/`), typecheck clean.

### Still not implemented / intentionally out of scope (do not claim)
- Channel-sequence causal discovery (assessed; adds noise, not used — researcher DAGs preferred).
- Path-specific mediation estimation (kept conceptual; not identified in this data — not estimated).
- General do-calculus (only backdoor identification is implemented).
- DR-learner / causal-forest HTE comparison (single T-learner exercised at scale).

### Blocked by environment network policy (not by method/compute)
- Criteo Uplift (E3 canonical), Criteo Attribution (E4), UCI Online Retail (E7): dataset hosts
  return 403 at the proxy. See `03 Data/ACQUISITION_STATUS.md`. Pipelines are ready; runs pending
  a network that permits those hosts.

### Evidence tier reached
Semi-synthetic known-truth (E2/E6), observational-under-assumptions (E1) and matched-budget
decision (E5) are CANONICAL and reproducible; randomized pipeline is FIXTURE-VALIDATED. See
`PUBLICATION_READINESS_AUDIT.md`.
