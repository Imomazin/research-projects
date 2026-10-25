"""Precision, recall, F1 and confusion matrices for the three documented-response rule sets.

Reference labels: Response Validation Reference Coding.csv (AI-assisted reference coding,
not human annotation). When two human coding sheets exist, run compute agreement.py
and replace the reference labels with the resolved human labels.

Design: the sample is stratified by rule-set stratum, category and period. Each item
carries a design weight (population pairs in its cell divided by pairs sampled), so
population precision and recall are estimated with weights. Unweighted counts and
Wilson intervals for precision are also reported. Weighted intervals come from 2,000
bootstrap resamples drawn within cells.

Usage: python "validate response measures.py"
Outputs: Response Validation Statistics.csv, Response Validation Confusion.csv,
Response Validation by Category.csv, Response Validation Errors.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
S = pd.read_csv(HERE / "Response Validation Sample.csv")
C = pd.read_csv(HERE / "Response Validation Reference Coding.csv")[["item_id", "category_relevant", "response_class",
                                                                     "threat_link", "status", "qualifies", "notes"]]
U = pd.read_csv(HERE / "Response Validation Universe Counts.csv")
D = S.merge(C, on="item_id")
D = D.merge(U, on=["stratum", "category", "period"])
D["w"] = D["population_pairs"] / D["sampled_pairs"]
RULES = {"Original rules": "original_positive", "Revised rules": "revised_positive", "High-confidence rules": "high_positive"}
LM = HERE / "Response Validation Language Model Scores.csv"
if LM.exists():
    lm = pd.read_csv(LM)
    D = D.merge(lm, on="item_id", how="left")
    D["lm_positive"] = (D["entail_implemented"] >= 0.5).astype(int)
    D["lm_and_high"] = ((D["lm_positive"] == 1) & (D["revised_positive"] == 1)).astype(int)
    RULES["Language model (entailment at least 0.5)"] = "lm_positive"
    RULES["Revised rules confirmed by language model"] = "lm_and_high"
    D["lm_candidates"] = ((D["lm_positive"] == 1) & (D["stratum"] != "other")).astype(int)
    RULES["Language model on candidate pairs (measure used in the models)"] = "lm_candidates"


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def metrics(d, col, y="qualifies"):
    w = d["w"]
    tp = (w * ((d[col] == 1) & (d[y] == 1))).sum()
    fp = (w * ((d[col] == 1) & (d[y] == 0))).sum()
    fn = (w * ((d[col] == 0) & (d[y] == 1))).sum()
    tn = (w * ((d[col] == 0) & (d[y] == 0))).sum()
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec == prec and rec == rec and prec + rec else np.nan
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": prec, "recall": rec, "f1": f1}


def boot(d, col, B=2000, seed=20261029):
    rng = np.random.default_rng(seed)
    cells = [g for _, g in d.groupby(["stratum", "category", "period"])]
    out = []
    for _ in range(B):
        parts = [g.iloc[rng.integers(0, len(g), len(g))] for g in cells]
        m = metrics(pd.concat(parts), col)
        out.append((m["precision"], m["recall"], m["f1"]))
    a = np.array(out, dtype=float)
    return np.nanpercentile(a, [2.5, 97.5], axis=0)


rows, conf = [], []
for name, col in RULES.items():
    for label, sub in (("All reference items", D), ("Excluding links inferred from country and timing",
                                                     D[~D["notes"].str.contains("implied", na=False)])):
        m = metrics(sub, col)
        ci = boot(sub, col)
        k = int(((sub[col] == 1) & (sub["qualifies"] == 1)).sum())
        n = int((sub[col] == 1).sum())
        lo, hi = wilson(k, n)
        rows.append({"rule_set": name, "sample": label, "items_flagged": n, "items_flagged_qualifying": k,
                     "precision_unweighted": k / n if n else np.nan, "precision_unweighted_wilson_low": lo,
                     "precision_unweighted_wilson_high": hi, "precision_weighted": m["precision"],
                     "precision_ci_low": ci[0, 0], "precision_ci_high": ci[1, 0], "recall_weighted": m["recall"],
                     "recall_ci_low": ci[0, 1], "recall_ci_high": ci[1, 1], "f1_weighted": m["f1"],
                     "f1_ci_low": ci[0, 2], "f1_ci_high": ci[1, 2],
                     "estimated_population_flagged": m["tp"] + m["fp"], "estimated_population_true": m["tp"] + m["fn"]})
        if label == "All reference items":
            for pred in (1, 0):
                for truth in (1, 0):
                    cell = sub[(sub[col] == pred) & (sub["qualifies"] == truth)]
                    conf.append({"rule_set": name, "rule_flags": pred, "reference_qualifies": truth,
                                 "items": len(cell), "estimated_population_pairs": cell["w"].sum()})
pd.DataFrame(rows).to_csv(HERE / "Response Validation Statistics.csv", index=False)
pd.DataFrame(conf).to_csv(HERE / "Response Validation Confusion.csv", index=False)

cat = []
for name, col in RULES.items():
    for c, g in D.groupby("category"):
        n = int((g[col] == 1).sum())
        k = int(((g[col] == 1) & (g["qualifies"] == 1)).sum())
        m = metrics(g, col)
        lo, hi = wilson(k, n)
        cat.append({"rule_set": name, "category": c, "items_flagged": n, "items_qualifying": k,
                    "precision_unweighted": k / n if n else np.nan, "wilson_low": lo, "wilson_high": hi,
                    "precision_weighted": m["precision"], "recall_weighted": m["recall"],
                    "reference_positives_in_sample": int(g["qualifies"].sum())})
pd.DataFrame(cat).to_csv(HERE / "Response Validation by Category.csv", index=False)


def reason(r):
    n = str(r["notes"]).lower()
    if r["category_relevant"] == 0:
        if "product" in n or "customer" in n or "offering" in n or "service" in n:
            return "product or customer offering, not the firm's own threat"
        if "label" in n or "rate schedule" in n or "tariff" in n:
            return "category word with another meaning"
        return "category not relevant"
    if "treasury" in n or "hedg" in n or "swap" in n:
        return "routine treasury instrument"
    if "acquisition" in n:
        return "acquisition without risk purpose"
    if r["response_class"] == 4:
        return "plan, target or conditional statement"
    if r["response_class"] == 0:
        return "no organisational action"
    if r["threat_link"] == 0:
        return "action without a stated link to the threat"
    if r["response_class"] == 1:
        return "routine operational activity"
    return "other"


err = []
for name, col in RULES.items():
    fp = D[(D[col] == 1) & (D["qualifies"] == 0)]
    for rs, g in fp.groupby(fp.apply(reason, axis=1)):
        err.append({"rule_set": name, "error": "false positive", "reason": rs, "items": len(g), "weighted": g["w"].sum()})
    fn = D[(D[col] == 0) & (D["qualifies"] == 1)]
    for st, g in fn.groupby("stratum"):
        err.append({"rule_set": name, "error": "false negative", "reason": f"stratum: {st}", "items": len(g), "weighted": g["w"].sum()})
pd.DataFrame(err).to_csv(HERE / "Response Validation Errors.csv", index=False)
pd.set_option("display.width", 220)
print(pd.DataFrame(rows)[["rule_set", "sample", "items_flagged", "precision_unweighted", "precision_weighted", "recall_weighted",
                          "f1_weighted", "precision_ci_low", "precision_ci_high", "recall_ci_low", "recall_ci_high"]].round(3).to_string())
print(pd.DataFrame(err).to_string())
