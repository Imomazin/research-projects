# Experiments

The experiment pipeline will generate manuscript tables and figures directly from versioned results.

Primary experiment families:

- E1: FedAvg/FedProx/sample-weighted baselines across IID to severe non-IID conditions
- E2: fixed versus adaptive privacy-budget schedules under matched total privacy budgets
- E3: robust and trust-aware aggregation under controlled Byzantine-client fractions
- E4: secure aggregation integration and systems overhead
- E5: membership-inference and inversion attack evaluation
- E6: healthcare-to-finance cross-domain replication

Every run records dataset version, partition seed, model, client count, participation rate, optimiser, aggregation method, attack configuration, privacy parameters, trust state, secure-aggregation state, utility, privacy, robustness, runtime and communication cost.
