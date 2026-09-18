# C Publication Handoff — P3 (Orbit)

Definitive engineering/research → manuscript handover. C should be able to write the paper from
this document plus the evidence pack, without reverse-engineering Orbit. All numbers trace to
committed result files. **C must not merge PR #17, modify production, or make the claims in §P.**

Provenance: Orbit `@ 559a262` (branch `claude/adoring-cerf-0rdyvt`, based on `research/p3-causal-orbit`,
PR #17); research workspace `@ c022fba`. Software: Python 3.11.15 / numpy 2.4.6 / scikit-learn
1.9.1 / scipy 1.17.1 / pandas 3.0.6; Node 22.

## A. Paper identity
- **Recommended title:** *Causal Attribution in Omnichannel Digital Commerce: A Customer Journey
  Graph Approach to Budget Optimisation.*
- **Alternative:** *From Attribution Credit to Incremental Value: Identification, Validation and
  Decision Consequences in Omnichannel Commerce.*
- **Target journal:** Electronic Commerce Research and Applications (per repository strategy).
- **Author order:** per repository governance/authorisation records; not set or changed here.
- **Purpose:** show, end-to-end and reproducibly, when/why heuristic attribution diverges from
  incremental causal contribution, validate the causal estimators against known and randomized
  truth, map the failure regions, and quantify the decision value of causal allocation.

## B. Final contribution
- **Exact contribution:** an integrated, software-synchronised evidence chain that (1) quantifies
  the attribution-vs-incrementality divergence and its *decision* consequences under matched
  budgets, (2) validates the estimator suite against known-truth and randomized designs, and
  (3) maps the identification-assumption failure regions — all reproducible from a running system
  (Orbit) with the estimator shared between product and research code.
- **Closest competing literature:** Berman 2018 (beyond last-touch); Li et al. 2016 (attribution→
  bidding); Gordon et al. 2019/2023 (observational vs experimental ad measurement); Graphical
  Point-Process MTA 2024; Waisman et al. 2025. See `02 Literature/STATE_OF_ART_2026.md`.
- **What is new (residual novelty):** the *joint* delivery — heuristic↔causal contrast + explicit
  DAG identification + semi-synthetic truth recovery + randomized-validation pipeline + assumption/
  failure mapping + matched-budget decision-value quantification + evidence-gated abstention — in
  one reproducible software-paper system. Not the individual pieces.
- **What is NOT new:** "beyond last touch"; multi-touch/journey-graph attribution; AIPW/DML/uplift
  as methods; attribution→budget linkage; that observational ≠ experimental.
- **What Orbit had before P3:** heuristic attribution (first/last/linear/time-decay/weighted),
  forecasting/recommendation surfaces, a rule-based optimiser. These are preserved as non-causal
  baselines and not relabelled causal.

## C. Research gap
Prior work establishes each component in isolation but does not deliver a reproducible, software-
embedded pipeline that (a) keeps historical credit and incremental contribution as distinct
objects end-to-end, (b) validates the estimators against both known and randomized truth, (c)
characterises where causal reliability breaks, and (d) ties the distinction to a matched-budget
decision with measured regret and an abstention rule.

## D. Research questions (final)
- **RQ1:** When/why does heuristic attribution diverge from incremental causal contribution, and
  does it invert channel ranking? (P3-E1)
- **RQ2:** Do cross-fitted causal estimators recover known/semi-synthetic and randomized effects?
  (P3-E2, P3-E3)
- **RQ3:** How do overlap, confounding, measurement and model assumptions affect reliability?
  (P3-E6)
- **RQ4:** How does causal-incremental-value allocation differ from attribution-informed allocation
  under matched budget? (P3-E5)
- **RQ5:** What decision value and failure conditions emerge, and when should the system abstain?
  (P3-E5, P3-E6, abstention policy)

## E. Conceptual frame (constructs for C; do not over-theorise)
attribution credit (descriptive) vs incremental contribution (interventional counterfactual);
customer journey; intervention/treatment; potential outcome; identification (exchangeability,
positivity, consistency); decision value under budget constraint; evidence quality / abstention.
Keep the frame in service of the RQs; no unrelated grand theory.

## F. Methods
See `FINAL_METHODS_SPECIFICATION.md` (design, estimand, backdoor identification, cross-fitted
nuisances, DIM/g-formula/IPW/AIPW with the influence-function SE, T-learner CATE, counterfactual
attribution, multiple-choice-knapsack allocation, abstention, the semi-synthetic DGP, statistics,
reproducibility). Assumptions per analysis: `CAUSAL_ASSUMPTION_REGISTER.md`.

## G. Experiments (canonical configs in `04 Experiments/configs/`)
- **P3-E1** heuristic vs causal, n=60,000, seed 20260918 — `p3_e1_heuristic_vs_causal.py`.
- **P3-E2** recovery, 100 seeds × 5 conditions, n=4000 — `p3_e2_semisynthetic_recovery.py`.
- **P3-E3** randomized validation, cross-fitted AIPW; **fixture-validated** (Criteo run pending
  data access) — `p3_e3_criteo_randomized_validation.py`, `make_criteo_fixture.py`.
- **P3-E5** matched-budget decision, 300 seeds, budget 20 — `p3_e5_matched_budget_decision.py`.
- **P3-E6** sensitivity/failure, 60 seeds — `p3_e6_assumption_sensitivity.py`.
- **P3-E4 / P3-E7** (observational-real / external): pipeline & methodology ready; canonical runs
  blocked by network policy (`03 Data/ACQUISITION_STATUS.md`). E1 demonstrates the E4 methodology
  on semi-synthetic observational journeys.

## H. Results (exact; from `04 Experiments/results/`)
- **E1:** retargeting true 0.010 / AIPW 0.005 / naive 0.122 / last-touch credit 0.674; display true
  0.000 / AIPW 0.001 / last-touch 0.111. Ranking Spearman vs truth: AIPW +1.00, first-touch +0.50,
  last-touch −0.50, time-decay −0.80, linear/weighted +0.10.
- **E2 (linear):** AIPW bias 0.003–0.006, coverage 0.92–0.98; DIM bias 0.58 (low) → 1.47 (high).
  g-formula near-unbiased but coverage 0.42–0.46. **Nonlinear:** AIPW bias +1.87 (linear learner)
  → +0.35 (GBM), coverage 0.
- **E3 (fixture):** visit AIPW 0.0498 (CI [0.044,0.055]) vs truth 0.050, randomized DIM 0.0493;
  conversion AIPW 0.0145 (CI [0.011,0.018]) vs truth 0.015.
- **E5:** regret vs oracle — causal 0.30%, causal-LCB 0.30%, rule-based 19.33%, historical 35.57%
  (realised values 235.15 / 190.26 / 151.95; oracle 235.85).
- **E6:** AIPW unbiased across confounding/noise/prevalence/HTE/n (precision only); biased under
  unmeasured confounding (+0.55 hiding x0), measurement error (+0.84), selection (−0.19); placebo −0.002.

## I. Figures
`FIGURE_REGISTER.md` (F1–F9 in `05 Manuscript/figures/`), all regenerable. MAIN: F1 (E1), F2/F3
(E2), F4/F5 (E6), F6 (E5), F7 (architecture). SUPP: F8/F9 (E3 fixture uplift deciles).

## J. Tables
`TABLE_REGISTER.md` (T1–T5 in `05 Manuscript/tables/`, CSV+MD). All MAIN.

## K. Null / negative findings (report, do not omit)
No estimator is unbiased under nonlinear misspecification with a linear learner; g-formula CIs
undercover; confounding strength alone does not bias AIPW (degrades overlap/precision);
AIPW mildly attenuated on the binary-outcome journey DGP (E1).

## L. Failure conditions
Unmeasured confounding, covariate measurement error, collider selection, and nuisance
misspecification with inflexible learners each degrade or break estimation (E6, E2). Overlap
collapses (min propensity → 0.01) under strong confounding even when bias stays low.

## M. Limitations
Semi-synthetic ground truth (external magnitudes not transportable); observational E1/E4
identification is assumption-dependent, not randomized; randomized (E3), observational-real (E4)
and external (E7) canonical runs are **not executed** (network policy); Criteo public release is
privacy-subsampled (magnitude ≠ platform incrementality); single-factor sensitivity; T-learner is
the only HTE learner exercised at scale.

## N. Implications
Research: attribution accuracy ≠ decision quality; validate against known/randomized truth and
report failure regions. Marketing analytics / digital commerce: causal allocation can recover
~all achievable incremental value where attribution-informed allocation loses a large share (36%
here). Managerial: prefer incrementality-based budgeting; adopt abstention when evidence is
inadequate. MarTech systems: keep credit and incrementality as distinct, labelled objects with
evidence gates.

## O. Reproducibility
Repo `Imomazin/research-projects` (branch `claude/adoring-cerf-0rdyvt`, `@ c022fba`) and
`Imomazin/ai-martech-growth-intelligence` (same branch, `@ 559a262`). Run experiment scripts with
their canonical configs, then `generate_figures_tables.py`. Orbit engine: `npm test` (32),
`npm run typecheck`. Provenance blocks in every result JSON.

## P. Claims C MUST NOT make
1. That any observational estimate (E1/E4) is randomized ground truth.
2. That Criteo/UCI real-data results exist — none were run (network-blocked); the fixture is synthetic.
3. That the semi-synthetic 36% decision gap is a specific real platform's loss.
4. That AIPW is robust regardless of specification (it fails in the nonlinear/inflexible region).
5. That structural DAG validity or covariate balance proves no unmeasured confounding.
6. That causal effects sum to observed revenue, or that heuristic attribution is "wrong" rather
   than answering a different (descriptive) question.
7. That Orbit implements general do-calculus (only backdoor identification), causal discovery, or
   path-specific mediation (not implemented; do not claim).

## Q. Open items
- **Blocking manuscript?** No, for the semi-synthetic + fixture-validated core (RQ1–RQ5 supported).
- **Not blocking, would strengthen:** execute E3 (Criteo uplift), E4 (Criteo attribution), E7 (UCI)
  once data access is available; these upgrade F8/F9 and add real-data tables. C should write the
  empirical core now and mark real-data validation as available-on-access, or wait if the journal
  requires the randomized real-data result in-paper (governance decision — see readiness audit).
