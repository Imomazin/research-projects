# P3 State of the Art and Novelty Gate, September 2026

This file records literature that directly constrains P3's novelty claims. It is a research-control document, not the final literature review.

## Core attribution and causal-measurement anchors

### Berman, Marketing Science 2018
Berman, R. (2018), *Beyond the Last Touch: Attribution in Online Advertising*, Marketing Science 37(5):771-792.

DOI: https://doi.org/10.1287/mksc.2018.1104

Implication: sophisticated attribution and the inefficiency of last-touch credit have strong theoretical foundations. P3 cannot frame 'moving beyond last touch' as new.

### Li, Kannan, Viswanathan and Pani, Marketing Science 2016
*Attribution Strategies and Return on Keyword Investment in Paid Search Advertising*.

DOI: https://doi.org/10.1287/mksc.2016.0987

Implication: attribution rules are already linked to downstream bidding and budget allocation. P3 must demonstrate causal decision value, not simply a new credit allocation rule.

### Gordon et al., Marketing Science 2019
*A Comparison of Approaches to Advertising Measurement: Evidence from Big Field Experiments at Facebook*.

DOI: https://doi.org/10.1287/mksc.2018.1135

Implication: observational advertising models can fail badly against randomized experiments even with rich covariates. This directly motivates P3's randomised Criteo uplift validation and sensitivity discipline.

### Gordon, Moakler and Zettelmeyer, Marketing Science 2023
*Close Enough? A Large-Scale Exploration of Non-Experimental Approaches to Advertising Measurement*.

DOI: https://doi.org/10.1287/mksc.2022.1413

Implication: modern observational causal methods still require careful identification. Predictive accuracy is not evidence of causal validity.

### Waisman, Nair and Carrion, Marketing Science 2025 volume
*Online Causal Inference for Advertising in Real-Time Bidding Auctions*.

DOI: https://doi.org/10.1287/mksc.2022.0406

Implication: causal ad-effect identification and adaptive experimentation already exist at a high theoretical level. P3 must state its identification conditions precisely.

### Graphical Point Process MTA, Management Science 2024
*A Graphical Point Process Framework for Understanding Removal Effects in Multi-Touch Attribution*.

DOI: https://doi.org/10.1287/mnsc.2023.00457

Implication: graph/sequential removal effects in MTA are already a contemporary high-level contribution. A customer journey graph by itself is not sufficient novelty.

### Adaptive Ad Sequencing, Marketing Science 2022
Rafieian, O., *Optimizing User Engagement Through Adaptive Ad Sequencing*.

DOI: https://doi.org/10.1287/mksc.2022.1423

Implication: dynamic policies combining causal inference and sequential decision-making are established. Reinforcement learning or adaptive sequencing must not be added to Orbit merely for novelty signalling.

## Direct recent collision

### Procedia Computer Science 2026
*Causal Inference-Based Digital Advertising Attribution Model and Budget Allocation Optimization System*.

DOI: https://doi.org/10.1016/j.procs.2026.04.257

The paper combines causal inference, causal forests, multi-touch attribution and budget allocation in a deployed-system framing.

Implication: P3's title and contribution cannot rest on 'causal attribution + budget optimisation system' alone. The study must be materially stronger in identification, validation and reproducibility.

## P3 defensible differentiation

P3 will therefore be designed around a stronger evidence chain:

1. preserve Orbit's heuristic first-touch, last-touch, linear, time-decay and weighted models as explicit non-causal baselines
2. define treatment, outcome, timing, confounders and estimands before modelling
3. validate treatment-effect components on the randomised Criteo uplift benchmark
4. test causal-effect recovery on semi-synthetic journeys with known ground truth
5. apply the frozen estimator to real Criteo attribution journeys only with explicit observational assumptions and diagnostics
6. report overlap, sensitivity and estimator instability instead of treating model output as causal truth
7. connect estimated incremental effects to a deterministic, auditable budget optimiser under matched spend constraints
8. expose the same validated causal evidence through the Orbit build, producing a code-to-paper evidence chain

## Claim discipline

P3 will not claim that observational clickstream data automatically identifies causal effects. It will separate:

- randomized causal validation
- semi-synthetic ground-truth recovery
- observational causal estimates conditional on stated assumptions
- predictive performance
- product recommendations derived from those estimates

This separation is central to both the scientific contribution and the credibility of Orbit's causal functions.

## Novelty freeze (2026-09-18, post-experiment)

Checked against the anchors above before freezing the contribution. Each individual component is
established prior art: "beyond last touch" (Berman 2018), attribution→bidding/budget (Li et al.
2016), observational-vs-experimental ad measurement (Gordon et al. 2019/2023), graph/removal-effect
MTA (Management Science 2024), AIPW/DML/uplift as methods. **None of these is claimed as new.**

The residual, defensible novelty is the **integrated, software-synchronised evidence chain**, not
any single method:
1. explicit historical-credit vs incremental-contribution contrast with quantified ranking inversion (E1);
2. estimator recovery against **known** truth with correct-CI evidence and a documented misspecification failure region (E2);
3. a randomized-validation pipeline (E3, fixture-validated here);
4. a one-factor **failure-region map** over identification assumptions (E6);
5. **matched-budget decision-value** quantification with regret vs an oracle (E5); and
6. an evidence-gated **abstention** policy — all delivered from a running product system (Orbit)
   with the AIPW estimator shared between product and research code.

Framing rule for the manuscript: lead with the *chain and its decision/failure consequences*, not
with the estimator or the journey graph. Magnitudes are semi-synthetic and not transportable; the
mechanisms are. Real-data randomized/observational/external validation (Criteo/UCI) is pipeline-ready
but not executed here (network policy) — see `03 Data/ACQUISITION_STATUS.md`.
