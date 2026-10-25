"""Write Datasets/Revision Dataset Manifest.csv: every dataset created or used in the revision with
rows, columns, SHA-256 checksum, producing script and whether it may be redistributed.

All inputs are public: SEC EDGAR filings and XBRL data, published uncertainty indices, BLS price
indices and a publicly released language model. No credentials or personal data are stored.
"""
import gzip
import hashlib
from pathlib import Path

import pandas as pd

PROJ = Path(__file__).resolve().parent.parent
FILES = [
    ("Datasets/Derived/Revision/Revision Firm Year Measures.csv", "Analysis/revision models.py", "Firm-year revision measures (convergence alternatives, four response measures)"),
    ("Datasets/Derived/Revision/Response Measures.csv", "Analysis/build response measures.py", "Response sentence counts by rule and category"),
    ("Datasets/Derived/Revision/Convergence Measures.csv", "Analysis/build convergence measures.py", "Boilerplate, firm-specific and interaction counts"),
    ("Datasets/Derived/Revision/Response Candidate Pairs.jsonl.gz", "Analysis/export response candidates.py", "Candidate sentence-category pairs for language-model scoring"),
    ("Datasets/Derived/Revision/Response Candidate Language Model Scores.csv.gz", "Data Collection/collection stages.py (stage corpusnli)", "Entailment scores for candidate pairs"),
    ("Datasets/Derived/Revision/Response Validation Sample.csv", "Analysis/build response measures.py", "Stratified validation sample"),
    ("Datasets/Derived/Revision/Validation Universe Counts.csv", "Analysis/build response measures.py", "Population pairs by stratum"),
    ("Validation/Response Validation Reference Coding.csv", "AI assistant applying Validation/Response Coding Manual.md", "Reference labels (not human annotation)"),
    ("Validation/Response Human Coding Sheet.csv", "Validation/validate response measures.py", "Blank sheet for human coders"),
    ("Validation/Response Human Coding Training Sheet.csv", "Validation/validate response measures.py", "Training items for human coders"),
    ("Validation/Response Validation Language Model Scores.csv", "Data Collection/collection stages.py (stage nli)", "Language-model scores for the validation sample"),
    ("Datasets/Raw Macro/Revision/Price Index Retrieval Manifest.csv", "Data Collection/collection stages.py (stage prices)", "CPI and PPI retrieval record"),
    ("Datasets/Raw Macro/Revision/Revision Retrieval Manifest.csv", "Data Collection/collection stages.py", "Macro re-download and version check"),
    ("Datasets/Derived/Research Panel.csv", "Analysis/assemble panel.py", "First-version firm-year panel (reproduced)"),
    ("Datasets/Derived/Financial Panel.csv", "Analysis/build financial panel.py", "First-reported XBRL financials (reproduced)"),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def shape(p):
    if p.name.endswith(".jsonl.gz"):
        with gzip.open(p, "rt") as f:
            return sum(1 for _ in f), None
    d = pd.read_csv(p, low_memory=False)
    return len(d), d.shape[1]


rows = []
for rel, script, desc in FILES:
    p = PROJ / rel
    if not p.exists():
        rows.append({"File": rel, "Description": desc, "Produced by": script, "Rows": None, "Columns": None, "SHA-256": "missing", "Redistributable": "Yes"})
        continue
    r, c = shape(p)
    rows.append({"File": rel, "Description": desc, "Produced by": script, "Rows": r, "Columns": c, "Bytes": p.stat().st_size,
                 "SHA-256": sha(p), "Redistributable": "Yes (derived from public SEC, BLS and index data)"})
pd.DataFrame(rows).to_csv(PROJ / "Datasets" / "Revision Dataset Manifest.csv", index=False)
print(pd.DataFrame(rows)[["File", "Rows", "Columns"]].to_string())
