# P3 Causal Orbit Build Specification

## Purpose

This document governs the causal upgrade of the AI MarTech Growth Intelligence build before substantive drafting of Paper 3. The build is the empirical and engineering foundation for the manuscript, not a post-paper demonstration.

## Publication target

Primary target after implementation and validation: **Electronic Commerce Research and Applications**.

The original grant named JTAER. The venue change is a publication-strategy decision while preserving the funded scientific scope and deliverables.

## Funded scientific scope

Paper 3 is defined around causal attribution in omnichannel digital commerce using customer-journey DAGs, causal discovery, intervention-effect estimation and counterfactual campaign evaluation. The funded commercial platform is expected to add a causal budget allocator, autonomous campaign optimiser, revenue pathway graph engine, trust-weighted attribution and uplift-based recommendations.

## Current Orbit baseline

The present attribution engine is non-causal and provides these benchmark models:

- first touch
- last touch
- linear
- time decay
- weighted multi-touch

The current optimiser is deterministic and rule based. These capabilities remain available because they provide the baselines for the causal upgrade and later P3 comparisons.

## Causal build principle

No component is to be labelled causal unless it has:

1. an explicit treatment and outcome definition
2. a stated causal graph or identification model
3. an adjustment strategy for confounding
4. an estimand
5. an estimator
6. uncertainty or sensitivity reporting where feasible
7. tests against known or semi-synthetic ground truth before product claims are exposed

## Required causal architecture

### 1. Causal Journey Graph

Represent customer journeys as graph-compatible causal records containing touchpoints, channel exposure, timing, customer state, campaign state, conversion and value outcomes.

Required capabilities:

- DAG schema and validation
- allowed and forbidden edges
- temporal ordering constraints
- confounder registry
- mediator and collider annotations
- graph versioning

### 2. Causal Effect Engine

Estimate incremental effects of marketing interventions rather than redistributing observed revenue by heuristic weights.

Initial estimands should include:

- average treatment effect where meaningful
- conditional average treatment effect for segmentation
- incremental conversion probability
- incremental revenue effect

Estimator selection must be finalised from the data-generating assumptions and validation protocol. Candidate families may include regression adjustment, inverse-probability weighting, doubly robust estimation and heterogeneous-treatment-effect models.

### 3. Counterfactual Campaign Engine

For an observed or candidate journey, estimate outcomes under alternative interventions such as channel exposure versus no exposure, alternative channel sequencing, campaign on versus off and spend/intensity bands where identification permits.

Counterfactual outputs must distinguish model estimates from observed facts.

### 4. Causal Attribution Layer

Add causal attribution as a new model family alongside the existing first-touch, last-touch, linear, time-decay and weighted baselines. The causal layer should attribute incremental contribution and must not simply transform the existing heuristic shares.

### 5. Revenue Pathway Graph

Expose causally supported pathways from interventions through intermediate journey states to conversion and revenue outcomes. Distinguish direct, mediated and total effects where the assumptions support that distinction.

### 6. Budget Intervention Optimiser

Replace purely correlational spend allocation with optimisation driven by estimated incremental effects under budget and operational constraints. The first production research version should be deterministic and auditable given a frozen causal-effect table. Bayesian optimisation or reinforcement learning should only be added where the environment and reward specification can be validated without overstating causal certainty.

### 7. Uplift Recommender

Recommend interventions to customers, audiences or segments based on estimated incremental response rather than raw conversion propensity.

The recommender must explicitly separate likely-to-convert customers, persuadable customers, low-response customers and customers for whom treatment may be neutral or harmful.

### 8. Trust and Bias Diagnostics

Provide diagnostics for selection bias, overlap/positivity, covariate imbalance, sensitivity to unobserved confounding where feasible, estimator instability and ad-fraud or unreliable-source flags where supported by available data.

## Proposed implementation boundary

- `packages/causal-core/`: graph schema, estimands, effect estimation, counterfactual evaluation, diagnostics and sensitivity
- `packages/attribution-core/`: preserve heuristic models, add causal attribution adapter and benchmark comparison
- `packages/analytics-core/`: outcome modelling and validation helpers where shared
- `packages/martech-core/`: uplift policy and budget decision orchestration
- `packages/atlas-core/`: retain current optimiser as baseline and add causal-budget optimisation only after validation
- `packages/schemas/`: treatment, outcome, DAG, effect-estimate, intervention and uncertainty contracts
- `apps/web/`: causal journey view, intervention simulator, causal attribution comparison, budget allocation and diagnostics

## Build-to-paper evidence contract

Before the P3 manuscript is materially drafted, Orbit must be able to produce versioned evidence for existing heuristic attribution results, causal graph specification, treatment/outcome definitions, causal-effect estimates, counterfactual predictions, uplift estimates, budget allocation recommendations, uncertainty/diagnostic outputs, benchmark comparisons and the configuration/code version used to generate every result.

## Validation stages

### Stage A: Semi-synthetic validation

Use data where the causal data-generating process and true treatment effects are known or controlled. This establishes whether the causal engine can recover ground truth under increasing confounding and noise.

### Stage B: Randomised/public causal validation

Use the Criteo uplift benchmark to validate treatment-effect and uplift components under randomised treatment assignment.

### Stage C: Observational attribution validation

Apply the frozen estimators to the Criteo attribution data after confirming that the required treatment, outcome and confounder variables can be constructed defensibly.

### Stage D: Operational validation

Where anonymised SkillHubs campaign data meet the required identification assumptions, compare causal recommendations with historical outcomes or prospective controlled interventions.

## P3 manuscript start gate

The manuscript shell, literature review and theory can be prepared in parallel, but empirical claims should not be written until:

1. causal-core is implemented and tested
2. current attribution models remain reproducible as baselines
3. at least one semi-synthetic validation suite is complete
4. the randomised uplift validation is complete
5. at least one real attribution dataset is processed through the same pipeline
6. causal estimates include diagnostics and uncertainty
7. result artefacts are versioned and reproducible
