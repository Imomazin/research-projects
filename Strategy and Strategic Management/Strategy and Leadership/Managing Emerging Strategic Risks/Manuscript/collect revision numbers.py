"""Gather every number quoted in the revised manuscript into Manuscript/Revision Numbers.json.

Sources: the original outputs (Numbers.json, reproduced in Reproduction/), the revision outputs
(Results/Revision), the response validation (Validation), the reproduction checks
(Reproduction) and the price indices. Nothing is typed by hand.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
REV = PROJ / "Results" / "Revision"
VAL = PROJ / "Validation"
REP = PROJ / "Reproduction"
O = json.loads((HERE / "Numbers.json").read_text())
R = json.loads((REV / "Revision Results.json").read_text())
N = {"original": O}


def rec(df):
    return df.replace({np.nan: None}).to_dict(orient="records")


# reproduction
ic = pd.read_csv(REP / "Independent Checks.csv")
N["independent_checks"] = {"match": int((ic["status"] == "match").sum()), "mismatch": int((ic["status"] == "mismatch").sum()),
                           "total": int(ic["status"].isin(["match", "mismatch"]).sum())}
if (REP / "Reproduction Summary.json").exists():
    N["reproduction"] = json.loads((REP / "Reproduction Summary.json").read_text())
att = ic[ic["check"].str.startswith("Episode A firms with severity but no FY2022")]
N["attrition_note"] = att["note"].iloc[0] if len(att) else ""

# principal models
pr = pd.read_csv(REV / "Principal Models Full Inference.csv")
N["principal"] = {f"{r['episode']}|{r['model']}|{r['outcome']}|{r['term']}": r for r in rec(pr)}
pl = pd.read_csv(REV / "Placebo Episode.csv")
N["placebo"] = {f"{r['model']}|{r['outcome']}|{r['term']}": r for r in rec(pl)}
N["clusters"] = R["clusters_episode_a"]

# response measures
rv = pd.read_csv(REV / "Response Measure Variants.csv")
N["response_variants"] = {f"{r['episode']}|{r['measure']}|{r['model']}|{r['outcome']}|{r['term']}": r for r in rec(rv)}
me = pd.read_csv(REV / "Marginal Effects by Response Measure.csv")
N["marginal"] = rec(me)
cr = pd.read_csv(REV / "Category Response Models.csv")
N["category_response"] = rec(cr)
vs = pd.read_csv(VAL / "Response Validation Statistics.csv")
N["validation"] = {f"{r['rule_set']}|{r['sample']}": r for r in rec(vs)}
vc = pd.read_csv(VAL / "Response Validation by Category.csv")
N["validation_category"] = rec(vc)
ve = pd.read_csv(VAL / "Response Validation Errors.csv")
N["validation_errors"] = rec(ve)
samp = pd.read_csv(VAL / "Response Validation Sample.csv")
code = pd.read_csv(VAL / "Response Validation Reference Coding.csv")
N["validation_sample"] = {"items": int(len(samp)), "qualifying": int(code["qualifies"].sum()),
                          "strata": samp["stratum"].value_counts().to_dict(),
                          "divisions": int(samp["division"].nunique()), "years": int(samp["fiscal_year"].nunique()),
                          "response_class": code["response_class"].value_counts().sort_index().to_dict()}
U = pd.read_csv(VAL / "Response Validation Universe Counts.csv")
N["universe"] = U.groupby("stratum")["population_pairs"].sum().astype(int).to_dict()
lmv = (VAL / "Language Model Version.txt").read_text().splitlines()
N["lm_version"] = {l.split()[0]: " ".join(l.split()[1:]) for l in lmv if l.strip()}
N["lm_candidates"] = R.get("lm_candidates")

# share of firms with any response by measure, FY2018 and over time
P = pd.read_csv(PROJ / "Datasets" / "Derived" / "Research Panel.csv", low_memory=False)
RM = pd.read_csv(PROJ / "Datasets" / "Derived" / "Revision" / "Response Measures.csv")
P = P.merge(RM.drop(columns=["accession", "n_sent_response"]), on=["cik", "fiscal_year"], how="left")
P = P[P["n_sent_1a"].notna() & P["fiscal_year"].between(2017, 2025)]
CATS = ["geopolitical", "trade", "regulatory", "cyber", "technology", "supply", "climate", "macro", "pandemic"]
lmf = PROJ / "Datasets" / "Derived" / "Revision" / "Response Candidate Language Model Scores.csv.gz"
if lmf.exists():
    lm = pd.read_csv(lmf)
    lmc = lm[lm["entail_implemented"] >= 0.5].groupby(["cik", "fiscal_year"]).size().rename("lm_pairs").reset_index()
    P = P.merge(lmc, on=["cik", "fiscal_year"], how="left")
    P["lm_pairs"] = P["lm_pairs"].fillna(0)
anyresp = {}
for k, cols in {"original": [f"act_original_{c}" for c in CATS], "revised": [f"act_revised_{c}" for c in CATS],
                "high": [f"act_high_{c}" for c in CATS]}.items():
    anyresp[k] = {int(y): round(100 * float((g[cols].sum(axis=1) > 0).mean()), 1) for y, g in P.groupby("fiscal_year")}
if "lm_pairs" in P:
    anyresp["lm"] = {int(y): round(100 * float((g["lm_pairs"] > 0).mean()), 1) for y, g in P.groupby("fiscal_year")}
N["any_response_pct"] = anyresp
N["high_pairs_total"] = int(P[[f"act_high_{c}" for c in CATS]].sum().sum())
N["high_pairs_by_category"] = {c: int(P[f"act_high_{c}"].sum()) for c in CATS}
N["high_firms_fy2018"] = int((P[P["fiscal_year"] == 2018][[f"act_high_{c}" for c in CATS]].sum(axis=1) > 0).sum())

# recovery and interaction investigations, robustness grid for breadth alone, added checks
N["recovery_investigation"] = rec(pd.read_csv(REV / "Recovery Investigation.csv"))
N["interaction_investigation"] = rec(pd.read_csv(REV / "Interaction Investigation.csv"))
N["grid_h1"] = rec(pd.read_csv(REV / "Robustness Grid Breadth Alone.csv"))
N["preregistered_added"] = rec(pd.read_csv(REV / "Preregistered Checks Added.csv"))
N["survival_logit"] = R["survival_logit"]

# convergence
N["alternative_convergence"] = rec(pd.read_csv(REV / "Alternative Convergence Measures.csv"))
mt = pd.read_csv(REV / "Measure Trends and Dispersion.csv")
N["measure_trends"] = rec(mt)
N["saturation"] = R["saturation"]
sb = pd.read_csv(REV / "Saturation Below Ceiling Firms.csv")
N["below_ceiling"] = rec(sb)
N["determinants"] = rec(pd.read_csv(REV / "Determinants of Breadth.csv"))

# shocks
sh = pd.read_csv(REV / "Shock Models Revision.csv")
N["shock"] = {f"{r['outcome']}|{r['timing']}|{r['effects']}|{r['cluster']}|{r['term']}": r for r in rec(sh)}
N["compounding"] = R["compounding_equivalence"]
N["cpi"] = {"source": R.get("cpi_source"), "interpolated": R.get("cpi_months_interpolated")}
pm = pd.read_csv(PROJ / "Datasets" / "Raw Macro" / "Revision" / "Price Index Retrieval Manifest.csv")
N["price_manifest"] = rec(pm)
vm = pd.read_csv(PROJ / "Datasets" / "Raw Macro" / "Revision" / "Revision Retrieval Manifest.csv")
vm = vm[vm["file"].str.startswith("version check")]
N["macro_version_check"] = {"files": int(len(vm)), "identical": int(vm["identical_to_stored"].astype(str).eq("True").sum())}

# references
rv_ = pd.read_csv(PROJ / "Literature" / "Reference Verification.csv")
N["reference_check"] = rv_["status"].value_counts().to_dict()

(HERE / "Revision Numbers.json").write_text(json.dumps(N, indent=1, default=lambda o: float(o) if np.isscalar(o) else str(o)))
print("keys", len(N))
