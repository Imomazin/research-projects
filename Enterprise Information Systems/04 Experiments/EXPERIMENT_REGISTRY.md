# Experiment Registry

| ID | Family | Dataset | Main comparison | Status |
|---|---|---|---|---|
| P2-E1 | Baseline federation | smoke-test then grant datasets | FedAvg vs FedProx vs sample-weighted | existing Meridian baseline; protocol registered |
| P2-E2 | Adaptive privacy | selected healthcare + fraud | fixed DP vs adaptive schedule at matched privacy budget | scheduler implemented; empirical run pending |
| P2-E3 | Robustness | selected healthcare + fraud | conventional vs median/trimmed-mean/trust-weighted under controlled Byzantine attacks | aggregation + deterministic attack harness implemented; experiment run pending |
| P2-E4 | Secure aggregation | representative final settings | secure off/on with overhead measurement | blocked pending protocol/novelty selection |
| P2-E5 | Privacy attacks | representative final settings | MIA/inversion across protocol combinations | inherited attack tooling present; integration run pending |
| P2-E6 | Cross-domain validation | NIH/ISIC/IEEE-CIS final set | stability of conclusions across domains | data sources registered; preprocessing pending |

No results are to be entered manually. Each completed row must point to configuration hashes, data/partition manifests, a Meridian commit and generated result artefacts. Development smoke tests are not manuscript results.

## Completion status (2026-09-18) — controlled-simulation stage

Canonical runs executed on synthetic controlled domains (clinical-sim, financial-sim),
20 frozen seeds, config `p2-canonical-1.0.0`. **These are clearly-labelled controlled
simulations, NOT the grant datasets.** Grant-dataset runs remain BLOCKED on acquisition.

| ID | Status now | Result artefact (in Meridian `research/results/`) |
|---|---|---|
| P2-E1 | RUN (synthetic) | `P2-E1_baseline.csv` |
| P2-E2 | RUN (synthetic; adaptive = negative result) | `P2-E2_adaptive_privacy.csv` |
| P2-E3 | RUN (synthetic) | `P2-E3_byzantine.csv` |
| P2-E4 | RUN (synthetic; secure-agg overhead + correctness) | `P2-E4_secure_agg.csv` |
| P2-E5 | RUN (synthetic; MIA near-chance regime) | `P2-E5_privacy_attacks.csv` |
| P2-E6 | RUN (synthetic; cross-domain evidence) | `P2-E6_evidence.csv`, `P2-E6_evidence_detailed.csv` |
| **P2-E7** | RUN (assurance envelope + transfer; **headline**) | `P2-E7_assurance_analysis.json`, `P2-E7_transfer.csv`, `P2-E7_contracts.json` |

Statistics: `research/results/STATISTICS.json`. Figures: `research/figures/`. Tables:
`research/tables/`. Provenance sidecars accompany every result CSV. Each result is
traceable to config version, git commit, seeds and driver script under
`research/harness/experiments/`. E7 is the P2 headline: E6 evidence is fed into the
assurance core to produce per-domain feasibility, Pareto fronts, the cross-domain
envelope and transfer audits.
