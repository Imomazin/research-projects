# P3 Claim–Evidence Matrix

Every claim C may make, mapped to research question → identification assumption → method →
code → experiment → result artefact → statistics → figure/table → limitation → manuscript
section. Claims are stated at the strength the evidence supports and no higher.

Paths are relative to `Electronic Commerce Research and Applications/`. Orbit code paths are in
`Imomazin/ai-martech-growth-intelligence` (branch `claude/adoring-cerf-0rdyvt`).

---

### CLAIM 1 — Heuristic attribution can invert the causal channel ranking under confounding.
- **RQ:** RQ1. **Assumption:** observational exchangeability given observed covariates (E1/§B).
- **Method:** heuristic attribution vs cross-fitted AIPW per channel (Methods §7).
- **Code:** `04 Experiments/p3_e1_heuristic_vs_causal.py`, `p3lib/heuristic.py`, `p3lib/estimators.py`.
- **Experiment:** P3-E1 (n=60,000). **Artefact:** `results/p3_e1_canonical_channels.csv`, `_ranking.csv`.
- **Statistics:** Spearman ranking vs true effect — AIPW +1.00, last-touch −0.50, time-decay −0.80.
- **Figure/Table:** Fig `fig_e1_heuristic_vs_causal.png`; Tables `table_e1_channels`, `table_e1_ranking`.
- **Limitation:** semi-synthetic; AIPW mildly attenuated; observational (not randomized).
- **Section:** Results §Attribution-vs-causal.

### CLAIM 2 — Cross-fitted AIPW recovers a known ATE with correct CIs under stated assumptions.
- **RQ:** RQ2. **Assumption:** all confounders observed; positivity (E2/§A).
- **Method:** cross-fitted nuisances + AIPW; recovery vs known truth (Methods §4–5,§10).
- **Code:** `p3_e2_semisynthetic_recovery.py`, `p3lib/estimators.py`; Orbit `packages/causal-core/src/effect.ts`.
- **Experiment:** P3-E2. **Artefact:** `results/p3_e2_canonical_ate_summary.csv`.
- **Statistics:** AIPW bias ≤0.006, coverage 0.92–0.98 across linear conditions; DIM biased ≥0.58.
- **Figure/Table:** `fig_e2_ate_bias.png`, `fig_e2_ci_coverage.png`; `table_e2_recovery`.
- **Limitation:** holds only under correct specification (see Claim 3). **Section:** Results §Recovery.

### CLAIM 3 — Estimation fails under nonlinear misspecification with inflexible learners (failure region).
- **RQ:** RQ2/RQ3. **Assumption:** correct nuisance functional form (violated).
- **Method:** same, linear vs GBM learner under a nonlinear confounder.
- **Code/Experiment:** P3-E2 conditions `nonlinear_linear_learner`, `nonlinear_gbm_learner`.
- **Artefact:** `p3_e2_canonical_ate_summary.csv`. **Statistics:** AIPW bias +1.87 (linear) → +0.35 (GBM), coverage 0.
- **Figure/Table:** `fig_e2_ate_bias.png`. **Limitation:** residual GBM bias unresolved at n=4000.
- **Section:** Results §Failure regions.

### CLAIM 4 — Causal reliability is governed by identification, not confounding magnitude.
- **RQ:** RQ3. **Assumption:** varies by stress (E6/§A).
- **Method:** one-factor sensitivity + placebo (Methods §9–10).
- **Code:** `p3_e6_assumption_sensitivity.py`. **Experiment:** P3-E6. **Artefact:** `p3_e6_canonical_summary.csv`.
- **Statistics:** AIPW unbiased across confounding/noise/prevalence/HTE/n; biased under unmeasured
  confounding (+0.55), measurement error (+0.84), selection (−0.19); placebo ≈0.
- **Figure/Table:** `fig_e6_confounding_overlap.png`, `fig_e6_failure_regions.png`; `table_e6_sensitivity_aipw`.
- **Limitation:** stresses applied singly. **Section:** Results §Sensitivity.

### CLAIM 5 — Allocating on incremental causal value markedly outperforms attribution-informed allocation under matched budget.
- **RQ:** RQ4/RQ5. **Assumption:** known response curves; matched budget (E5/§A).
- **Method:** multiple-choice knapsack; realised value vs oracle (Methods §8).
- **Code:** `p3_e5_matched_budget_decision.py`; Orbit `packages/atlas-core/src/causal-budget.ts`.
- **Experiment:** P3-E5 (300 seeds). **Artefact:** `results/p3_e5_canonical_summary.csv`.
- **Statistics:** regret vs oracle — causal 0.30%, rule-based 19.3%, historical 35.6%.
- **Figure/Table:** `fig_e5_matched_budget.png`; `table_e5_allocation`.
- **Limitation:** magnitude is DGP-specific; mechanism generalises. **Section:** Results §Decision value.

### CLAIM 6 — The randomized-validation and decision-abstention machinery is implemented and correct.
- **RQ:** RQ2 (validation) / RQ5 (governance). **Assumption:** randomization (E3/§C).
- **Method:** cross-fitted AIPW with randomization-rate propensity; evidence-gated abstention.
- **Code:** `p3_e3_criteo_randomized_validation.py`; Orbit `martech-core/src/uplift-recs.ts` (abstain).
- **Experiment:** P3-E3 (fixture). **Artefact:** `results/p3_e3_fixture/summary.json`.
- **Statistics:** fixture visit AIPW 0.0498 (CI [0.044,0.055]) = randomized DIM 0.0493 = truth 0.05.
- **Figure/Table:** `fig_e3_fixture_uplift_deciles_*.png`. **Limitation:** fixture only; Criteo run blocked.
- **Section:** Methods §Randomized validation; Limitations.

### CLAIM 7 — Structural DAG identification is enforced in software (backdoor; refuses when not identified).
- **RQ:** RQ3 (transparency). **Assumption:** correct DAG (structural, not causal truth).
- **Method:** backdoor d-separation; post-treatment adjustment rejected (Methods §3).
- **Code:** `packages/causal-core/src/identification.ts`; tests `test/identification.test.ts`.
- **Experiment:** unit tests (5 identification tests). **Artefact:** `npm test` (32 pass).
- **Limitation:** structural validity ≠ causal truth (documented). **Section:** Methods §Identification.

---

**Claims C must NOT make** are listed in `C_PUBLICATION_HANDOFF.md` §P and enforced by the
assumption register.
