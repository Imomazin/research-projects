# Frozen confirmatory protocol

This protocol was committed before any confirmatory seed was executed. The commit that adds this file, together with Study Configuration.json and Tuned Hyperparameters.json, fixes the code, hyperparameters, seeds, endpoints and analysis plan. Deviations are recorded in Protocol Deviations.md with the reason and date.

## Method under test

Private aggregate risk control (PARC). Clients train a shared model with DP-FedAvg (local DP-SGD, Poisson sampling, per-example clipping, RDP accounting with Google dp_accounting). Each client then bins the scores of its own calibration records into a fixed histogram, adds Skellam noise with parameter mu/K and submits the masked integer vector through pairwise-mask secure aggregation. The server sees only the noisy sum. It certifies an automatic-pass threshold (miss rate at most alpha_miss) and an automatic-alarm threshold (false-alarm rate at most alpha_false_alarm) by a fixed-sequence scan whose p-values are exact binomial-Skellam convolutions evaluated at a high-probability lower bound on the noisy class total. Scores between the two thresholds are escalated to a person. The same scan certifies selective classification (joint error at most alpha_selective) for multiclass tasks and prediction intervals (exceedance at most alpha_interval) for regression.

Training and calibration records are assigned by independent per-record coin flips, so the record-level guarantee of the full pipeline is the maximum of the training and calibration budgets (parallel composition). The calibration budget is set equal to the training budget for each DP model; for the non-private FedAvg model it is fixed at epsilon 4.

## Fixed settings

Rounds 25, local epochs 2, batch 64 (IoT 256), hidden layers 64 and 32, clip norm 1.0, delta 1e-5, epsilon grid 1, 2, 4, 8 (headline 4), four simulated clients with Dirichlet concentration 0.5 where no natural clients exist, alpha_miss 0.10, alpha_false_alarm 0.05, alpha_selective 0.10, alpha_interval 0.10, delta_test 0.04 and delta_count 0.01 per side, 26 score bins on the logit grid. Learning rates and DP batch, momentum and class weight were selected on tuning seed 0 using an internal split of training rows only; the selections are stored in Tuned Hyperparameters.json and are not revised after this commit.

## Seeds and designs

Confirmatory seeds 1 to 10 for maintenance, steel, semiconductor, power, gas, Bosch (machines, time holdout, machine holdout) and HAI (sessions); seeds 1 to 5 for IoT because of run time. Sensitivity and attack stages use seeds 1 to 5. Seed 0 is reserved for tuning and is never reported as a confirmatory result.

## Primary endpoints and hypotheses

H1 (validity, simulation). In the Monte Carlo validation with known score distributions, the population miss rate and false-alarm rate of PARC thresholds exceed their targets in at most 5 per cent of replications in every condition. The private plug-in rule is expected to exceed this rate. Falsified if any PARC condition exceeds 5 per cent by more than the 99 per cent binomial sampling margin.

H2 (validity, data). On in-distribution test rows of the binary tasks, the share of runs whose realised test miss rate exceeds alpha_miss is lower under PARC than under the private plug-in rule applied to the same model and the same noisy histograms (paired over runs; one-sided exact McNemar test).

H3 (price of private calibration). For DP models at epsilon 4, the escalation rate under PARC exceeds the escalation rate of non-private Learn-then-Test calibration of the same model by less than 5 percentage points (paired bootstrap 95 per cent upper bound below 0.05).

H4 (boundary). On non-exchangeable tests (gas turbine 2014 and 2015, Bosch later periods, Bosch unseen machine, HAI later sessions) the realised miss rate or interval exceedance under PARC is higher than on the matching in-distribution test (paired over runs; Wilcoxon signed-rank).

Holm correction is applied across H2, H3 and H4. H1 is assessed against its stated margin.

## Secondary endpoints

Utility by epsilon (PR-AUC for binary tasks, macro F1 for steel, RMSE for regression) for FedAvg, FedProx, SCAFFOLD, trimmed mean, median, DP-FedAvg, pooled and local-only models; worst-client utility; calibration error of raw and privately binned probabilities; membership-inference AUC and advantage; reconstruction accuracy from single-record updates; communication bytes and secure aggregation cost; HAI event detection rate and delay; sensitivity to heterogeneity, client count, participation, label noise, model poisoning, histogram poisoning, test-time corruption and bin count. Secondary comparisons use paired bootstrap intervals over seeds with Benjamini-Hochberg control within each table.

## Interpretation rules

Seed-level intervals describe variation over random partitions, initialisations and noise draws for a fixed dataset, not variation over industrial sites. Simulated clients are not organisations. Results from the 2015 gas-turbine year are not blind because the pilot inspected that year. Hyperparameter selection used the same records as the confirmatory runs under a different seed and its privacy cost is not included in the reported epsilon. Feature normalisation constants are estimated from pooled training rows and treated as public metadata.
