# P3 Table Register

All tables regenerate from committed results via `04 Experiments/generate_figures_tables.py`
(CSV + Markdown). Paths relative to `05 Manuscript/tables/`.
Status: MAIN · SUPPLEMENTARY · CANDIDATE.

| ID | File | Title | Status | Experiment | Source results | Statistics | Interpretation | Caveat |
|---|---|---|---|---|---|---|---|---|
| T1 | table_e2_recovery.{csv,md} | Semi-synthetic ATE recovery | MAIN | P3-E2 | p3_e2_canonical_ate_summary.csv | bias, RMSE, empirical SD, mean SE, 95% coverage, n_reps | Recovery under correct spec; failure under nonlinearity | Known-truth |
| T2 | table_e6_sensitivity_aipw.{csv,md} | AIPW sensitivity to assumption stress | MAIN | P3-E6 | p3_e6_canonical_summary.csv | bias, RMSE, coverage, min propensity per factor level | Identification governs reliability | Single-factor |
| T3 | table_e1_channels.{csv,md} | Per-channel heuristic credit vs AIPW effect | MAIN | P3-E1 | p3_e1_canonical_channels.csv | true effect, AIPW ± CI, naive DIM, 5 heuristic shares | Divergence localised to confounded channels | Semi-synthetic |
| T4 | table_e1_ranking.{csv,md} | Channel-ranking correlation with true effect | MAIN | P3-E1 | p3_e1_canonical_ranking.csv | Spearman vs true & vs AIPW | AIPW +1.0; last-touch −0.5; time-decay −0.8 | — |
| T5 | table_e5_allocation.{csv,md} | Matched-budget realised value & regret | MAIN | P3-E5 | p3_e5_canonical_summary.csv | mean/SD realised value, regret vs oracle | Causal ≈ oracle; historical worst | Magnitude DGP-specific |

Recommended additional MAIN tables for C to assemble from existing material (no new computation):
- **Dataset characteristics** — from `FINAL_METHODS_SPECIFICATION.md §9` + `03 Data/DATASET_MANIFEST.md`
  + `ACQUISITION_STATUS.md`.
- **Estimands & assumptions** — from `CAUSAL_ASSUMPTION_REGISTER.md`.

CANDIDATE (pending data access): Criteo randomized ATE table, observational Criteo attribution
table, UCI external-validity table.
