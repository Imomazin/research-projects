# P2 Final Methods Specification (for C)

This specifies the frozen method exactly as implemented and run. Every definition
maps to code in `Imomazin/ppdl-cross-org-intelligence`. C should write the Methods
section from this document, not from memory or from README prose.

> **Evidence scope.** The completed canonical experiments are **controlled
> synthetic-simulation** studies on two materially different domains. The frozen
> grant datasets (NIH ChestX-ray14, ISIC, IEEE-CIS) are **not yet run** — data
> acquisition is a blocker (see PUBLICATION_READINESS_AUDIT). The pipeline is
> built to re-run unchanged on grant data once the loader/partitioner is swapped.

## 1. Research design

Cross-silo federated learning studied as an **enterprise assurance** problem. The
unit of analysis is the *portability of a federated configuration and its evidence
contract across materially different regulated domains*, not a single
privacy–utility curve per dataset. Design is factorial and fully seeded.

Research questions (from `01 Research Design/NOVELTY_DECISION.md`):
- **RQ1** Pareto-front stability of privacy/robustness/utility across domains.
- **RQ2** Transfer regret and constraint violation when a source-domain config is reused in a target domain.
- **RQ3** Whether an evidence-constrained selector identifies a smaller cross-domain feasible envelope.
- **RQ4** Operational cost of requiring cross-domain assurance vs domain-specific tuning.

## 2. Formal definitions (implemented in `packages/assurance-core/src/assurance.ts`)

- **Federated evidence** `M(c,d) = (utility↑, robustness↑, ε↓, runtimeMs↓, communicationBytes↓, evidenceComplete∈{T,F})` for configuration `c` in domain `d`. Directions are fixed; no metric is reweighted.
- **Assurance contract** `A(d)`: hard admissibility constraints `minUtility, minRobustness, maxEpsilon, maxRuntimeMs, maxCommunicationBytes, requireCompleteEvidence`. Constraints are **strict-inequality boundaries admissible** (equality passes). Missing required evidence is a violation, never a silent pass.
- **Assurance evaluation** `evaluateAssurance(M,A)` → pass iff no violation.
- **Pareto dominance** `a ≻ b` iff `a` is no worse on every objective and strictly better on ≥1 (objective directions above). **Pareto front** = non-dominated set.
- **Domain assurance envelope** `E(d) = { c : evaluateAssurance(M(c,d), A(d)).pass }`.
- **Cross-domain assurance envelope** `⋂_d E(d)`; a config with missing evidence in any requested domain is excluded.
- **Configuration transfer** `A→B`: evaluate source-selected `c` under `A(B)`. Reports `targetEvidencePresent`, `targetAssurancePass`, `targetViolations`, **transfer regret** = `max(0, U*_B − U_B(c))` where `U*_B` is the best utility among **target-feasible** configs (null if none feasible), and `targetParetoEfficient`.

The Python analysis `04 Experiments/p2_assurance_analysis.py` reimplements these and
produces **identical** envelope and transfer results on the canonical evidence
(cross-implementation verification).

## 3. Model, data, federation

- **Model** logistic regression `σ(w·x + b)`; real per-sample BCE gradients (`fl-runtime/src/model.ts`).
- **Synthetic domains** (`research/harness/lib/domains.ts`):
  - `clinical-sim`: dim 8, 4 Gaussian clusters, balanced (~0.45 positive), 10 clients × 300 samples, label-flip Bayes noise 0.12.
  - `financial-sim`: dim 12, 6 clusters, imbalanced (~0.12 positive), 20 clients × 200 samples, label-flip noise 0.10.
  - Materially different in feature geometry, class balance, client count and separability.
- **Heterogeneity** standard Dirichlet cluster partitioning (Hsu et al. 2019). Frozen α: iid=100, mild=1.0, moderate=0.3, severe=0.1. Fully reproducible from (domain, level, seed, nClients).
- **Held-out test set** drawn from population prevalence, seed-shifted, never used in training.

## 4. Privacy mechanism and accounting

- **DP-SGD** per-sample L2 clip C, Gaussian noise σ·C/B (`fl-runtime/src/dp.ts`).
- **RDP accountant** sub-sampled Gaussian, α-grid, RDP→(ε,δ) conversion (`privacy-core/src/rdp.ts`); **inverse planner** bisects σ to hit ε (`budget-planner.ts`). Verified bit-identical to the Python SDK by `scripts/python-parity.mjs`.
- **Static-DP**: one σ achieving total ε over all rounds under RDP composition.
- **Adaptive-DP** (`privacy-core/src/adaptive-schedule.ts`): per-round ε allocation under **conservative basic composition** (∑ε_r = ε_total), σ_r planned per round. **Scheduler signals are pre-declared/public functions of round index only** (utility-gap decreasing, privacy-risk increasing, heterogeneity constant per level) — they are NOT derived from private client data, preserving the basic-composition accounting claim. This is stated because feeding private statistics into the scheduler would invalidate the guarantee.

## 5. Trust, attacks, aggregation, secure aggregation

- **Trust** bounded EWMA update in [0,1] from anomaly/validation/violation evidence (`fl-runtime/src/trust.ts`); multiplier in [floor,1]. In experiments the anomaly signal is the server-observable L2 distance from the coordinate-wise median. **This requires per-update visibility and therefore conflicts with full secure aggregation** — the interaction is explicit and measured (§ secure agg, E4).
- **Byzantine harness** deterministic transforms (`byzantine.ts`): sign-flip(×s), scale(×f), constant(v), seeded Gaussian(σ,seed). Applied to a seed-frozen malicious client set at fraction ρ.
- **Aggregation** (`aggregation.ts`): FedAvg, FedProx (server-identical), sample-weighted, coordinate-wise median, coordinate-wise 10% trimmed mean, trust-weighted (sample × trust multiplier). Shape-validated; deterministic.
- **Secure aggregation** (`fl-runtime/src/secure-agg.ts`, new): additive pairwise masking (confidentiality core of Bonawitz et al. 2017). Masks cancel in the sum → exact aggregate; individual updates hidden from an honest-but-curious server. **Guarantees:** input privacy under honest-but-curious server + secure pairwise channels + secure PRG; exact sum correctness. **Not guaranteed (must not be claimed):** dropout recovery, malicious-server/-client integrity, production cryptographic security. Composed with (not a substitute for) robust aggregation.

## 6. Experiments (frozen config `research/harness/lib/config.ts`, `CONFIG_VERSION=p2-canonical-1.0.0`)

Fixed: 40 rounds, 1 local epoch, batch 32, lr 0.2, full participation, clip 1.0, δ=1e-5, **20 frozen seeds**.

| ID | Factors | Primary outcomes |
|---|---|---|
| P2-E1 | agg {6} × heterogeneity {4} × domain {2} | AUROC, worst-client AUROC, dispersion, convergence, runtime, comm |
| P2-E2 | privacy {no-dp, static, adaptive} × ε {1,3,6,10} × domain | AUROC, realized ε spent, convergence |
| P2-E3 | agg {fedavg,median,trimmed,trust} × attack {4} × ρ {0.1,0.2,0.3} × domain | clean/attacked AUROC, degradation, worst-client |
| P2-E4 | n_clients {5..80} × dim {9,13} | mask/payload byte ratio, time overhead, reconstruction error |
| P2-E5 | privacy {no-dp, static ε∈{1,3,6,10}} × domain | MIA AUC, advantage, attack accuracy |
| P2-E6 | config family (agg{4} × privacy{3}) × domain | utility, robustness (retained AUROC under sign-flip×5 @20%), ε, runtime, comm |
| P2-E7 | assurance analysis over E6 evidence | per-domain feasibility, Pareto front, cross-domain envelope, transfer audit |

## 7. Statistics

Paired by seed. Central tendency + SD + 95% CI (t-based). Paired comparisons via
Wilcoxon signed-rank (scipy), effect size Cohen's d_z. 20 seeds per cell. Significance
is reported alongside magnitude; it is not treated as the sole importance criterion.
Outputs: `research/results/STATISTICS.json`.

## 8. Software environment & reproducibility

- Node 22 (native TS type-stripping), esbuild bundler for harness (`research/harness/run.mjs`, `test.mjs`).
- Python 3.11 + numpy/scipy/matplotlib for statistics and figures.
- Every result CSV has a sibling `*.provenance.json` (experiment id, `CONFIG_VERSION`, git commit, node version, timestamp, evidence-kind, grant-dataset=NOT-USED).
- Reproduce: run the seven driver scripts under `research/harness/experiments/`, then `research/analysis/stats.py` and `figures.py`. Unit tests: `research/harness/tests/` (45 tests).
