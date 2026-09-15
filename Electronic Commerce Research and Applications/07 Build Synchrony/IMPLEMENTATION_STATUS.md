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

### Budget decision layer

- exact deterministic causal budget optimiser over discretised channel response options
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
- uplift/CATE learner
- Criteo data ingestion and validation
- production UI for causal diagnostics
- prospective SkillHubs validation

## Evidence discipline

These are causal computation primitives, not evidence that any historical Orbit campaign has a causal effect. Product-facing causal claims remain blocked until semi-synthetic and randomised-benchmark validation passes and identification assumptions are recorded.
