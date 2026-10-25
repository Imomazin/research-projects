"""Illustrative cases for qualitative triangulation.

Rule (fixed before reading any filing text): split the pandemic-episode sample at the median
of fiscal 2018 breadth and by whether the firm reported any documented action in fiscal 2018.
Within each of the four groups take the largest firm by fiscal 2019 revenue whose revenue fell
by more than ten per cent from fiscal 2019 to 2020 and the largest whose revenue did not fall.
For each case the fiscal 2018 material categories, documented actions (with the action
sentences) and outcomes are recorded from the study data.
"""
import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DER = HERE.parent / "Datasets" / "Derived"
CATS = list(json.loads((HERE / "Risk Taxonomy Dictionary.json").read_text())["categories"].keys())


def load(n, p):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


tm = load("tm", HERE / "text measures.py")
fp = load("fp", HERE.parent / "Data Collection" / "filing parser.py")
A = pd.read_csv(DER / "Episode A Frame.csv")
P = pd.read_csv(DER / "Research Panel.csv", low_memory=False)
A = A.join(P[P["fiscal_year"] == 2019].set_index("cik")[["revenue", "name"]], on="cik").dropna(subset=["severity", "recovery", "revenue"])
med = A["breadth"].median()
cases = []
for hb in [False, True]:
    for ac in [False, True]:
        g = A[((A["breadth"] > med) == hb) & ((A["any_action"] == 1) == ac)]
        for outcome, sub in [("revenue fell more than ten per cent", g[g["severity"] < np.log(0.9)]),
                             ("revenue did not fall", g[g["severity"] >= 0])]:
            if len(sub):
                r = sub.sort_values("revenue").iloc[-1]
                cases.append({"cik": int(r["cik"]), "name": r["name"], "breadth_group": "above median" if hb else "at or below median",
                              "documented_action": "yes" if ac else "no", "outcome_group": outcome, "breadth": int(r["breadth"]),
                              "coverage": round(float(r["coverage"]), 3),
                              "material": [c for c in CATS if r[f"mat_{c}"] == 1], "actions": [c for c in CATS if r[f"act_{c}"] > 0],
                              "revenue_fy2019_bn": round(float(r["revenue"]) / 1e9, 2), "severity": round(float(r["severity"]), 3),
                              "recovery": round(float(r["recovery"]), 3), "margin_change": None if pd.isna(r["margin_change"]) else round(float(r["margin_change"]), 3)})
want = {c["cik"] for c in cases}
sent = {}
for p in sorted((Path(__import__("sys").argv[1])).glob("Filing Texts Part *.jsonl.gz")):
    with gzip.open(p, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if int(r["cik"]) in want and int(r["fiscal_year"]) == 2018:
                ss = fp.sentences(r.get("item7", "")) + fp.sentences(r.get("item1", ""))
                sent[int(r["cik"])] = [(tm.action_categories(s), s) for s in ss if tm.action_categories(s)]
for c in cases:
    c["action_sentences"] = [{"categories": a, "sentence": s[:400]} for a, s in sent.get(c["cik"], [])][:6]
(HERE.parent / "Results" / "Illustrative Cases.json").write_text(json.dumps(cases, indent=1))
for c in cases:
    print(c["breadth_group"], c["documented_action"], c["outcome_group"], "|", c["name"], c["breadth"], c["material"], c["actions"], c["severity"], c["recovery"], c["margin_change"])
    for a in c["action_sentences"][:3]:
        print("    ", a["categories"], a["sentence"][:250])
