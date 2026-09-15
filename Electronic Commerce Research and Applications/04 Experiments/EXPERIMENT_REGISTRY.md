# Experiment Registry

| ID | Dataset | Main comparison | Primary metric | Status |
|---|---|---|---|---|
| P3-E1 | Criteo Attribution | first/last/linear/time-decay/weighted | attribution distribution and downstream decision differences | planned |
| P3-E2 | semi-synthetic journeys | heuristic vs causal estimators | causal effect / attribution recovery error | implementation ready in Orbit; canonical run pending |
| P3-E3 | Criteo Uplift unbiased v2.1 | randomized difference-in-means vs cross-fitted AIPW + predicted uplift ranking | ATE, 95% CI, randomized uplift by score decile | pipeline ready; public dataset acquisition/run pending |
| P3-E4 | Criteo Attribution | identified causal models | effect stability and sensitivity diagnostics | planned |
| P3-E5 | causal effect outputs | existing optimiser vs causal budget allocator | incremental utility/revenue under matched budget | optimiser implemented; evidence run pending |
| P3-E6 | simulated violations | sensitivity analyses | bias under confounding/overlap/measurement stress | planned |
| P3-E7 | UCI + optional SkillHubs | external-validity checks | stability of commercial conclusions | acquisition script ready for UCI; analysis pending |

No empirical section is considered writable until the causal Orbit implementation and the corresponding experiment row are reproducible. Development smoke tests are not manuscript results.
