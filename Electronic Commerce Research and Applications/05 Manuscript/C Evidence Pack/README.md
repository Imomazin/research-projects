# C Evidence Pack — P3 (Orbit)

Everything C needs to write the paper without reverse-engineering Orbit. Links are relative to
`Electronic Commerce Research and Applications/`. Provenance: research `@ c022fba`,
Orbit `@ 559a262` (branch `claude/adoring-cerf-0rdyvt`, PR #17 not merged, production untouched).

## Start here
1. `05 Manuscript/C_PUBLICATION_HANDOFF.md` — definitive handover (A–Q), incl. claims C must not make.
2. `07 Build Synchrony/PUBLICATION_READINESS_AUDIT.md` — PASS/PARTIAL/BLOCKED per item.

## Methods & assumptions
- `05 Manuscript/FINAL_METHODS_SPECIFICATION.md`
- `05 Manuscript/CAUSAL_ASSUMPTION_REGISTER.md`

## Results & traceability
- `05 Manuscript/RESULTS_INTERPRETATION.md` — exact numbers, what C may/must-not claim.
- `05 Manuscript/CLAIM_EVIDENCE_MATRIX.md` — 7 claims → RQ → assumption → code → experiment →
  artefact → statistics → figure/table → limitation → section.

## Figures & tables (regenerable)
- `05 Manuscript/FIGURE_REGISTER.md`, `05 Manuscript/figures/` (F1–F9 PNG).
- `05 Manuscript/TABLE_REGISTER.md`, `05 Manuscript/tables/` (T1–T5 CSV+MD).
- Regenerate: `python3 "04 Experiments/generate_figures_tables.py"`.

## Canonical results (machine-readable)
- `04 Experiments/results/` — CSV/Parquet/JSON per experiment, each with a provenance block:
  `p3_e1_canonical_*`, `p3_e2_canonical_*`, `p3_e5_canonical_*`, `p3_e6_canonical_*`,
  `p3_e3_fixture/*`.

## Experiments & configs
- `04 Experiments/EXPERIMENT_REGISTRY.md`, `04 Experiments/configs/p3_e{1,2,5,6}_canonical.json`.
- Scripts: `04 Experiments/p3_e{1,2,3,5,6}_*.py`; harness `04 Experiments/p3lib/`.

## Literature & novelty
- `02 Literature/STATE_OF_ART_2026.md` — novelty gate (constrains claims).

## Data
- `03 Data/DATASET_MANIFEST.md`, `03 Data/ACQUISITION_STATUS.md` (Criteo/UCI network-block record).

## Orbit software (paired build)
- `packages/causal-core` (graph, identification, effect estimators, diagnostics, synthetic),
  `packages/atlas-core/src/causal-budget.ts`, `packages/martech-core/src/uplift-recs.ts`,
  `apps/web/app/causal/page.tsx`. Tests: `packages/causal-core/test/` (32 pass via `npm test`).

## Status in one line
Semi-synthetic known-truth programme (RQ1–RQ5) complete, validated, reproducible; randomized
pipeline validated on a fixture; Criteo/UCI real-data runs blocked by network policy. See the
readiness audit for the exact governance decision left to the author team.
