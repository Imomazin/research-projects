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
