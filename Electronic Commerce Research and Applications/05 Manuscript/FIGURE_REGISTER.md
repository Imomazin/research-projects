# P3 Figure Register

All figures regenerate from committed results via
`04 Experiments/generate_figures_tables.py`. Paths relative to `05 Manuscript/figures/`.
Status: MAIN (recommended for the paper) · SUPPLEMENTARY · CANDIDATE.

| ID | File | Title | Status | Experiment | Source results | Interpretation | Caveat |
|---|---|---|---|---|---|---|---|
| F1 | fig_e1_heuristic_vs_causal.png | Heuristic credit vs incremental causal contribution | MAIN | P3-E1 | p3_e1_canonical_channels.csv | Retargeting: 67% last-touch credit, ~0 causal effect; AIPW tracks truth | Semi-synthetic; observational |
| F2 | fig_e2_ate_bias.png | ATE recovery bias by estimator × condition | MAIN | P3-E2 | p3_e2_canonical_ate_summary.csv | Adjusted estimators unbiased under correct spec; all fail under nonlinearity | Known-truth DGP |
| F3 | fig_e2_ci_coverage.png | 95% CI coverage by estimator × condition | MAIN | P3-E2 | p3_e2_canonical_ate_summary.csv | AIPW ≈ nominal; g-formula undercovers; nonlinear → 0 | — |
| F4 | fig_e6_confounding_overlap.png | AIPW error & overlap vs confounding strength | MAIN | P3-E6 | p3_e6_canonical_summary.csv | Bias flat; RMSE ↑ and min-propensity ↓ (precision cost, not bias) | Single-factor |
| F5 | fig_e6_failure_regions.png | Failure regions: unmeasured confounding, measurement error, selection | MAIN | P3-E6 | p3_e6_canonical_summary.csv | Graded bias; identification failures break AIPW | Single-factor stresses |
| F6 | fig_e5_matched_budget.png | Matched-budget realised value & regret | MAIN | P3-E5 | p3_e5_canonical_summary.csv | Causal 0.3% regret vs 19% (rule) / 36% (historical) | Magnitude DGP-specific |
| F7 | fig_architecture.png | Orbit P3 causal research architecture | MAIN | — | (schematic; reflects implemented pipeline) | Data→spec→ID→nuisance→estimation→diagnostics→attribution→HTE→budget→decision | Schematic |
| F8 | fig_e3_fixture_uplift_deciles_visit.png | Uplift by predicted decile (visit, fixture) | SUPPLEMENTARY | P3-E3 | p3_e3_fixture/uplift_deciles_visit.csv | Pipeline illustration; observed uplift tracks predicted | Synthetic fixture, NOT Criteo |
| F9 | fig_e3_fixture_uplift_deciles_conversion.png | Uplift by predicted decile (conversion, fixture) | SUPPLEMENTARY | P3-E3 | p3_e3_fixture/uplift_deciles_conversion.csv | As F8 | Synthetic fixture, NOT Criteo |

Candidate additions once Criteo/UCI data access is available: randomized Criteo uplift curve
(replace F8/F9 with real data), observational Criteo attribution comparison, UCI external-validity
panel. These are CANDIDATE and cannot be produced under the current network policy.
