# P2 Publication Readiness Audit

Verdicts: **PASS** / **PARTIAL** / **BLOCKED**. No numeric scores. Every
PARTIAL/BLOCKED item states the exact remaining work.

| Criterion | Verdict | Basis / remaining work |
|---|---|---|
| Novelty | PARTIAL | Cross-domain configuration-transfer gap is defensible (NOVELTY_MATRIX). Remaining: C runs one targeted confirmatory search ("federated configuration transfer", "operating/assurance envelope federated AI"); narrow to feasibility-vs-regret + no-private-diagnostic if a collision appears. |
| Research questions | PASS | RQ1–RQ4 frozen (NOVELTY_DECISION.md), each mapped to an experiment. |
| Conceptual framing | PASS | Assurance envelope + transfer framing defined and implemented. |
| Formalisation | PASS | Formal definitions in FINAL_METHODS §2 match code; two independent implementations agree exactly. |
| Implementation | PARTIAL | Assurance core, robust aggregation, trust, adaptive privacy, Byzantine harness, secure aggregation implemented + tested. Remaining: production-grade secure aggregation (dropout/integrity) if a stronger security claim is wanted; not required for the assurance contribution. |
| Data | BLOCKED | Grant datasets (NIH ChestX-ray14, ISIC, IEEE-CIS) not acquired — Box/challenge downloads + Kaggle competition-rules acceptance required (see §"Blockers"). Synthetic controlled domains are frozen and documented as an interim, clearly-labelled substitute. |
| Experiments | PARTIAL | E1–E7 complete on synthetic domains (20 seeds, frozen config). Remaining: re-run the identical pipeline on grant datasets once available (loader/partitioner swap only). |
| Statistics | PASS | Paired Wilcoxon + 95% CI + Cohen's d_z over 20 seeds; STATISTICS.json. |
| Robustness | PASS | E3 attack matrix + repeated seeds; clear effects with CIs; known trimmed-mean breakdown documented. |
| Ablations | PASS | Aggregation, privacy, trust, secure aggregation isolated across E2/E3/E4/E6. |
| Figures | PASS | F2–F9 generated from result CSVs; registered with caveats. |
| Tables | PASS | T2/T4/T5/T8/T9 generated from results; registered. |
| Claim–evidence traceability | PASS | CLAIM_EVIDENCE_MATRIX maps C1–C12 to code/experiment/result/stats/figure with limitations; no major claim unsupported. |
| Reproducibility | PASS | Provenance sidecars (commit, config version, node), frozen seeds, unit tests (45), deterministic harness. |
| Limitations | PASS | Explicit in RESULTS_INTERPRETATION, handoff §13, and per-figure/table caveats. |
| C handoff | PASS | C_PUBLICATION_HANDOFF.md complete incl. "claims C must not make". |

## Blockers requiring the investigator (IMO)
1. **Kaggle IEEE-CIS**: create/authenticate Kaggle account and accept the
   `ieee-fraud-detection` competition rules; provide credentials or a local export.
   Do not circumvent Kaggle terms.
2. **NIH ChestX-ray14**: download from the NIH Box release; provide a local path
   (raw images not to be committed).
3. **ISIC**: confirm the exact challenge year/task to freeze (candidate: ISIC 2018
   Task 3 / HAM10000) and provide access.
4. **Secure-aggregation security claim** (optional): decide whether a production
   protocol/library is in scope; if so, author/governance selection needed.
5. **Novelty sign-off + journal confirmation** (author decision).

## Overall
**MERIDIAN STATUS: PARTIAL** — READY-FOR-C on the controlled-evidence contribution
and the full method/analysis pipeline; NOT ready to publish the **grant-dataset**
empirical section until data blockers are cleared and the identical pipeline is re-run.
