# Real Time IoT intrusion data

Official source: https://archive.ics.uci.edu/dataset/942
Citation: B. S. and Rohini Nagapadma, RT-IoT2022, UCI Machine Learning Repository, DOI 10.24432/C5P338.
Licence: Creative Commons Attribution 4.0 International.

This collection covers normal and malicious traffic in a real-time IoT infrastructure with device and network attack scenarios. It is valuable for security, transfer learning, privacy and trust experiments, but does not constitute production measurements at independent industrial factories. Do not label simulated network attacks as naturally occurring incidents.

The original UCI source ZIP is retained without editing when acquisition completes. Acquisition Audit.json holds SHA-256 hashes for the original archive and the uncompressed labelled data, columns, exact row count, class distribution and provenance. The full ZIP can be extracted locally by the research team. Avoid treating source row order as chronological without an independently verified time field.

Before modelling:
- Make an explicit binary or multiclass attack-label mapping; preserve rare attack classes.
- Remove identifiers or proxies that reveal the label, if appropriate to the pre-specified prediction question.
- Partition devices only when genuine stable identities are present. Otherwise say simulated federation.
- Fit encoding, scaling and feature selection only on training folds.
- Use class-balanced metrics, false-positive rates and adversarial tests.
- Keep privacy accounting and secure aggregation claims separate.
