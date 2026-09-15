# Supplementary Checks

This folder contains the post-audit robustness suite for the Strategic Organization paper.

## Run

From the repository root:

```bash
python "Strategic Organization/04 Analysis/Supplementary Checks/supplementary-checks.py"
```

Synthetic schema test:

```bash
python "Strategic Organization/04 Analysis/Supplementary Checks/supplementary-checks.py" --demo
```

The script reads the same primary and analysis-ready CSV files as the validated analysis pipeline. It first reconciles core estimates against `../Statistical Modeling/analysis_manifest.json`, then runs S1-S11. It writes aggregate outputs only to `Outputs/` and does not overwrite the validated Statistical Modeling folder.

## Interpretation

The controlling manuscript interpretation is `../../05 Manuscript/POST_AUDIT_CLAIM_RESOLUTION.md`.

Key post-audit rules are:

- treat the 16.63-point cross-domain difference as a raw within-instrument profile until common score calibration is documented;
- treat the conventional-minus-AI/data gap descriptively, not as a reliable person-level construct;
- qualify the full-sample unadjusted exposure sorting result because it attenuates under low-score screening;
- use WCR Webb and occupation-level randomisation inference for occupational-exposure claims because the effective cluster count is small;
- centre the paper on the robust adjusted finding that targeted high-exposure occupations do not show a distinctive relative AI/data readiness advantage once conventional capability is considered;
- use targeted-occupation or occupational-aspiration language throughout.
