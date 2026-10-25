"""Alternative convergence measures that need a second pass over the Item 1A text.

Boilerplate. Following the tetragram approach to boilerplate in financial text, a
four-word sequence is common in a fiscal year when it appears in at least 30 per cent and
at most 75 per cent of that year's Item 1A sections in the sample. A sentence is treated
as boilerplate when it contains at least one common tetragram. Boilerplate share is the
share of Item 1A words in boilerplate sentences. Firm-specific category counts use only
the sentences that are not boilerplate.

Explicit interaction. A sentence is an explicit interaction sentence when it names two or
three categories and contains wording that states a causal or compounding relation
(exacerbate, compound, amplify, intensify, in turn, combined with, lead to, result in and
similar terms listed in INTERACTION).

Usage: python "build convergence measures.py" <folder with Filing Texts parts> <output csv>
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tm = load("tm", HERE / "text measures.py")
fp = load("fp", PROJ / "Data Collection" / "filing parser.py")
CATS = tm.CATS
TOKEN = re.compile(r"[a-z]+")
INTERACTION = re.compile(
    r"\b(?:exacerbat\w*|compound\w*|amplif\w*|intensif\w*|magnif\w*|aggravat\w*|worsen\w*|heighten\w*|in turn|"
    r"combined with|coupled with|in combination with|interplay|interact\w*|cascad\w*|knock-on|ripple|spill(?:s|ed)? over|"
    r"spillover\w*|lead to|leads to|led to|leading to|result in|results in|resulted in|resulting in|trigger\w*|"
    r"give rise to|gives rise to|caus(?:e|es|ed|ing))\b", re.I)
P1, P2, P3 = np.uint64(1000003), np.uint64(998244353), np.uint64(1469598103)
LOW, HIGH = 0.30, 0.75


def tetragrams(tokens: list[int]) -> np.ndarray:
    if len(tokens) < 4:
        return np.empty(0, dtype=np.uint64)
    a = np.asarray(tokens, dtype=np.uint64)
    with np.errstate(over="ignore"):
        h = ((a[:-3] * P1 + a[1:-2]) * P2 + a[2:-1]) * P3 + a[3:]
    return h


def final_sample() -> set:
    import pandas as pd
    f = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Firms.csv")
    x = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")
    return set(f["cik"]) - set(x["cik"])


FINAL = final_sample()


def stream(src):
    parts = sorted(src.glob("Filing Texts Part *.jsonl.gz"), key=lambda p: (len(p.stem), p.stem))
    for p in parts:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if int(r["cik"]) in FINAL:
                    yield r


def main(src: Path, out: Path):
    vocab: dict[str, int] = {}
    ids = lambda s: [vocab.setdefault(w, len(vocab) + 1) for w in TOKEN.findall(s.lower())]
    per_year = defaultdict(list)
    docs = defaultdict(int)
    for r in stream(src):
        fy = int(r["fiscal_year"])
        per_year[fy].append(np.unique(tetragrams(ids(r["item1a"]))))
        docs[fy] += 1
    common = {}
    for fy, arrs in per_year.items():
        u, c = np.unique(np.concatenate(arrs), return_counts=True)
        share = c / docs[fy]
        common[fy] = u[(share >= LOW) & (share <= HIGH)]
        print(fy, docs[fy], "documents;", len(u), "tetragrams;", len(common[fy]), "common")
    del per_year
    rows = []
    for r in stream(src):
        cik, fy = int(r["cik"]), int(r["fiscal_year"])
        sents = fp.sentences(r["item1a"])
        words = boiler_words = 0
        spec = dict.fromkeys(CATS, 0)
        n_inter = n_bp = 0
        for s in sents:
            toks = ids(s)
            words += len(toks)
            bp = bool(np.isin(tetragrams(toks), common.get(fy, np.empty(0, dtype=np.uint64))).any())
            cs = tm.classify(s)
            if bp:
                boiler_words += len(toks)
                n_bp += 1
            else:
                for c in cs:
                    spec[c] += 1
            if 2 <= len(cs) < tm.CATALOGUE and INTERACTION.search(s):
                n_inter += 1
        row = {"cik": cik, "fiscal_year": fy, "n_sent_1a": len(sents), "n_boilerplate_sentences": n_bp,
               "boilerplate_share": boiler_words / words if words else float("nan"), "n_interaction": n_inter}
        row.update({f"spec_{c}": spec[c] for c in CATS})
        rows.append(row)
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "filings written to", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
