# P2 Novelty Matrix

Structured novelty audit. Complements `STATE_OF_ART_2026.md` (which records the
direct DP+Byzantine+trust+secure-aggregation collisions). This matrix tests the
**specific** remaining direction: cross-domain configuration transfer under an
evidence-constrained assurance envelope. Verified against literature Sept 2026.

Columns: Citation · Year · Venue · Problem · Domain · Method · Overlap with P2 · Difference from P2 · Residual gap.

## A. Mechanism-combination collisions (close the "stacking is novel" door)
See `STATE_OF_ART_2026.md` for full entries. Summary:

| Citation | Year | Overlap with P2 | Difference | Residual gap |
|---|---|---|---|---|
| DP-BREM+ (USENIX Sec) | 2025 | DP + Byzantine + secure agg jointly | single-domain; no cross-domain transfer | transfer feasibility across domains |
| ByzSecAgg (IEEE TIT) | 2025 | robustness under secure agg | crypto scheme, single setting | evidence-contract selection, portability |
| Sophon (IEEE TDSC) | 2025 | dual trust Byzantine-robust FL | trust mechanism, single domain | cross-domain config admissibility |
| FORTRESS-FL / FedJoint | 2026 | adaptive orchestration | runtime controller, single domain | cross-domain evidence envelope |
| PD-FL (SMARTCOMP) | 2026 | policy/governance-driven FL | policy enforcement, single domain | measured cross-domain transfer regret |

**Consequence:** Meridian's median/trimmed/trust/adaptive/secure primitives are
**baselines**, not novelty. Confirmed by our own negative results (adaptive DP no
benefit; MIA near-chance) — we do not claim mechanism novelty.

## B. Multi-objective / Pareto FL collisions (close the "within-domain envelope is novel" door)

| Citation | Year | Venue | Method | Overlap with P2 | Difference from P2 | Residual gap |
|---|---|---|---|---|---|---|
| Optimizing Privacy, Utility & Efficiency in Constrained Multi-Objective FL (arXiv 2305.00312) | 2023 | arXiv | constrained MOO over privacy/utility/efficiency; "boundaries of protection mechanisms" | **within-domain feasible region / protection boundary is essentially our single-domain assurance envelope** | single domain; no transfer analysis; weighted preference vectors | portability of the feasible region across domains |
| Voronoi Pareto-Front Learning for Collaborative FL (arXiv 2505.20648) | 2025 | arXiv/OpenReview | hypernetwork Pareto-front approximation | Pareto-front construction over FL objectives | single distribution; preference-to-solution mapping, not hard evidence contracts | cross-domain Pareto-front **stability** and transfer |
| Performance–Fairness trade-offs in FL (arXiv 2504.21775) | 2025 | arXiv | heterogeneous trade-off learning | multi-objective trade-off surface | fairness axis, single domain | privacy/robustness cross-domain transfer |

**Consequence:** the **within-domain** assurance envelope (feasible region under
hard constraints + Pareto front) overlaps materially with constrained multi-objective
FL and must **not** be claimed as novel.

## C. Cross-domain / domain-generalization FL (test the remaining gap)

| Citation | Year | Method | Overlap with P2 | Difference from P2 | Residual gap |
|---|---|---|---|---|---|
| FedCCRL: Federated Domain Generalization (arXiv 2410.11267) | 2024 | cross-client representation learning for DG | cross-domain FL | generalising a **model** to unseen domains, not transferring a **configuration + its evidence contract** | config-level (not model-level) transfer feasibility |
| FL for Cross-Domain Data Privacy (arXiv 2504.00282) | 2025 | cross-domain privacy-preserving FL | multiple domains + privacy | model transfer / privacy, no assurance-contract admissibility test | evidence-constrained transfer feasibility vs regret |
| FL distorts feature space → OOD performance drop (2025 finding, via robust-FL surveys) | 2025 | empirical OOD degradation | cross-distribution failure | model-performance OOD, not configuration admissibility | configuration feasibility under a target-domain contract |

## Residual gap statement (defensible, narrow)

> No located work poses the **cross-domain admissibility and transfer of a
> federated configuration under an explicit, evidence-constrained assurance
> contract**, separating **transfer feasibility (hard constraint satisfaction)**
> from **transfer regret (utility loss vs best feasible target config)**, and
> requiring that missing evidence never counts as feasible and that no private
> client-level diagnostic is used to certify feasibility.

Adjacent work either (i) builds a within-domain feasible/Pareto region (B), or
(ii) transfers/generalises a **model** across domains (C). P2's contribution is the
**configuration-and-evidence-contract portability** framing plus the empirical
finding that within-domain-optimal configurations can be inadmissible after
transfer, asymmetrically, driven by constraint violation rather than utility loss.

## Novelty gate status

**Provisionally defensible, narrowed.** Before final submission, C should re-run a
targeted search on: "federated configuration transfer", "operating envelope
federated learning", "assurance case federated AI", "constraint satisfaction
transfer cross-silo". If a direct collision on cross-domain *configuration
admissibility transfer* appears, narrow further to the feasibility-vs-regret
distinction and the no-private-diagnostic constraint, which remain the least-covered
elements. Do not overclaim: the mechanisms and the within-domain envelope are prior art.
