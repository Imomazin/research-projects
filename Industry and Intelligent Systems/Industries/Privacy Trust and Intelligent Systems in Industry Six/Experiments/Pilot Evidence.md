# Computational pilot evidence

Source: GitHub Actions run https://github.com/Imomazin/research-projects/actions/runs/40359405872 (completed 26 October 2026). All six jobs concluded successfully. Run artefacts contain the complete source hashes and model output JSON.

## Pilot configuration

Two simulated clients; one federated round; 500 stratified or year-aware observations per dataset; single seed 42; Dirichlet alpha 0.5; DP noise multiplier 1.2 and clipping norm 1.0. Full data are stored separately, but these runs used subsamples. The output below is a code and experimental-design smoke test, not an inferential study.

## Observed test metrics

| Dataset | Metric | Linear | Pooled neural | FedAvg | DP FedAvg | Max client epsilon |
|---|---|---:|---:|---:|---:|---:|
| Gas turbine | RMSE (mg/m³) | 15.081 | 13.869 | 14.081 | 14.024 | 3.909 |
| IoT intrusion | Balanced accuracy | 0.813 | 0.555 | 0.610 | 0.500 | 3.840 |
| Power generation | RMSE (MW) | 4.345 | 13.244 | 16.365 | 18.388 | 3.909 |
| Semiconductor | Balanced accuracy | 0.564 | 0.500 | 0.500 | 0.479 | 3.840 |
| Maintenance | Balanced accuracy | 0.500 | 0.500 | 0.500 | 0.500 | 4.164 |
| Steel faults | Balanced accuracy | 0.637 | 0.143 | 0.221 | 0.248 | 3.909 |

Lower RMSE is better; higher balanced accuracy is better. Each row is a distinct task, so the figures cannot be averaged across datasets. Epsilon is a per-client estimate from Opacus at the recorded delta, not a claim of cryptographic secure aggregation or end-to-end distributed deployment.

## Research interpretation

- Maintenance: neural methods display accuracy near 96% but balanced accuracy of 0.500; they did not adequately detect rare failures under this pilot configuration.
- Semiconductor: 93.3% accuracy for pooled and FedAvg coincided with chance-level balanced accuracy (0.500). Class imbalance is a critical issue.
- Steel quality: the linear reference outperformed all neural pilot configurations by balanced accuracy; one training round is insufficient to establish neural performance.
- Power and gas turbine: error metrics are on different physical scales, with year-separated gas-turbine evaluation. A single low-training run does not justify choosing any model.
- IoT intrusion: the private neural pilot reported balanced accuracy 0.500 despite high nominal accuracy, highlighting failure of class-balanced detection.

## Publication evidence still required

Five or more matched seeds, stable validation-tuned hyperparameters, full-data experiments, multiple predeclared non-IID regimes, independent holdouts, uncertainty intervals, sample-size and compute parity, calibration, membership-inference and poisoning experiments, actual device-held-out tests, and a well-motivated original method. Opacus was run with secure random generator disabled for reproducible research simulation; no production-grade cryptographic guarantee is claimed. Avoid selecting winning configurations using the reported test results. Preserve negative findings.
