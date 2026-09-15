# P2 State of the Art and Novelty Gate, September 2026

This file records literature that directly constrains what P2 may claim as novel. It is a living research-control document, not the final literature review.

## Direct novelty collisions

### BOBA, AISTATS 2024
Bao, W., Wu, J. and He, J. (2024), *BOBA: Byzantine-Robust Federated Learning with Label Skewness*, PMLR 238:892-900.

Source: https://proceedings.mlr.press/v238/bao24a.html

Implication: Byzantine robustness under realistic non-IID label skew is already a strong research line. P2 cannot claim that combining non-IID federation with Byzantine robustness is itself novel.

### Noise-Aware Heterogeneous DP-FL, ICML 2024
Malekmohammadi, S., Yu, Y. and Cao, Y. (2024), *Noise-Aware Algorithm for Heterogeneous Differentially Private Federated Learning*, PMLR 235:34461-34498.

Source: https://proceedings.mlr.press/v235/malekmohammadi24a.html

Implication: heterogeneous privacy requirements/noise and aggregation weighting are already treated theoretically. P2 must distinguish its adaptive privacy mechanism from client-heterogeneous DP weighting.

### SAMFL, Journal of Systems Architecture 2024
*Secure Aggregation Mechanism for Federated Learning with Byzantine-robustness by functional encryption*.

DOI: https://doi.org/10.1016/j.sysarc.2024.103304

Implication: secure aggregation plus Byzantine robustness plus differential privacy has already been integrated cryptographically. P2 cannot use the phrase 'first integrated secure + robust + DP federated framework' without much narrower evidence.

### ByITFL, 2024/2025
Xia, Y. et al., *Byzantine-Resilient Secure Aggregation for Federated Learning Without Privacy Compromises*.

Source: https://arxiv.org/abs/2405.08698

Implication: privacy-preserving trust-score computation has already been designed around FLTrust using coded computation, verifiable secret sharing and re-randomisation. Generic compatibility of secure aggregation and trust scoring is not novel.

### Partially trusted robust FL, Computers & Security 2025
*A robust federated learning algorithm for partially trusted environments*.

DOI: https://doi.org/10.1016/j.cose.2024.104161

Implication: trust-aware robust federation is not new in itself. Meridian's participant trust score should initially be treated as a research baseline and orchestration primitive, not the headline novelty.

### Sophon, IEEE TDSC 2025
*Sophon: Byzantine-Robust Federated Learning via Dual Trust Mechanism*.

DOI: https://doi.org/10.1109/TDSC.2025.3577267

Implication: dual trust scoring under IID and non-IID Byzantine conditions is established recent work. P2's trust-aware aggregation requires a differentiated enterprise-system role or new algorithmic mechanism.

### ByzSecAgg, IEEE Transactions on Information Theory 2025
Jahani-Nezhad, T., Maddah-Ali, M.A. and Caire, G. (2025), *ByzSecAgg: A Byzantine-Resistant Secure Aggregation Scheme for Federated Learning Based on Coded Computing and Vector Commitment*, 71(8):6410-6424.

DOI: https://doi.org/10.1109/TIT.2025.3577019

Implication: the privacy-versus-robustness observability problem is directly addressed using secure computation of pairwise distances and vector commitments. P2 cannot claim that detecting malicious clients while hiding individual updates is an unaddressed problem.

### FedGT, IEEE TIFS 2025
*FedGT: Identification of Malicious Clients in Federated Learning with Secure Aggregation*.

DOI: https://doi.org/10.1109/TIFS.2025.3539964

Implication: overlapping secure groups can already trade privacy against malicious-client identification in cross-silo settings. Group-level observability is therefore an established design family.

### DP-BREM+, USENIX Security 2025
Gu, X., Li, M. and Xiong, L. (2025), *DP-BREM: Differentially-Private and Byzantine-Robust Federated Learning with Client Momentum*.

Source: https://www.usenix.org/conference/usenixsecurity25/presentation/gu-xiaolan

Implication: differential privacy, Byzantine robustness and secure aggregation without a trusted server have already been jointly treated with theoretical and empirical guarantees.

### Byzantine-resilient FL under DP, Information Sciences 2026
*Byzantine-resilient federated learning with dynamic scoring matrix and variant PBFT consensus under differential privacy*.

DOI: https://doi.org/10.1016/j.ins.2025.122682

Implication: dynamic trust/scoring, Byzantine resilience and heterogeneous privacy budgets already coexist in recent literature.

### AdaScaleDP, Journal of Systems Architecture 2026
*AdaScaleDP: An adaptive and scale-aware differential privacy aggregation framework for federated learning*.

DOI: https://doi.org/10.1016/j.sysarc.2026.103790

Implication: adaptive noise/privacy allocation cannot be claimed as new at a generic level. P2 must specify exactly what its controller observes, optimises and guarantees.

### FORTRESS-FL, Array 2026
*FORTRESS-FL: Byzantine-robust and privacy-preserving federated orchestration for next-generation networks*.

DOI: https://doi.org/10.1016/j.array.2026.100680

Implication: privacy-preserving orchestration with adaptive DP, reputation and Byzantine detection is already a current research theme. Generic 'adaptive orchestration' is not a sufficient novelty claim.

### FedJoint, Information and Software Technology 2026
*FedJoint: A software architecture for adaptive orchestration in federated learning systems*.

DOI: https://doi.org/10.1016/j.infsof.2026.108177

Implication: coupled runtime FL orchestration has already been framed explicitly as a software-architecture problem and optimised with a DRL controller.

### Policy-Driven Federated Learning, IEEE SMARTCOMP Companion 2026
Ranathunga, T., Bharti, S. and McGibney, A. (2026), *Policy-Driven Federated Learning: Operationalising Governance, Trust, and Compliance in Cross-Organisational AI*.

DOI: https://doi.org/10.1109/SmartComp-Companion70724.2026.00041

Implication: machine-readable governance policies, policy enforcement and observability in cross-organisational FL already exist as a published framework. Policy-driven FL alone is not sufficient novelty.

### SA-FL, IEEE TCCN 2026
*SA-FL: Secure Aggregation Scheme in Federated Learning Against Poisoning Attacks*.

DOI: https://doi.org/10.1109/TCCN.2026.3656284

Implication: the fact that secure aggregation obscures anomaly detection is explicitly recognised and a privacy-preserving poisoning-detection mechanism is already proposed.

### EPRA-VFL, Journal of Parallel and Distributed Computing 2026
*EPRA-VFL: A privacy-preserving and efficient verifiable federated learning scheme with robust aggregation*.

DOI: https://doi.org/10.1016/j.jpdc.2026.105266

Implication: verifiability, privacy protection, client-quality evaluation and robust aggregation are also converging in current systems literature.

## Consequence for P2

The initial Meridian additions of median, trimmed mean, trust weighting, deterministic attack fixtures and adaptive privacy scheduling are **baselines and engineering primitives**, not the scientific novelty claim.

Two initially attractive novelty directions are now closed:

1. 'secure aggregation while still identifying malicious clients' is already covered by ByzSecAgg, FedGT, ByITFL, SA-FL and related work;
2. 'policy-driven or adaptive FL orchestration' is already covered by FedJoint, FORTRESS-FL and PD-FL.

P2 must therefore be narrower and more defensible. The strongest remaining direction to test is an **enterprise evidence-constrained co-orchestration problem** in which privacy, robustness and participation decisions are selected under a formally declared evidence contract and cross-domain constraints, with the scientific contribution residing in the decision rule, constraint formulation and validated systems trade-off rather than in merely combining existing mechanisms.

Candidate research question for the next novelty pass:

> Can a federated enterprise controller select privacy and robustness configurations that remain Pareto-efficient and auditable across materially different cross-organisational domains, without using private client-level diagnostics that invalidate the stated privacy model?

This candidate is **not yet declared novel**. Before freezing an algorithm, the next search must test multi-objective/Pareto FL controllers, constrained online policy selection and audit/evidence-aware federated orchestration from 2024-2026.
