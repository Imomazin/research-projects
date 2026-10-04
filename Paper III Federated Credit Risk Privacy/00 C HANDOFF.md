# Paper III — Final Revision Handoff for C

## Controlling task

Complete the final revision of **Paper III: Privacy-Resilient Federated Credit-Risk Forecasting: Differential Privacy, Membership-Inference Risk and Utility Loss under Operational Stress** after Preston's reviewer audit.

Use the latest revised Word manuscript **Paper III V3.1 - fully revised v2 (tracked changes).docx** as the controlling manuscript and Preston's original **V3.1.docx** comments as the controlling reviewer record. Ignore author reply notes when determining whether a reviewer request is satisfied; judge the accepted body text itself.

The new experimental evidence below is genuine. It was run against the Taiwan Credit Card Default dataset using the Paper III design and archived Paper III seeds. Do not invent, estimate, interpolate or smooth any experimental number, confidence interval or figure trajectory.

## GitHub workspace

Root:
https://github.com/Imomazin/research-projects/tree/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy

Verified experiment summary:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/03%20New%20Experimental%20Results/EXPERIMENT%20RESULTS%20SUMMARY.md

Severe-stress 100-seed summary:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/03%20New%20Experimental%20Results/Paper%20III%20severe%20stress%20summary.csv

Stricter-clip 4,800-run compact summary:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/03%20New%20Experimental%20Results/Paper%20III%20stricter%20clip%20sweep%20compact%20summary.csv

Gradient-norm D4 30-seed round-level summary:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/04%20Diagnostics/Paper%20III%20gradient%20norm%20D4%20summary.csv

Regenerated Figure 2:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/05%20Figures/Paper%20III%20Figure%202%20-%20membership%20advantage.svg

Regenerated Figure 7 with D4:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/05%20Figures/Paper%20III%20Figure%207%20-%20gradient%20norms%20with%20D4.svg

Stricter-clipping diagnostic figure:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/05%20Figures/Paper%20III%20stricter%20clip%20sweep%20-%20D0C%20AUC.svg

Reproducibility runner:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/06%20Reproducibility/Paper%20III%20experimental%20extension.py

Reproducibility manifest:
https://github.com/Imomazin/research-projects/blob/main/Paper%20III%20Federated%20Credit%20Risk%20Privacy/06%20Reproducibility/Paper%20III%20experimental%20extension%20manifest.txt

## New experimental evidence that must now be integrated

### Severe imbalance plus 20% symmetric label noise — S1

100 seeds across D0, D0C, D1, D2, D3 and D4.

Key D2 results: test AUC **0.7138 [0.7122, 0.7154]**; observed-label loss membership advantage **-0.1068 [-0.1089, -0.1046]**; clean-label loss membership advantage **+0.0462 [0.0439, 0.0484]**; confidence/entropy membership advantage approximately **+0.0492 [0.0467, 0.0516]**.

The manuscript must therefore NOT equate a negative observed-label advantage under label noise with non-memorisation. The correct interpretation is that label corruption can reverse the sign of a label-aware observed-label attack while clean-label or label-agnostic attacks still show a positive membership signal.

D0 mean AUC is **0.6952 [0.6910, 0.6994]** and D0C mean AUC is **0.7148 [0.7133, 0.7164]**, an improvement of about **0.01962** from clipping alone. D2 and D4 remain close to the clipping-only result, which strengthens the mechanism interpretation that bounded gradients carry most of the stress benefit.

### Severe imbalance plus 40% client participation — S2

100 seeds across D0, D0C, D1, D2, D3 and D4.

D0 mean AUC **0.7010 [0.6975, 0.7045]**; D0C **0.7115 [0.7093, 0.7136]**; D2 **0.7120 [0.7100, 0.7139]**; D4 **0.7121 [0.7102, 0.7140]**. D2 observed-label membership advantage **0.0409 [0.0388, 0.0430]**.

The D0C improvement over D0 is about **0.01045**, again supporting clipping rather than Gaussian noise as the main stabilising mechanism.

Do not report the numerically unstable S2-D3 calibration slope unless it is independently recomputed with a robust method. It is not needed for the reviewer response.

### Stricter clip-norm sweep

Actual run: C1-C6 × 100 seeds × clip norms 1.00, 0.75, 0.50 and 0.25 × D0C and D2 = **4,800 runs**.

Under D0C, tightening the clip from 1.00 to 0.25 changes mean AUC by:
C1 -0.00687; C2 -0.00283; C3 -0.00064; C4 -0.00588; C5 +0.00014; C6 -0.00481.

Therefore stricter clipping does **not** monotonically improve utility. Clip norm 1.0 is at or near the stronger end of the tested range for most conditions, and aggressive clipping generally sacrifices discrimination. This request has been experimentally answered and must no longer remain phrased only as future work.

### Figures

Use the new Figure 2 and Figure 7 above. Figure 2 now contains D0C, D1, D2, D3 and D4 from the genuine 100-seed main matrix with 95% confidence intervals and a zero/chance reference line. Figure 7 now includes a genuine D4 front-loaded trajectory using the archived 30 diagnostic seeds.

Recommended Figure 2 caption:
**Figure 2. Membership advantage across the six operational conditions for clipping-only D0C, uniform privacy treatments D1-D3 and front-loaded D4, 100 seeds, mean with 95 per cent confidence intervals. The horizontal reference at zero is the chance/no-signal baseline. D4 is matched to the D2 formal privacy budget.**

Recommended Figure 7 caption:
**Figure 7. Mean pre-clip gradient L2 norm by federated round under D0 (non-private), D3 (strong privacy) and D4 (front-loaded, matched to the D2 budget), 30-seed diagnostic. Gradient norms are largest early; the D4 trajectory is included to show the schedule against the mechanism it targets. This is a training-dynamics diagnostic, not a transcript-level privacy guarantee.**

## Remaining editorial corrections to close while integrating the new evidence

Work through the latest manuscript itself and make every outstanding Preston correction rather than relying on previous author replies.

1. Abstract: ensure plural data usage exactly where requested; state the utility improvement explicitly relative to the non-private model; retain standard DP-SGD integration, the unexpected clipping result, spelled-out ROC/AUC terminology and the exact 0.0016 / 0.16 percentage-point cost; retain practical privacy-budget wording and the front-loaded result where supported.
2. Introduction: ensure the loss-threshold attack is named alongside operational-stressor examples and the companion Paper II is explicitly cited for conditions that matter.
3. Related work/threat model: keep definitions for DP-SGD, empirical risk minimisation, convex learning and non-IID; use named authors in prose where requested; use **the credit-scoring model** rather than generic **the model** in the attack passage; replace **the cleanest measurement** with **a direct measurement**.
4. Membership paragraph: move the members/non-members clarification into the following sentence, not the definition sentence. State attack-AUC meaning, chance baseline, interval method and four attack scores clearly.
5. Training prose: use **For default prediction, we apply...** with the comma.
6. Results prose: bracket treatment codes cleanly, e.g. **At the medium budget (D2), ...**; use **at D0** rather than **without privacy** where Preston requested the code; include the comma after C4; retain an explicit rationale for focusing on D2.
7. Table 3: D4 noise-multiplier cell must read exactly **variable (front-loaded)**.
8. Table 6 caption: explicitly name the chance/no-signal comparator. Table 6b caption: explicitly name **C2** and **D2**.
9. Discussion: use the exact phrase **the privacy-utility tension** where Preston requested it. Retain the citation supporting the **usual expectation** claim and a citation immediately after **often used in practice**.
10. Correct **membership member set** to **member set** everywhere.
11. Confirm Truex et al. (2019), Zhu et al. (2019) and Yousefpour et al. (2021) are present in the reference list and every in-text citation resolves.
12. Remove any residual accepted-text garbling, duplicated figure references, broken table remnants, duplicated words or tracked-change collisions.

## Section structure

Implement Preston's structural request by merging the present privacy-accounting/attack section into Section 4 and renaming it:

**4. Experimental design, privacy accounting and attack evaluation**

Retain logical subheadings beneath Section 4. Remove the standalone current Section 5 heading. Renumber the remainder consistently so Results becomes Section 5, Discussion becomes Section 6, Practical implications becomes Section 7, Limitations becomes Section 8 and Conclusion becomes Section 9. Update every in-text section cross-reference and figure/table reference after renumbering.

## Differential-privacy equation

Replace prose-only notation with a proper displayed equation. For neighbouring datasets D and D' differing in one record and every measurable output set S:

**Pr[M(D) ∈ S] ≤ exp(ε) Pr[M(D') ∈ S] + δ.**

State directly beneath it that this is (ε, δ)-differential privacy. Use proper ε and δ symbols and true equation formatting in Word, not plain-text pseudo-equation formatting.

## Limitations and implications after the new experiments

Do not leave the stricter-clip sweep or the severe-imbalance-plus-noise/partial-participation combinations as experiments for future work: they have now been run. Integrate them as reviewer-driven robustness extensions, preferably without allowing them to overwhelm the main six-condition design.

Higher-capacity models, stronger likelihood-ratio/shadow-model attacks, additional datasets and transcript-level adversaries remain legitimate future work.

Tighten the limitation language so it distinguishes what is now tested from what remains untested. Do not generalise the new severe-stress findings beyond this linear Taiwan-credit setting.

## Final reviewer audit after editing

After the manuscript is fully revised, re-audit **all 185 Preston comments in Preston's original order**. For every comment, judge ONLY the final accepted body text, not reply/resolution notes. Mark **Implemented / Partially implemented / Not implemented** and quote the exact final sentence or table/caption wording as evidence. Apply the strict rule that any requested specific wording, definition, citation, comma, table label or caption content is not implemented unless it is actually present.

Then provide:
- the final tracked-changes Word manuscript;
- a clean accepted-changes Word manuscript;
- the complete 185-comment audit table;
- a short final outstanding-items list;
- a defects check covering empty/broken tables, garbled sentences, duplicate words, broken figure references and in-text citations missing from the reference list.

## Absolute experimental-integrity rule

Do not fabricate or infer new results. Do not invent confidence intervals, table values, trajectories or effect sizes. Use only values supported by the archived Paper III evidence or the genuine new artifacts above. If any additional claim would require an experiment that is not represented in these artifacts, state **requires an actual experimental run** and leave the result blank rather than estimating it.