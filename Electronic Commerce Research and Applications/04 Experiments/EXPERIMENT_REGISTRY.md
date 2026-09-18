# P3 Experiment Registry (final state)

Provenance: research `@ c022fba` (branch `claude/adoring-cerf-0rdyvt`); Orbit `@ 559a262`.
Software: Python 3.11.15 / numpy 2.4.6 / scikit-learn 1.9.1 / scipy 1.17.1 / pandas 3.0.6.
Validation vocabulary: CANONICAL (frozen config run) · FIXTURE-VALIDATED · BLOCKED (data access).

## Summary

| ID | Dataset | Main comparison | Primary metric | Status |
|---|---|---|---|---|
| P3-E1 | semi-synthetic journeys | first/last/linear/time-decay/weighted vs AIPW | channel ranking (Spearman), credit vs effect | CANONICAL |
| P3-E2 | semi-synthetic | DIM/g-formula/IPW/AIPW vs known truth | ATE bias, RMSE, 95% coverage; PEHE | CANONICAL |
| P3-E3 | Criteo Uplift v2.1 (randomized) | randomized DIM vs cross-fitted AIPW + uplift deciles | ATE, CI, uplift by decile | FIXTURE-VALIDATED; canonical BLOCKED (network policy) |
| P3-E4 | Criteo Attribution (observational) | heuristic vs identified AIPW | effect stability, sensitivity | Methodology in E1; real-data BLOCKED |
| P3-E5 | known response curves | historical vs rule-based vs causal allocation | realised value, regret vs oracle | CANONICAL |
| P3-E6 | simulated stresses | AIPW under assumption violations | bias, coverage, overlap | CANONICAL |
| P3-E7 | UCI Online Retail | external-validity checks | operational-architecture stability | BLOCKED (network policy) |

## Detail

### P3-E1 — Heuristic attribution vs incremental causal contribution
- **RQ:** RQ1. **Estimand:** per-channel ATE of exposure on conversion. **Design:** observational
  (semi-synthetic journeys with confounded retargeting, zero-effect display).
- **Method:** 5 heuristic models + cross-fitted AIPW (logistic, K=5). **Baselines:** heuristics; naive DIM.
- **Config:** `configs/p3_e1_canonical.json` (n=60,000, seed 20260918). **Code:** `p3_e1_heuristic_vs_causal.py`, `p3lib/heuristic.py`.
- **Metrics/Results:** AIPW ranking ρ=+1.00 vs truth; last-touch −0.50; time-decay −0.80; retargeting
  last-touch 0.674 vs true 0.010. **Artefacts:** `results/p3_e1_canonical_channels.csv`, `_ranking.csv`.
- **Figures/Tables:** F1; T3, T4. **Validation:** CANONICAL (observational under stated assumptions).

### P3-E2 — Semi-synthetic truth recovery
- **RQ:** RQ2/RQ3. **Estimand:** ATE/CATE (known). **Design:** semi-synthetic, 5 conditions.
- **Method:** cross-fitted DIM/g-formula/IPW/AIPW + T-learner. **Config:** `configs/p3_e2_canonical.json`
  (n=4000, 100 seeds; GBM condition 40 seeds). **Code:** `p3_e2_semisynthetic_recovery.py`.
- **Metrics/Results:** AIPW bias 0.003–0.006, coverage 0.92–0.98 (linear); nonlinear+linear AIPW +1.87;
  nonlinear+GBM +0.35. **Artefacts:** `results/p3_e2_canonical_ate_summary.csv`, `_hte_summary.csv`, `_runs.*`.
- **Figures/Tables:** F2, F3; T1. **Validation:** CANONICAL.

### P3-E3 — Randomized Criteo uplift validation
- **RQ:** RQ2. **Estimand:** ATE within released benchmark distribution. **Design:** randomized.
- **Method:** cross-fitted AIPW, propensity = empirical randomization rate; uplift deciles.
- **Config:** default (folds 5, seed 2026). **Code:** `p3_e3_criteo_randomized_validation.py`; fixture `make_criteo_fixture.py`.
- **Results (fixture):** visit AIPW 0.0498 (CI [0.044,0.055]) vs truth 0.050; conversion 0.0145 vs 0.015.
- **Artefacts:** `results/p3_e3_fixture/summary.json`, `uplift_deciles_*.csv`. **Figures:** F8, F9 (SUPP).
- **Validation:** FIXTURE-VALIDATED. **Canonical BLOCKED:** `criteostorage.blob.core.windows.net` 403 at proxy.

### P3-E4 — Observational causal attribution (Criteo Attribution)
- **RQ:** RQ1/RQ3. **Estimand:** observational ATE under DAG/adjustment. **Status:** methodology executed
  in E1 on semi-synthetic observational journeys; real-data run BLOCKED (network policy).

### P3-E5 — Matched-budget causal decision
- **RQ:** RQ4/RQ5. **Estimand:** realised incremental value under matched budget. **Design:** known response curves.
- **Method:** multiple-choice knapsack; strategies oracle/causal/causal-LCB/rule-based/historical.
- **Config:** `configs/p3_e5_canonical.json` (budget 20, 300 seeds, est. noise 0.15). **Code:** `p3_e5_matched_budget_decision.py`.
- **Results:** regret vs oracle — causal 0.30%, rule-based 19.33%, historical 35.57%. **Artefacts:** `results/p3_e5_canonical_summary.csv`, `_runs.*`.
- **Figures/Tables:** F6; T5. **Validation:** CANONICAL.

### P3-E6 — Assumption/sensitivity & failure regions
- **RQ:** RQ3. **Method:** one-factor sweeps + placebo (60 seeds). **Config:** `configs/p3_e6_canonical.json`. **Code:** `p3_e6_assumption_sensitivity.py`.
- **Results:** robust to confounding/noise/prevalence/HTE/n; biased under unmeasured confounding (+0.55),
  measurement error (+0.84), selection (−0.19); placebo −0.002. **Artefacts:** `results/p3_e6_canonical_summary.csv`, `_runs.*`.
- **Figures/Tables:** F4, F5; T2. **Validation:** CANONICAL.

### P3-E7 — External validity (UCI Online Retail)
- **RQ:** external validity. **Status:** BLOCKED — `archive.ics.uci.edu` 403 at proxy; acquisition script `03 Data/acquire_uci_online_retail.py` ready. No standalone causal claim (no randomized exposure).

---
Development smoke runs (`--smoke`, `--max-seeds`) are not manuscript evidence. Canonical rows above
were produced from the frozen configs and are the paper's evidence base.
