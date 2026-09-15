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
- deterministic Byzantine research attack harness with sign-flip, scaling, constant-vector and seeded Gaussian update attacks

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
- full Byzantine experiment matrix and result artefacts
- grant-dataset preprocessing pipelines
- synthetic compliance twin

## Evidence discipline

The new robust/trust/privacy/attack primitives are implementation progress, not empirical findings. No manuscript result is marked complete until the experiment pipeline is run on frozen configurations and datasets.
