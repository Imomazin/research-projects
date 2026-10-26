# Privacy, Trust & Intelligent Systems in Industry 6.0

## Article and empirical question

Intended article: Original computational and empirical research, targeted at *Industries* (MDPI).

Primary question: Under industrial heterogeneity, what combinations of distributed neural-network training and formally measured record-level differential privacy preserve operational prediction accuracy, calibration and reliability within realistic resource limits?

Industry 6.0 is a contested and emerging future-industrial term. The empirical contribution is tested using contemporary industrial observations and clearly labelled industrial simulations.

## Data inclusion and external validity

Observed industrial:
- SECOM semiconductor measurements: 1,567 rows; 590 sensor measures; 104 positive labels.
- Steel Plates quality faults: 1,941 observations, seven defect categories.
- Combined Cycle Power Plant: 9,568 observed operation points; no independent factory or chronological identifier.
- Gas Turbine Emissions: 36,733 measurements from one turbine, annual original files from 2011 to 2015. Held-out final-year generalisation is required.

Synthetic industrial:
- AI4I: 10,000 generated maintenance observations; binary machine-failure prediction. Failure-mode indicator fields are prohibited predictors.

Additional external data:
- Bosch CNC: measured machine identity enables physically distinct client holdouts; obtain official source data before field-like validation.
- HAI: industrial control testbed, versioned attack sequences; no mixing of overlapping windows across train/test.
- TON IoT, Edge IIoTset, CIC IoT, N BaIoT, RT IoT: security and transfer tasks, with provider permissions checked individually.
- SWaT: access agreement; raw data may not be redistributed.
- NASA turbofan: simulation; donor terms require individual confirmation.

Do not pool incompatible labels or claim that a testbed and factory measurement have equivalent provenance. For each outcome task, freeze its feature dictionary, pre-processing and measurement units before experiments.

## Study phases

### Phase A: Technical integrity

Validate source hashes, unique row counts, class frequencies, missingness, types, per-year consistency and provenance. Commit licensed small files; preserve access restrictions for other datasets. The smoke workflows demonstrate software execution only.

### Phase B: Predictive utility

Classification primary endpoint: macro-F1 with 95% uncertainty intervals, plus balanced accuracy, MCC and minority-class PR-AUC. For detection tasks with uncommon events, accuracy is not a primary metric.

Regression primary endpoint: RMSE in native units with MAE and distribution-shift sensitivity. For gas turbine NOx emissions, reserve the entire 2015 dataset for one final temporal test; 2014 is validation and 2011–2013 are training.

Use a linear or ridge baseline, centralized pooled neural network, local-only models, non-private federated learning and DP-SGD federation. Add FedProx and SCAFFOLD only with matched computational budgets and documented hyperparameters.

### Phase C: Privacy

Assume an honest-but-curious aggregator for the first analysis; distinguish malicious participants as a separate threat model. For formal example-level DP, record per-client clipping norm, Gaussian noise, sampling method, privacy accountant, \u03b5, \u03b4, participation schedule and the privacy unit. Privacy budgets must compose across *every* selected local optimisation step, not restart every federated round. Present the worst-case participating-client \u03b5 at its stated \u03b4.

Threat evaluations: well-defined black-box membership inference (AUC and TPR at low FPR); gradient inversion where aggregated updates are visible; poisoning/byzantine interference only when the adversary is modelled; and empirical record-level reconstruction tests. These are not interchangeable with a formal differential privacy guarantee. No secure aggregation claim without a cryptographic implementation and defined assumptions.

### Phase D: Trust and safety of decisions

Test ECE, Brier score (binary classification), selective prediction/abstention, calibration after dataset shift, adversarial robustness and false-negative rates for safety-relevant failures. For regression, test coverage of prediction intervals and out-of-period degradation. Quantify performance separately for minority or failure classes.

### Phase E: Industrial efficiency

Log per-round transmitted parameter bytes, actual network bytes when a real network is run, time, power consumption where metered, memory, CPU/GPU and participation counts. Do not infer measured network or electricity cost from parameter sizes.

## Prespecified experiments

- Random seeds: at least 5 paired seeds per condition, with identical source splits per paired comparison.
- Simulated client concentration: alpha = 0.1, 0.5, 2.0.
- Participation fraction: 0.5, 0.75, 1.0.
- DP noise multipliers: 0.8, 1.2, 2.0; record resulting epsilon, not a guessed epsilon.
- Number of simulated clients: 4, 8, 16 where sample size permits at least 20 training examples per client; rare outcomes may require a higher minimum.
- Compare IID, Dirichlet non-IID and observable real-device partitions when possible.
- Freeze test sets and seeds before method selection, fitting imputation/scaling only on training data.
- Tune on validation data only; repeat locked test evaluation after hyperparameter freeze.
- Control for multiple testing across declared primary hypotheses (Holm correction or an appropriately preregistered hierarchical model).
- Report paired 95% bootstrap confidence intervals for model differences, with run-level independence respected, and describe negative findings.
- Do not average performance across tasks with incompatible measurement scales without a principled normalisation.

## Claims gate

A Q1-standard manuscript requires reproducible original experiments, credible novelty against the latest prior work, evidence of privacy-utility trade-offs, uncertainty quantification, real industrial evidence beyond synthetic maintenance, at least one relevant temporal or unseen-device validation, and explicit negative controls. Passing a smoke workflow alone does not clear these criteria. No unexecuted results, estimated attacks or hypothetical improvements may appear in a Results section.

## Source evidence

UCI maintenance https://archive.ics.uci.edu/dataset/601 (10.24432/C5HS5C)
UCI steel https://archive.ics.uci.edu/dataset/198 (10.24432/C5J88N)
UCI semiconductor https://archive.ics.uci.edu/dataset/179 (10.24432/C54305)
UCI power https://archive.ics.uci.edu/dataset/294 (10.24432/C5002N)
UCI gas turbine https://archive.ics.uci.edu/dataset/551 (10.24432/C5WC95)
