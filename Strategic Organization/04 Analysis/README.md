# Analysis

The complete statistical modelling package for the Strategic Organization paper is stored here.

## `Statistical Modeling/`

This folder is the authoritative source for empirical claims in the manuscript.

Start with:

- `STATISTICAL_MODELING_REPORT.md` — narrative interpretation of the completed modelling.
- `MODEL_SPECIFICATION_AND_CLAIM_DISCIPLINE.md` — model definitions and strict boundaries on what the paper may claim.
- `analysis_manifest.json` — machine-readable key results and reproducibility metadata.

It also contains the full publication tables and figures:

- sample flow and sample characteristics;
- missingness and descriptives;
- reliability, item-total correlations and parallel analysis;
- within-person capability-asymmetry tests;
- ILO exposure-group descriptives and omnibus tests;
- correlations;
- five core occupation-clustered regression specifications;
- robustness specifications;
- influence diagnostics;
- Huber robust and median-regression results;
- exploratory post-score appendix and sensitivity analyses;
- four main 300-dpi empirical figures plus the parallel-analysis appendix figure.

## `Reproducible Analysis/`

Contains `analysis_pipeline.py`, the exact deterministic Python pipeline used to rebuild the modelling package from the committed primary and analysis-ready data. Random procedures use seed `20260915`.

## Core empirical conclusion

The mapped analytical sample contains 198 participants across 19 ISCO-08 occupation clusters. Mean conventional strategic capability is 86.43 while mean AI/data capability is 69.80, producing a 16.63-point within-person capability asymmetry. The standardized within-person effect is very large (Cohen dz ≈ 2.81).

Participants targeting ILO Gradient 3/4 occupations have higher absolute capability. However, once conventional capability is accounted for, high occupational GenAI exposure does not predict a relative AI/data capability advantage. This adjusted null result is stable across the completed robustness analyses.

The defensible paper-level interpretation is therefore **absolute capability sorting without commensurate relative AI/data readiness**, not a causal claim that occupational exposure creates a capability gap.

## Follow-up data

Only 12 participants have an overall post-assessment score. Those results are retained as exploratory appendix evidence only and must not be used to claim intervention effectiveness.
