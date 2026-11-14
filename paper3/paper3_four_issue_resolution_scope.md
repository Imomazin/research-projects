# Paper III: four-issue methodological resolution and scope
Version: 14 November 2026

## Status and source of truth
The original 100-seed reviewer experiments are complete (run 43652275680). The corrected follow-up design is `paper3_four_issue_validation.py`, final run 43655172569. Earlier follow-up runs 43655035585 and 43655098855 were superseded by fixes to empty-batch Gaussian noise and stable per-ID partitioning. Do not combine those earlier results with the final run.

## Issue 1: privacy accounting
The original manuscript's epsilon numbers are *conditional local-update accountant estimates* only. The original data-dependent standardisation, quantile client boundaries, per-client sampling rates and client-size-weighted aggregation prevent a certified end-to-end raw-record DP claim. The original appendix's formula comparing balanced-prior hypothesis-testing advantage to 2×attack AUC−1 has been withdrawn.

The new sensitivity experiment defines a distinct, more defensible protected-training mechanism: stable publicly designated ID-based train/public-calibration/test allocation; fixed public feature scales and credit-limit cutoffs; fixed per-record Poisson inclusion probability q=0.02; per-example L2 clip 1; Gaussian noise multiplier sigma=1.5 applied on *every* private step, including empty Poisson batches; fixed denominator 128; and equal-weight aggregation across five clients. The released DP object is the final trained private model. Client assignment is recordwise and based on fixed public cutoffs. The protected unit is add/remove of one record in the designated training partition, with the auxiliary public calibration/test sets and stable IDs held fixed.

For integer alpha >=2, the subsampled Gaussian RDP per step uses log A_alpha/(alpha-1), where
A_alpha = sum_{k=0}^alpha binom(alpha,k) (1-q)^(alpha-k) q^k exp(k(k-1)/(2 sigma^2)).
Compose 400 local steps for the affected client and convert with eps = RDP + log(1/delta)/(alpha-1). This gives a conservative integer-order bound near eps=1.643 at delta=1e-5 for q=.02, sigma=1.5, 400 steps, conditional on the exact public/auxiliary assumptions. A separate implementation-level audit is still appropriate before describing this as a deployment guarantee.

**Important release limitation:** The model trained with clipping and Gaussian noise is the only object for which this training-only accountant is offered. Non-private control models, raw training-dependent metrics, and published experiment CSVs are research outputs on the public UCI benchmark, not covered by the model's DP guarantee. No privacy is claimed for the designated public auxiliary records. This is a separate sensitivity design, not a retroactive privacy guarantee for the original manuscript experiment.

## Issue 2: clipping versus effective step magnitude
The new `normmatched` control uses exactly the same Poisson sample and learning rate as the clipped model. It rescales the **unclipped aggregate gradient** to match the Euclidean norm of the clipped aggregate gradient for that step. This controls update magnitude while allowing direction to differ. Compare unclipped, clipped, normmatched and private treatments within seed. This is a mechanistic sensitivity test, not a claim that every nonlinear effect of clipping is isolated.

## Issue 3: reference attack
The new independent shadow/reference model uses the same five-client federated logistic-regression training architecture on a disjoint, publicly designated auxiliary partition. The membership attack compares retained training members and held-out nonmembers matched exactly by publicly fixed credit-limit segment and observed outcome. It reports direct loss and shadow-reference gap attacks, plus empirical TPR at an attainable FPR <=1% (no interpolation). Shadow training population is smaller, so it is not a full multi-shadow LiRA implementation; avoid such a label.

## Issue 4: calibration privacy
The new public auxiliary calibration split is excluded from protected training and fixed by stable public ID hashes. Isotonic and Platt transformations fitted to those explicitly public labels are post-processing of the private model with public information; no additional privacy cost is charged **for protected training records**. This does not protect the calibration records themselves. The original calibration on a private holdout remains a utility-only result and is not covered by the original accountant.

## Manuscript reconciliation
The corrected manuscript and privacy appendix are in the existing Paper III Google Drive folder. Do not replace the original 80/20 results with the distinct 70/15/15 or hash-partition supplementary experiments without identifying their different populations and privacy scope. Once final run 43655172569 completes, archive its raw artifacts and add its actual means and seed-paired confidence intervals to the supplementary section. Do not infer results from job status alone.
