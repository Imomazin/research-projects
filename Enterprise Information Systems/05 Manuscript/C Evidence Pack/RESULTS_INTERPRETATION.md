# P2 Results Interpretation (for C)

Working notes, not journal prose. All numbers are mean over 20 frozen seeds on the
**synthetic controlled domains** (clinical-sim, financial-sim). NOT grant-dataset
results. Source: `research/results/` + `STATISTICS.json`.

---

## R1 — Non-IID degrades utility (P2-E1)
- **Question:** RQ1 — how does heterogeneity affect the operating landscape?
- **Result:** FedAvg AUROC falls iid→severe: clinical 0.815→0.769 (drop 0.046), financial 0.740→0.731 (drop 0.009).
- **Uncertainty/robustness:** paired Wilcoxon p<1e-5 both domains; Cohen's d_z 0.90 (clinical), 0.99 (financial). Robust.
- **Interpretation:** heterogeneity is a first-order factor for the healthcare-like domain and secondary for the imbalanced financial-like domain.
- **Can claim:** heterogeneity measurably and significantly reduces utility, with domain-dependent magnitude. **Cannot claim:** any specific magnitude transfers to NIH/ISIC/IEEE-CIS.
- **Limitation:** logistic-regression model; synthetic separability.

## R2 — Robust aggregation defends against Byzantine attacks; trimmed-mean has a known breakdown (P2-E3)
- **Question:** RQ (robustness) — do median/trimmed/trust defend under controlled attacks?
- **Result (sign-flip×5, 30% adversarial, clinical):** FedAvg collapses to 0.424 (below chance), **median 0.724**, trust-weighted 0.665, **trimmed-mean 0.415 (fails)**. Median vs FedAvg gain +0.299 (financial +0.283).
- **Uncertainty:** paired p<1e-5; d_z 2.67 (clinical), 3.25 (financial). Very large, robust.
- **Interpretation:** coordinate-wise median is the strongest single defence here. **Trimmed-mean (10% trim) collapses once adversarial fraction exceeds the trim fraction** — an expected, correct breakdown, not a bug.
- **Can claim:** median and trust-weighted aggregation significantly restore utility under sign-flip; trimmed-mean's guarantee is bounded by its trim fraction. **Cannot claim:** these are novel robustness mechanisms (they are established baselines — see novelty matrix).
- **Limitation:** controlled deterministic attacks; robustness metric = retained AUROC, not certified radius.

## R3 — Static privacy–utility frontier is clean; **adaptive scheduling is a negative result** (P2-E2)
- **Question:** RQ (adaptive privacy) — does adaptive per-round scheduling beat static allocation?
- **Result (clinical):** no-DP 0.801; static-DP ε=1→0.760, ε=3→0.793, ε=6→0.798, ε=10→0.800 (monotone frontier). **Adaptive-DP is flat ≈0.760 and, critically, overshoots its budget: nominal ε=1 realises ε≈7.6, nominal ε=6 realises ε≈8.0.** Static beats adaptive at ε=6 by 0.038 (clinical, d_z 0.89, p<1e-5) and 0.019 (financial, d_z 1.31).
- **Uncertainty:** significant and moderate-to-large effect. Robust.
- **Interpretation:** under its declared **conservative basic-composition** accounting, the adaptive scheduler cannot achieve small per-round ε over many rounds within the bounded noise search, so realized privacy loss **exceeds** the nominal budget and utility never improves on static RDP allocation.
- **Can claim:** the implemented adaptive schedule provides **no utility benefit** over static RDP allocation and has a **budget-feasibility failure mode** at small ε / many rounds. This is honest evidence *against* treating "adaptive privacy" as a contribution. **Cannot claim:** adaptive privacy improves the privacy–utility trade-off.
- **Limitation:** a tighter adaptive-RDP accountant (rather than basic composition) is future work and might change this; the current code uses basic composition by design.

## R4 — Membership inference is near-chance in this regime (P2-E5)
- **Question:** RQ (privacy attacks) — does DP reduce MIA success, and how much leakage exists?
- **Result:** MIA advantage ≈0.06 with no DP and ≈0.057 at ε=6 (clinical); AUC ≈0.53 throughout.
- **Uncertainty:** CIs straddle near-chance; no significant DP effect because there is almost no leakage to remove.
- **Interpretation:** a well-regularised logistic model with abundant data and label noise barely memorises members, so confidence-threshold MIA is near chance regardless of DP. DP holds MIA at chance essentially "for free" (≤0.3% utility cost at ε≥6).
- **Can claim:** in this regime privacy leakage via MIA is negligible and DP preserves it at chance without meaningful utility cost. **Cannot claim:** DP produces a large MIA reduction (it cannot, because baseline leakage is already ~chance).
- **Limitation:** demonstrating a DP-driven MIA reduction needs a memorising architecture (deep model) on the grant datasets — **blocked**.

## R5 — Secure-aggregation overhead is well-characterised; it trades off against robustness observability (P2-E4)
- **Result:** additive masking reconstructs the exact aggregate (max error 0). Byte overhead scales ~linearly with client count (n=10 → 1.38× payload, n=20 → 2.92×; masks are O(n²), payload O(n)). Wall-time overhead 7× (n=10) to 15× (n=20) in this in-process simulation.
- **Interpretation:** confidentiality is exact under the stated honest-but-curious model; cost grows with cohort size. Because masking hides individual updates, it removes the per-update signal median/trimmed/trust rely on — a genuine tension.
- **Can claim:** correct confidentiality-preserving aggregation with quantified, cohort-scaling overhead, under an explicit threat model. **Cannot claim:** cryptographic production security, dropout tolerance, or integrity against a malicious server.
- **Limitation:** simulation PRG/channels; O(n²) pairwise masks; no Shamir dropout recovery.

## R6 — Cross-domain configuration transfer fails asymmetrically (P2-E6/E7) — **headline**
- **Question:** RQ2/RQ3 — do domain-optimal configurations remain feasible across domains?
- **Result:**
  - Per-domain feasibility differs sharply: **clinical 6/12 feasible, financial 3/12** (financial's stricter robustness ≥0.70 and ε≤3.5 prune most configs).
  - **Cross-domain envelope = 3/12** configs feasible in both: `median|no-dp`, `trust-weighted|no-dp`, `trust-weighted|static-dp@3`.
  - **Transfer asymmetry:** clinical's best feasible config `trust-weighted|static-dp@6` **fails when transferred to financial** — an **ε constraint violation** (6 > 3.5), transfer regret 0.006. The financial best `trust-weighted|no-dp` **transfers successfully to clinical** (pass, regret 0.0006).
  - TS assurance-core and the independent Python analysis agree exactly.
- **Interpretation:** a configuration selected as optimal under a permissive (healthcare) contract can be **inadmissible** under a stricter (financial) contract, while the conservative choice ports upward. The binding failure is a **hard constraint violation (feasibility), distinct from utility regret** — supporting the RQ2/RQ3 separation of *feasibility* from *regret*.
- **Can claim:** within-domain-optimal configurations are **not** guaranteed cross-domain feasible; the evidence-constrained selector identifies a strictly smaller cross-domain envelope; transfer failure is driven primarily by constraint violation, not utility loss. **Cannot claim:** external validity to real regulated datasets (blocked); the specific 3/12 envelope is dataset/contract-specific.
- **Limitation:** synthetic domains and hand-specified (but explicit, justified) contracts; utility-regret magnitudes are small here because the configs' utilities are close — the *feasibility* result is the robust one.

---

## Cross-cutting honesty notes
- Two results are negative/null (R3 adaptive privacy, R4 MIA). They are reported, not hidden, and they *strengthen* the paper's thesis that stacking mechanisms is not automatically beneficial and that configurations must be selected on measured evidence.
- No result uses development smoke runs; all use the frozen 20-seed canonical config.
- The primary grant-dataset evidence is **not yet produced** (data blocked).
