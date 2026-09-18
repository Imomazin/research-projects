# P3 Publication Readiness Audit

Date 2026-09-18. Status vocabulary: **PASS** / **PARTIAL** / **BLOCKED**. Every PARTIAL/BLOCKED
item states the exact gap. No numerical grades. Provenance: research `@ c022fba`, Orbit `@ 559a262`.

| Item | Status | Basis / exact gap |
|---|---|---|
| Novelty | PARTIAL | Residual novelty is the integrated evidence-chain + software synchrony (handoff §B), checked against `STATE_OF_ART_2026.md`. Gap: individual components are not novel; C must frame around the chain, not the parts. |
| Research gap | PASS | Stated and literature-anchored (handoff §C). |
| Research questions | PASS | RQ1–RQ5 finalised and each mapped to an executed experiment. |
| Conceptual framing | PASS | Constructs specified (handoff §E); restrained by design. |
| Causal graph | PASS | Contracts + validation (duplicate/unknown/self/forbidden/temporal/cycle); tested. |
| Identification | PASS | Backdoor d-separation engine; refuses when not identified; post-treatment adjustment rejected; unit-tested. Scope limited to backdoor (documented, not general do-calculus). |
| Estimators | PASS | DIM, g-formula, IPW(Hájek), AIPW; AIPW math verified; reference tests pass. |
| Nuisance models | PASS | Logistic/linear + GBM; transparent-first. |
| Cross-fitting | PASS | K=5 StratifiedKFold, out-of-fold predictions, seeded; single-class-fold handling. |
| Diagnostics | PASS | Overlap (min/max propensity, ESS, extreme weights), SMD balance (unadjusted + weighted). |
| HTE / uplift | PARTIAL | T-learner CATE + PEHE/rank/decile/Qini/policy value implemented and evaluated on known truth (E2) and journeys (E1). Gap: only one HTE learner exercised at scale; no DR-learner/causal-forest comparison. |
| Counterfactual attribution | PASS | Per-channel AIPW incremental effect vs heuristic baselines (E1); not forced to sum to revenue. |
| Budget optimisation | PASS | Exact multiple-choice knapsack; optimality unit-tested; E5 decision experiment. |
| Decision policy / abstention | PASS | Evidence-quality + significance gates; abstention tested. |
| Semi-synthetic validation | PASS | P3-E2 canonical (100 seeds × 5 conditions); recovery + failure region. |
| Randomized validation | PARTIAL | Pipeline correct and validated on a schema-exact randomized fixture (E3). Gap: canonical Criteo uplift run not executed — **network policy blocks** `criteostorage.blob.core.windows.net`. |
| Observational application | PARTIAL | Methodology executed on semi-synthetic observational journeys (E1). Gap: Criteo Attribution real-data run blocked by network policy. |
| Sensitivity analysis | PASS | P3-E6 canonical (confounding, prevalence, noise, HTE, n, unmeasured confounding, measurement error, selection, placebo). |
| External validity | BLOCKED | UCI Online Retail unreachable (`archive.ics.uci.edu` 403 at proxy); acquisition script ready. |
| Data provenance | PASS | Per-result provenance blocks (git SHA, versions, config hash, seed); dataset manifest + acquisition status. |
| Statistics | PASS | Repeated seeds; bias/RMSE/SD/SE/coverage; regret; not p-value-driven. |
| Figures | PASS | F1–F9 regenerable from results (register). |
| Tables | PASS | T1–T5 regenerable from results (register). |
| Claim-evidence traceability | PASS | `CLAIM_EVIDENCE_MATRIX.md` (7 claims fully mapped). |
| Reproducibility | PASS | Configs + scripts + provenance; Orbit `npm test` (32) + typecheck. |
| Limitations | PASS | Handoff §M + assumption register + null/failure sections. |
| C handoff | PASS | `C_PUBLICATION_HANDOFF.md` (A–Q) + evidence pack complete. |

## Overall
**PARTIAL — ready for C to write the empirical core now.** The known-truth programme (RQ1–RQ5)
is complete, validated and reproducible, and the randomized pipeline is validated on a fixture.
The only gaps are **real-data canonical runs** (Criteo E3/E4, UCI E7), which are **blocked by the
environment network policy**, not by method or compute. Governance decision for the author team:
write the empirical core now with real-data validation marked available-on-access, or run E3/E4/E7
from a network that permits those hosts before submission if the target journal requires the
randomized real-data result in-paper.
