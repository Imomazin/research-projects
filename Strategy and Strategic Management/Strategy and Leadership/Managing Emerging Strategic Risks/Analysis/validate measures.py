"""Construct-validity checks for the dictionary measures that do not require human coding.

1. Known groups: category intensity by SIC division in FY2018 (for example supply-chain
   language should be highest in manufacturing and retail).
2. Convergent validity with firm fundamentals: correlation of geopolitical and trade
   intensity with the FY2018 foreign share of pre-tax income.
3. Tracking: annual mean category intensity against the matching macro index
   (fiscal-year averages), 2017 to 2025.
4. Homogenisation: dispersion of breadth by fiscal year.
Output: Results/Measure Validation.json and CSV tables.
"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DER = HERE.parent / "Datasets" / "Derived"
RES = HERE.parent / "Results"
CATS = list(json.loads((HERE / "Risk Taxonomy Dictionary.json").read_text())["categories"].keys())
P = pd.read_csv(DER / "Research Panel.csv")
P = P[P["n_sent_1a"].notna()]
out = {}

y18 = P[P["fiscal_year"] == 2018]
kg = y18.groupby("division")[[f"int_{c}" for c in CATS]].mean() * 100
kg["firms"] = y18.groupby("division")["cik"].nunique()
kg.round(3).to_csv(RES / "Known Groups Intensity.csv")
out["known_groups_pct_of_sentences"] = kg.round(3).to_dict(orient="index")
tests = {}
for c in CATS:
    groups = [g[f"int_{c}"].dropna().values for _, g in y18.groupby("division") if len(g) >= 10]
    h, p = stats.kruskal(*groups)
    tests[c] = {"kruskal_h": h, "p": p}
out["known_groups_kruskal"] = tests

fs = y18[["foreign_share", "int_geopolitical", "int_trade", "int_macro"]].dropna()
out["foreign_share_spearman"] = {c: dict(zip(["rho", "p"], stats.spearmanr(fs["foreign_share"], fs[c])))
                                 for c in ["int_geopolitical", "int_trade", "int_macro"]}
out["foreign_share_n"] = len(fs)

pairs = {"geopolitical": "fy_gpr", "supply": "fy_gscpi", "trade": "fy_epu_trade", "regulatory": "fy_epu_regulation",
         "macro": "fy_epu_us", "pandemic": "fy_wui_global"}
yr = P[P["fiscal_year"].between(2017, 2025)].groupby("fiscal_year")
track = {}
rows = []
for c, m in pairs.items():
    a = yr[f"int_{c}"].mean()
    b = yr[m].mean()
    r, p = stats.pearsonr(a, b)
    track[c] = {"index": m, "pearson_r": r, "p": p, "years": int(len(a))}
    for y in a.index:
        rows.append({"fiscal_year": y, "category": c, "mean_intensity": a[y], "index": m, "index_value": b[y]})
pd.DataFrame(rows).to_csv(RES / "Category Tracking.csv", index=False)
out["tracking"] = track

d = yr["breadth"].agg(["mean", "std", "count"])
d["cv"] = d["std"] / d["mean"]
d["share_nine"] = yr["breadth"].apply(lambda s: (s == 9).mean())
d["share_eight_plus"] = yr["breadth"].apply(lambda s: (s >= 8).mean())
d["linkage_mean"] = yr["linkage"].mean()
d["coverage_mean"] = yr["coverage"].mean()
d["any_action"] = yr["any_action"].mean()
d["item1a_words_median"] = yr["item1a_words"].median()
bal = P[P["fiscal_year"].between(2017, 2025)].groupby("cik")["fiscal_year"].nunique()
b = P[P["cik"].isin(bal[bal == 9].index) & P["fiscal_year"].between(2017, 2025)]
d["breadth_mean_balanced"] = b.groupby("fiscal_year")["breadth"].mean()
out["balanced_firms"] = int(b["cik"].nunique())
d.to_csv(RES / "Breadth Dispersion.csv")
out["dispersion"] = d.round(6).to_dict(orient="index")
(RES / "Measure Validation.json").write_text(json.dumps(out, indent=1, default=float))
print(kg.round(2).to_string())
print(json.dumps({k: out[k] for k in ["foreign_share_spearman", "tracking"]}, indent=1, default=float))
