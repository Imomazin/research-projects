"""Write every candidate sentence-category pair for language-model scoring.

Candidates are the pairs in the validation universe outside the remainder stratum: pairs
flagged by the original, revised or high-confidence rules, and near misses (an
organisational subject and an action verb in a sentence that names the category). In the
reference coding none of the 27 remainder-stratum pairs qualified, so scoring is limited to
the candidates. Classification functions are imported from build response measures.py
unchanged, so strata are identical to those used for the validation draw.

Usage: python "export response candidates.py" <folder with Filing Texts parts> <output .jsonl.gz> [part letters, e.g. ABC]
With part letters, only those parts are read; the per-part outputs are concatenated afterwards
(gzip members concatenate into a valid gzip file).
"""
import gzip
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("brm", HERE / "build response measures.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def main(src: Path, out: Path, parts: str = ""):
    import pandas as pd
    firms = pd.read_csv(B.PROJ / "Datasets" / "Sampling Frame" / "Sample Firms.csv")
    excl = pd.read_csv(B.PROJ / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")
    final = set(firms["cik"]) - set(excl["cik"])
    n = 0
    counts = {}
    with gzip.open(out, "wt") as fo:
        for p in sorted(src.glob("Filing Texts Part *.jsonl.gz"), key=lambda p: (len(p.stem), p.stem)):
            if parts and p.name.split("Part ")[1].split(".")[0] not in parts:
                continue
            with gzip.open(p, "rt") as fh:
                for line in fh:
                    r = json.loads(line)
                    cik, fy = int(r["cik"]), int(r["fiscal_year"])
                    if cik not in final or fy not in B.PERIODS:
                        continue
                    for i, s in enumerate(B.fp.sentences(r.get("item7", "")) + B.fp.sentences(r.get("item1", ""))):
                        a2 = B.v2.action_categories(s)
                        a1 = B.v1.action_categories(s)
                        a3, _ = B.high_confidence(s, a2)
                        terms = set(B.v2.classify(s)) | set(a1)
                        if not terms:
                            continue
                        near = bool(B.v2.SUBJECT.search(s) and B.ANY_VERB.search(s))
                        for c in sorted(terms):
                            st = ("high" if c in a3 else "revised" if c in a2 else "original" if c in a1
                                  else "near miss" if near else "other")
                            if st == "other":
                                continue
                            fo.write(json.dumps({"cik": cik, "fiscal_year": fy, "sentence_index": i, "category": c,
                                                 "stratum": st, "sentence": s.strip()[:2000]}) + "\n")
                            n += 1
                            counts[st] = counts.get(st, 0) + 1
    print(n, "candidate pairs", counts)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "")
