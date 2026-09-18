# P2 Claim–Evidence Matrix

Maps every major empirical claim to research question, method, code, experiment,
result artefact, statistics, figure/table, limitation and manuscript section.
No major empirical claim is left unsupported. Evidence is **controlled synthetic
simulation** unless a grant-dataset row is later added.

| # | Claim | RQ | Method / code | Experiment | Result artefact | Statistics | Fig/Table | Limitation | MS section |
|---|---|---|---|---|---|---|---|---|---|
| C1 | Heterogeneity significantly reduces federated utility, domain-dependent magnitude | RQ1 | Dirichlet partitioning `domains.ts`; FedAvg `aggregation.ts` | P2-E1 | `P2-E1_baseline.csv` | drop 0.046/0.009; p<1e-5; d_z 0.90/0.99 | F3, T2 | LR model; synthetic | Results §non-IID |
| C2 | Coordinate-wise median and trust-weighted aggregation significantly restore utility under Byzantine attack | Robustness | `aggregation.ts`, `byzantine.ts`, `trust.ts` | P2-E3 | `P2-E3_byzantine.csv` | +0.299/+0.283; p<1e-5; d_z 2.67/3.25 | F4, F5, T5 | controlled attacks; baselines not novel | Results §robustness |
| C3 | Trimmed-mean robustness is bounded by its trim fraction (collapses when ρ>trim) | Robustness | `aggregation.ts` (10% trim) | P2-E3 | `P2-E3_byzantine.csv` | trimmed 0.415 at ρ=0.3 vs median 0.724 | F4, T5 | one trim setting | Results §robustness |
| C4 | Static DP yields a clean monotone privacy–utility frontier | Privacy | DP-SGD `dp.ts`, RDP `rdp.ts` | P2-E2 | `P2-E2_adaptive_privacy.csv` | ε1→0.760 … ε10→0.800 | F2, T4 | LR model | Results §privacy |
| C5 | The implemented adaptive schedule gives no utility benefit over static allocation and overshoots the budget at small ε (negative result) | Privacy | `adaptive-schedule.ts` (basic composition) | P2-E2 | `P2-E2_adaptive_privacy.csv` | static−adaptive@6 = +0.038/+0.019; realized ε 7.6–8.0 vs nominal 1–6; p<1e-5 | T4 | basic composition; adaptive-RDP is future work | Results §privacy; Discussion |
| C6 | Membership-inference is near-chance in this regime; DP preserves privacy at ~no utility cost | Privacy attacks | `mia.ts` confidence-threshold | P2-E5 | `P2-E5_privacy_attacks.csv` | advantage ≈0.06→0.057; AUC≈0.53 | F6 | no memorising model | Results §privacy attacks |
| C7 | Additive-masking secure aggregation is confidentiality-correct with cohort-scaling overhead under an honest-but-curious model | Secure agg | `secure-agg.ts` | P2-E4 | `P2-E4_secure_agg.csv` | max recon error 0; byte overhead 1.38×–12×; time 7×–40× | F7 | HbC only; no dropout/integrity | Methods §secure agg; Results |
| C8 | Secure aggregation removes the per-update signal that median/trust use — a genuine robustness/confidentiality tension | Secure agg × robustness | `secure-agg.ts`, `trust.ts` | conceptual + E4 | provenance note | — | — | qualitative | Discussion |
| C9 | Within-domain-optimal configurations are not guaranteed cross-domain feasible; the evidence selector yields a strictly smaller cross-domain envelope | RQ3 | `assurance.ts` + `p2_assurance_analysis.py` | P2-E6/E7 | `P2-E7_assurance_analysis.json` | clinical 6/12, financial 3/12, envelope 3/12; TS≡Python | F8, T8 | synthetic domains; explicit contracts | Results §cross-domain (headline) |
| C10 | Cross-domain transfer failure is driven primarily by hard constraint violation (feasibility), asymmetric across domains, distinct from utility regret | RQ2 | `auditConfigurationTransfer` | P2-E7 | `P2-E7_transfer.csv` | clinical→financial FAIL (ε viol), financial→clinical PASS; regret 0.006/0.0006 | F9, T9 | small regret magnitudes | Results §transfer (headline); Discussion |
| C11 | The assurance layer never treats missing evidence as a pass and never collapses objectives into a weighted score | Method integrity | `assurance.ts`, unit tests | unit tests | `research/harness/tests/assurance.test.ts` | 45 tests pass; edge cases | — | — | Methods §assurance |
| C12 | Formal assurance definitions match the implementation (two independent implementations agree) | Method integrity | TS core vs Python analysis | P2-E7 | `P2-E7_assurance_analysis.json` vs `P2-E7_python_analysis.json` | identical envelope + transfer | — | — | Methods §assurance |

## Claims C MUST NOT make
- No claim that combining DP + trust + Byzantine robustness + secure aggregation is itself novel (STATE_OF_ART_2026 collisions).
- No cryptographic/production security claim for secure aggregation.
- No claim that synthetic-domain magnitudes are NIH/ISIC/IEEE-CIS results.
- No claim that adaptive privacy scheduling improves the trade-off (evidence says otherwise).
- No claim of a large DP-driven MIA reduction (baseline leakage is ~chance here).
