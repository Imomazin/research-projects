# Paper III: 100-seed evidence reconciliation and limitations
Date: 14 November 2026
Manuscript: IEEE Access, Access-2026-55913

## Verified computation
GitHub Actions run 43652275680: 30/30 jobs successful. The 30 ZIP artifacts were downloaded and combined. Exactly 100 seeds (17286 through 17385) are represented per mode, without missing rows: 1,200 membership rows (3 treatments x 4 attacks x 100), 400 clipping-control rows (4 treatments x 100), and 900 calibration rows (3 treatments x 3 mappings x 100). The original Taiwan spreadsheet matched the recorded SHA-256 30c6be3abd8dcfd3e6096c828bad8c2f011238620f5369220bd60cfc82700933. The three merged raw result files and paired-contrast CSV are in the existing Paper III Google Drive folder.

## Observed findings
D2 membership advantage: unmatched 0.03106; outcome-matched 0.02170; outcome-and-segment-matched -0.00030; reference-gap 0.01743. Paired segment-matched minus unmatched advantage: -0.03136, 95% CI approximately [-0.03433, -0.02839]. The result supports the interpretation that candidate-pool composition substantially affects the apparent attack advantage. It does NOT establish that all membership leakage disappears. Matched subgroups and the reference attack have distinct sampling and estimands.

D2 raw calibration: ECE 0.09545; Brier 0.15121; AUC 0.72080. D2 isotonic: ECE 0.01293; Brier 0.14174; AUC 0.72073. The paired AUC change is approximately -0.000068 and its 95% interval crosses zero. Calibration was fitted on a disjoint 15% holdout and evaluated on another 15% test holdout; the training proportion was 70%, so these values must not be conflated with the original 80/20 experimental design.

Control-mode means: D0 AUC 0.72026, Brier 0.14633; D0C AUC 0.72022, Brier 0.15110; gradient_scale_matched AUC 0.72176, Brier 0.14575; lr_scale_matched AUC 0.72176, Brier 0.14574. The last two are practically indistinguishable, and are NOT independent well-matched controls. The source comment claiming selection by prespecified grid and validation set is unsupported: the code uses a fixed mean clipping multiplier computed from training gradients at theta=0. Do not claim that clipping's effect has been causally isolated.

## Critical limitations requiring resolution before final submission
1. The formal privacy-accounting appendix describes q=128/n_min while the code uses q_i=min(1,128/n_i), separately per client. Recalculate and independently check privacy accounting against the actual mechanism and release protocol.
2. Training-derived standardisation and client quantile boundaries are outside the DP mechanism. Client sizes determine aggregation weights and sampling rates. A full end-to-end (epsilon,delta)-DP guarantee for the published pipeline is NOT established. Report a conditional local-update accountant only unless preprocessing and other disclosures are addressed.
3. The appendix formula (exp(epsilon)-1+2delta)/(exp(epsilon)+1) is not, without additional derivation, a universal bound on 2*attack AUC-1. Do not compare the two as if directly equivalent.
4. Reference-gap attack trains a single-client reference model on half of the held-out test population; its architecture and population differ from the target five-client FL model. It is a sensitivity check, not a fully matched independent shadow-model evaluation or LiRA.
5. The membership experiment's severe class selection excludes records from the target training set. The attack evaluates retained members against holdout nonmembers, and the estimated advantage depends on the membership candidate definition. Confirm whether excluded training-split records are part of the intended privacy unit and attack universe.
6. Per-seed bootstrap intervals (400 resamples in the committed runner) do not substitute for between-seed paired uncertainty; use the archived paired-contrast table for seed-level inference. The 1%-FPR metric is interpolated from empirical ROC and needs sensitivity analysis with appropriate discrete operating points.
7. Isotonic/Platt calibration uses labelled calibration records and is not covered by the local-update DP accountant. Either use an independently public calibration dataset, privatise this stage and account for it, or explicitly limit the privacy claim.
8. The original supplementary 600-row checkpoint is not reproduced by the three new studies. Preserve it as a separate unverified evidence item until its provenance and 600-row archive are independently confirmed.
9. The 100-seed results should be presented as supplementary controlled experiments; do not silently replace the manuscript's original 80/20 design, 50-round experimental results or previously reported epsilon values.
10. The manuscript and response letter must explicitly acknowledge the statistically detectable D2-D0C difference (reported p=0.009; paired interval [-0.00040,-0.00006]) and use the correct worst-case versus mean epsilon labels (C1 max 2.41/mean 2.35; C2 max 4.04/mean 3.93) only when the accountant is independently validated.

## Required final action
Revise the privacy-accounting claims, document the control experiment's limitations, present supplementary matched membership and calibration findings with their distinct train/test design, reconcile manuscript tables/figures/reviewer replies, and obtain independent privacy and statistical sign-off. Successful execution alone is not proof of full methodological validity.
