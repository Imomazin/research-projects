"""Year-on-year updating of Item 1A: one minus the cosine similarity of content-word
frequency vectors (stop words and words under three letters removed) between a
firm's Item 1A and its previous fiscal year's Item 1A.

Usage: python "build updating measure.py" <folder with Filing Texts parts> <output csv>
"""
import csv
import gzip
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

WORD = re.compile(r"[a-z][a-z\-']{2,}")


def vec(text):
    return Counter(w for w in WORD.findall(text.lower()) if w not in ENGLISH_STOP_WORDS)


def cos(a, b):
    num = sum(a[k] * b[k] for k in set(a) & set(b))
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else float("nan")


src, out = Path(sys.argv[1]), Path(sys.argv[2])
parts = sorted(src.glob("Filing Texts Part *.jsonl.gz"), key=lambda p: (len(p.stem), p.stem))
prev, rows = {}, []
for p in parts:
    with gzip.open(p, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            cik, fy = int(r["cik"]), int(r["fiscal_year"])
            v = vec(r["item1a"])
            u = float("nan")
            if cik in prev and prev[cik][0] == fy - 1 and v and prev[cik][1]:
                u = 1 - cos(v, prev[cik][1])
            prev[cik] = (fy, v)
            rows.append({"cik": cik, "fiscal_year": fy, "updating": u})
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["cik", "fiscal_year", "updating"])
    w.writeheader()
    w.writerows(rows)
print(len(rows))
