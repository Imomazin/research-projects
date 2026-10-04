# Paper III Experimental Extension — Verified Results Summary

Run date: 4 October 2026

All values below come from actual runs against the Taiwan Credit Card Default dataset. No values are estimated or interpolated.

## 1. Severe-imbalance extensions — 100 seeds

### S1 — severe non-IID + 20% symmetric label noise, full participation

| Treatment | Test AUC, mean [95% CI] | Observed-label membership advantage, mean [95% CI] |
| --- | --- | --- |
| D0 | 0.6952 [0.6910, 0.6994] | -0.1081 [-0.1104, -0.1058] |
| D0C | 0.7148 [0.7133, 0.7164] | -0.1064 [-0.1085, -0.1043] |
| D2 | 0.7138 [0.7122, 0.7154] | -0.1068 [-0.1089, -0.1046] |
| D4 | 0.7140 [0.7125, 0.7156] | -0.1067 [-0.1089, -0.1046] |

At D2, the clean-label loss membership advantage is **0.0462 [0.0439, 0.0484]** and the confidence attack advantage is **0.0492 [0.0467, 0.0516]**. Therefore the negative observed-label advantage does not establish absence of membership signal. Under label corruption, a label-aware attack using the corrupted training label can reverse sign while label-free or clean-label attacks remain positive.

Relative to D0, D0C raises mean AUC by approximately **0.01962**, showing a substantial clipping-associated stabilisation under this severe-plus-noise condition.

### S2 — severe non-IID + 40% client participation, no added label noise

| Treatment | Test AUC, mean [95% CI] | Observed-label membership advantage, mean [95% CI] |
| --- | --- | --- |
| D0 | 0.7010 [0.6975, 0.7045] | 0.0404 [0.0383, 0.0426] |
| D0C | 0.7115 [0.7093, 0.7136] | 0.0425 [0.0403, 0.0448] |
| D2 | 0.7120 [0.7100, 0.7139] | 0.0409 [0.0388, 0.0430] |
| D4 | 0.7121 [0.7102, 0.7140] | 0.0409 [0.0388, 0.0430] |

Relative to D0, D0C raises mean AUC by approximately **0.01045**. Again, D2 and D4 are close to the clipping-only result, supporting the interpretation that bounded gradients rather than Gaussian noise carry most of the stress benefit.

## 2. Stricter clip-norm sweep — 4,800 runs

Design: C1–C6 × 100 seeds × clip norms 1.00, 0.75, 0.50 and 0.25 × D0C and D2.

For D0C, the change in mean AUC when the clip is tightened from 1.00 to 0.25 is:

| Condition | AUC change, clip 0.25 minus clip 1.00 |
| --- | ---: |
| C1 | -0.00687 |
| C2 | -0.00283 |
| C3 | -0.00064 |
| C4 | -0.00588 |
| C5 | +0.00014 |
| C6 | -0.00481 |

The result does **not** support a monotonic claim that stricter clipping improves utility. The existing clip norm of 1.0 is at or near the stronger end of the tested range for most conditions, while aggressive clipping generally sacrifices discrimination. D2 shows the same qualitative pattern. This reviewer request is therefore experimentally answered and should no longer be left only as future work.

## 3. Gradient-norm diagnostic

The C1 diagnostic was rerun on the archived 30 diagnostic seeds using D0, D3 and D4 across all 50 rounds. Figure 7 can now contain a genuine D4 front-loaded trajectory rather than a fabricated or inferred line.

## 4. Figure 2

Figure 2 was regenerated directly from the archived 100-seed Paper III main-matrix results and includes D0C, D1, D2, D3 and D4 with 95% confidence intervals and a zero membership-advantage reference line.

## 5. Manuscript consequences

1. Replace any claim that negative membership advantage under label noise necessarily reflects non-memorisation. The new S1 experiment shows a negative observed-label loss advantage alongside positive clean-label and label-free membership signals.
2. Report the severe-imbalance-plus-noise and severe-imbalance-plus-partial-participation experiments as completed extensions rather than future work.
3. Replace the clip-sweep future-work sentence with the actual finding: increasingly strict clipping does not monotonically improve discrimination and usually lowers AUC below the clip-norm-1.0 result.
4. Replace Figure 2 and Figure 7 using only the genuine generated figures.
5. Retain higher-capacity model classes and stronger likelihood-ratio/shadow attacks as legitimate future work; these new experiments do not answer those questions.

## Strict integrity rule

Do not invent, smooth, estimate or interpolate numbers, confidence intervals or figure trajectories. If a manuscript claim requires a result not contained in the archived evidence or the new run outputs, label it as requiring an actual experimental run.