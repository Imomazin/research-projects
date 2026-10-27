# Federated deep learning benchmark

This pipeline is a preregistration-ready computational pilot for the paper **Privacy, Trust & Intelligent Systems in Industry 6.0**. It DOES NOT yet establish a novel method or a publication finding.

## Run

From the repository root:

    python -m pip install -r "Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six/Experiments/Requirements.txt"
    python "Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six/Experiments/Industrial Federated Benchmark.py" --dataset maintenance --rounds 8
    python "Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six/Experiments/Industrial Federated Benchmark.py" --dataset steel --rounds 8
    python "Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six/Experiments/Industrial Federated Benchmark.py" --dataset semiconductor --rounds 8
    python "Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six/Experiments/Industrial Federated Benchmark.py" --dataset power --rounds 8

Quick code-level pilot: add --max-rows 500 --rounds 1 --clients 2.

## Controls and scientific limitations

- Linear model, pooled neural network, FedAvg neural network and Opacus DP-SGD federated neural network are separately evaluated.
- A fixed held-out train/validation/test division is used. Imputation and scaling are fitted on training records only.
- No actual industrial organisations or federated network endpoints participate. Dirichlet clients are **simulated**, never genuine factory clients.
- AI4I failure-mode flags, product ID and row identifier are excluded to prevent label leakage. AI4I is synthetic, not a real factory record.
- SECOM consists of thirteen lossless industrial sensor segments and observed binary labels, with pronounced class imbalance; no independent factory IDs.
- Power output is a continuous regression task and uses MW error metrics. Its archived observations were shuffled; no chronological claim is justified.
- DP-SGD uses per-example gradient clipping, additive Gaussian noise, Poisson sampling and Opacus Rényi privacy accounting **per client across participating rounds**. The reported epsilon is the largest observed client epsilon at the stated delta. Participation of nonselected clients does not add an event.
- No cryptographic secure aggregation is implemented. All model parameters are aggregated in process. Do not claim encryption or a deployed multi-party system.
- Membership inference, gradient inversion, poisoning, distribution-shift attacks, calibration research, energy consumption and communication timing remain future tasks. Communication bytes are **estimated parameters**, not observed network traffic.
- Running one fixed seed provides a smoke test only; a paper requires repeated random seeds, intervals, resource matching, multiple non-IID regimes, ablations and testing on natural device/client identities where available.
- The same held-out test partition is used for each predefined baseline. Do not select a preferred model from test results, and do not change preprocessing or hyperparameters after viewing test results.
- Industry 6.0 has no universally settled operational definition; this code evaluates existing industrial datasets and cannot demonstrate Industry 6.0 deployments.

## Next empirical work

Benchmark alpha 0.1, 0.5, 2.0; client participation 0.5, 0.75, 1.0; Gaussian noise 0.8, 1.2, 2.0; 5 or more paired seeds. Record utility-versus-epsilon frontiers, privacy attack advantage, device-held-out performance, cost and uncertainty. Run observational baselines on Bosch CNC machine-labelled records when authoritative dataset files are acquired. Validate the novel contribution independently against current published methods before claiming methodological superiority.

## Gas turbine annual holdout

The gas-turbine task predicts NOx emissions from nine contemporaneous non-emission sensor variables, excluding CO and NOx from predictors. All 2011–2013 records form training, 2014 is validation and 2015 is a never-seen testing period. The 500-row CI pilot proportionally samples within each period without crossing year boundaries. Federated client labels remain simulated partitions drawn only from the training period; a year is not an independent factory. Metrics are expressed in mg per cubic metre. A successful CI run is a computational smoke test only.

## Intrusion-security transfer pilot

The IoT task uses original UCI 942 RT-IoT2022 archived data (123,117 network-flow observations) as a separate security transfer benchmark. Benign traffic is the three original categories Thing_Speak, MQTT_Publish and Wipro_bulb; the other nine original labels are treated as attacks. The original multiclass labels remain preserved in the archive and provenance audit. The unrelated Unnamed row identifier is excluded, as are the target label and any explicit one-to-one target encodings. Categorical protocols and service values are one-hot encoded before train-only preprocessing. The pilot uses simulated non-IID clients; IoT testbed traffic is not field evidence from independent industrial factories. Interpret security results with class imbalance and potential correlated traffic flows in mind. Future assessments should use attack-family and device holdouts when authenticated identifiers are available.

## Repeated paired experiments

Execute the provided multi-seed runner with full datasets and a preregistered grid:

    python "Experiments/Run Paired Benchmarks.py" --datasets maintenance steel semiconductor power gas iot --seeds 11 23 37 47 59 --alphas 0.1 0.5 2.0 --noises 0.8 1.2 2.0 --rounds 8 --clients 4 --max-rows 0

Paths above are relative to the Industry Six paper folder. The default research grid is computationally substantial and needs sufficient run time. Each combination archives an individual JSON output; the runner records every failed job in a separate file and generates Trial Metrics.csv and Seed Summary.csv (names in GitHub are spelled with spaces). Confidence intervals describe variability across repeated random seeds only and are not external-validation intervals.

The automated paired pilot currently runs maintenance and steel with three matched seeds, two simulated clients, two rounds and 800 samples per task to validate the pipeline. This is not the definitive research sample or the full grid.

Every model family must be assessed on the same prespecified task. Different epsilon budgets are distinct privacy conditions; do not imply that unequal privacy budgets or training costs yield a causal method improvement. Do not rank configurations using the reserved test set. Any decisions driven by validation findings require an untouched final evaluation protocol.

## Existing pilot evidence

See Pilot Evidence.md for six GitHub Actions smoke-test results, including unsuccessful method outcomes and class-imbalance failures. Test statistics should not be quoted as representative industrial field performance.

## Confirmatory study

The pilot pipeline above is retained as recorded. The confirmatory study uses Experiments/Private Risk Control, which implements DP-SGD in NumPy (Opacus could not be installed in the execution environment) with Google dp_accounting, secure aggregation and private aggregate risk control. Its pilot artefacts could not be re-verified because GitHub Actions artefacts were not accessible from the execution environment, so the pilot numbers in Pilot Evidence.md and Paired Pilot Findings.md are not used as results.
