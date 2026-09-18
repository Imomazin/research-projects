# C Evidence Pack — P2 / Meridian

Self-contained evidence for the writing agent (C). Everything here is generated
from versioned experiment artefacts; **synthetic controlled-simulation evidence**,
not grant datasets (grant-dataset runs are blocked — see PUBLICATION_READINESS_AUDIT).

## Read in this order
1. `C_PUBLICATION_HANDOFF.md` — the master handover (identity, contribution, findings, claims C must not make).
2. `FINAL_METHODS_SPECIFICATION.md` — exact method → code mapping for the Methods section.
3. `RESULTS_INTERPRETATION.md` — per-result what-can/cannot-be-claimed.
4. `../CLAIM_EVIDENCE_MATRIX.md` — claim → evidence traceability (in `05 Manuscript/`).
5. `FIGURE_REGISTER.md`, `TABLE_REGISTER.md` — artefact provenance + caveats.
6. `PUBLICATION_READINESS_AUDIT.md` — PASS/PARTIAL/BLOCKED per criterion.

## Supporting references (in the research repo)
- Novelty: `../../02 Literature/STATE_OF_ART_2026.md`, `../../02 Literature/NOVELTY_MATRIX.md`
- Design: `../../01 Research Design/NOVELTY_DECISION.md`
- Datasets: `../../03 Data/DATASET_MANIFEST.md`
- Experiment registry + assurance analysis: `../../04 Experiments/`
- Build audit: `../../07 Build Synchrony/P2_COMPLETION_AUDIT.md`

## Artefacts included
- `figures/F2–F9.png` — publication figures.
- `tables/T2,T4,T5,T8,T9.md` — publication tables.
- `results/` — all canonical result CSV/JSON + provenance sidecars + `STATISTICS.json`
  + `P2-E7_assurance_analysis.json` (TS core) and `P2-E7_python_analysis.json` (Python; identical).

## Canonical source (regenerate everything)
Software repo `Imomazin/ppdl-cross-org-intelligence`, branch `claude/exciting-pasteur-q1pxdr`:
`research/harness/` (drivers + 45 unit tests), `research/analysis/{stats,figures}.py`.
Config version `p2-canonical-1.0.0`, 20 frozen seeds.

## Status
**MERIDIAN STATUS: PARTIAL.** Contribution frozen and validated on controlled
evidence; grant-dataset empirical section blocked on data acquisition.
