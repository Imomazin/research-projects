# Specialist review before submission

Internal review of the manuscript built on 27 October 2026, read from five specialist positions. Each entry states the concern, what was changed in response and what remains for the author or for reviewers to judge.

## Machine learning

The neural models are small three-layer perceptrons trained for 25 rounds, so the utility numbers describe this model class and may understate what larger models achieve on Bosch and HAI. Hyperparameters were tuned on seed 0 only and SCAFFOLD diverged at larger learning rates on AI4I during tuning; both are reported. Six of eight tasks use simulated Dirichlet federations, so the natural-partition evidence rests on Bosch machines and HAI sessions. RT-IoT2022 sits at ceiling and adds little to the utility comparison, which the text says. Response: the Discussion and Limitations name all four points and the linear model is kept as a reference on every table. Remaining: a larger-model replication would strengthen RQ1 and RQ2.

## Differential privacy and security

Proposition 2 depends on per-record independent role assignment, which the code implements through Bernoulli role flips and the unit tests check. Skellam noise is calibrated with the exact hockey-stick divergence and DP-SGD with the RDP accountant from dp_accounting 0.6.0. Three items sit outside the formal guarantee: normalisation statistics, hyperparameter tuning and public class weights. Secure aggregation runs in one process with an honest-but-curious server and no dropout recovery, and it prevents the server from screening poisoned updates or counts. The membership attack is a loss threshold and is a lower bound on leakage. Response: all are stated in Methods, Limitations and the threat model, and the calibration budget without secure aggregation (ε up to 5.28 at the ε = 4 setting) is reported. Remaining: range proofs for client counts and a networked secure-aggregation run.

## Industrial engineering

AI4I is synthetic, HAI is a testbed and none of the federations are independent companies. Escalation is measured but not priced, so the operating rules give evidence thresholds without a cost model for human review. Timing figures are in-process and exclude network latency. HAI alarm delay was measured per event and is the most deployment-like result. Response: the paper states these limits and frames the operating rules as conditional on calibration evidence. Remaining: a site cost model for escalated decisions would make Table 11 more directly usable by plant managers.

## Information systems and strategy

The Industry 6.0 label has no agreed definition and the cited sources are white papers, conference papers and short journal articles. The manuscript treats the label as a set of proposed capabilities and does not claim the study tests it. The governance argument ties escalation to Article 14 of the EU AI Act and the NIST AI RMF and assigns owners in Table 11. Response: wording was checked for promotional claims and the Industry 6.0 section states what the evidence does not show. Remaining: reviewers at *Industries* may ask for a sharper link to organisational adoption studies.

## Statistics

The frozen tests treat run-model combinations as independent although models within a run share one data partition. Response: run-clustered versions of H2 and H4 were added as labelled secondary checks; H2 holds at run level (plug-in worse in 25 of 65 runs, never better, sign test p = 3.0e-8) and H4 holds at run level (mean rise 14.4 points, p = 0.0017) but is carried entirely by the gas turbine (mean rise without gas 0.2 points). H3 is reported as frozen and described as uninformative because DP models escalate about 96 per cent of decisions under both rules; the calibration-only sweep, which is post hoc, carries the interpretation. Test-set sampling noise contributes to exceedance counts, as the Results state. The 2015 gas-turbine year was inspected in an earlier pilot, which is disclosed. Both deviations are recorded in Experiments/Private Risk Control/Protocol Deviations.md.

## Items for the author before submission

Confirm the affiliation line and contact email, the CRediT statement, the funding and conflict statements and the generative AI disclosure. Confirm the Enang et al. IEEE Access 2026 reference details against the final published record. Decide whether to name suggested reviewers. The paper must not be submitted without the author's approval.
