# P2 Meridian Implementation Status

## Implemented on `research/p2-systems-paper`

### Privacy core

- adaptive per-round privacy schedule primitive
- conservative basic-composition budget contract
- explicit warning that adaptive signals must be public, pre-declared or privacy-safe
- per-round sigma planning through the existing RDP budget planner

### Federated runtime

- coordinate-wise median aggregation baseline
- coordinate-wise trimmed-mean aggregation baseline
- trust-weighted aggregation baseline
- bounded participant trust update rule
- shape validation for aggregation inputs

## Existing inherited Meridian baseline

- FedAvg
- FedProx
- sample-count weighted aggregation
- RDP accountant and budget planner
- DP clipping/noise infrastructure
- membership-inference and inversion attack tooling

## Not yet claimed as implemented

- cryptographic secure aggregation
- final heterogeneity-aware proposed weighting algorithm
- formal convergence proof
- final Byzantine attack harness and experiment matrix
- grant-dataset preprocessing pipelines
- synthetic compliance twin

## Evidence discipline

The new robust/trust/privacy primitives are implementation progress, not empirical findings. No manuscript result is marked complete until the experiment pipeline is run on frozen configurations and datasets.
