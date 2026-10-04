# Paper III — Federated Credit Risk Privacy

**Working title:** Privacy-Resilient Federated Credit-Risk Forecasting: Differential Privacy, Membership-Inference Risk and Utility Loss under Operational Stress

This folder is the dedicated research workspace for Paper III.

## Folder structure

- `01 Manuscript and Audit` — current manuscript and reviewer-audit materials when committed.
- `02 Baseline Evidence` — archived baseline results and reproduction evidence.
- `03 New Experimental Results` — reviewer-driven experimental extensions.
- `04 Diagnostics` — round-level and mechanism diagnostics.
- `05 Figures` — manuscript-ready figures generated from genuine experimental results.
- `06 Reproducibility` — runner, manifest and complete artifact pack.

## Experimental extension completed 4 October 2026

The extension uses the Taiwan Credit Card Default dataset and the Paper III experimental design. It includes:

1. Severe non-IID plus 20% symmetric label noise across D0, D0C, D1, D2, D3 and D4, 100 seeds.
2. Severe non-IID plus 40% client participation across D0, D0C, D1, D2, D3 and D4, 100 seeds.
3. Stricter clipping sweep across C1–C6 at clip norms 1.00, 0.75, 0.50 and 0.25 under D0C and D2, 100 seeds.
4. D4 front-loaded gradient-norm diagnostic using the archived 30 diagnostic seeds.
5. Regenerated Figure 2 using D0C, D1, D2, D3 and D4.
6. Regenerated Figure 7 including D0, D3 and D4.

## Integrity rule

No experimental number may be invented, interpolated or estimated. Manuscript claims must be drawn only from the archived results or genuine new experimental outputs. Any further empirical request that is not supported by these files requires an actual experimental run before a result is inserted.

See `03 New Experimental Results/EXPERIMENT RESULTS SUMMARY.md` and `06 Reproducibility/Paper III experimental extension manifest.txt` for the handoff record.