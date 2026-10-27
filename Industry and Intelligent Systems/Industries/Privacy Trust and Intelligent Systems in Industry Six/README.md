# Privacy, Trust & Intelligent Systems in Industry 6.0

Target journal: **Industries (MDPI)**. Article type: original empirical research.

This project studies privacy-preserving deep learning, federated intelligent systems, industrial reliability, operational trust and cyber-physical resilience. Industry 6.0 is an emerging academic construct and must be defined explicitly. Available empirical datasets concern present industrial technologies.

## Project structure

- Datasets: registered sources, small original or traceable CC-licensed datasets and audit.
- Data Collection: authoritative acquisition procedures and verification.
- Methodology: research design and leakage-safe federated partitions.
- Literature: prior work and novelty requirements.
- Submission: paper deliverables and deadline.

## Data tiers

Industrial equipment and production: Bosch CNC, SECOM, Steel Plates Faults, AI4I.

Industrial control security: HAI and SWaT (restricted).

Industrial and IoT intrusion: TON IoT, Edge IIoTset, CIC IoT, N BaIoT and RT IoT.

Supplemental prognostics: NASA PCoE.

The **Source Register.csv** explicitly distinguishes committed source files from sources that still require downloading. Data labelled as restricted must never be pushed into this public repository.

## Ethics and reproducibility

Credit source authors and licences; separate actual machine/device partitions from simulated federation. Prevent test leakage, document threat models, log formal privacy-accounting parameters, evaluate adversarial robustness and calibration and include full baselines, uncertainty intervals and unsuccessful experiments.

## Confirmatory study (26 October 2026)

- Method: private aggregate risk control (PARC) with DP-FedAvg, Skellam-noised calibration histograms and pairwise-mask secure aggregation. Code in Experiments/Private Risk Control.
- Protocol frozen in commit 1dc2dbf before any confirmatory seed; deviations in Experiments/Private Risk Control/Protocol Deviations.md.
- Data: the six committed tasks plus Bosch CNC (three machines) and HAI 21.03 (attack sessions), with provenance in Datasets/Source Register.csv.
- Outputs: per-run JSON in Experiments/Private Risk Control/Results, analysis tables in Results/Analysis, figures in Figures, manuscript and workbook in Manuscript.
- Literature: Literature/Literature Evidence Matrix.csv and Literature/Verified Bibliography.md.
