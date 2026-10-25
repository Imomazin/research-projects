# Managing Emerging Strategic Risks

Target journal: Strategy & Leadership (Emerald), research paper.

Title: When every risk is material: disclosed risk convergence, documented response and organisational resilience in US firms, 2017 to 2025.

## Status

Data collected, measures built, pre-registered models estimated and the manuscript drafted. The manuscript is ready for author review. Outstanding before submission: human double-coding of the released validation samples (Datasets/Derived/Validation Sample Original Dictionary.csv and Validation Holdout Revised Dictionary.csv), confirmation of author metadata, funding and competing-interest declarations, and a decision on whether this public repository should hold the draft before submission.

## Evidence base

787 US non-financial firms (stratified random sample from 1,597 eligible), 6,214 10-K filings for fiscal 2017 to 2025, 2,240,714 XBRL fact rows and five public uncertainty indices. All collection ran through `.github/workflows/strategic-risk-pipeline.yml` because the analysis workspace could not reach SEC or the index publishers directly.

## Key files

- Manuscript/Managing Emerging Strategic Risks Manuscript.docx (author copy) and Submission/Managing Emerging Strategic Risks Anonymised Manuscript.docx
- Results/Managing Emerging Strategic Risks Analysis Workbook.xlsx (every table and figure source)
- Analysis/Analysis Plan.md (hypotheses and decision rules committed before outcomes were merged; dated deviations)
- Submission/Critical Assessment.md (reviewer-style assessment)

## Reproduce

1. Collection: edit `Data Collection/Run Request.txt` (stages probe, literature, frame, macro, facts, filings) and push to `research/strategic-risk`; the workflow commits outputs. Large filing texts and XBRL facts are on branch `data/strategic-risk`.
2. `python "Data Collection/draw sample.py"`
3. `python "Analysis/build financial panel.py" "<data branch>/Company Facts/Financial Facts Long.csv.gz" "Datasets/Derived/Financial Panel.csv"`
4. `python "Analysis/build text measures.py" "<data branch>/Filing Texts" Datasets/Derived` (set VALIDATION_SEED=20261025 for the holdout sample) and `python "Analysis/build updating measure.py" ...`
5. `python "Analysis/build macro series.py"`, `python "Analysis/assemble panel.py"`, `python "Analysis/estimate models.py"`, `python "Analysis/validate measures.py"`, `python "Analysis/select cases.py" "<data branch>/Filing Texts"`, `python "Analysis/make figures.py"`
6. `python "Manuscript/collect numbers.py"`, `python "Manuscript/build blocks.py"`, `node "Manuscript/build manuscript.js" <out.docx> [anonymised]`, `python "Results/build workbook.py"`

Python 3.11 to 3.13 with pandas, numpy, statsmodels 0.15, linearmodels 7.1, scikit-learn, lxml, matplotlib; Node with docx 9.

## Revision (branch revision/strategic-risk, 25 October 2026)

The revision reproduces the first version from the raw data, rebuilds the documented-response measure, adds small-cluster and multiple-testing inference, tests alternative convergence measures and shock channels, and rewrites the manuscript. The first-version files above are preserved unchanged.

Deliverables:

- Manuscript/Managing Emerging Strategic Risks Revised Manuscript.docx and Submission/Managing Emerging Strategic Risks Revised Anonymised Manuscript.docx
- Results/Managing Emerging Strategic Risks Revision Workbook.xlsx (read me and reproducibility record, data dictionary and inventory, reconciliation, corrections register, sample and validation, hypothesis tests, robustness, convergence and shocks, figure data)
- Datasets/Revision Data Dictionary.csv, Datasets/Revision Dataset Manifest.csv and Datasets/Derived/Revision/
- Validation/Response Coding Manual.md, the validation sample, AI reference coding, blank human coding sheets and Validation/compute agreement.py. Human double-coding has not been done; the reference labels were assigned by an AI assistant and are not human annotation.
- Reproduction/ (reproduce study.py, independent checks.py, Reconciliation Report.csv, File Comparison.csv, Corrections Register.csv)
- Analysis/Analysis Plan.md, section Revision deviations

Revision run order: `python Reproduction/"reproduce study.py" --data <data branch> --work <folder>`; `python Analysis/"export response candidates.py" "<data branch>/Filing Texts" "Datasets/Derived/Revision/Response Candidate Pairs.jsonl.gz"`; push `stage: corpusnli` in Data Collection/Run Request.txt to score candidates in GitHub Actions; `python Validation/"validate response measures.py"`; `python Analysis/"revision models.py"`; `python Analysis/"make revision figures.py"`; `python Manuscript/"collect revision numbers.py"`; `python Reproduction/"build corrections register.py"`; `python Analysis/"build revision manifest.py"`; `python Manuscript/"build blocks revision.py"`; `node Manuscript/"build manuscript revision.js" <out.docx> [anonymised]`; `python Results/Revision/"build revision workbook.py"`.

Repository visibility: this repository is public on GitHub. Draft manuscripts and derived data held here are visible to anyone until the repository is made private.
