"""Documented-response measures under three rule sets and the stratified validation draw.

Rule sets (all applied to Items 1 and 7 of each 10-K):
  original   frozen original dictionary and action rules (version one)
  revised    revised dictionary and action rules (version two, used in the first submission)
  high       revised rules plus the high-confidence rules in Response Rules High Confidence.json
             (organisational subject governing a realised verb, no future or aspirational
             wording, no routine treasury instruments, no product-offering descriptions, an
             explicit link to a threat, and a strong purpose link for transaction-only verbs)

Validation universe: every sentence-category pair in Items 1 and 7 of the 787 final
sample firms in which the sentence contains a revised-dictionary category term or is an
original-rule action for that category. Pairs are partitioned into five strata:
  high       high-confidence positive
  revised    revised positive, not high-confidence
  original   original positive, not revised
  near miss  organisational subject and an action verb present, not positive under any rule set
  other      remaining pairs
Within each stratum, category and fiscal-year period (2017-2019, 2020-2022, 2023-2025) a
reservoir sample of fixed size is drawn with seed 20261026. Population counts per cell are
written so that recall can be estimated with design weights.

Usage: python "build response measures.py" <folder with Filing Texts parts> <output folder>
Outputs: Response Measures.csv, Validation Universe Counts.csv, Response Validation Sample.csv
"""
from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent


def load(name, path, dictionary=None):
    old = os.environ.get("RISK_DICTIONARY")
    if dictionary:
        os.environ["RISK_DICTIONARY"] = dictionary
    elif "RISK_DICTIONARY" in os.environ:
        del os.environ["RISK_DICTIONARY"]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if old is None:
        os.environ.pop("RISK_DICTIONARY", None)
    else:
        os.environ["RISK_DICTIONARY"] = old
    return mod


v2 = load("tm_revised", HERE / "text measures.py")
v1 = load("tm_original", HERE / "text measures.py", "Risk Taxonomy Dictionary Original.json")
fp = load("fp", PROJ / "Data Collection" / "filing parser.py")
CATS = v2.CATS
R = json.loads((HERE / "Response Rules High Confidence.json").read_text())
RX = {k: re.compile(v, re.I) for k, v in R.items() if k not in ("version", "notes")}
TRANSACTION = {"acquired", "purchased", "entered into", "signed", "formed", "hedged", "completed"}
PERIODS = {2017: "2017-2019", 2018: "2017-2019", 2019: "2017-2019", 2020: "2020-2022", 2021: "2020-2022",
           2022: "2020-2022", 2023: "2023-2025", 2024: "2023-2025", 2025: "2023-2025"}
SIZE = {"high": 3, "revised": 3, "original": 2, "near miss": 2, "other": 1}
ANY_VERB = v2.VERBS


def high_confidence(s: str, revised_cats: list[str]) -> tuple[list[str], dict]:
    """Return the categories that pass the high-confidence rules and the rule flags."""
    flags = {"subject_verb": bool(RX["subject_verb"].search(s)), "future": bool(RX["exclude_future_or_aspiration"].search(s)),
             "treasury": bool(RX["routine_treasury"].search(s)), "offering": bool(RX["exclude_offering"].search(s)),
             "link": bool(RX["threat_link"].search(s)), "strong_link": bool(RX["strong_link"].search(s)),
             "resource": bool(RX["resource_commitment"].search(s))}
    if not revised_cats or not flags["subject_verb"] or flags["future"] or flags["treasury"] or flags["offering"] or not flags["link"]:
        return [], flags
    verbs = set()
    for m in RX["subject_verb"].finditer(s):
        g = m.group(0).lower()
        verbs.add("entered into" if g.endswith("entered into") else "passed through" if g.endswith("passed through") else g.split()[-1])
    if verbs and verbs <= TRANSACTION and not flags["strong_link"]:
        return [], flags
    return list(revised_cats), flags


def main(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    firms = __import__("pandas").read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Firms.csv")
    excl = __import__("pandas").read_csv(PROJ / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")
    final = set(firms["cik"]) - set(excl["cik"])
    division = dict(zip(firms["cik"], firms["division"]))
    rng = random.Random(20261026)
    seen: Counter = Counter()
    reservoir: dict = defaultdict(list)
    rows = []
    parts = sorted(src.glob("Filing Texts Part *.jsonl.gz"), key=lambda p: (len(p.stem), p.stem))
    for p in parts:
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                cik, fy = int(r["cik"]), int(r["fiscal_year"])
                sents = fp.sentences(r.get("item7", "")) + fp.sentences(r.get("item1", ""))
                row = {"cik": cik, "fiscal_year": fy, "accession": r["accession"], "n_sent_response": len(sents)}
                cnt = {k: Counter() for k in ("original", "revised", "high", "high_resource")}
                n_high = 0
                for s in sents:
                    a2 = v2.action_categories(s)
                    a1 = v1.action_categories(s)
                    a3, flags = high_confidence(s, a2)
                    cnt["revised"].update(a2)
                    cnt["original"].update(a1)
                    cnt["high"].update(a3)
                    if a3:
                        n_high += 1
                        if flags["resource"]:
                            cnt["high_resource"].update(a3)
                    if cik not in final or fy not in PERIODS:
                        continue
                    terms = set(v2.classify(s)) | set(a1)
                    if not terms:
                        continue
                    near = bool(v2.SUBJECT.search(s) and ANY_VERB.search(s))
                    for c in terms:
                        if c in a3:
                            st = "high"
                        elif c in a2:
                            st = "revised"
                        elif c in a1:
                            st = "original"
                        elif near:
                            st = "near miss"
                        else:
                            st = "other"
                        cell = (st, c, PERIODS[fy])
                        seen[cell] += 1
                        k = SIZE[st]
                        item = {"cik": cik, "fiscal_year": fy, "division": division.get(cik, ""), "stratum": st,
                                "category": c, "period": PERIODS[fy], "sentence": s.strip(),
                                "original_positive": int(c in a1), "revised_positive": int(c in a2),
                                "high_positive": int(c in a3)}
                        if len(reservoir[cell]) < k:
                            reservoir[cell].append(item)
                        else:
                            j = rng.randrange(seen[cell])
                            if j < k:
                                reservoir[cell][j] = item
                row["n_high_sentences"] = n_high
                for c in CATS:
                    for k in ("original", "revised", "high", "high_resource"):
                        row[f"act_{k}_{c}"] = cnt[k][c]
                rows.append(row)
    with open(out / "Response Measures.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with open(out / "Validation Universe Counts.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "category", "period", "population_pairs", "sampled_pairs"])
        for cell, n in sorted(seen.items()):
            w.writerow([*cell, n, len(reservoir[cell])])
    sample = [it for cell in sorted(reservoir) for it in reservoir[cell]]
    random.Random(7).shuffle(sample)
    for i, it in enumerate(sample, 1):
        it["item_id"] = f"R{i:03d}"
    with open(out / "Response Validation Sample.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item_id"] + [k for k in sample[0] if k != "item_id"])
        w.writeheader()
        w.writerows(sample)
    print(len(rows), "filings;", len(sample), "validation pairs;", sum(seen.values()), "universe pairs")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
