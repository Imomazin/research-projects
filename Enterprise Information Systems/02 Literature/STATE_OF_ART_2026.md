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

### Partially trusted robust FL, Computers & Security 2025
*A robust federated learning algorithm for partially trusted environments*.

DOI: https://doi.org/10.1016/j.cose.2024.104161

Implication: trust-aware robust federation is not new in itself. Meridian's participant trust score should initially be treated as a research baseline and orchestration primitive, not the headline novelty.

### Sophon, IEEE TDSC 2025
*Sophon: Byzantine-Robust Federated Learning via Dual Trust Mechanism*.

DOI: https://doi.org/10.1109/TDSC.2025.3577267

Implication: dual trust scoring under IID and non-IID Byzantine conditions is established recent work. P2's trust-aware aggregation requires a differentiated enterprise-system role or new algorithmic mechanism.

### Byzantine-resilient FL under DP, Information Sciences 2026
*Byzantine-resilient federated learning with dynamic scoring matrix and variant PBFT consensus under differential privacy*.

DOI: https://doi.org/10.1016/j.ins.2025.122682

Implication: dynamic trust/scoring, Byzantine resilience and heterogeneous privacy budgets already coexist in recent literature.

### AdaScaleDP, Journal of Systems Architecture 2026
*AdaScaleDP: An adaptive and scale-aware differential privacy aggregation framework for federated learning*.

DOI: https://doi.org/10.1016/j.sysarc.2026.103790

Implication: adaptive noise/privacy allocation cannot be claimed as new at a generic level. P2 must specify exactly what its controller observes, optimises and guarantees.

### ByITFL, 2024 preprint
Xia, Y. et al., *Byzantine-Resilient Secure Aggregation for Federated Learning Without Privacy Compromises*.

Source: https://arxiv.org/abs/2405.08698

Implication: trust-based Byzantine resilience can be embedded in a privacy-preserving secure aggregation design. P2 must not claim the generic compatibility of secure aggregation and trust scoring as novelty.

## Consequence for P2

The initial Meridian additions of median, trimmed mean, trust weighting and adaptive privacy scheduling are **baselines and engineering primitives**, not the scientific novelty claim.

The P2 contribution must survive a stricter novelty test. Candidate directions to investigate before freezing the algorithm include:

1. **Policy-constrained privacy/robustness co-orchestration** for cross-organisational enterprise systems, where privacy allocation and aggregation policy are jointly selected under explicit enterprise risk, audit and operational constraints.
2. **The observability conflict between secure aggregation and reliability scoring**, with a mechanism that preserves useful robustness evidence without exposing raw client updates.
3. **Cross-domain decision rules** that remain auditable across medical imaging and fraud settings instead of being tuned to one benchmark family.
4. **Formal evidence contracts** linking privacy accounting, adversarial robustness, enterprise trust state and reproducible governance artefacts.

No one of these directions is yet declared novel. The next literature pass must test each against 2024-2026 work before the proposed P2 algorithm is frozen.
