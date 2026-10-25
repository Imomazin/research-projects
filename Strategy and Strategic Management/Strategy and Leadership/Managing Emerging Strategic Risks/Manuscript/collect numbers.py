"""Gather every number quoted in the manuscript from the Results and Datasets files
into Manuscript/Numbers.json. The manuscript builder reads only from this file."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
RES = PROJ / "Results"
DER = PROJ / "Datasets" / "Derived"
M = json.loads((RES / "Model Results.json").read_text())
V = json.loads((RES / "Measure Validation.json").read_text())
N: dict = {}

log = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Selection Log.csv")
N["frame_float_entities"] = int(log.iloc[0, 1])
N["frame_float_half_bn"] = int(log.iloc[1, 1])
N["frame_eligible"] = int(log.iloc[7, 1])
N["sample_drawn"] = int(log.iloc[8, 1])
N["sample_final"] = int(log.iloc[9, 1])
N["validation_excluded"] = N["sample_drawn"] - N["sample_final"]
idx = pd.read_csv(PROJ / "Datasets" / "Filings Index.csv")
excl = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")
idx = idx[~idx["cik"].isin(excl["cik"])]
N["filings"] = int(len(idx))
N["filings_item1a_ok_pct"] = round(100 * idx["item1a_ok"].mean(), 1)
N["filings_item7_ok_pct"] = round(100 * idx["item7_ok"].mean(), 1)
N["filings_by_year"] = idx.groupby("fiscal_year").size().astype(int).to_dict()
facts_rows = 2240714
N["xbrl_fact_rows"] = facts_rows
P = pd.read_csv(DER / "Research Panel.csv", low_memory=False)
P = P[P["n_sent_1a"].notna() & P["fiscal_year"].between(2017, 2025)]
N["panel_firm_years"] = int(len(P))
N["panel_firms"] = int(P["cik"].nunique())
N["sentences_item1a_total"] = int(P["n_sent_1a"].sum())
N["median_item1a_words"] = {int(k): int(v) for k, v in P.groupby("fiscal_year")["item1a_words"].median().items()}

d = V["dispersion"]
N["breadth_mean"] = {int(k): round(v["mean"], 2) for k, v in d.items()}
N["breadth_cv"] = {int(k): round(v["cv"], 3) for k, v in d.items()}
N["breadth_balanced"] = {int(k): round(v["breadth_mean_balanced"], 2) for k, v in d.items()}
N["balanced_firms"] = V["balanced_firms"]
N["linkage_pct"] = {int(k): round(100 * v["linkage_mean"], 2) for k, v in d.items()}
N["any_action_pct"] = {int(k): round(100 * v["any_action"], 1) for k, v in d.items()}
N["coverage_mean_pct"] = {int(k): round(100 * v["coverage_mean"], 1) for k, v in d.items()}
N["share_nine_pct"] = {int(k): round(100 * v["share_nine"], 1) for k, v in d.items()}
N["share_eight_plus_pct"] = {int(k): round(100 * v["share_eight_plus"], 1) for k, v in d.items()}
tr = M["trends"]
CATS = ["geopolitical", "trade", "regulatory", "cyber", "technology", "supply", "climate", "macro", "pandemic"]
N["material_pct"] = {c: {int(y): round(100 * tr[y][f"share_material_{c}"], 1) for y in tr} for c in CATS}
N["tracking"] = {c: {"r": round(v["pearson_r"], 2), "p": round(v["p"], 3), "index": v["index"]} for c, v in V["tracking"].items()}
N["foreign_share_rho"] = {k: {"rho": round(v["rho"], 2), "p": float(v["p"])} for k, v in V["foreign_share_spearman"].items()}
N["foreign_share_n"] = V["foreign_share_n"]
kg = V["known_groups_pct_of_sentences"]
N["known_groups"] = {div: {c: round(kg[div][f"int_{c}"], 2) for c in CATS} for div in kg}
N["known_groups_kruskal_p"] = {c: float(v["p"]) for c, v in V["known_groups_kruskal"].items()}

au0 = pd.read_csv(RES / "Validation Audit Original Dictionary.csv", index_col=0)
au1 = pd.read_csv(RES / "Validation Audit Revised Dictionary Holdout.csv", index_col=0)
cats = [c for c in au0.index if c not in ("action", "none")]
N["audit_original"] = {c: {"correct": int(au0.loc[c, "sum"]), "n": int(au0.loc[c, "count"])} for c in au0.index}
N["audit_revised"] = {c: {"correct": int(au1.loc[c, "sum"]), "n": int(au1.loc[c, "count"])} for c in au1.index}
N["audit_pooled_original"] = round(au0.loc[cats, "sum"].sum() / au0.loc[cats, "count"].sum(), 2)
N["audit_pooled_revised"] = round(au1.loc[cats, "sum"].sum() / au1.loc[cats, "count"].sum(), 2)

ep = pd.DataFrame(M["episode_coefficients"])
meta = M["episode_meta"]
N["episode"] = {}
for _, r in ep.iterrows():
    N["episode"][f"{r['model']}|{r['term']}"] = {"b": r["coef"], "se": r["se"], "p": r["p"], "p_hc1": r["p_hc1"],
                                                  "lo": r["ci_low"], "hi": r["ci_high"], "n": meta[r["model"]]["n"],
                                                  "r2": meta[r["model"]]["r2"], "clusters": meta[r["model"]]["clusters"]}
N["marginal"] = M["marginal_effects"]
N["coverage_fy2018"] = M["coverage_fy2018"]
rob = pd.DataFrame(M["robustness"])
summ = {}
for (e, y, t), g in rob.groupby(["episode", "outcome", "term"]):
    prim = g[g["check"] == "Primary specification"]["coef"].iloc[0]
    summ[f"{e}|{y}|{t}"] = {"checks": int(len(g)), "same_sign": int((np.sign(g["coef"]) == np.sign(prim)).sum()),
                            "p05": int((g["p"] < 0.05).sum()), "p05_hc1": int((g["p_hc1"] < 0.05).sum()),
                            "min": float(g["coef"].min()), "max": float(g["coef"].max())}
N["robustness_summary"] = summ
N["robustness_detail"] = {f"{r['episode']}|{r['outcome']}|{r['term']}|{r['check']}": {"b": r["coef"], "p": r["p"], "p_hc1": r["p_hc1"], "n": r["n"]}
                          for r in M["robustness"]}
N["panel"] = {f"{r['model']}|{r['term']}": {"b": r["coef"], "se": r["se"], "p": r["p"]} for r in M["panel_coefficients"]}
N["panel_meta"] = M["panel_meta"]
N["shock"] = {f"{r['model']}|{r['term']}": {"b": r["coef"], "se": r["se"], "p": r["p"]} for r in M["shock_coefficients"]}
N["shock_meta"] = M["shock_meta"]
N["prediction"] = M["prediction"]
alt = pd.read_csv(RES / "Alternative Original Dictionary" / "Episode Models.csv")
N["episode_original_dictionary"] = {f"{r['model']}|{r['term']}": {"b": r["coef"], "p": r["p"]} for _, r in alt.iterrows()}
A = pd.read_csv(DER / "Episode A Frame.csv")
N["episodeA_desc"] = {c: {"mean": float(A[c].mean()), "sd": float(A[c].std()), "median": float(A[c].median()), "n": int(A[c].notna().sum())}
                      for c in ["severity", "margin_change", "recovery", "recovered", "breadth", "coverage", "linkage", "updating"]}
N["episodeA_share_fall"] = float((A["severity"] < 0).mean())
N["episodeA_share_fall_10"] = float((A["severity"] < np.log(0.9)).mean())
macro = pd.read_csv(DER / "Macro Monthly.csv")
macro["month"] = pd.PeriodIndex(macro["month"], freq="M")
mm = macro.set_index("month")
for col in ["gpr", "gscpi", "epu_us", "epu_trade"]:
    s = mm.loc["2017-01":"2025-12", col]
    N[f"peak_{col}"] = {"value": round(float(s.max()), 2), "month": str(s.idxmax())}
N["gpr_since"] = str(mm.loc[:pd.Period("2022-02", freq="M"), "gpr"].iloc[:-1][mm.loc[:pd.Period("2022-02", freq="M"), "gpr"].iloc[:-1] >= mm.loc["2022-03", "gpr"]].index.max()) if (mm.loc[:"2022-02", "gpr"] >= mm.loc["2022-03", "gpr"]).any() else "before 2014"
import warnings
warnings.filterwarnings("ignore")
RAW = PROJ / "Datasets" / "Raw Macro"
gs = pd.read_excel(RAW / "Global Supply Chain Pressure Index.xlsx", sheet_name="GSCPI Monthly Data", header=None)[[0, 1]].iloc[5:].dropna()
gs[1] = gs[1].astype(float)
N["gscpi_series_max"] = {"month": str(gs.loc[gs[1].idxmax(), 0]), "value": round(float(gs[1].max()), 2), "series_start": str(gs.iloc[0, 0])}
g = pd.read_excel(RAW / "Geopolitical Risk Monthly.xls")
g["month"] = pd.to_datetime(g["month"])
m22 = float(g.loc[g["month"] == "2022-03-01", "GPR"].iloc[0])
N["gpr_march_2022"] = {"value": round(m22, 1), "previous_higher": str(g.loc[(g["month"] < "2022-03-01") & (g["GPR"] >= m22), "month"].max().date())}
c = pd.read_excel(RAW / "Economic Policy Uncertainty Categorical.xlsx")
c = c[pd.to_numeric(c["Month"], errors="coerce").notna()]
row = c.loc[c["9. Trade policy"].astype(float).idxmax()]
N["trade_epu_series_max"] = {"year": int(row["Year"]), "month": int(row["Month"]), "series_start": int(c["Year"].iloc[0])}
N["updating_mean"] = {int(k): round(float(v), 4) for k, v in P.groupby("fiscal_year")["updating"].mean().items()}
(HERE / "Numbers.json").write_text(json.dumps(N, indent=1, default=float))
print(json.dumps({k: N[k] for k in ["sample_final", "filings", "panel_firm_years", "breadth_mean", "breadth_cv", "peak_gpr", "peak_gscpi", "peak_epu_trade", "peak_epu_us", "audit_pooled_original", "audit_pooled_revised"]}, indent=0, default=float))
