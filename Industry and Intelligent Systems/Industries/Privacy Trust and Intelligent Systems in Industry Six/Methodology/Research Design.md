# Research design

## Core research question
How can industrial intelligence systems learn collaboratively while preserving confidentiality, trustworthy predictions, operational resilience and acceptable resource use across heterogeneous devices and production environments?

## Experimental tracks

**Manufacturing:** Bosch CNC machine- and time-separated recordings, SECOM semiconductor measurements, Steel Plates Faults, AI4I synthetic maintenance.

**Industrial controls:** HAI and, subject to individual data-use approval, SWaT. Use event-aware windows and attack-detection measures.

**Industrial/IoT security:** TON IoT, Edge IIoTset, CIC IoT, N BaIoT, RT IoT. Report consumer IoT transfer evidence separately from industrial evidence.

## Methods and benchmarks

Local-only, pooled centralised, FedAvg, FedProx and SCAFFOLD (subject to implementation feasibility); privacy-protected federation with calibrated DP-SGD; optional secure aggregation with an explicit protocol and adversary assumption.

Metrics: macro F1, balanced accuracy, MCC, PR AUC, calibration error, Brier score, time-to-detect, distribution shift performance, privacy-budget epsilon/delta and membership-inference advantage. Under applicable threat models evaluate reconstruction, poisoning and evasion. Report rounds, bytes transmitted, inference latency and computational cost.

## Validation

Natural clients where actual machine/device identities exist; site-simulated partitions otherwise. Fit transformations only on training data. Hold out chronologically distinct or unseen-device sets where appropriate; prevent related attack windows crossing folds. Repeat seeds, calculate uncertainty intervals, perform privacy-budget and non-IID ablations and compare against matched baseline compute.

Formal differential privacy, encrypted aggregation and empirical leakage testing protect different properties and must be reported separately.

Industry 6.0 remains emerging; do not frame these current datasets as evidence of a fully established Industry 6.0 deployment.
