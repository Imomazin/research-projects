# Federated and leakage-safe partition protocol

**Natural observed clients:** Bosch physical machines (M01, M02, M03); N BaIoT physical device identities; other dataset clients only when source fields identify devices.

**Time-series industrial plants:** HAI and SWaT use run and time separation, event-level ground truth, and never random adjacent-window splits.

**Simulated clients:** SECOM, Steel Plates and AI4I have no established independent plant identities. Label every random/Dirichlet or class-stratified client split as simulation.

Model partial participation, label imbalance, sensor shift and client quantity skew, each with documented random seeds and severity parameters.

Never fit scaling, imputation, feature selection, oversampling or calibration across final test rows. Use task-specific heads for heterogeneous tasks unless labels and inputs have defensible common semantics.

Privacy logs must include threat level, unit of privacy, clipping norm, noise multiplier, sample rate, accountant, epsilon and delta. Secure aggregation without implementation or execution must never be described as actual cryptographic protection.
