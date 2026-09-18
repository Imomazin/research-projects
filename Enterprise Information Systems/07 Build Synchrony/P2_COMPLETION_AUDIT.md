# P2 Meridian Completion Audit

Date: 2026-09-18
Auditor stage: final development and empirical-validation (pre-C handoff)
Meridian build branch under evaluation: `research/p2-systems-paper` (+ this stage's work)
Evidence produced on: development branch `claude/exciting-pasteur-q1pxdr`

## Classification legend

`NOT STARTED` · `PARTIAL` · `IMPLEMENTED` · `BUILD VALIDATED` · `DEVELOPMENT TESTED` ·
`CANONICALLY EXPERIMENTED` · `MANUSCRIPT EVIDENCE READY`

All classifications below were verified **from source code and from executed runs**, not from README claims.

## Baseline (inherited Meridian) infrastructure — NOT P2 novelty

| Component | Source | Status |
|---|---|---|
| Logistic-regression FL model + per-sample gradients | `packages/fl-runtime/src/model.ts` | IMPLEMENTED / DEVELOPMENT TESTED |
| DP-SGD (per-sample clip + Gaussian noise) | `packages/fl-runtime/src/dp.ts` | IMPLEMENTED / DEVELOPMENT TESTED |
| RDP accountant + inverse budget planner | `packages/privacy-core/src/{rdp,budget-planner}.ts` | IMPLEMENTED / DEVELOPMENT TESTED (monotonicity + inversion tests added) |
| FedAvg / FedProx / sample-weighted aggregation | `packages/fl-runtime/src/aggregation.ts` | IMPLEMENTED / DEVELOPMENT TESTED |
| Membership-inference (confidence-threshold + shadow) | `packages/attack-lab/src/mia.ts` | IMPLEMENTED / CANONICALLY EXPERIMENTED (E5) |
| Gradient inversion (DLG) | `packages/attack-lab/src/inversion.ts` | IMPLEMENTED (not in canonical matrix; see limitations) |

These are treated as baseline infrastructure. **The prior optimiser / privacy-risk-under-non-IID contribution is NOT recycled as P2 novelty.**

## P2 research additions

| Component | Source | Prior status | Status after this stage |
|---|---|---|---|
| Coordinate-wise median aggregation | `aggregation.ts` | IMPLEMENTED | CANONICALLY EXPERIMENTED (E3) + unit-tested |
| Trimmed-mean aggregation | `aggregation.ts` | IMPLEMENTED | CANONICALLY EXPERIMENTED (E3) + unit-tested |
| Trust scoring + trust-weighted aggregation | `trust.ts`, `aggregation.ts` | IMPLEMENTED | CANONICALLY EXPERIMENTED (E3/E6/E7) + unit-tested |
| Deterministic Byzantine attack harness | `byzantine.ts` | IMPLEMENTED | CANONICALLY EXPERIMENTED (E3) + determinism tests |
| Adaptive per-round privacy schedule | `privacy-core/src/adaptive-schedule.ts` | IMPLEMENTED | CANONICALLY EXPERIMENTED (E2) + budget-conservation tests. **Negative result: dominated by static RDP allocation; overshoots budget at small ε (basic composition).** |
| Assurance-core (contracts, Pareto, envelope, transfer) | `packages/assurance-core/src/assurance.ts` | IMPLEMENTED | MANUSCRIPT EVIDENCE READY (E6/E7) + full edge-case unit tests + Python cross-implementation agreement |
| Python assurance analysis | `04 Experiments/p2_assurance_analysis.py` | IMPLEMENTED | BUILD VALIDATED — produces identical envelope/transfer to the TS core on canonical evidence |
| Secure aggregation (additive pairwise masking) | `packages/fl-runtime/src/secure-agg.ts` (**new this stage**) | NOT STARTED | IMPLEMENTED / CANONICALLY EXPERIMENTED (E4) + correctness tests. Honest-but-curious threat model only; documented limits. |

## Experiments

| ID | Description | Status | Artefact |
|---|---|---|---|
| P2-E1 | Baseline federation landscape (agg × heterogeneity) | CANONICALLY EXPERIMENTED | `research/results/P2-E1_baseline.csv` |
| P2-E2 | Adaptive vs static privacy at matched budget | CANONICALLY EXPERIMENTED (negative result) | `P2-E2_adaptive_privacy.csv` |
| P2-E3 | Byzantine robustness (4 attacks × fractions × agg) | CANONICALLY EXPERIMENTED | `P2-E3_byzantine.csv` |
| P2-E4 | Secure-aggregation overhead + correctness | CANONICALLY EXPERIMENTED | `P2-E4_secure_agg.csv` |
| P2-E5 | Membership-inference vs privacy | CANONICALLY EXPERIMENTED (near-chance regime) | `P2-E5_privacy_attacks.csv` |
| P2-E6 | Cross-domain configuration evidence | CANONICALLY EXPERIMENTED | `P2-E6_evidence.csv` |
| P2-E7 | Assurance envelope + transfer audit | MANUSCRIPT EVIDENCE READY | `P2-E7_assurance_analysis.json`, `P2-E7_transfer.csv` |

**Evidence kind: controlled synthetic simulation on two materially different domains.** This is the primary evidence available now. It is clearly labelled everywhere and is NOT presented as the grant-dataset result.

## Genuine publication blockers requiring the investigator (IMO)

1. **Grant datasets are inaccessible from this environment.** NIH ChestX-ray14 (Box), ISIC (challenge archive) and IEEE-CIS (Kaggle, competition-rules acceptance) all require credentialed/gated download and must not be committed. Canonical experiments on the frozen grant datasets (the primary grant evidence) are **BLOCKED** until data is provisioned. The controlled-simulation pipeline is built to re-run on real data with only the data loader/partitioner swapped.
2. **Secure aggregation cryptographic hardening / dropout recovery.** The implemented additive-masking scheme is confidentiality-correct under honest-but-curious assumptions but is not a production cryptographic protocol (no Shamir dropout recovery, no malicious-server integrity). A production claim needs a vetted library/protocol decision.
3. **Final novelty sign-off + journal confirmation** (author/governance decision).

## What was intentionally NOT done (per instructions)

- PR #34 not merged; default/production branch not modified.
- No fabricated results; the adaptive-privacy negative result and near-chance MIA are reported, not hidden.
- No generic "DP + trust + Byzantine + secure aggregation" novelty claim.
- No cryptographic-security claim from performance testing.
- No restricted datasets or credentials committed.

## Overall

**MERIDIAN STATUS: PARTIAL** — method frozen, assurance contribution validated end-to-end on controlled evidence, full pipeline + statistics + figures + tables complete; blocked only on grant-dataset acquisition for the primary empirical evidence.
