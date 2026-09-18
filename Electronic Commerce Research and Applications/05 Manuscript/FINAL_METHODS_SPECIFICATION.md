# P3 Final Methods Specification

Purpose: let the writing agent **C** draft the Methods section without reverse-engineering
Orbit. All notation, estimands, models, and configurations used in the P3 empirical
programme are here. Numbers appear in `RESULTS_INTERPRETATION.md`.

Provenance: Orbit `@ commit 559a262` (branch `claude/adoring-cerf-0rdyvt`, based on
`research/p3-causal-orbit`, PR #17); research workspace `@ commit c022fba`.
Software: Python 3.11.15, numpy 2.4.6, scikit-learn 1.9.1, scipy 1.17.1, pandas 3.0.6;
Node 22 for the Orbit `causal-core` engine and its tests.

## 1. Research design

Mixed-evidence causal-measurement study contrasting **historical attribution credit** with
**incremental causal contribution** in omnichannel digital commerce, then propagating causal
estimates into a constrained budget-allocation decision. Evidence tiers, strongest first for
internal validity:

1. **Semi-synthetic known-truth** (P3-E2, P3-E6): the ground-truth ATE/CATE is known, so
   estimator recovery and assumption-failure regions are measurable.
2. **Observational-under-assumptions** (P3-E1): AIPW on semi-synthetic journeys with an
   explicit DAG and adjustment set; identification assumptions stated, not assumed true.
3. **Randomized validation** (P3-E3): cross-fitted AIPW on a randomized design; pipeline
   validated on a schema-exact fixture (canonical Criteo run pending data access).
4. **Decision experiment** (P3-E5): matched-budget allocation scored on known response curves.

## 2. Estimand

Primary estimand: the **average treatment effect** ATE = E[Y(1) − Y(0)] of a binary marketing
exposure T on outcome Y, and its conditional version CATE(x) = E[Y(1) − Y(0) | X = x].
"Historical attribution credit" is a distinct, descriptive accounting quantity (share of
observed converting journeys assigned to a channel) and is never equated with the ATE.

## 3. Identification

Backdoor adjustment under a researcher-specified DAG. For treatment T, outcome Y and
adjustment set Z, the effect is identified if (i) no Z is a descendant of T (no
post-treatment/mediator/collider conditioning) and (ii) Z blocks every backdoor path
(path with an arrowhead into T) by d-separation. Orbit `causal-core/identification.ts`
implements this via descendant computation + simple-path enumeration with the collider rule
and **refuses to certify identification** (`status = "not-identified" | "invalid-adjustment"`)
otherwise. The parents-of-treatment set is offered as a canonical sufficient adjustment set,
with unobserved parents flagged. Assumptions recorded per analysis: conditional
exchangeability, positivity, consistency/SUTVA, correct DAG (see `CAUSAL_ASSUMPTION_REGISTER.md`).

## 4. Nuisance models and cross-fitting

Nuisances: propensity e(x)=P(T=1|x); outcome regressions μ0(x)=E[Y|T=0,x], μ1(x)=E[Y|T=1,x]
(T-learner). **K-fold cross-fitting** (K=5, `StratifiedKFold` on treatment, seeded): each
fold's nuisances are predicted by models trained on the other folds, so no observation's
nuisance is in-sample. Learners: transparent baselines first — logistic regression
(propensity, binary outcome), linear regression (continuous outcome) — with gradient boosting
as a flexible-learner robustness variant. Propensity clipped to [0.01, 0.99] for positivity
stability; clipped fraction reported. For randomized designs (E3) the propensity is the
empirical randomization rate per training fold, **not** a modelled propensity.

## 5. ATE estimators

For unit i with cross-fitted (e_i, μ0_i, μ1_i):

- **Difference in means** (naive baseline): mean(Y|T=1) − mean(Y|T=0).
- **Outcome regression / g-formula**: mean(μ1_i − μ0_i).
- **IPW (Hájek, stabilised)**: Σ(T Y/e)/Σ(T/e) − Σ((1−T)Y/(1−e))/Σ((1−T)/(1−e)).
- **AIPW (doubly robust)**: mean of the pseudo-outcome
  ψ_i = μ1_i − μ0_i + T_i(Y_i − μ1_i)/e_i − (1−T_i)(Y_i − μ0_i)/(1−e_i).
  Point estimate = mean(ψ); SE = sd(ψ)/√n (efficient-influence-function variance); 95% CI
  = estimate ± 1.96·SE. This estimator is identical in the Orbit `causal-core` product engine
  (`effect.ts`) and the Python research harness (`p3lib/estimators.py`); the harness adds the
  real cross-fitted nuisance estimation.

## 6. Heterogeneous effects / uplift

CATE via cross-fitted **T-learner** (μ1(x) − μ0(x)). Known-truth evaluation: PEHE
= √mean((τ̂ − τ)²), Spearman rank correlation with true CATE. Randomized/observational
evaluation: uplift by predicted-effect decile, Qini coefficient, and doubly-robust policy value.

## 7. Counterfactual causal attribution

Per channel c: treatment = exposed-to-c; outcome = conversion; estimand = ATE of exposure;
adjustment = observed pre-exposure covariates; estimator = cross-fitted AIPW with CI.
Incremental conversions = ATE × (#exposed). Channel effects are **not** forced to sum to
observed revenue. Heuristic baselines (first-touch, last-touch, linear, 7-day time-decay,
position-based weighted) computed on the same converting journeys as the descriptive contrast.

## 8. Budget optimisation and decision policy

Allocation: exact **multiple-choice knapsack** over discretised per-channel spend maximising
summed incremental response (Orbit `atlas-core/causal-budget.ts`, mirrored in
`p3_e5` for evaluation). The optimiser makes no causal claim; causal validity comes from the
supplied incremental-response estimates. A conservative variant substitutes a lower-confidence
response. Decision policy (Orbit `martech-core/uplift-recs.ts`) classifies persuadable /
likely-anyway / low-response / harmful and **abstains** (`insufficient-evidence`) when the
effect is not statistically distinguishable from zero or evidence quality is below a required
floor (randomized > observational > insufficient).

## 9. Semi-synthetic DGP (`p3lib/dgp.py`)

X ~ N(0, I_d), d=5. logit e(X) = intercept + confounding·(β·X) [+ confounding·nonlinear].
T ~ Bernoulli(e). μ0(X) = base + γ·X [+ nonlinear]; τ(X) = ate + hte·X0; μ1 = μ0 + τ.
Y = μ_T + noise·N(0,1) (continuous) or Bernoulli(σ(μ_T)) (binary). Controls: confounding
strength, treatment-prevalence intercept, outcome noise, HTE strength, nonlinearity, hidden
covariates (unmeasured confounding), covariate measurement error, collider selection. True
ATE = ate; true sample ATE = mean(τ_i); τ_i retained for CATE/PEHE.

## 10. Statistics

Repeated seeds (E2: 100; E6: 60; E5: 300). Report mean bias, RMSE, empirical SD, mean SE,
and 95%-CI coverage against the known truth; for decisions, realised value, SD and regret vs
the oracle. Not p-value-driven; uncertainty via influence-function SEs and across-seed spread.

## 11. Reproducibility

All results regenerate from committed configs: `configs/p3_e{1,2,5,6}_canonical.json`; run
`python3 p3_e{1,2,5,6}_*.py`, then `generate_figures_tables.py`. Each result file carries a
provenance block (git SHA, versions, config hash, seed). Orbit engine: `npm test`
(32 tests) and `npm run typecheck`.
