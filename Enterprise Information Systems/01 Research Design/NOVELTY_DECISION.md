# P2 Provisional Novelty Decision

## Decision status

**Provisional, not yet a novelty claim.**

The September 2026 literature audit closes several broad claims that would be unsafe to make. Secure aggregation plus Byzantine robustness, adaptive privacy, trust-aware aggregation, policy-driven FL, multi-objective FL and adaptive orchestration all have substantial recent prior art.

P2 will therefore not compete by stacking known mechanisms and calling the stack novel.

## Strongest remaining research direction

The paper will test a narrower enterprise-systems problem:

> **Are privacy/robustness configurations that appear Pareto-efficient in one regulated federated domain transferable to another, and can an evidence-constrained assurance layer identify configurations that remain feasible across domains without relying on private client-level diagnostics?**

This preserves every funded mechanism but changes the scientific burden. Meridian becomes the experimental system used to expose and manage configuration failure across domains.

## Working construct: Federated Assurance Envelope

Let a federated configuration `c` specify the mechanisms that can materially change system behaviour, for example:

- aggregation rule
- privacy schedule and total privacy budget
- clipping/noise settings
- secure aggregation state
- trust/reliability mechanism
- participation rule
- adversarial operating condition

For domain `d`, the system produces an evidence vector `M(c,d)` containing utility, privacy, robustness, convergence, communication and runtime measures.

A domain-specific assurance contract `A(d)` defines hard admissibility constraints such as:

- maximum privacy loss
- minimum task utility
- minimum attack resilience
- maximum runtime or communication cost
- required reproducibility/evidence completeness

The **assurance envelope** for domain `d` is the set of configurations satisfying `A(d)`. A cross-domain assurance envelope is the intersection of admissible configurations across the selected domains.

## Transferability test

The paper will distinguish three ideas:

1. **Within-domain optimality**: whether a configuration is Pareto-efficient within one domain.
2. **Cross-domain feasibility**: whether the same configuration remains inside the assurance envelope of another domain.
3. **Transfer regret**: the loss in objective quality and/or constraint violations incurred when a configuration selected in domain A is deployed in domain B.

This is materially different from reporting one privacy-utility curve per dataset. The unit of analysis is the portability of an enterprise FL configuration and its evidence contract.

## Revised research questions for testing

**RQ1.** How stable are privacy, robustness and utility Pareto fronts across healthcare and financial federated settings under matched federation protocols?

**RQ2.** How much transfer regret and constraint violation occurs when a configuration selected in one domain is reused in the other?

**RQ3.** Can an evidence-constrained configuration selector identify a smaller cross-domain assurance envelope that remains feasible across both settings?

**RQ4.** What operational cost is introduced by requiring cross-domain assurance compared with domain-specific tuning?

## Build implication

Meridian requires an assurance layer that consumes generated experiment evidence and reports:

- hard constraint pass/fail
- Pareto dominance status
- domain-specific feasible sets
- cross-domain feasible intersection
- evidence completeness
- configuration provenance

This layer is a research/assurance component. It must not manufacture evidence or infer metrics that were not measured.

## Relationship to the funded compliance twin

The grant's synthetic compliance twin can be implemented as the product-facing representation of the assurance evidence. The twin should replay versioned configurations and measured outcomes against declared constraints. It should not be presented as a legal-compliance oracle.

## Novelty gate still open

Before the manuscript makes any novelty statement, the literature review must specifically test:

- cross-dataset/domain transfer of FL security/privacy configurations
- configuration portability in cross-silo FL
- Pareto-front stability across domains
- assurance envelopes / operating envelopes for federated AI
- evidence-based configuration selection under privacy and robustness constraints

If direct prior work is found, the contribution will be narrowed again before results are interpreted.
