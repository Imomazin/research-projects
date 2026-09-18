# P3 Causal Assumption Register

For every causal analysis: treatment, outcome, estimand, target population, DAG, adjustment
set, and the four core assumptions plus diagnostics and known threats. This exists to stop C
overstating causality. Descriptive attribution rows are included to mark what is **not** causal.

Legend for assumption support: **by design** (guaranteed, e.g., randomization/known DGP) ·
**stated** (assumed, checkable diagnostics only) · **violated-on-purpose** (stress condition).

---

## A. P3-E2 / P3-E6 — Semi-synthetic known-truth

- **Treatment:** binary exposure T (simulated). **Outcome:** Y (continuous/binary, simulated).
- **Estimand:** ATE = E[Y(1)−Y(0)]; CATE(x). **Population:** the generated sample.
- **DAG:** X → T, X → Y, T → Y (X a measured confounder vector); optional hidden U → T,Y.
- **Adjustment set:** full observed X.
- Exchangeability: **by design** when all confounders observed; **violated-on-purpose** in E6
  (hidden covariates) to quantify unmeasured-confounding bias.
- Positivity: **by design**, degrades as confounding grows (min propensity → 0.01; diagnosed).
- Consistency/SUTVA: **by design** (no interference in the DGP).
- Measurement: **by design**; **violated-on-purpose** in E6 (covariate measurement error).
- Selection: none by default; **violated-on-purpose** in E6 (collider selection).
- **Diagnostics:** overlap (min/max propensity, ESS, extreme weights), SMD balance, CI coverage
  vs known truth. **Known threats:** documented failure regions (see RESULTS_INTERPRETATION).

## B. P3-E1 / P3-E4 — Observational causal attribution (semi-synthetic journeys)

- **Treatment:** exposed-to-channel-c (per channel). **Outcome:** conversion.
- **Estimand:** ATE of exposure on conversion. **Population:** simulated journey population.
- **DAG:** latent interest z → conversion and z → retargeting exposure (confounding); channel
  exposures → conversion; retargeting is post-interest and fires last.
- **Adjustment set:** observed pre-exposure covariates (including z); other channels are **not**
  adjusted for (potential colliders/mediators via z).
- Exchangeability: **stated** — holds in the DGP because z is observed; in real data it would be
  an assumption, not a fact. Label all E1/E4 estimates "observational under stated assumptions."
- Positivity: **stated**, satisfied (retargeting propensity in ~[0.05,0.95]); diagnosable.
- Consistency/SUTVA: **stated** (no cross-user interference modelled).
- Temporal: exposures precede conversion; retargeting recency encoded.
- **Known threats:** if a real confounder of exposure and conversion is unobserved, E1/E4
  estimates are biased (quantified generically by E6). Heuristic attribution rows in E1 are
  **descriptive, not causal**.

## C. P3-E3 — Randomized validation (Criteo uplift; fixture-validated)

- **Treatment:** randomized advertising exposure. **Outcome:** visit; conversion.
- **Estimand:** ATE within the released benchmark distribution.
- **DAG:** T ⟂ X by randomization; T → Y.
- **Adjustment set:** none required for identification; outcome models used only for efficiency.
- Exchangeability: **by design** (randomized assignment); propensity = empirical randomization
  rate, not modelled.
- Positivity: **by design**. Consistency/SUTVA: **stated**. 
- **Known threats / caveat:** the public release is privacy-subsampled; its effect magnitude is
  **not** the platform's original commercial incrementality (documented). Canonical run pending
  data access; only the fixture (synthetic) has been executed here.

## D. P3-E7 — External validity (UCI Online Retail)

- Transactional data with **no randomized marketing exposure** → **cannot identify** channel
  treatment effects on its own. Use for revenue/customer structure and operational-architecture
  external checks or semi-synthetic overlays only. No standalone causal claim. Run blocked by
  network policy.

## E. Descriptive attribution (heuristic baselines) — NOT causal

first/last/linear/time-decay/weighted attribution answer "which observed touchpoints receive
credit," a descriptive accounting question. **No exchangeability/positivity/consistency claim
applies or is made.** They are the non-causal comparison baseline only.
