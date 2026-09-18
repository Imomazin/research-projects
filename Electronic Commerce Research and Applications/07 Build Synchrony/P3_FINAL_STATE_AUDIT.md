# P3 / Orbit — Final-Stage State Audit

**Audit date:** 2026-09-18
**Auditor session:** P3 final causal engineering, experimentation and publication-evidence completion.

## Provenance at audit time

| Repository | Branch inspected | Commit SHA |
|---|---|---|
| Imomazin/ai-martech-growth-intelligence (Orbit) | `research/p3-causal-orbit` (PR #17 head) | `e4bfc1dee1f1bd073c1b6439e274b40f22859b23` |
| Imomazin/research-projects (ECRA workspace) | `main` | `9f9ae5b6090944df58ed1b5041927dfa3b1cf1b9` |

Working branch for this stage (both repos): `claude/adoring-cerf-0rdyvt`, based on the P3 work above.
PR #17 is **not** merged and the production/default branch is **not** modified.

## Method

Read recursively: ECRA `01`–`07`, Orbit `packages/causal-core`, `packages/schemas/src/causal.ts`,
`packages/atlas-core/src/causal-budget.ts`, `packages/martech-core/src/uplift-recs.ts`,
`apps/web/app/causal/page.tsx`, existing heuristic attribution, experiment registry, dataset manifest.
Mathematically checked the AIPW score and its variance; checked DAG validation logic.

## Capability classification

Legend: NOT STARTED · PARTIAL · IMPLEMENTED (code exists, unproven) · BUILD VALIDATED ·
DEV TESTED (unit/smoke) · CANONICAL EXPERIMENTED · MANUSCRIPT EVIDENCE READY.

| Capability | State at audit | Evidence / gap |
|---|---|---|
| Causal data contracts (schemas) | IMPLEMENTED | `schemas/src/causal.ts`: nodes/edges/graph, observation, effect, overlap, counterfactual, channel effect. |
| DAG structural validation | IMPLEMENTED | `graph.ts`: duplicate/unknown/self/forbidden/temporal/cycle. Correct. No role/adjacency-set/identification logic. |
| AIPW ATE estimator | IMPLEMENTED (math verified) | `effect.ts` score `mu1-mu0 + T(Y-mu1)/e - (1-T)(Y-mu0)/(1-e)`; SE = influence-function sample variance. Correct **but consumes oracle nuisances**; no estimation, no cross-fitting, no treatment-encoding guard. |
| Difference-in-means baseline | IMPLEMENTED | `effect.ts`. |
| Overlap diagnostics | PARTIAL | `diagnostics.ts`: min/max propensity, outside-region, clipped count. No SMD balance, no ESS, no extreme-weight fraction. |
| Counterfactual helper | IMPLEMENTED | `counterfactual.ts`, labelled model-implied. |
| Incremental causal attribution | IMPLEMENTED | `attribution.ts`, does not force sum-to-revenue. |
| Semi-synthetic generator | PARTIAL | `synthetic.ts`: 1 covariate, known sample ATE, but **covariate X not exposed** (cannot fit nuisances); no overlap/prevalence/selection controls. |
| Causal budget allocator | IMPLEMENTED | `atlas-core/causal-budget.ts`: exact multiple-choice knapsack DP. No min/max/uncertainty constraints. |
| Uplift recommendation policy | PARTIAL | `martech-core/uplift-recs.ts`: 4 segments + expected value. **No abstention / insufficient-evidence / uncertainty** handling. |
| Nuisance-model training + cross-fitting | NOT STARTED | Acknowledged in `IMPLEMENTATION_STATUS.md`. |
| Identification engine (backdoor / adjustment validity) | NOT STARTED | Section 12 major gap. |
| HTE / CATE learner + uplift evaluation | NOT STARTED | Policy consumes external estimates only. |
| Heuristic vs causal comparison layer | NOT STARTED | Heuristic baselines exist in `attribution-core`; no comparison harness. |
| P3-E1 heuristic baseline run | NOT STARTED | |
| P3-E2 semi-synthetic canonical run | NOT STARTED | Generator partial; no estimation harness, no results. |
| P3-E3 Criteo randomized validation | PARTIAL | Script `p3_e3_criteo_randomized_validation.py` present; dataset not acquired; no cross-fitting yet. |
| P3-E4 observational causal attribution | NOT STARTED | |
| P3-E5 matched-budget decision experiment | NOT STARTED | Allocator exists; no experiment. |
| P3-E6 assumption / sensitivity stress | NOT STARTED | |
| P3-E7 external validity (UCI) | PARTIAL | `acquire_uci_online_retail.py` present; no analysis. |
| Machine-readable canonical results area | NOT STARTED | |
| Figures / tables from results | NOT STARTED | |
| Claim–evidence matrix, methods spec, assumption register, handoff, evidence pack | NOT STARTED | |

## Mathematical audit result (AIPW)

The implemented estimand is the ATE. The per-unit pseudo-outcome equals the canonical
doubly-robust / efficient-influence-function form; the point estimate is its (weighted) mean and
the SE is `sqrt(sample_var(pseudo-outcome)/n)`. **Correct.** Two scientific caveats:
(1) it uses supplied `propensity`, `mu0`, `mu1` — so all identification and cross-fitting burden is
upstream and currently unbuilt in code; (2) no guard forces `treatment ∈ {0,1}`.

## Consequence for this stage (execution plan)

1. Strengthen + unit-test `causal-core`: treatment guard, IPW & outcome-regression estimators,
   balance/ESS diagnostics, backdoor identification module, covariate-exposing DGP, uplift abstention.
2. Build a Python research estimation harness with **real cross-fitted nuisance models** (the piece
   TypeScript product code intentionally does not do), used for canonical experiments.
3. Execute the self-contained known-truth programme (no external data needed): **P3-E2** (recovery),
   **P3-E6** (sensitivity/failure), **P3-E1** (heuristic vs causal), **P3-E5** (matched-budget decision).
4. Provide E3 (randomized Criteo) / E4 (observational) / E7 (external) as validated, schema-tested
   pipelines; execute where dataset acquisition is feasible in-session, otherwise mark data-blocked.
5. Produce machine-readable results, figures, tables, and the full C evidence pack + readiness audit.

This audit is updated at stage end by `P3_FINAL_STATE_AUDIT.md` revisions and the
`PUBLICATION_READINESS_AUDIT.md`.
