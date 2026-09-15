# Privacy-Preserving Federated Intelligence Ecosystems: An Adaptive Privacy, Trust and Secure Aggregation Architecture for Cross-Organisational Machine Learning

**Target journal:** Enterprise Information Systems

**Status:** Working research manuscript. Claims and results must remain bound to the P2 grant-build-paper map and repository evidence.

## Abstract

Cross-organisational machine learning is constrained by a structural tension between collaborative model development and the legal, technical and institutional limits on centralising sensitive data. Federated learning reduces raw-data movement but does not by itself resolve privacy leakage, heterogeneous local data, unreliable participants or adversarial updates. This study develops and evaluates an integrated privacy-preserving federated intelligence architecture that combines adaptive differential privacy budgeting, heterogeneity-aware aggregation, participant trust scoring, Byzantine-robust aggregation and secure aggregation within a reproducible cross-organisational learning workflow. The architecture is implemented as an extension of the Meridian federated intelligence platform and evaluated against its existing FedAvg, FedProx and sample-weighted baselines. The study is designed around controlled non-IID partitions, benign and adversarial client conditions, privacy-attack evaluation and cross-domain validation in healthcare and financial fraud settings. Privacy is quantified through Rényi differential privacy accounting and empirical membership-inference and inversion attacks, while utility, robustness, communication cost and runtime are measured under matched experimental conditions. The study examines when integrated privacy and robustness mechanisms improve cross-organisational learning without rendering the system operationally impractical. All reported results will be generated from versioned experiment configurations and reproducibility certificates, creating a direct trace between manuscript evidence and the implemented platform.

## 1. Introduction

Organisations increasingly need to train machine-learning systems across institutional boundaries while retaining control of locally held data. Healthcare providers, banks, public agencies and other regulated organisations often face a common constraint: predictive performance can improve when information is pooled across institutions, yet the underlying records cannot simply be centralised. Federated learning addresses part of this problem by moving model updates instead of raw records. The resulting distributed learning process still exposes several unresolved system-level risks.

First, local datasets may be strongly non-independent and identically distributed. A hospital may serve a different patient population from another hospital. A bank may observe a transaction mix that differs materially across geographies, products or customer segments. Standard aggregation can therefore amplify dominant clients, slow convergence or reduce performance for under-represented participants. Second, shared model updates can leak information about local training data. Third, a participant may submit corrupted, strategically manipulated or otherwise unreliable updates. Fourth, privacy and robustness mechanisms impose communication, computation and utility costs that are rarely assessed as one integrated cross-organisational system.

This paper addresses these problems through a privacy-preserving federated intelligence architecture that treats privacy allocation, heterogeneity, participant reliability, adversarial robustness and secure aggregation as connected enterprise-system design decisions. The work extends Meridian, whose current research runtime already provides differential-privacy accounting, federated execution, FedAvg, FedProx, sample-weighted aggregation and empirical privacy-attack tooling. These inherited capabilities form the baseline. The present study introduces and validates the grant-defined mechanisms that are not yet part of the core runtime.

The paper makes four intended contributions. First, it develops an adaptive per-round privacy-budget orchestration mechanism that allocates a fixed total privacy budget across training rounds while preserving auditable Rényi differential privacy accounting. Second, it develops heterogeneity-aware and trust-aware aggregation mechanisms and evaluates them against conventional aggregation under controlled non-IID and Byzantine-client conditions. Third, it integrates secure aggregation with differential privacy and robust aggregation so that privacy, security, utility and systems cost can be examined jointly. Fourth, it evaluates the resulting architecture across healthcare and financial fraud settings using one reproducible experimental contract and attack-evaluation pipeline.

The remainder of the manuscript is structured as follows. Section 2 reviews federated learning, differential privacy, secure aggregation, robust aggregation and enterprise/cross-organisational governance. Section 3 defines the system model, threat model and design requirements. Section 4 presents the proposed architecture and algorithms. Section 5 specifies the experimental protocol. Section 6 reports the results. Section 7 discusses enterprise systems implications, governance, limitations and deployment considerations. Section 8 concludes the study.

## 2. Related Work

### 2.1 Federated learning under non-IID data

To be developed from the structured literature review and positioned against FedAvg, FedProx, adaptive weighting and personalised or clustered FL where relevant.

### 2.2 Differential privacy in federated learning

To cover client-level and example-level privacy, privacy accounting, Rényi differential privacy, privacy amplification, static and adaptive privacy allocation and privacy-utility trade-offs.

### 2.3 Secure aggregation and multi-party protection of model updates

To distinguish cryptographic protection of updates in transit and aggregation from differential privacy guarantees about learned information.

### 2.4 Byzantine-robust aggregation and participant reliability

To position coordinate-wise median, trimmed mean, Krum-family methods and trust or reputation-based approaches, subject to final algorithm selection and implementation.

### 2.5 Integrated privacy, robustness and cross-organisational intelligence

This section will establish the principal gap: privacy, heterogeneity, secure aggregation and adversarial robustness are often optimised separately, while operational cross-organisational systems must manage them jointly and expose their combined cost and failure modes.

## 3. System and Threat Model

### 3.1 Cross-organisational federation model

Define organisations, local datasets, global model, communication rounds and aggregation server or coordinating service.

### 3.2 Data heterogeneity model

Define the non-IID partitioning mechanism and severity parameter used across datasets.

### 3.3 Adversary model

Separate honest-but-curious coordination, malicious or Byzantine clients, privacy attackers and model-update observers.

### 3.4 Privacy model

Define the differential privacy unit, adjacency relation, epsilon, delta, clipping and noise mechanism.

### 3.5 Design requirements

R1 Privacy accounting must be auditable across rounds.

R2 The architecture must remain valid under heterogeneous client data.

R3 Aggregation must tolerate a controlled fraction of unreliable or malicious clients.

R4 Raw client updates must not be exposed where secure aggregation is enabled.

R5 Every experiment must be reproducible from repository artefacts.

## 4. Proposed Architecture

### 4.1 Meridian research baseline

Document inherited components only. No inherited capability will be claimed as a new P2 contribution.

### 4.2 Adaptive privacy-budget orchestration

Algorithm specification to be frozen after implementation and proof obligations are fixed.

### 4.3 Heterogeneity-aware federated weighting

Algorithm specification to be frozen after implementation and ablation design are fixed.

### 4.4 Participant trust scoring

Define the evidence used to update trust, the temporal update rule and the point at which trust influences aggregation.

### 4.5 Byzantine-robust aggregation

Select robust baselines and define the proposed trust-aware robust mechanism.

### 4.6 Secure aggregation layer

Specify protocol assumptions, confidentiality guarantee, failure cases and integration with robust aggregation.

### 4.7 Reproducibility and evidence chain

Bind configuration, implementation version, results and certificate hash.

## 5. Experimental Protocol

### 5.1 Research questions

**RQ1.** How does adaptive per-round privacy budget orchestration affect the privacy-utility frontier under increasing non-IID heterogeneity in cross-organisational federated learning?

**RQ2.** How do heterogeneity-aware and trust-aware aggregation mechanisms compare with FedAvg, FedProx and conventional sample weighting under benign and Byzantine client behaviour?

**RQ3.** What security, privacy and utility properties emerge when differential privacy, secure aggregation and Byzantine-robust aggregation are integrated into one federated intelligence architecture?

**RQ4.** How consistently do these effects generalise across simulated healthcare and financial cross-organisational settings?

### 5.2 Datasets

Planned grant-aligned evaluation:

- NIH ChestX-ray14
- ISIC, exact benchmark version to be frozen
- IEEE-CIS Fraud Detection

Exact subsets, tasks, licences, preprocessing and computational feasibility will be frozen before experiments begin.

### 5.3 Baselines

- FedAvg
- FedProx
- sample-count weighted aggregation
- static DP schedule
- no-DP control where methodologically appropriate
- selected Byzantine-robust baselines

### 5.4 Experimental factors

- non-IID severity
- number of organisations
- client participation rate
- adversarial-client fraction
- aggregation method
- privacy allocation policy
- total privacy budget
- secure aggregation on/off
- trust scoring on/off

### 5.5 Outcome measures

Utility, convergence, worst-client performance where appropriate, privacy budget, membership-inference success, inversion quality, robustness under attack, communication volume and runtime.

### 5.6 Statistical analysis

To be specified before result inspection. Multi-seed evaluation, uncertainty intervals, effect sizes and multiplicity handling will be fixed in the protocol.

## 6. Results

No numerical result will be added until produced by the versioned experimental pipeline.

### 6.1 Baseline behaviour under non-IID federation

### 6.2 Adaptive privacy allocation

### 6.3 Robustness and trust-aware aggregation

### 6.4 Secure aggregation systems cost

### 6.5 Privacy attack resistance

### 6.6 Cross-domain generalisation

## 7. Discussion

### 7.1 Scientific implications

### 7.2 Enterprise and cross-organisational systems implications

### 7.3 Privacy, governance and auditability

### 7.4 Practical deployment trade-offs

### 7.5 Limitations

## 8. Conclusion

To be written after empirical results are frozen.

## Reproducibility statement

The final manuscript will identify the stable Meridian release or commit used for all experiments. Experiment definitions, seeds, configuration hashes, result artefacts and regeneration instructions will be retained in the research and build repositories. Quantitative manuscript tables and figures will be generated from those artefacts.
