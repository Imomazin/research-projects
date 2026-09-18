# C Publication Handoff — P2 / Meridian

Final Meridian → writing-agent (C) handover. C writes the manuscript from this
document and the Evidence Pack. **Do not reconstruct the research; do not exceed
the claims permitted here.**

## 0. Paper identity
- **Grant:** P2, UOWD URC26026 — Privacy-Preserving Federated Intelligence Ecosystems.
- **Platform:** Meridian (`Imomazin/ppdl-cross-org-intelligence`), research branch `research/p2-systems-paper`; this stage's evidence on branch `claude/exciting-pasteur-q1pxdr`.
- **Target journal:** Enterprise Information Systems (per PUBLICATION_STRATEGY.md).
- **Lead author (documented):** Dr Imo Enang. Other authorship/governance = author decision (not set here).

## 1. Title
- **Current working title** (in WORKING_MANUSCRIPT.md): *"Privacy-Preserving Federated Intelligence Ecosystems: An Adaptive Privacy, Trust and Secure Aggregation Architecture for Cross-Organisational Machine Learning."*
- **Problem:** that title foregrounds mechanism combination (adaptive privacy + trust + secure aggregation), which the novelty audit shows is **prior art** (STATE_OF_ART_2026, NOVELTY_MATRIX). Writing to it would overclaim.
- **Recommended title:** *"Federated Assurance Envelopes: Testing Cross-Domain Transferability of Privacy–Robustness Configurations in Regulated Enterprise Machine Learning."*
- **Alternative:** *"When Good Federated Configurations Do Not Transfer: An Evidence-Constrained Assurance Study Across Regulated Domains."*

## 2. Final contribution (frozen)
An **evidence-constrained federated assurance envelope** and an empirical study of
**cross-domain configuration transfer**. Contribution is the decision/constraint
framing and the measured transfer behaviour, **not** any single mechanism.
- Formal assurance contract, domain envelope, cross-domain envelope, transfer
  feasibility vs transfer regret (all implemented and unit-tested).
- Empirical demonstration that within-domain-optimal configurations can be
  **inadmissible after transfer**, asymmetrically, driven by **constraint
  violation** rather than utility loss.

## 3. Closest literature, gap, novelty
- **Closest:** constrained multi-objective FL (arXiv 2305.00312) = within-domain
  feasible region/"protection boundary"; Pareto-front learning for FL (2505.20648);
  federated domain generalization (FedCCRL 2410.11267) = **model** transfer.
- **Gap (residual, defensible):** cross-domain **configuration + evidence-contract**
  admissibility transfer, separating feasibility from regret, with missing evidence
  never a pass and no private client-level diagnostic used to certify feasibility.
- **Novelty statement (allowed):** "We introduce federated assurance envelopes and,
  to our knowledge, provide the first controlled study of cross-domain **configuration**
  admissibility transfer under explicit evidence contracts, distinguishing transfer
  feasibility from transfer regret." Keep the qualifier; the within-domain envelope
  and all mechanisms are prior art.

## 4. Research questions (frozen — NOVELTY_DECISION.md)
RQ1 Pareto-front/utility stability across domains · RQ2 transfer regret & constraint
violation · RQ3 whether an evidence selector yields a smaller cross-domain envelope ·
RQ4 operational cost of cross-domain assurance.

## 5. Conceptual framing & formal definitions
See FINAL_METHODS_SPECIFICATION.md §2 for exact definitions (evidence vector,
contract, evaluation, dominance, Pareto front, domain envelope, cross-domain
envelope, transfer feasibility, transfer regret). Implemented in
`packages/assurance-core/src/assurance.ts`; independently reproduced in Python
(`04 Experiments/p2_assurance_analysis.py`) with identical output.

## 6. Methods, datasets, sample sizes, conditions
- Full method: FINAL_METHODS_SPECIFICATION.md.
- **Datasets used for the completed evidence:** two **synthetic controlled domains**
  (clinical-sim, financial-sim) — see §3 there. **Grant datasets (NIH ChestX-ray14,
  ISIC, IEEE-CIS) are registered but NOT run — blocked on acquisition.**
- **Sample sizes:** 20 frozen seeds per cell; clinical 10 clients×300, financial
  20 clients×200; test sets 1200/2000.
- **Conditions:** heterogeneity {iid,mild,moderate,severe}; aggregation {fedavg,
  fedprox,weighted,median,trimmed-mean,trust-weighted}; privacy {no-dp,static-dp,
  adaptive-dp} × ε{1,3,6,10}; attacks {sign-flip,scale,constant,gaussian} × ρ{0.1,0.2,0.3};
  secure-agg n∈{5..80}.

## 7. Algorithms, privacy/security assumptions
- DP-SGD + RDP accounting (verified vs Python SDK); static vs adaptive (basic composition).
- Adaptive scheduler signals are **pre-declared/public** (round-index functions), not
  private data — required for the accounting to hold.
- Secure aggregation: additive pairwise masking; **honest-but-curious server**, secure
  pairwise channels, secure PRG; **no** dropout recovery, **no** malicious-server/-client
  integrity, **no** production-crypto claim.
- Trust anomaly signal needs per-update visibility → conflicts with full secure
  aggregation (stated tension, measured overhead in E4).

## 8. Statistical procedures
Paired-by-seed; mean/SD/95% CI; Wilcoxon signed-rank; Cohen's d_z; 20 seeds.
`research/results/STATISTICS.json`.

## 9. Canonical results — main numerical findings (with uncertainty)
(Means over 20 seeds; synthetic domains.)
- **Heterogeneity (E1):** FedAvg AUROC iid→severe 0.815→0.769 clinical (p<1e-5, d_z 0.90), 0.740→0.731 financial (d_z 0.99).
- **Robustness (E3):** sign-flip×5 @30%: FedAvg 0.424 vs **median 0.724** (gain +0.299, d_z 2.67); financial gain +0.283 (d_z 3.25). **Trimmed-mean fails (0.415)** once ρ>trim.
- **Privacy (E2):** static-DP frontier ε1→0.760…ε10→0.800. **Adaptive-DP: no benefit and budget overshoot** (nominal ε=6 realises ε≈8.0; static beats adaptive by 0.038, d_z 0.89).
- **MIA (E5):** advantage ≈0.06 (no-DP) → 0.057 (ε6); near-chance regime.
- **Secure agg (E4):** exact reconstruction (error 0); byte overhead 1.38× (n=10) to 12× (n=80); time 7×–40×.
- **Cross-domain (E6/E7) — headline:** clinical feasible 6/12, financial 3/12, **cross-domain envelope = 3/12**. Clinical's best config (`trust-weighted|static-dp@6`) **fails transfer to financial** (ε violation, 6>3.5); financial's best transfers to clinical (pass). Regrets 0.006 / 0.0006 — the binding failure is **feasibility, not regret**.

## 10. Null findings / failure conditions (report, do not bury)
- Adaptive privacy scheduling: no utility gain + budget-feasibility failure at small ε (basic composition).
- MIA near-chance: no measurable DP-driven reduction in this model regime.
- Trimmed-mean: robustness collapses when adversarial fraction exceeds trim fraction.

## 11. Robustness / ablation
The configuration family (agg×privacy) in E6 already acts as an ablation across the
aggregation and privacy axes per domain; E3 ablates aggregation×attack×fraction.
Trust is isolated (trust-weighted vs median vs fedavg). Secure aggregation isolated in E4.

## 12. Figures & tables
FIGURE_REGISTER.md (F2–F9), TABLE_REGISTER.md (T2,T4,T5,T8,T9). Headline: **F8/F9,
T8/T9**. Architecture figure to be drawn by C from Methods §2–§5.

## 13. Limitations (must appear in the paper)
- Logistic-regression model + synthetic domains; external validity to real regulated
  datasets is **untested** (blocked). Do not present synthetic magnitudes as grant results.
- Assurance contracts are hand-specified (explicit, justified) not learned.
- Secure aggregation is an honest-but-curious simulation, not production crypto.
- Adaptive privacy uses basic composition; a tighter adaptive-RDP accountant may change E2.

## 14. Theoretical & enterprise/systems implications
- Enterprise takeaway: **configuration selection must be evidence- and contract-driven
  and re-validated per domain**; a config certified in one regulated domain may be
  inadmissible in another, primarily via hard-constraint violation.
- Systems cost: cross-domain assurance shrinks the admissible set (RQ4) and secure
  aggregation adds cohort-scaling overhead.

## 15. Reproducibility & exact artefact paths
Software repo `Imomazin/ppdl-cross-org-intelligence`, branch `claude/exciting-pasteur-q1pxdr`:
- Harness: `research/harness/` (libs, experiments, tests, `run.mjs`/`test.mjs`).
- Results: `research/results/*.csv|json` (+ `*.provenance.json`, `STATISTICS.json`).
- Figures: `research/figures/F*.png`. Tables: `research/tables/T*.md`.
- Assurance code: `packages/assurance-core/src/assurance.ts`; secure agg `packages/fl-runtime/src/secure-agg.ts`.
- Analysis: `04 Experiments/p2_assurance_analysis.py` (research repo).
Evidence Pack mirror: `Enterprise Information Systems/05 Manuscript/C Evidence Pack/{figures,tables,results}`.

## 16. Claims C MUST NOT make
1. Not novel: combining DP + trust + Byzantine robustness + secure aggregation.
2. Not novel: the within-domain assurance/Pareto envelope (constrained multi-objective FL prior art).
3. No cryptographic/production security for secure aggregation.
4. No claim that synthetic-domain numbers are NIH/ISIC/IEEE-CIS results.
5. No claim adaptive privacy improves the trade-off (evidence: it does not).
6. No large DP-driven MIA reduction claim (baseline ≈ chance).
7. No "first integrated secure+robust+DP framework" claim.

## 17. Readiness
**MERIDIAN STATUS: PARTIAL.** Method frozen, assurance contribution validated
end-to-end on controlled evidence, pipeline/stats/figures/tables complete and
reproducible. Primary **grant-dataset** evidence is blocked on data acquisition.
See PUBLICATION_READINESS_AUDIT.md.
