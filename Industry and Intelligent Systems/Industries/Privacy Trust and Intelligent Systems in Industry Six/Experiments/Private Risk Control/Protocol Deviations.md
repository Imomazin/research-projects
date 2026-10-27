# Protocol deviations

Each entry records a change made after the freeze commit 1dc2dbf (26 October 2026, 20:32 UTC), the reason and whether confirmatory results had been seen.

## Calibration-only privacy sweep (added 26 October 2026)

What changed: a secondary sensitivity variant, "calibration epsilon", trains the non-private FedAvg model and certifies its thresholds with private aggregate risk control at calibration budgets of 0.5, 1, 2, 4 and 8, alongside the non-private Learn-then-Test rule and the private plug-in and uncorrected rules.

Reason: the first confirmatory runs (maintenance seed 1, Bosch machines seeds 1 and 2) showed that DP-trained models at every training budget place enough faults at low scores that no automatic-pass threshold can be certified, with or without private calibration. The frozen H3 comparison is therefore uninformative about the cost of private calibration itself. The sweep isolates that cost on a model whose ranking is good enough for certification.

Results seen: yes, seed 1 to 2 outputs for two tasks. H3 is still reported exactly as frozen; the sweep is labelled as an added secondary analysis.

## Run-clustered checks of H2 and H4 (added 27 October 2026)

What changed: Analyse Results.py adds secondary versions of H2 and H4 that treat each dataset-design-seed run as one cluster. For H2 a sign test compares, run by run, how many model combinations exceeded the miss target under the private plug-in rule and under PARC. For H4 the shifted-minus-in-period differences are averaged within each run before a one-sided Wilcoxon test; the H4 mean is also reported without the gas turbine.

Reason: the frozen tests treat run-model combinations as independent although models within a run share one data partition, which can overstate precision.

Results seen: yes, all confirmatory results. The frozen H2 to H4 tests and their Holm adjustment are reported unchanged; the clustered versions are labelled as secondary checks.
