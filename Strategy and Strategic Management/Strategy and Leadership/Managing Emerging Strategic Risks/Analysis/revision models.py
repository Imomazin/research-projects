"""Models for the revision: response-measure variants, small-cluster inference, multiple
testing, investigation of the recovery and interaction results, alternative convergence
measures, saturation, determinants of breadth and the macro shock checks.

Inputs (Datasets/Derived): Research Panel.csv, Revision/Response Measures.csv,
Revision/Convergence Measures.csv, Category Pairs.csv; Datasets/Raw Macro/Revision price
indices. Outputs: Results/Revision/*.csv and Results/Revision/Revision Results.json.

Definitions of outcomes, controls, winsorisation and fixed effects are those of
estimate models.py (reproduced independently in Reproduction/independent checks.py).
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scipy import stats

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
DER = PROJ / "Datasets" / "Derived"
RES = PROJ / "Results" / "Revision"
RES.mkdir(parents=True, exist_ok=True)
CATS = ["geopolitical", "trade", "regulatory", "cyber", "technology", "supply", "climate", "macro", "pandemic"]
INTS = [f"int_{c}" for c in CATS]
CONTROLS = ["ln_assets", "leverage", "cash_ratio", "roa", "prior_growth", "ln_item1a_words"]
OUT: dict = {}
rng_master = np.random.default_rng(20261027)


def bh(p):
    """Benjamini-Hochberg adjusted p-values (step-up), returned in the input order."""
    p = np.asarray(p, float)
    m = len(p)
    o = np.argsort(p)
    adj = p[o] * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m)
    out[o] = np.clip(adj, 0, 1)
    return out


def winsor(s, lo=0.01, hi=0.99):
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)


def z(s):
    return (s - s.mean()) / s.std()


# ------------------------------------------------------------------ estimation engine
def design(d, y, rhs, fe=("sic2", "fye_month"), cluster="sic2"):
    cols = [y] + rhs + list(fe) + ([cluster] if cluster else [])
    dd = d.dropna(subset=list(dict.fromkeys(cols))).copy()
    D = pd.get_dummies(dd[list(fe)].astype(str), drop_first=True, dtype=float) if fe else pd.DataFrame(index=dd.index)
    X = np.column_stack([np.ones(len(dd)), dd[rhs].to_numpy(float), D.to_numpy()])
    keep = [0] + list(range(1, 1 + len(rhs)))
    # drop collinear dummy columns, never the regressors of interest
    q, r = np.linalg.qr(X)
    good = np.abs(np.diag(r)) > 1e-9 * np.abs(np.diag(r)).max()
    good[keep] = True
    X = X[:, good]
    return dd, X, dd[y].to_numpy(float)


def ols_cluster(X, Y, groups, small=True):
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    e = Y - X @ beta
    n, k = X.shape
    ug, inv = np.unique(groups, return_inverse=True)
    G = len(ug)
    S = np.zeros((G, k))
    np.add.at(S, inv, X * e[:, None])
    c = (G / (G - 1)) * ((n - 1) / (n - k)) if small else 1.0
    V = c * XtX_inv @ (S.T @ S) @ XtX_inv
    return beta, np.sqrt(np.diag(V)), e, G


def ols_hc1(X, Y):
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    e = Y - X @ beta
    n, k = X.shape
    V = n / (n - k) * XtX_inv @ (X.T * e ** 2) @ X @ XtX_inv
    return beta, np.sqrt(np.diag(V))


def wild_cluster_p(X, Y, groups, j, B=9999, seed=0):
    """Wild cluster restricted bootstrap p-value (Rademacher weights, null imposed) for column j."""
    rng = np.random.default_rng(seed)
    beta, se, _, G = ols_cluster(X, Y, groups)
    t_obs = beta[j] / se[j]
    Xr = np.delete(X, j, axis=1)
    br = np.linalg.pinv(Xr.T @ Xr) @ Xr.T @ Y
    fit_r, e_r = Xr @ br, Y - Xr @ br
    ug, inv = np.unique(groups, return_inverse=True)
    XtX_inv = np.linalg.pinv(X.T @ X)
    A = XtX_inv @ X.T
    n, k = X.shape
    c = (G / (G - 1)) * ((n - 1) / (n - k))
    ts = np.empty(B)
    for b in range(B):
        w = rng.choice([-1.0, 1.0], size=G)[inv]
        ys = fit_r + e_r * w
        bs = A @ ys
        es = ys - X @ bs
        S = np.zeros((G, k))
        np.add.at(S, inv, X * es[:, None])
        v = c * (XtX_inv[j] @ (S.T @ S) @ XtX_inv[j])
        ts[b] = bs[j] / np.sqrt(v)
    return float(np.mean(np.abs(ts) >= abs(t_obs))), float(t_obs)


def fit(d, y, rhs, terms=None, fe=("sic2", "fye_month"), cluster="sic2", wild=False, B=9999):
    terms = terms or rhs[:1]
    dd, X, Y = design(d, y, rhs, fe, cluster)
    groups = dd[cluster].astype(str).to_numpy()
    beta, se, e, G = ols_cluster(X, Y, groups)
    bh, seh = ols_hc1(X, Y)
    out = []
    for t in terms:
        j = 1 + rhs.index(t)
        tval = beta[j] / se[j]
        row = {"term": t, "coef": beta[j], "se": se[j], "p": 2 * stats.norm.sf(abs(tval)),
               "p_t": 2 * stats.t.sf(abs(tval), G - 1), "ci_low": beta[j] - 1.96 * se[j], "ci_high": beta[j] + 1.96 * se[j],
               "ci_low_t": beta[j] - stats.t.ppf(0.975, G - 1) * se[j], "ci_high_t": beta[j] + stats.t.ppf(0.975, G - 1) * se[j],
               "p_hc1": 2 * stats.norm.sf(abs(bh[j] / seh[j])), "n": len(dd), "clusters": G, "sd_y": float(np.std(Y, ddof=1)),
               "r2": 1 - (e @ e) / ((Y - Y.mean()) @ (Y - Y.mean()))}
        if wild:
            row["p_wild"], _ = wild_cluster_p(X, Y, groups, j, B=B, seed=int(rng_master.integers(1e9)))
        out.append(row)
    return out, dd


# ------------------------------------------------------------------ data
P = pd.read_csv(DER / "Research Panel.csv", parse_dates=["fy_end", "filing_date"]).sort_values(["cik", "fiscal_year"])
RM = pd.read_csv(DER / "Revision" / "Response Measures.csv")
CV = pd.read_csv(DER / "Revision" / "Convergence Measures.csv")
P = P.merge(RM.drop(columns=["accession", "n_sent_response"]), on=["cik", "fiscal_year"], how="left")
P = P.merge(CV.drop(columns=["n_sent_1a"]), on=["cik", "fiscal_year"], how="left")
LMF = DER / "Revision" / "Response Candidate Language Model Scores.csv.gz"
if LMF.exists():
    lmsc = pd.read_csv(LMF)
    OUT["lm_candidates"] = {"pairs": int(len(lmsc)), "positive": int((lmsc["entail_implemented"] >= 0.5).sum())}
    lmc = (lmsc[lmsc["entail_implemented"] >= 0.5].groupby(["cik", "fiscal_year", "category"]).size()
           .unstack(fill_value=0).reindex(columns=CATS, fill_value=0).add_prefix("act_lm_").reset_index())
    P = P.merge(lmc, on=["cik", "fiscal_year"], how="left")
    for c in CATS:
        P[f"act_lm_{c}"] = P[f"act_lm_{c}"].fillna(0).where(P["n_high_sentences"].notna() & P["fiscal_year"].between(2017, 2025))
cnt = P[[f"cnt_{c}" for c in CATS]].to_numpy(float)
mat = cnt >= 3
nm = mat.sum(1)


def coverage(act_prefix, minimum=1):
    a = P[[f"{act_prefix}_{c}" for c in CATS]].to_numpy(float)
    return np.where(nm > 0, (mat & (a >= minimum)).sum(1) / np.maximum(nm, 1), np.nan)


P["cov_original"] = coverage("act_original")
P["cov_revised"] = coverage("act_revised")
P["cov_high"] = coverage("act_high")
P["cov_revised_two"] = coverage("act_revised", 2)
P["cov_high_resource"] = coverage("act_high_resource")
P["cov_lm"] = coverage("act_lm") if LMF.exists() else np.nan
P["any_high"] = (P[[f"act_high_{c}" for c in CATS]].sum(1) > 0).astype(float).where(P["n_high_sentences"].notna())
OUT["check_revised_equals_panel_coverage"] = float(np.nanmax(np.abs(P["cov_revised"] - P["coverage"])))
# alternative convergence measures
for th in (1, 5):
    P[f"breadth_t{th}"] = (cnt >= th).sum(1)
P["mention_density"] = cnt.sum(1) / P["n_sent_1a"].replace(0, np.nan)
spec = P[[f"spec_{c}" for c in CATS]].to_numpy(float)
P["breadth_specific"] = (spec >= 3).sum(1)
P["breadth_specific"] = P["breadth_specific"].where(P["boilerplate_share"].notna())
P["breadth_nocat"] = (P[[f"nocat_{c}" for c in CATS]].to_numpy(float) >= 3).sum(1)
P["breadth_nocat"] = P["breadth_nocat"].where(P["boilerplate_share"].notna())
P["interaction_share"] = P["n_interaction"] / P["n_sent_1a"].replace(0, np.nan)
pairs = pd.read_csv(DER / "Category Pairs.csv")
P = P.merge(pairs.groupby(["cik", "fiscal_year"]).size().rename("linked_pairs").reset_index(), on=["cik", "fiscal_year"], how="left")
P["linked_pairs"] = P["linked_pairs"].fillna(0).where(P["n_sent_1a"].notna())
g = P.groupby("cik")
prev_ok = g["fiscal_year"].shift(1) == P["fiscal_year"] - 1
M = pd.DataFrame(mat, index=P.index, columns=CATS).astype(int)
Mp = M.groupby(P["cik"]).shift(1)
inter = (M & Mp.fillna(0).astype(int)).sum(1)
union = (M | Mp.fillna(0).astype(int)).sum(1)
P["composition_change"] = (1 - inter / union.replace(0, np.nan)).where(prev_ok & P["n_sent_1a"].notna())
P["novelty"] = ((M == 1) & (Mp == 0)).sum(1).where(prev_ok & P["n_sent_1a"].notna())
P["breadth_industry_adj"] = P["breadth"] - P.groupby(["sic2", "fiscal_year"])["breadth"].transform("mean")
P["goodwill_assets"] = P["goodwill"].fillna(0) / P["assets"]
P["ln_item1_words"] = np.log1p(P["item1_words"])
P["inventory_assets"] = P["inventory"].fillna(0) / P["assets"]
P["gross_margin"] = (P["gross_profit"].fillna(P["revenue"] - P["cost_of_revenue"])) / P["revenue"].where(P["revenue"] > 0)
P["ln_cost"] = np.log(P["cost_of_revenue"].where(P["cost_of_revenue"] > 0))
P["ln_sga"] = np.log(P["sga"].where(P["sga"] > 0))
P["ln_inventory"] = np.log(P["inventory"].where(P["inventory"] > 0))
idx = pd.read_csv(PROJ / "Datasets" / "Filings Index.csv")[["cik", "fiscal_year", "text_chars"]]
P = P.merge(idx, on=["cik", "fiscal_year"], how="left")
P["ln_text_chars"] = np.log(P["text_chars"])
# analysis-ready firm-year file of every revision measure (documented in Datasets/Revision Data Dictionary.csv)
REV_COLS = ["cik", "fiscal_year", "sic2", "division", "breadth", "breadth_t1", "breadth_t5", "breadth_specific", "breadth_nocat",
            "breadth_industry_adj", "mention_density", "diversity", "linkage", "linked_pairs", "interaction_share", "composition_change",
            "novelty", "boilerplate_share", "cov_original", "cov_revised", "cov_high", "cov_revised_two", "cov_high_resource", "cov_lm",
            "any_high", "item1a_words", "item1_words", "item7_words"] + [f"cnt_{c}" for c in CATS] + \
           [f"act_{r}_{c}" for r in ("original", "revised", "high", "lm") for c in CATS]
P[[c for c in REV_COLS if c in P]][P["n_sent_1a"].notna()].to_csv(DER / "Revision" / "Revision Firm Year Measures.csv", index=False)


def wide(var, year):
    return P[P["fiscal_year"] == year].set_index("cik")[var]


TEXT_KEEP = INTS + ["breadth", "coverage", "linkage", "diversity", "ln_item1a_words", "n_sent_1a", "filing_date",
                    "cov_original", "cov_revised", "cov_high", "cov_revised_two", "cov_high_resource", "cov_lm", "any_high", "any_action",
                    "breadth_t1", "breadth_t5", "mention_density", "breadth_specific", "boilerplate_share", "interaction_share",
                    "linked_pairs", "composition_change", "novelty", "breadth_industry_adj", "ln_item1_words", "ln_text_chars", "breadth_nocat",
                    "catalogue_share"] + [f"mat_{c}" for c in CATS] + [f"act_high_{c}" for c in CATS] + [f"act_revised_{c}" for c in CATS] + [f"act_lm_{c}" for c in CATS] \
    + [f"cnt_{c}" for c in CATS]


def episode_frame(text_year, base_year, extra_filter=None):
    t = P[P["fiscal_year"] == text_year].set_index("cik")
    if extra_filter is not None:
        t = t[extra_filter(t)]
    b = P[P["fiscal_year"] == base_year].set_index("cik")
    d = pd.DataFrame(index=t.index)
    for k in TEXT_KEEP + ["sic2", "division", "us_incorporated", "fye_month", "sic"]:
        d[k] = t[k]
    for k in ["ln_assets", "leverage", "cash_ratio", "roa", "op_margin", "reconfiguration", "foreign_share", "goodwill_assets",
              "rnd_intensity", "inventory_assets", "revenue", "gross_margin", "capex_rate"]:
        d[k] = b[k].reindex(d.index)
    rb, rb2 = wide("ln_revenue", base_year).reindex(d.index), wide("ln_revenue", base_year - 2).reindex(d.index)
    d["prior_growth"] = (rb - rb2) / 2
    return d


def outcomes_a(d):
    r = {y: wide("ln_revenue", y).reindex(d.index) for y in (2019, 2020, 2021, 2022)}
    m19, m20 = (wide("op_margin", y).reindex(d.index) for y in (2019, 2020))
    d["severity"] = r[2020] - r[2019]
    d["margin_change"] = m20 - m19
    d["recovery"] = r[2022] - r[2019]
    d["rebound"] = r[2022] - r[2020]
    return d


def outcomes_b(d):
    r21, r23 = (wide("ln_revenue", y).reindex(d.index) for y in (2021, 2023))
    m21, m22, m23 = (wide("op_margin", y).reindex(d.index) for y in (2021, 2022, 2023))
    d["margin_change"] = m22 - m21
    d["margin_change_two"] = m23 - m21
    d["severity"] = r23 - r21
    return d


ZVARS = ["breadth", "coverage", "linkage", "diversity", "cov_original", "cov_revised", "cov_high", "cov_revised_two",
         "cov_high_resource", "cov_lm", "breadth_t1", "breadth_t5", "mention_density", "breadth_specific", "interaction_share",
         "linked_pairs", "composition_change", "novelty", "breadth_industry_adj", "boilerplate_share", "breadth_nocat"]


def prepare(d, outs):
    d = d.copy()
    for o in outs:
        d[o] = winsor(d[o])
    for c in ["leverage", "cash_ratio", "roa", "prior_growth"]:
        d[c] = winsor(d[c])
    for c in ZVARS:
        d[c + "_z"] = z(d[c])
    d["sic2"] = d["sic2"].astype(int).astype(str)
    d["sic3"] = (d["sic"] // 10).astype(int).astype(str)
    d["fye_month"] = d["fye_month"].astype(int).astype(str)
    return d


A_OUT = ["severity", "margin_change", "recovery", "rebound"]
B_OUT = ["margin_change", "margin_change_two", "severity"]
A = prepare(outcomes_a(episode_frame(2018, 2019)), A_OUT)
B = prepare(outcomes_b(episode_frame(2020, 2021)), B_OUT)
A["sev_raw"] = outcomes_a(episode_frame(2018, 2019))["severity"]
BASE = INTS + CONTROLS

# ------------------------------------------------------------------ 1. cluster structure
cl = A.dropna(subset=["severity"] + BASE)["sic2"].value_counts()
OUT["clusters_episode_a"] = {"clusters": int(len(cl)), "min": int(cl.min()), "median": float(cl.median()),
                             "max": int(cl.max()), "largest_share": float(cl.max() / cl.sum()),
                             "singletons": int((cl == 1).sum()), "under_five": int((cl < 5).sum()),
                             "largest_five": cl.head(5).to_dict(),
                             "effective_clusters_herfindahl": float(1 / ((cl / cl.sum()) ** 2).sum())}
cl.rename_axis("sic2").rename("firms").reset_index().to_csv(RES / "Cluster Sizes Episode A.csv", index=False)

# ------------------------------------------------------------------ 2. principal models with full inference
rows = []
SPECS = {"H1": (["breadth_z"], ["breadth_z"]), "H2": (["coverage_z"], ["coverage_z"]),
         "H3": (["breadth_z", "coverage_z", "bxc"], ["breadth_z", "coverage_z", "bxc"]),
         "E1": (["breadth_z", "linkage_z"], ["breadth_z", "linkage_z"])}
for lab, d, outs in (("A", A, ["severity", "margin_change", "recovery", "rebound"]), ("B", B, B_OUT)):
    d["bxc"] = d["breadth_z"] * d["coverage_z"]
    for y in outs:
        for h, (rhs, terms) in SPECS.items():
            use_wild = (lab == "A" and y in ("severity", "recovery")) or (lab == "B" and y == "margin_change_two")
            res, dd = fit(d, y, rhs + BASE, terms, wild=use_wild, B=4999)
            for r in res:
                rows.append({"episode": lab, "outcome": y, "model": h, **r,
                             "family": "confirmatory" if (lab == "A" and y == "severity" and h in ("H1", "H2", "H3") and
                                                          r["term"] == {"H1": "breadth_z", "H2": "coverage_z", "H3": "bxc"}[h])
                             else "exploratory"})
prin = pd.DataFrame(rows)
conf = prin["family"] == "confirmatory"
order = prin.loc[conf, "p"].sort_values().index
m = len(order)
holm, run = {}, 0.0
for i, ix in enumerate(order):
    run = max(run, min(1.0, (m - i) * prin.loc[ix, "p"]))
    holm[ix] = run
prin.loc[conf, "p_holm"] = pd.Series(holm)
ex = prin[~conf & ~((prin["model"] == "H3") & (prin["term"] != "bxc"))].copy()
prin.loc[ex.index, "q_bh"] = bh(ex["p"].to_numpy())
prin["effect_pct_per_sd"] = np.where(prin["outcome"].isin(["severity", "recovery", "rebound"]),
                                     100 * (np.exp(prin["coef"]) - 1), np.nan)
prin["standardised"] = prin["coef"] / prin["sd_y"]
prin.to_csv(RES / "Principal Models Full Inference.csv", index=False)
OUT["principal"] = prin.to_dict(orient="records")

# ------------------------------------------------------------------ 2b. placebo episode without a systemic shock
def outcomes_placebo(d):
    r18, r19 = (wide("ln_revenue", y).reindex(d.index) for y in (2018, 2019))
    m18, m19 = (wide("op_margin", y).reindex(d.index) for y in (2018, 2019))
    d["severity"] = r19 - r18
    d["margin_change"] = m19 - m18
    return d


PL = prepare(outcomes_placebo(episode_frame(2017, 2018)), ["severity", "margin_change"])
PL["bxc"] = PL["breadth_z"] * PL["coverage_z"]
plc = []
for y in ("severity", "margin_change"):
    for h, (rhs, terms) in SPECS.items():
        if h == "E1":
            continue
        res, dd = fit(PL, y, rhs + BASE, terms, wild=(y == "severity"), B=4999)
        plc += [{"episode": "Placebo FY2018 to FY2019", "outcome": y, "model": h, **r} for r in res]
plc = pd.DataFrame(plc)
plc.to_csv(RES / "Placebo Episode.csv", index=False)
OUT["placebo"] = plc.to_dict(orient="records")

# ------------------------------------------------------------------ 3. response-measure variants (H2 and H3)
VAR = {"Original rules": "cov_original", "Revised rules": "cov_revised", "High-confidence rules": "cov_high",
       "Revised rules, two or more sentences": "cov_revised_two", "High-confidence with resource commitment": "cov_high_resource",
       "Language model (entailment at least 0.5)": "cov_lm"}
rv = []
for lab, d, outs in (("A", A, ["severity", "margin_change", "recovery"]), ("B", B, B_OUT)):
    for vname, v in VAR.items():
        nonzero = int((d[v] > 0).sum())
        if nonzero < 10:   # too few firms with any response for a slope to be estimated
            rv.append({"episode": lab, "outcome": "all", "measure": vname, "model": "not estimated", "term": "",
                       "n": int(d[v].notna().sum()), "share_zero": float((d[v] == 0).mean()), "mean": float(d[v].mean()),
                       "note": f"only {nonzero} firms with a non-zero value"})
            continue
        d["cv_z"] = d[v + "_z"]
        d["bxcv"] = d["breadth_z"] * d["cv_z"]
        for y in outs:
            r2, _ = fit(d, y, ["cv_z"] + BASE, ["cv_z"])
            r3, _ = fit(d, y, ["breadth_z", "cv_z", "bxcv"] + BASE, ["breadth_z", "cv_z", "bxcv"])
            for r in r2:
                rv.append({"episode": lab, "outcome": y, "measure": vname, "model": "H2", **r,
                           "share_zero": float((d[v] == 0).mean()), "mean": float(d[v].mean())})
            for r in r3:
                rv.append({"episode": lab, "outcome": y, "measure": vname, "model": "H3", **r,
                           "share_zero": float((d[v] == 0).mean()), "mean": float(d[v].mean())})
    d["anyh"] = d["any_high"]
    d["bxanyh"] = d["breadth_z"] * d["any_high"]
    for y in outs:
        r3, _ = fit(d, y, ["breadth_z", "anyh", "bxanyh"] + BASE, ["breadth_z", "anyh", "bxanyh"])
        for r in r3:
            rv.append({"episode": lab, "outcome": y, "measure": "Any high-confidence response (indicator)", "model": "H3", **r,
                       "share_zero": float((d["any_high"] == 0).mean()), "mean": float(d["any_high"].mean())})
rv = pd.DataFrame(rv)
# Benjamini-Hochberg across every response and response-by-breadth term in this family
fam = rv["term"].isin(["cv_z", "bxcv", "anyh", "bxanyh"]) & rv["p"].notna()
rv.loc[fam, "q_bh"] = bh(rv.loc[fam, "p"].to_numpy())
rv["family_size"] = int(fam.sum())
rv.to_csv(RES / "Response Measure Variants.csv", index=False)
OUT["response_variants"] = rv.to_dict(orient="records")

# category-level: firms with the category material, high-confidence response indicator
cat_rows = []
for lab, d, outs in (("A", A, ["severity", "margin_change", "recovery"]), ("B", B, B_OUT)):
    for c in CATS:
        sub = d[d[f"mat_{c}"] == 1].copy()
        sub["resp"] = (sub[f"act_high_{c}"] > 0).astype(float)
        sub["resp_rev"] = (sub[f"act_revised_{c}"] > 0).astype(float)
        sub["resp_lm"] = (sub[f"act_lm_{c}"] > 0).astype(float) if f"act_lm_{c}" in sub else 0.0
        for y in outs:
            for rname in ("resp", "resp_rev", "resp_lm"):
                if sub[rname].sum() < 15 or len(sub) < 80:
                    continue
                r, _ = fit(sub, y, [rname] + BASE, [rname])
                cat_rows.append({"episode": lab, "outcome": y, "category": c,
                                 "rule": {"resp": "high-confidence", "resp_rev": "revised", "resp_lm": "language model"}[rname],
                                 "firms_material": len(sub), "firms_responding": int(sub[rname].sum()), **r[0]})
pd.DataFrame(cat_rows).to_csv(RES / "Category Response Models.csv", index=False)
OUT["category_response"] = cat_rows

# ------------------------------------------------------------------ 4. marginal effects of breadth by coverage, each measure
me = []
grid = [0.0, 0.25, 0.5, 0.75, 1.0]
for vname, v in VAR.items():
    d = A.copy()
    if int((d[v] > 0).sum()) < 10:
        continue
    mu, sdv = d[v].mean(), d[v].std()
    d["cv_z"] = d[v + "_z"]
    d["bxcv"] = d["breadth_z"] * d["cv_z"]
    for y in ["severity", "recovery"]:
        dd, X, Y = design(d, y, ["breadth_z", "cv_z", "bxcv"] + BASE)
        groups = dd["sic2"].to_numpy()
        beta, se, e, G = ols_cluster(X, Y, groups)
        XtX_inv = np.linalg.pinv(X.T @ X)
        n, k = X.shape
        ug, inv = np.unique(groups, return_inverse=True)
        S = np.zeros((G, k))
        np.add.at(S, inv, X * e[:, None])
        V = (G / (G - 1)) * ((n - 1) / (n - k)) * XtX_inv @ (S.T @ S) @ XtX_inv
        for cval in grid:
            zc = (cval - mu) / sdv
            g_ = np.zeros(k)
            g_[1], g_[3] = 1, zc
            est, s = g_ @ beta, np.sqrt(g_ @ V @ g_)
            me.append({"measure": vname, "outcome": y, "coverage": cval, "effect": est, "se": s,
                       "ci_low": est - stats.t.ppf(0.975, G - 1) * s, "ci_high": est + stats.t.ppf(0.975, G - 1) * s,
                       "p": 2 * stats.t.sf(abs(est / s), G - 1),
                       "share_at_or_below": float((d[v] <= cval).mean())})
pd.DataFrame(me).to_csv(RES / "Marginal Effects by Response Measure.csv", index=False)
OUT["marginal_by_measure"] = me

# ------------------------------------------------------------------ 5. recovery investigation
rec = []
A["peer_recovery"] = A.groupby("sic2")["recovery"].transform(lambda s: (s.sum() - s) / (s.count() - 1))
A["peer_severity"] = A.groupby("sic2")["severity"].transform(lambda s: (s.sum() - s) / (s.count() - 1))
A["ln_revenue_base"] = np.log(A["revenue"])
A["rev_share_sic2"] = A["revenue"] / A.groupby("sic2")["revenue"].transform("sum")
for c in ["goodwill_assets", "rnd_intensity", "inventory_assets", "capex_rate", "foreign_share"]:
    A[c + "_w"] = winsor(A[c])
steps = [
    ("Primary specification", ["breadth_z"] + BASE, ("sic2", "fye_month")),
    ("Three-digit SIC fixed effects", ["breadth_z"] + BASE, ("sic3", "fye_month")),
    ("Peer recovery (industry leave-one-out mean)", ["breadth_z", "peer_recovery"] + BASE, ("sic2", "fye_month")),
    ("Pandemic demand shock (peer severity)", ["breadth_z", "peer_severity"] + BASE, ("sic2", "fye_month")),
    ("Foreign income share (geographic diversification)", ["breadth_z", "foreign_share_w"] + BASE, ("sic2", "fye_month")),
    ("Goodwill to assets (acquisition-based diversification)", ["breadth_z", "goodwill_assets_w"] + BASE, ("sic2", "fye_month")),
    ("Item 1 length (business scope and revenue mix)", ["breadth_z", "ln_item1_words"] + BASE, ("sic2", "fye_month")),
    ("Total 10-K length (reporting intensity)", ["breadth_z", "ln_text_chars"] + BASE, ("sic2", "fye_month")),
    ("Revenue size and share of industry revenue (market position)", ["breadth_z", "ln_revenue_base", "rev_share_sic2"] + BASE, ("sic2", "fye_month")),
    ("R&D intensity, capex rate and inventory (strategic flexibility)", ["breadth_z", "rnd_intensity_w", "capex_rate_w", "inventory_assets_w"] + BASE, ("sic2", "fye_month")),
    ("Pandemic category material in FY2018", ["breadth_z", "mat_pandemic"] + BASE, ("sic2", "fye_month")),
]
allc = ["breadth_z", "peer_severity", "foreign_share_w", "goodwill_assets_w", "ln_item1_words", "ln_text_chars", "ln_revenue_base",
        "rev_share_sic2", "rnd_intensity_w", "capex_rate_w", "inventory_assets_w"] + BASE
steps.append(("All of the above jointly", allc, ("sic2", "fye_month")))
for y in ["recovery", "rebound", "severity"]:
    for name, rhs, fe in steps:
        r, dd = fit(A, y, rhs, ["breadth_z"], fe=fe, wild=(y == "recovery" and name in ("Primary specification", "All of the above jointly")), B=4999)
        rec.append({"outcome": y, "specification": name, **r[0]})
# category composition: which material categories carry the recovery association
r, dd = fit(A, "recovery", [f"mat_{c}" for c in CATS] + BASE, [f"mat_{c}" for c in CATS])
for x in r:
    rec.append({"outcome": "recovery", "specification": "Material-category indicators in place of breadth", **x})
rec = pd.DataFrame(rec)
rec.to_csv(RES / "Recovery Investigation.csv", index=False)
OUT["recovery_investigation"] = rec.to_dict(orient="records")

# ------------------------------------------------------------------ 5b. robustness grid for the H1 specification (breadth alone)
g1 = []
A["updating"] = P[P["fiscal_year"] == 2018].set_index("cik")["updating"].reindex(A.index)
A["updating_z"] = z(A["updating"])
for c in ["reconfiguration", "foreign_share"]:
    A[c + "_w2"] = winsor(A[c])
raw_a = outcomes_a(episode_frame(2018, 2019))
base_rev = wide("revenue", 2019)
for y in ["recovery", "severity"]:
    checks = {
        "Primary specification": (A, ["breadth_z"]),
        "Materiality threshold one sentence": (A, ["breadth_t1_z"]),
        "Materiality threshold five sentences": (A, ["breadth_t5_z"]),
        "Diversity in place of breadth": (A, ["diversity_z"]),
        "Hazard-catalogue sentences excluded": (A, ["breadth_nocat_z"]),
        "Breadth from non-boilerplate sentences": (A, ["breadth_specific_z"]),
        "December fiscal year-end only": (A[A["fye_month"] == "12"], ["breadth_z"]),
        "Item 1A of at least 1,000 words": (A[A["ln_item1a_words"] >= np.log1p(1000)], ["breadth_z"]),
        "US-incorporated firms only": (A[A["us_incorporated"] == 1], ["breadth_z"]),
        "Base-year revenue of at least 100 million US dollars": (A[base_rev.reindex(A.index) >= 1e8], ["breadth_z"]),
        "Manufacturing only": (A[A["division"] == "Manufacturing"], ["breadth_z"]),
        "Excluding manufacturing": (A[A["division"] != "Manufacturing"], ["breadth_z"]),
        "Reconfiguration control": (A, ["breadth_z", "reconfiguration_w2"]),
        "Foreign income share control": (A, ["breadth_z", "foreign_share_w2"]),
        "Updating control": (A, ["breadth_z", "updating_z"]),
        "Unwinsorised outcome": (A.assign(**{y: raw_a[y]}), ["breadth_z"]),
    }
    for div in sorted(A["division"].dropna().unique()):
        sub = A[A["division"] != div]
        if len(A) - len(sub) >= 10:
            checks[f"Dropping {div}"] = (sub, ["breadth_z"])
    for name, (d, rhs) in checks.items():
        rhs_full = rhs + ([c for c in INTS] if name != "Without category intensity controls" else []) + CONTROLS
        r, _ = fit(d, y, rhs_full, [rhs[0]])
        g1.append({"outcome": y, "check": name, **r[0]})
    r, _ = fit(A, y, ["breadth_z"] + CONTROLS, ["breadth_z"])
    g1.append({"outcome": y, "check": "Without category intensity controls", **r[0]})
g1 = pd.DataFrame(g1)
g1.to_csv(RES / "Robustness Grid Breadth Alone.csv", index=False)
OUT["grid_h1"] = g1.to_dict(orient="records")

# ------------------------------------------------------------------ 6. interaction investigation
ii = []
A["bxc"] = A["breadth_z"] * A["coverage_z"]
A["distressed"] = ((A["roa"] < 0) | (A["leverage"] > A["leverage"].quantile(0.8))).astype(float)
for y in ["severity", "recovery"]:
    base_rhs = ["breadth_z", "coverage_z", "bxc"] + BASE
    variants = {
        "Primary specification": (A, base_rhs),
        "Firms with any revised-rule response only": (A[A["any_action"] == 1], base_rhs),
        "Excluding distressed firms (negative ROA or top-quintile leverage)": (A[A["distressed"] == 0], base_rhs),
        "Distressed firms only": (A[A["distressed"] == 1], base_rhs),
        "Excluding manufacturing": (A[A["division"] != "Manufacturing"], base_rhs),
        "Manufacturing only": (A[A["division"] == "Manufacturing"], base_rhs),
        "Control for supply and macro intensity interactions with coverage": (
            A.assign(sxc=A["int_supply"] * A["coverage_z"], mxc=A["int_macro"] * A["coverage_z"]), base_rhs + ["sxc", "mxc"]),
        "Control for mention density": (A, base_rhs + ["mention_density"]),
        "Control for peer severity": (A, base_rhs + ["peer_severity"]),
    }
    for name, (d, rhs) in variants.items():
        if d["coverage"].std() == 0 or len(d) < 100:
            continue
        r, dd = fit(d, y, rhs, ["bxc"])
        ii.append({"outcome": y, "specification": name, **r[0]})
    # timing: FY2019 text filed before March 2020
    d19 = prepare(outcomes_a(episode_frame(2019, 2019, lambda t: t["filing_date"] < "2020-03-01")), A_OUT)
    d19["bxc"] = d19["breadth_z"] * d19["coverage_z"]
    r, _ = fit(d19, y, ["breadth_z", "coverage_z", "bxc"] + BASE, ["bxc"])
    ii.append({"outcome": y, "specification": "FY2019 text filed before 1 March 2020", **r[0]})
ii = pd.DataFrame(ii)
ii.to_csv(RES / "Interaction Investigation.csv", index=False)
OUT["interaction_investigation"] = ii.to_dict(orient="records")

# pre-registered checks missing from the original grid: hazard catalogues excluded, survivors only, attrition weights
pre = []
surv = set(P[(P["fiscal_year"] == 2022) & P["revenue"].notna()]["cik"])
A["survivor"] = A.index.isin(surv).astype(float)
lg = A.dropna(subset=["breadth_z", "ln_assets", "roa", "leverage"]).copy()
import statsmodels.api as sm
pm = sm.Logit(lg["survivor"], sm.add_constant(lg[["breadth_z", "ln_assets", "roa", "leverage", "cash_ratio"]].fillna(0))).fit(disp=0)
lg["w"] = 1 / pm.predict()
A["attrition_weight"] = lg["w"]
OUT["survival_logit"] = {"coef": pm.params.to_dict(), "p": pm.pvalues.to_dict(), "survival_rate": float(lg["survivor"].mean())}
for y in ["severity", "margin_change", "recovery"]:
    for t, rhs in (("breadth_z", ["breadth_z"] + BASE), ("bxc", ["breadth_z", "coverage_z", "bxc"] + BASE)):
        r, _ = fit(A[A["survivor"] == 1], y, rhs, [t])
        pre.append({"outcome": y, "check": "Survivors to FY2022 only", **r[0]})
        # weighted least squares by attrition weights
        d = A.dropna(subset=[y] + rhs + ["attrition_weight"]).copy()
        sw = np.sqrt(d["attrition_weight"].to_numpy())
        dd, X, Y = design(d, y, rhs)
        wv = np.sqrt(dd["attrition_weight"].to_numpy())
        beta, se, e, G = ols_cluster(X * wv[:, None], Y * wv, dd["sic2"].to_numpy())
        j = 1 + rhs.index(t)
        pre.append({"outcome": y, "check": "Inverse-probability attrition weights", "term": t, "coef": beta[j], "se": se[j],
                    "p": 2 * stats.norm.sf(abs(beta[j] / se[j])), "n": len(dd), "clusters": G})
for y in ["severity", "margin_change", "recovery"]:
    r, _ = fit(A, y, ["breadth_nocat_z"] + BASE, ["breadth_nocat_z"])
    pre.append({"outcome": y, "check": "Hazard-catalogue sentences excluded from category counts (H1)", **r[0]})
pd.DataFrame(pre).to_csv(RES / "Preregistered Checks Added.csv", index=False)
OUT["preregistered_added"] = pre

# ------------------------------------------------------------------ 7. alternative convergence measures
alt = []
MEAS = {"Breadth, threshold three (primary)": "breadth_z", "Breadth, threshold one": "breadth_t1_z",
        "Breadth, threshold five": "breadth_t5_z", "Mention density": "mention_density_z", "Diversity (entropy)": "diversity_z",
        "Linked category pairs": "linked_pairs_z", "Linkage share": "linkage_z", "Explicit interaction share": "interaction_share_z",
        "Composition change from prior year": "composition_change_z", "Novelty (newly material categories)": "novelty_z",
        "Breadth from non-boilerplate sentences": "breadth_specific_z", "Industry-adjusted breadth": "breadth_industry_adj_z",
        "Boilerplate share": "boilerplate_share_z"}
for lab, d, outs in (("A", A, ["severity", "margin_change", "recovery"]), ("B", B, B_OUT)):
    for name, v in MEAS.items():
        for y in outs:
            # mention density is the sum of the nine intensities, so the intensities are dropped for that measure
            rhs = [v] + (CONTROLS if v == "mention_density_z" else BASE)
            r, _ = fit(d, y, rhs, [v])
            alt.append({"episode": lab, "outcome": y, "measure": name, **r[0]})
    # breadth and explicit interaction together
    for y in outs:
        r, _ = fit(d, y, ["breadth_z", "interaction_share_z"] + BASE, ["breadth_z", "interaction_share_z"])
        for x in r:
            alt.append({"episode": lab, "outcome": y, "measure": "Joint: breadth with explicit interaction share", **x})
alt = pd.DataFrame(alt)
alt.to_csv(RES / "Alternative Convergence Measures.csv", index=False)
OUT["alternative_convergence"] = alt.to_dict(orient="records")

# ------------------------------------------------------------------ 8. saturation and trends of every measure
T = P[P["fiscal_year"].between(2017, 2025) & P["n_sent_1a"].notna()]
trend_rows = []
for v in ["breadth_t1", "breadth", "breadth_t5", "breadth_specific", "mention_density", "diversity", "linked_pairs",
          "linkage", "interaction_share", "composition_change", "novelty", "boilerplate_share"] + INTS:
    gy = T.groupby("fiscal_year")[v]
    for y, s in gy:
        s = s.dropna()
        trend_rows.append({"measure": v, "fiscal_year": y, "mean": s.mean(), "sd": s.std(), "cv": s.std() / s.mean() if s.mean() else np.nan,
                           "p90_p10": s.quantile(0.9) - s.quantile(0.1), "n": len(s),
                           "share_at_max": float((s == 9).mean()) if v.startswith("breadth") else np.nan})
tr = pd.DataFrame(trend_rows)
tr.to_csv(RES / "Measure Trends and Dispersion.csv", index=False)
# within-firm: is the dispersion decline driven by firms hitting the ceiling?
T2 = T.copy()
T2["below_ceiling_2017"] = T2["cik"].map(T2[T2["fiscal_year"] == 2017].set_index("cik")["breadth"] <= 6)
sat = T2[T2["below_ceiling_2017"] == True].groupby("fiscal_year")["breadth"].agg(["mean", "std"])
sat["cv"] = sat["std"] / sat["mean"]
sat.to_csv(RES / "Saturation Below Ceiling Firms.csv")
lat = (T.groupby("fiscal_year")["mention_density"].std() / T.groupby("fiscal_year")["mention_density"].mean())
OUT["saturation"] = {"cv_mention_density": lat.to_dict(),
                     "cv_breadth": (T.groupby("fiscal_year")["breadth"].std() / T.groupby("fiscal_year")["breadth"].mean()).to_dict(),
                     "cv_breadth_t5": (T.groupby("fiscal_year")["breadth_t5"].std() / T.groupby("fiscal_year")["breadth_t5"].mean()).to_dict(),
                     "cv_breadth_specific": (T.groupby("fiscal_year")["breadth_specific"].std() / T.groupby("fiscal_year")["breadth_specific"].mean()).to_dict(),
                     "boilerplate_share_mean": T.groupby("fiscal_year")["boilerplate_share"].mean().to_dict(),
                     "below_ceiling_firms": int(T2[(T2["below_ceiling_2017"] == True) & (T2["fiscal_year"] == 2017)]["cik"].nunique())}

# ------------------------------------------------------------------ 9. determinants of breadth
det = []
for y in (2018, 2021, 2025):
    d = T[T["fiscal_year"] == y].copy()
    d["foreign_w"] = winsor(d["foreign_share"])
    d["sic2s"] = d["sic2"].astype(int).astype(str)
    sets = {"Item 1A length": ["ln_item1a_words"], "Firm size": ["ln_assets"], "Foreign income share": ["foreign_w"],
            "Industry (two-digit SIC)": [], "Length, size and foreign share": ["ln_item1a_words", "ln_assets", "foreign_w"],
            "All including industry": ["ln_item1a_words", "ln_assets", "foreign_w"]}
    for name, rhs in sets.items():
        fe = ("sic2s",) if "Industry" in name or "industry" in name else ()
        dd = d.dropna(subset=["breadth", "ln_item1a_words", "ln_assets", "foreign_w"])
        Dm = pd.get_dummies(dd[list(fe)].astype(str), drop_first=True, dtype=float) if fe else pd.DataFrame(index=dd.index)
        X = np.column_stack([np.ones(len(dd)), dd[rhs].to_numpy(float), Dm.to_numpy()])
        Y = dd["breadth"].to_numpy(float)
        b = np.linalg.lstsq(X, Y, rcond=None)[0]
        e = Y - X @ b
        r2 = 1 - e @ e / ((Y - Y.mean()) @ (Y - Y.mean()))
        row = {"fiscal_year": y, "predictors": name, "r2": r2, "n": len(dd)}
        for i, v in enumerate(rhs):
            row[f"coef_{v}"] = b[1 + i]
        det.append(row)
pd.DataFrame(det).to_csv(RES / "Determinants of Breadth.csv", index=False)
OUT["determinants"] = det

# ------------------------------------------------------------------ 10. macro shock models
RAWREV = PROJ / "Datasets" / "Raw Macro" / "Revision"
bls = RAWREV / "Consumer Price Index All Urban Consumers Seasonally Adjusted BLS.csv"
if bls.exists() and len(pd.read_csv(bls)) > 100:
    cpi = pd.read_csv(bls)
    cpi["month"] = pd.PeriodIndex.from_fields(year=cpi["year"], month=cpi["month"], freq="M")
    cpi = cpi.rename(columns={"value": "cpi"}).set_index("month").reindex(pd.period_range(cpi["month"].min(), cpi["month"].max(), freq="M"))
    OUT["cpi_months_interpolated"] = [str(m) for m in cpi.index[cpi["cpi"].isna()]]
    cpi["cpi"] = cpi["cpi"].interpolate()   # October 2025 was not published (BLS footnote X); linear between September and November
    cpi = cpi.rename_axis("month").reset_index()
    OUT["cpi_source"] = "BLS CUSR0000SA0 (download.bls.gov flat file)"
else:
    cpi = pd.DataFrame({"month": pd.period_range("2010-01", "2026-12", freq="M"), "cpi": np.nan})
    OUT["cpi_source"] = "not available"
cpi_fy = cpi.set_index("month")["cpi"].rolling(12).mean()
macro = pd.read_csv(DER / "Macro Monthly.csv")
macro["month"] = pd.PeriodIndex(macro["month"], freq="M")
mm = macro.set_index("month")
key = pd.PeriodIndex(P["fy_end"], freq="M")
P["cpi_fy"] = cpi_fy.reindex(key).to_numpy()
P["ln_real_revenue"] = P["ln_revenue"] - np.log(P["cpi_fy"])
lag = lambda col: P.groupby("cik")[col].shift(1).where(P.groupby("cik")["fiscal_year"].shift(1) == P["fiscal_year"] - 1)
P["real_growth"] = P["ln_real_revenue"] - lag("ln_real_revenue")
P["cost_growth"] = P["ln_cost"] - lag("ln_cost")
P["sga_growth"] = P["ln_sga"] - lag("ln_sga")
P["d_gross_margin"] = P["gross_margin"] - lag("gross_margin")
P["inventory_growth"] = P["ln_inventory"] - lag("ln_inventory")
for col, src in (("pt_gpr", "gpr"), ("pt_gscpi", "gscpi"), ("pt_epu_us", "epu_us"), ("pt_epu_trade", "epu_trade"),
                 ("pt_epu_regulation", "epu_regulation")):
    P[col] = mm[src].reindex(key).to_numpy()                       # value in the fiscal year-end month
    P["pk" + col[2:]] = mm[src].rolling(12).max().reindex(key).to_numpy()   # peak within the fiscal year
    P["ch" + col[2:]] = (mm[src].rolling(12).mean() - mm[src].rolling(12).mean().shift(12)).reindex(key).to_numpy()  # change
base18 = P[P["fiscal_year"] == 2018].set_index("cik")[INTS + ["breadth"]]
S = P[P["fiscal_year"].between(2019, 2025)].copy()
S = S.join(base18.add_suffix("_18"), on="cik")
SHOCK = {"geopolitical": "gpr", "supply": "gscpi", "trade": "epu_trade", "regulatory": "epu_regulation", "macro": "epu_us"}
for c in ["rev_growth", "d_op_margin", "real_growth", "cost_growth", "sga_growth", "d_gross_margin", "inventory_growth"]:
    S[c] = winsor(S[c]) if S[c].notna().any() else S[c]


def shock_fit(S, y, timing="fy", effects="year", cluster="firm", convergence=True):
    d = S.copy()
    xs = []
    for c, m in SHOCK.items():
        col = {"fy": f"fy_{m}", "point": f"pt_{m}", "peak": f"pk_{m}", "change": f"ch_{m}"}[timing]
        d[f"x_{c}"] = z(d[f"int_{c}_18"]) * z(d[col])
        xs.append(f"x_{c}")
    d["x_pandemic"] = z(d["int_pandemic_18"]) * (d["fiscal_year"] == 2020).astype(float)
    xs.append("x_pandemic")
    d["shock_count"] = sum((z(d[f"fy_{m}"]) > 1).astype(int) for m in SHOCK.values()) + (d["fiscal_year"] == 2020).astype(int)
    d["x_breadth_shocks"] = z(d["breadth_18"]) * d["shock_count"]
    rhs = xs + (["x_breadth_shocks"] if convergence else [])
    dd = d.dropna(subset=[y] + rhs).copy()
    dd["sic2_year"] = pd.Categorical(dd["sic2"].astype(int).astype(str) + "_" + dd["fiscal_year"].astype(str))
    dd["sic2c"] = dd["sic2"].astype(int)
    dd = dd.set_index(["cik", "fiscal_year"])
    if effects == "year":
        mod = PanelOLS(dd[y], dd[rhs], entity_effects=True, time_effects=True)
    else:
        mod = PanelOLS(dd[y], dd[rhs], entity_effects=True, other_effects=dd[["sic2_year"]])
    if cluster == "firm":
        r = mod.fit(cov_type="clustered", cluster_entity=True)
    elif cluster == "industry":
        r = mod.fit(cov_type="clustered", clusters=dd[["sic2c"]])
    else:
        r = mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
    rows = []
    for t in rhs:
        ci90 = (r.params[t] - 1.645 * r.std_errors[t], r.params[t] + 1.645 * r.std_errors[t])
        rows.append({"term": t, "coef": r.params[t], "se": r.std_errors[t], "p": r.pvalues[t],
                     "ci_low": r.params[t] - 1.96 * r.std_errors[t], "ci_high": r.params[t] + 1.96 * r.std_errors[t],
                     "ci90_low": ci90[0], "ci90_high": ci90[1], "n": int(r.nobs)})
    return rows


sh = []
OUTS_SHOCK = ["rev_growth", "d_op_margin", "cost_growth", "sga_growth", "d_gross_margin", "inventory_growth"] + \
    (["real_growth"] if OUT["cpi_source"] != "not available" else [])
for y in OUTS_SHOCK:
    for timing in ("fy", "point", "peak", "change"):
        if timing != "fy" and y not in ("rev_growth", "d_op_margin"):
            continue
        for r in shock_fit(S, y, timing):
            sh.append({"outcome": y, "timing": timing, "effects": "firm and year", "cluster": "firm", **r})
    if y in ("rev_growth", "d_op_margin"):
        for cl_ in ("industry", "two-way"):
            for r in shock_fit(S, y, "fy", cluster=cl_):
                sh.append({"outcome": y, "timing": "fy", "effects": "firm and year", "cluster": cl_, **r})
        for r in shock_fit(S, y, "fy", effects="industry-year"):
            sh.append({"outcome": y, "timing": "fy", "effects": "firm and industry-by-year", "cluster": "firm", **r})
sh = pd.DataFrame(sh)
sh.to_csv(RES / "Shock Models Revision.csv", index=False)
OUT["shock_revision"] = sh.to_dict(orient="records")
# equivalence view of the compounding term: bounds equal to the smallest single-exposure effect in absolute value
eq = []
for y in ["rev_growth", "d_op_margin"]:
    s0 = sh[(sh["outcome"] == y) & (sh["timing"] == "fy") & (sh["effects"] == "firm and year") & (sh["cluster"] == "firm")]
    conv = s0[s0["term"] == "x_breadth_shocks"].iloc[0]
    singles = s0[(s0["term"].str.startswith("x_")) & (s0["term"] != "x_breadth_shocks") & (s0["p"] < 0.05)]
    bound = float(singles["coef"].abs().min()) if len(singles) else np.nan
    t_lo = (conv["coef"] + bound) / conv["se"] if bound == bound else np.nan
    t_hi = (bound - conv["coef"]) / conv["se"] if bound == bound else np.nan
    eq.append({"outcome": y, "coef": conv["coef"], "se": conv["se"], "ci95": [conv["ci_low"], conv["ci_high"]],
               "ci90": [conv["ci90_low"], conv["ci90_high"]], "bound_smallest_significant_single_effect": bound,
               "tost_p": float(max(stats.norm.sf(t_lo), stats.norm.sf(t_hi))) if bound == bound else np.nan,
               "largest_effect_excluded_95": float(max(abs(conv["ci_low"]), abs(conv["ci_high"])))})
OUT["compounding_equivalence"] = eq

(RES / "Revision Results.json").write_text(json.dumps(OUT, indent=1, default=lambda o: float(o) if np.isscalar(o) else str(o)))
print(json.dumps({k: OUT[k] for k in ["clusters_episode_a", "check_revised_equals_panel_coverage", "compounding_equivalence"]}, indent=1, default=str))
print(prin[["episode", "outcome", "model", "term", "coef", "p", "p_t", "p_wild", "p_holm", "q_bh"]].round(4).to_string())
