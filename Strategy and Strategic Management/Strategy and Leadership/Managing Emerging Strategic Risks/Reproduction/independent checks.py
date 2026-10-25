"""Checks written separately from the analysis code.

The sample draw, panel assembly, episode frames, winsorisation, standardisation and
clustered regressions are re-implemented here with numpy and pandas only, starting
from Frame Candidates.csv, Text Measures.csv, Updating Measure.csv, Financial
Panel.csv and Frame Validation Exclusions.csv. Nothing is imported from the analysis
scripts. Results are compared with the committed Numbers.json.

Usage: python "independent checks.py" [project folder]   (defaults to the parent folder)
Output: Independent Checks.csv and Exit and Attrition Check.csv in this folder.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent
FR, DER = ROOT / "Datasets" / "Sampling Frame", ROOT / "Datasets" / "Derived"
N = json.loads((HERE.parent / "Manuscript" / "Numbers.json").read_text())
CATS = ["geopolitical", "trade", "regulatory", "cyber", "technology", "supply", "climate", "macro", "pandemic"]
rows = []


def check(name, original, reproduced, tol=1e-6, note=""):
    o, r = float(original), float(reproduced)
    rows.append({"check": name, "original": o, "independent": r, "abs_difference": abs(o - r),
                 "status": "match" if abs(o - r) <= tol else "mismatch", "note": note})


# ---------------------------------------------------------------- sample
cand = pd.read_csv(FR / "Frame Candidates.csv")
sic = pd.to_numeric(cand["sic"], errors="coerce")
ok = (cand["entity_type"] == "operating") & sic.notna() & ~sic.between(6000, 6999) & ~sic.between(4900, 4999) \
    & (sic < 9000) & (cand["has_fy2018_tenk"] == 1)
elig = cand[ok].assign(sic=sic[ok])
check("Candidates with float of at least 0.5 billion", N["frame_float_half_bn"], len(cand))
check("Eligible frame", N["frame_eligible"], len(elig))
bins = [(100, 1000, "Agriculture"), (1000, 1500, "Mining"), (1500, 1800, "Construction"), (2000, 4000, "Manufacturing"),
        (4000, 4900, "Transportation and communications"), (5000, 5200, "Wholesale trade"), (5200, 6000, "Retail trade"),
        (7000, 9000, "Services")]
elig["div"] = "Other"
for lo, hi, lab in bins:
    elig.loc[elig["sic"].between(lo, hi - 1e-9), "div"] = lab
cnt = elig["div"].value_counts()
quota = cnt / cnt.sum() * 800
alloc = np.floor(quota).astype(int)
for d in (quota - alloc).sort_values(ascending=False).index[: 800 - alloc.sum()]:
    alloc[d] += 1
rng = np.random.default_rng(20181231)
chosen = []
for d, k in alloc.items():
    pool = elig[elig["div"] == d].sort_values("cik")["cik"].to_numpy()
    chosen += list(pool[np.sort(rng.choice(len(pool), size=k, replace=False))])
sample = pd.read_csv(FR / "Sample Firms.csv")
check("Sample drawn", N["sample_drawn"], len(chosen))
check("Sample firm identifiers identical to Sample Firms.csv (1 = yes)", 1, float(set(chosen) == set(sample["cik"])))
excl = pd.read_csv(FR / "Frame Validation Exclusions.csv")
check("Validation exclusions all drawn from the sample (1 = yes)", 1, float(excl["cik"].isin(chosen).all()))
final = sorted(set(chosen) - set(excl["cik"]))
check("Final sample", N["sample_final"], len(final))

# rule-based recreation of the implausible-float exclusions from FY2018 accounting values
fin = pd.read_csv(DER / "Financial Panel.csv", parse_dates=["fy_end"])
f18 = fin[fin["fiscal_year"] == 2018].set_index("cik")
s = sample.set_index("cik")
big = pd.concat([f18["assets"], f18["revenue"]], axis=1).max(axis=1).reindex(s.index)
small = (f18["assets"].reindex(s.index).fillna(0) < 1e8) & (f18["revenue"].reindex(s.index).fillna(0) < 1e8)
rule = s.index[(s["float"] > 20 * big) & small & big.notna()]
listed = excl.loc[excl["reason"].str.startswith("Implausible"), "cik"]
check("Implausible-float exclusions recreated by rule", len(listed), len(set(rule)),
      note=f"rule-only firms: {sorted(set(rule) - set(listed))}; listed-only firms: {sorted(set(listed) - set(rule))}")
no_usd = [c for c in s.index if c not in f18.index or pd.isna(f18.loc[c, "assets"])]
rows.append({"check": "Sample firms with no FY2018 US-dollar assets in XBRL", "original": np.nan, "independent": len(no_usd),
             "abs_difference": np.nan, "status": "information", "note": f"ciks: {no_usd}"})

# ---------------------------------------------------------------- filings and exits
idx = pd.read_csv(ROOT / "Datasets" / "Filings Index.csv")
idx = idx[idx["cik"].isin(final)]
check("Filings in final sample", N["filings"], len(idx))
last = idx.groupby("cik")["fiscal_year"].max()
first = idx.groupby("cik")["fiscal_year"].min()
exit_rows = pd.DataFrame({"last_fiscal_year": last.value_counts().sort_index()})
exit_rows["firms"] = exit_rows["last_fiscal_year"]
exit_rows = last.value_counts().sort_index().rename_axis("last 10-K fiscal year").rename("firms").reset_index()

# ---------------------------------------------------------------- text measures to firm-year variables
t = pd.read_csv(DER / "Text Measures.csv")
t = t[t["cik"].isin(final) & t["fiscal_year"].between(2017, 2025)]
fin_keys = fin[fin["cik"].isin(final)][["cik", "fiscal_year"]]
t = t.merge(fin_keys, on=["cik", "fiscal_year"], how="inner")
t = t[t["n_sent_1a"].notna()]
C = t[[f"cnt_{c}" for c in CATS]].to_numpy(float)
A = t[[f"act_{c}" for c in CATS]].to_numpy(float)
mat = C >= 3
t["breadth"] = mat.sum(1)
t["coverage"] = np.where(mat.sum(1) > 0, (mat & (A > 0)).sum(1) / np.maximum(mat.sum(1), 1), np.nan)
t["linkage"] = t["n_linked"] / t["n_sent_1a"].replace(0, np.nan)
check("Panel firm-years with Item 1A", N["panel_firm_years"], len(t))
check("Item 1A sentences in total", N["sentences_item1a_total"], t["n_sent_1a"].sum())
g = t.groupby("fiscal_year")
for y in (2017, 2018, 2020, 2025):
    check(f"Mean breadth FY{y}", N["breadth_mean"][str(y)], round(g["breadth"].mean()[y], 2), tol=0.005)
    check(f"Share with eight or more categories FY{y} (per cent)", N["share_eight_plus_pct"][str(y)],
          round(100 * (g["breadth"].apply(lambda b: (b >= 8).mean())[y]), 1), tol=0.05)
    check(f"Share with all nine categories FY{y} (per cent)", N["share_nine_pct"][str(y)],
          round(100 * (g["breadth"].apply(lambda b: (b == 9).mean())[y]), 1), tol=0.05)
    check(f"Coefficient of variation of breadth FY{y}", N["breadth_cv"][str(y)],
          round(g["breadth"].std()[y] / g["breadth"].mean()[y], 3), tol=0.0005)
    check(f"Mean linkage FY{y} (per cent)", N["linkage_pct"][str(y)], round(100 * g["linkage"].mean()[y], 2), tol=0.005)
    check(f"Mean coverage FY{y} (per cent)", N["coverage_mean_pct"][str(y)], round(100 * g["coverage"].mean()[y], 1), tol=0.05)
    check(f"Median Item 1A words FY{y}", N["median_item1a_words"][str(y)], int(g["item1a_words"].median()[y]), tol=0.5)
for c in ["technology", "trade", "geopolitical", "pandemic"]:
    for y in (2017, 2025):
        check(f"Share with material {c} FY{y} (per cent)", N["material_pct"][c][str(y)],
              round(100 * (g[f"cnt_{c}"].apply(lambda v: (v >= 3).mean())[y]), 1), tol=0.05)
bal = t.groupby("cik")["fiscal_year"].nunique()
check("Balanced panel firms", N["balanced_firms"], int((bal == 9).sum()))

# divisions in the final sample
div_counts = sample[sample["cik"].isin(final)]["division"].value_counts()
for d, k in div_counts.items():
    rows.append({"check": f"Final sample firms in {d}", "original": np.nan, "independent": k, "abs_difference": np.nan,
                 "status": "information", "note": ""})

# ---------------------------------------------------------------- episode A rebuilt and estimated with numpy
F = fin[fin["cik"].isin(final)].copy()
F["liab"] = F["liabilities"].fillna(F["assets"] - F["equity"])
F["opinc"] = F["operating_income"].fillna(F["revenue"] - F["costs_and_expenses"])
F["lnrev"] = np.log(F["revenue"].where(F["revenue"] > 0))
F["margin"] = F["opinc"] / F["revenue"].where(F["revenue"] > 0)
W = lambda col, y: F[F["fiscal_year"] == y].set_index("cik")[col]
x = t[t["fiscal_year"] == 2018].set_index("cik").copy()
upd = pd.read_csv(DER / "Updating Measure.csv").set_index(["cik", "fiscal_year"])["updating"]
for c in CATS:
    x[f"int_{c}"] = x[f"cnt_{c}"] / x["n_sent_1a"].replace(0, np.nan)
x["ln_words"] = np.log1p(x["item1a_words"])
b19 = F[F["fiscal_year"] == 2019].set_index("cik")
x["ln_assets"] = np.log(b19["assets"].where(b19["assets"] > 0)).reindex(x.index)
x["leverage"] = (b19["liab"] / b19["assets"]).reindex(x.index)
x["cash_ratio"] = (b19["cash"] / b19["assets"]).reindex(x.index)
x["roa"] = (b19["net_income"] / b19["assets"]).reindex(x.index)
x["prior_growth"] = ((W("lnrev", 2019) - W("lnrev", 2017)) / 2).reindex(x.index)
x["severity"] = (W("lnrev", 2020) - W("lnrev", 2019)).reindex(x.index)
x["recovery"] = (W("lnrev", 2022) - W("lnrev", 2019)).reindex(x.index)
x["margin_change"] = (W("margin", 2020) - W("margin", 2019)).reindex(x.index)
attr = sample.set_index("cik")
x["sic2"] = (attr["sic"] // 100).astype(int).reindex(x.index)
x["fye"] = pd.to_datetime(F[F["fiscal_year"] == 2018].set_index("cik")["fy_end"]).dt.month.reindex(x.index)


def wins(s):
    lo, hi = s.quantile([0.01, 0.99])
    return s.clip(lo, hi)


for c in ["severity", "recovery", "margin_change", "leverage", "cash_ratio", "roa", "prior_growth"]:
    x[c] = wins(x[c])
for c in ["breadth", "coverage"]:
    x[c + "_z"] = (x[c] - x[c].mean()) / x[c].std()
x["inter"] = x["breadth_z"] * x["coverage_z"]
INTS = [f"int_{c}" for c in CATS]
CTRL = ["ln_assets", "leverage", "cash_ratio", "roa", "prior_growth", "ln_words"]


def cluster_ols(d, y, rhs):
    d = d.dropna(subset=[y] + rhs + ["sic2", "fye"])
    D = pd.get_dummies(d[["sic2", "fye"]].astype(str), drop_first=True, dtype=float)
    X = np.column_stack([np.ones(len(d)), d[rhs].to_numpy(float), D.to_numpy()])
    Y = d[y].to_numpy(float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    e = Y - X @ beta
    k = np.linalg.matrix_rank(X)
    groups = d["sic2"].to_numpy()
    meat = np.zeros((X.shape[1], X.shape[1]))
    for gval in np.unique(groups):
        s_ = X[groups == gval].T @ e[groups == gval]
        meat += np.outer(s_, s_)
    G, n = len(np.unique(groups)), len(d)
    V = (G / (G - 1)) * ((n - 1) / (n - k)) * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))[1:1 + len(rhs)]
    tval = beta[1:1 + len(rhs)] / se
    return dict(zip(rhs, zip(beta[1:1 + len(rhs)], se, 2 * stats.norm.sf(np.abs(tval)),
                             2 * stats.t.sf(np.abs(tval), G - 1)))), n, G


specs = {"H1": ["breadth_z"], "H2": ["coverage_z"], "H3": ["breadth_z", "coverage_z", "inter"]}
for y in ["severity", "margin_change", "recovery"]:
    for h, terms in specs.items():
        res, n, G = cluster_ols(x, y, terms + INTS + CTRL)
        for term in terms:
            key = f"A|{h}|{y}|" + ("breadth_z:coverage_z" if term == "inter" else term)
            o = N["episode"][key]
            b, se, p, pt = res[term]
            check(f"Episode A {h} {y} {term}: coefficient", o["b"], b, tol=1e-6)
            check(f"Episode A {h} {y} {term}: clustered standard error", o["se"], se, tol=1e-6)
            check(f"Episode A {h} {y} {term}: p-value (normal reference, as in the original)", o["p"], p, tol=1e-6)
            rows.append({"check": f"Episode A {h} {y} {term}: p-value with t({G - 1}) reference", "original": o["p"],
                         "independent": pt, "abs_difference": abs(o["p"] - pt), "status": "information",
                         "note": "small-cluster reference distribution; not reported in the original"})
        check(f"Episode A {h} {y}: observations", N["episode"][f"A|{h}|{y}|{terms[0] if terms[0] != 'inter' else 'breadth_z'}"]["n"], n)
        check(f"Episode A {h} {y}: clusters", N["episode"][f"A|{h}|{y}|{terms[0]}"]["clusters"], G)

# ---------------------------------------------------------------- attrition: are exits retained?
A18 = x.index
alive = {y: set(F[(F["fiscal_year"] == y) & F["revenue"].notna()]["cik"]) for y in range(2019, 2026)}
att = []
for y in range(2019, 2026):
    att.append({"fiscal year": y, "episode A firms with revenue": len(set(A18) & alive[y]),
                "episode A firms": len(A18)})
attdf = pd.DataFrame(att)
lost = x[x["severity"].notna() & x["recovery"].isna()]
kept = x[x["severity"].notna() & x["recovery"].notna()]
tt = stats.ttest_ind(lost["breadth"], kept["breadth"], equal_var=False)
rows.append({"check": "Episode A firms with severity but no FY2022 recovery outcome", "original": np.nan,
             "independent": len(lost), "abs_difference": np.nan, "status": "information",
             "note": f"mean breadth {lost['breadth'].mean():.2f} versus {kept['breadth'].mean():.2f} for retained firms; Welch p = {tt.pvalue:.3f}"})
exit_rows.to_csv(HERE / "Last Filing Year of Sample Firms.csv", index=False)
attdf.to_csv(HERE / "Exit and Attrition Check.csv", index=False)
out = pd.DataFrame(rows)
out.to_csv(HERE / "Independent Checks.csv", index=False)
print(out["status"].value_counts().to_string())
print(out[out["status"] == "mismatch"].to_string())
