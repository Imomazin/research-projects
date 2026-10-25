"""Build firm-year text measures from the stored 10-K sections.

Usage: python "build text measures.py" <folder with Filing Texts parts> <output folder>

Outputs
  Text Measures.csv            one row per filing (firm by fiscal year)
  Category Pairs.csv           linked-sentence counts by category pair and filing
  Validation Sample.csv        stratified random sentences for manual coding
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tm = load("tm", HERE / "text measures.py")
fp = load("fp", HERE.parent / "Data Collection" / "filing parser.py")
CATS = tm.CATS
MATERIAL = 3


def words(text: str) -> int:
    return len(text.split())


def main(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    parts = sorted(src.glob("Filing Texts Part *.jsonl.gz"), key=lambda p: (len(p.stem), p.stem))
    rows, pair_rows = [], []
    prev_vec: dict[int, tuple[int, Counter]] = {}
    rng = random.Random(20251025)
    pool = {c: [] for c in CATS}
    pool["none"] = []
    pool_action = []
    def stream():
        for p in parts:
            with gzip.open(p, "rt") as fh:
                for line in fh:
                    yield json.loads(line)

    for r in stream():  # filings are stored firm by firm in fiscal-year order
        cik, fy = int(r["cik"]), int(r["fiscal_year"])
        s1a = fp.sentences(r["item1a"])
        resp_sents = fp.sentences(r.get("item7", "")) + fp.sentences(r.get("item1", ""))
        rp = tm.risk_profile(s1a)
        rs = tm.response_profile(resp_sents)
        vec = tm.term_vector(r["item1a"])
        upd = float("nan")
        if cik in prev_vec and prev_vec[cik][0] == fy - 1:
            upd = 1 - tm.cosine(vec, prev_vec[cik][1])
        prev_vec[cik] = (fy, vec)
        row = {"cik": cik, "fiscal_year": fy, "accession": r["accession"], "filing_date": r["filing_date"],
               "report_date": r["report_date"], "item1a_words": words(r["item1a"]),
               "item7_words": words(r.get("item7", "")), "item1_words": words(r.get("item1", "")),
               "n_sent_1a": rp["n_sent"], "n_linked": rp["n_linked"], "n_catalogue": rp["n_catalogue"],
               "n_sent_response": len(resp_sents), "n_action": rs["n_action"], "updating": upd}
        counts = []
        for c in CATS:
            row[f"cnt_{c}"] = rp[f"cnt_{c}"]
            row[f"act_{c}"] = rs[f"act_{c}"]
            counts.append(rp[f"cnt_{c}"])
        rows.append(row)
        for k, v in rp["pairs"].items():
            a, b = k.split("|")
            pair_rows.append({"cik": cik, "fiscal_year": fy, "cat_a": a, "cat_b": b, "n": v})
        # validation pools
        for s in s1a:
            cs = tm.classify(s)
            if len(cs) == 1:
                pool[cs[0]].append((cik, fy, "item1a", s))
            elif not cs and rng.random() < 0.02:
                pool["none"].append((cik, fy, "item1a", s))
        for s in resp_sents:
            ac = tm.action_categories(s)
            if ac and rng.random() < 0.2:
                pool_action.append((cik, fy, "item1 or item7", s, "|".join(ac)))
    with open(out / "Text Measures.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(out / "Category Pairs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cik", "fiscal_year", "cat_a", "cat_b", "n"])
        w.writeheader()
        w.writerows(pair_rows)
    sample = []
    for c, items in pool.items():
        rng.shuffle(items)
        for it in items[:40]:
            sample.append({"cik": it[0], "fiscal_year": it[1], "section": it[2], "sentence": it[3],
                           "dictionary_label": c, "coder_label": "", "coder_notes": ""})
    rng.shuffle(pool_action)
    for it in pool_action[:120]:
        sample.append({"cik": it[0], "fiscal_year": it[1], "section": it[2], "sentence": it[3],
                       "dictionary_label": "action:" + it[4], "coder_label": "", "coder_notes": ""})
    with open(out / "Validation Sample.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sample[0].keys()))
        w.writeheader()
        w.writerows(sample)
    print(len(rows), "filings;", len(pair_rows), "pair rows;", len(sample), "validation sentences")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
