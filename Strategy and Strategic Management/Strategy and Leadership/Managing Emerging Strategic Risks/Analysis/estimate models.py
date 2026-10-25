"""Estimate the pre-registered models (Analysis Plan.md) and write every reported
number to Results/Model Results.json, with tables as CSV files.

Usage: python "estimate models.py"
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DER = HERE.parent / "Datasets" / "Derived"
RES = HERE.parent / "Results"
RES.mkdir(exist_ok=True)
CATS = list(json.loads((HERE / "Risk Taxonomy Dictionary.json").read_text())["categories"].keys())
INTS = [f"int_{c}" for c in CATS]
CONTROLS = ["ln_assets", "leverage", "cash_ratio", "roa", "prior_growth", "ln_item1a_words"]
OUT: dict = {}


def winsor(s: pd.Series, lo=0.01, hi=0.99) -> pd.Series:
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)


def z(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def tidy(res, names, label):
    rows = []
    for n in names:
        if n in res.params.index:
            rows.append({"model": label, "term": n, "coef": res.params[n], "se": res.bse[n],
                         "t": res.tvalues[n], "p": res.pvalues[n],
                         "ci_low": res.conf_int().loc[n, 0], "ci_high": res.conf_int().loc[n, 1]})
    return rows


# ------------------------------------------------------------------ data
P = pd.read_csv(DER / "Research Panel.csv", parse_dates=["fy_end", "filing_date"])
P = P.sort_values(["cik", "fiscal_year"])


def wide(var, year):
    return P[P["fiscal_year"] == year].set_index("cik")[var]


def episode_frame(pre_text_year: int, base_year: int, label: str, threshold: int | None = None,
                  extra_filter=None) -> pd.DataFrame:
    """Cross-section of firms with text predictors from pre_text_year and accounting
    controls from base_year (the last full year before the shock)."""
    t = P[P["fiscal_year"] == pre_text_year].set_index("cik")
    if extra_filter is not None:
        t = t[extra_filter(t)]
    b = P[P["fiscal_year"] == base_year].set_index("cik")
    d = pd.DataFrame(index=t.index)
    keep = INTS + ["breadth", "coverage", "linkage", "diversity", "alignment", "updating", "ln_item1a_words",
                   "catalogue_share", "any_action", "n_sent_1a", "filing_date"] + [f"mat_{c}" for c in CATS] \
        + [f"cnt_{c}" for c in CATS] + [f"act_{c}" for c in CATS]
    for k in keep:
        d[k] = t[k]
    for k in ["sic2", "division", "us_incorporated", "sampling_weight", "fye_month"]:
        d[k] = t[k]
    for k in ["ln_assets", "leverage", "cash_ratio", "roa", "op_margin", "reconfiguration", "foreign_share"]:
        d[k] = b[k].reindex(d.index)
    rb, rb2 = wide("ln_revenue", base_year).reindex(d.index), wide("ln_revenue", base_year - 2).reindex(d.index)
    d["prior_growth"] = (rb - rb2) / 2
    d["label"] = label
    return d


def add_outcomes_a(d):
    r19, r20, r21, r22 = (wide("ln_revenue", y).reindex(d.index) for y in (2019, 2020, 2021, 2022))
    m19, m20 = (wide("op_margin", y).reindex(d.index) for y in (2019, 2020))
    d["severity"] = r20 - r19
    d["margin_change"] = m20 - m19
    d["recovery"] = r22 - r19
    d["recovered"] = (r21 >= r19).astype(float).where(r21.notna() & r19.notna())
    return d


def add_outcomes_b(d):
    r21, r23 = (wide("ln_revenue", y).reindex(d.index) for y in (2021, 2023))
    m21, m22, m23 = (wide("op_margin", y).reindex(d.index) for y in (2021, 2022, 2023))
    d["margin_change"] = m22 - m21
    d["margin_change_two"] = m23 - m21
    d["severity"] = r23 - r21
    return d


def prepare(d, outcomes):
    d = d.copy()
    for o in outcomes:
        if o in d and o != "recovered":
            d[o] = winsor(d[o])
    for c in ["leverage", "cash_ratio", "roa", "prior_growth"]:
        d[c] = winsor(d[c])
    d["breadth_z"] = z(d["breadth"])
    d["coverage_z"] = z(d["coverage"])
    d["linkage_z"] = z(d["linkage"])
    d["diversity_z"] = z(d["diversity"])
    d["sic2"] = d["sic2"].astype(int).astype(str)
    d["fye_month"] = d["fye_month"].astype(int).astype(str)
    return d


def ols(d, y, rhs, label, weights=None):
    f = f"{y} ~ {' + '.join(rhs)} + C(sic2) + C(fye_month)"
    cols = [y] + [c for c in rhs if ":" not in c] + ["sic2", "fye_month"]
    dd = d.dropna(subset=[c for c in cols if c in d.columns])
    res = smf.ols(f, data=dd).fit(cov_type="cluster", cov_kwds={"groups": dd["sic2"]})
    hc3 = smf.ols(f, data=dd).fit(cov_type="HC1")
    return res, hc3, dd


def episode_models(d, outcomes, label):
    rows, meta = [], {}
    base = INTS + CONTROLS
    specs = {
        "H1": ["breadth_z"] + base,
        "H2": ["coverage_z"] + base,
        "H3": ["breadth_z", "coverage_z", "breadth_z:coverage_z"] + base,
        "E1": ["breadth_z", "linkage_z"] + base,
    }
    for y in outcomes:
        for h, rhs in specs.items():
            res, hc3, dd = ols(d, y, rhs, f"{label} {h} {y}")
            key = f"{label}|{h}|{y}"
            terms = [t for t in ["breadth_z", "coverage_z", "breadth_z:coverage_z", "linkage_z"] if t in rhs]
            rows += [{**r, "p_hc1": float(hc3.pvalues[r["term"]])} for r in tidy(res, terms, key)]
            meta[key] = {"n": int(res.nobs), "r2": res.rsquared, "adj_r2": res.rsquared_adj,
                         "hc3_p": {t: float(hc3.pvalues[t]) for t in terms},
                         "clusters": int(dd["sic2"].nunique())}
    return rows, meta


# ------------------------------------------------------------------ episode A
A = add_outcomes_a(episode_frame(2018, 2019, "A"))
A_OUT = ["severity", "margin_change", "recovery", "recovered"]
A = prepare(A, A_OUT)
rowsA, metaA = episode_models(A, A_OUT, "A")
B = add_outcomes_b(episode_frame(2020, 2021, "B"))
B_OUT = ["margin_change", "margin_change_two", "severity"]
B = prepare(B, B_OUT)
rowsB, metaB = episode_models(B, B_OUT, "B")
episode = pd.DataFrame(rowsA + rowsB)
episode.to_csv(RES / "Episode Models.csv", index=False)
OUT["episode_meta"] = {**metaA, **metaB}
OUT["episode_coefficients"] = episode.to_dict(orient="records")
A.to_csv(DER / "Episode A Frame.csv")
B.to_csv(DER / "Episode B Frame.csv")

# descriptive statistics for the episode samples
desc = {}
for lab, d, outs in [("A", A, A_OUT), ("B", B, B_OUT)]:
    cols = outs + ["breadth", "coverage", "linkage", "diversity", "alignment", "updating"] + INTS + CONTROLS
    desc[lab] = d[cols].describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
    desc[lab].to_csv(RES / f"Descriptives Episode {'A' if lab == 'A' else 'B'}.csv")
OUT["descriptives"] = {k: v.round(6).to_dict(orient="index") for k, v in desc.items()}
corr_cols = ["severity", "margin_change", "recovery", "breadth", "coverage", "linkage", "diversity",
             "alignment", "updating", "ln_assets", "leverage", "cash_ratio", "roa", "prior_growth", "ln_item1a_words"]
corrA = A[corr_cols].corr()
corrA.to_csv(RES / "Correlations Episode A.csv")
OUT["correlations_A"] = corrA.round(4).to_dict()

# ------------------------------------------------------------------ robustness grid
ROB = []
EPI = {"A": (2018, 2019, add_outcomes_a, A_OUT, A), "B": (2020, 2021, add_outcomes_b, B_OUT, B)}


def rob(ep, label, d, y, rhs_extra=None, rhs=None):
    rhs = rhs or (["breadth_z", "coverage_z", "breadth_z:coverage_z"] + INTS + CONTROLS)
    if rhs_extra:
        rhs = rhs + rhs_extra
    res, hc1, dd = ols(d, y, rhs, label)
    for t in ["breadth_z", "coverage_z", "breadth_z:coverage_z"]:
        if t in res.params.index:
            ROB.append({"episode": ep, "check": label, "outcome": y, "term": t, "coef": res.params[t],
                        "se": res.bse[t], "p": res.pvalues[t], "p_hc1": hc1.pvalues[t], "n": int(res.nobs)})


def rebuild(ep, th=None, text_year=None, extra_filter=None):
    ty, by, add, outs, _ = EPI[ep]
    d = episode_frame(text_year or ty, by, ep, extra_filter=extra_filter)
    if th is not None:
        cnt = d[[f"cnt_{c}" for c in CATS]].to_numpy()
        act = d[[f"act_{c}" for c in CATS]].to_numpy()
        mat = cnt >= th
        d["breadth"] = mat.sum(axis=1)
        d["coverage"] = np.where(mat.sum(axis=1) > 0, (mat & (act > 0)).sum(axis=1) / np.maximum(mat.sum(axis=1), 1), np.nan)
    return prepare(add(d), outs)


GRID = {"A": ["severity", "margin_change", "recovery"], "B": ["margin_change", "margin_change_two", "severity"]}
for ep, outs in GRID.items():
    ty, by, add, allouts, D = EPI[ep]
    base_rev = wide("revenue", by)
    for y in outs:
        rob(ep, "Primary specification", D, y)
        rob(ep, "Materiality threshold one sentence", rebuild(ep, 1), y)
        rob(ep, "Materiality threshold five sentences", rebuild(ep, 5), y)
        dv = D.copy()
        dv["breadth_z"] = dv["diversity_z"]
        rob(ep, "Diversity in place of breadth", dv, y)
        rob(ep, "Without category intensity controls", D, y, rhs=["breadth_z", "coverage_z", "breadth_z:coverage_z"] + CONTROLS)
        rob(ep, "December fiscal year-end only", D[D["fye_month"] == "12"], y)
        rob(ep, "Item 1A of at least 1,000 words", D[D["ln_item1a_words"] >= np.log1p(1000)], y)
        rob(ep, "US-incorporated firms only", D[D["us_incorporated"] == 1], y)
        rob(ep, "Base-year revenue of at least 100 million US dollars", D[base_rev.reindex(D.index) >= 1e8], y)
        rob(ep, "Manufacturing only", D[D["division"] == "Manufacturing"], y)
        rob(ep, "Excluding manufacturing", D[D["division"] != "Manufacturing"], y)
        rob(ep, "Reconfiguration control", D, y, rhs_extra=["reconfiguration"])
        rob(ep, "Foreign income share control", D, y, rhs_extra=["foreign_share"])
        rob(ep, "Updating control", D.assign(updating_z=z(D["updating"])), y, rhs_extra=["updating_z"])
        if ep == "A":
            rob(ep, "FY2019 text filed before 1 March 2020",
                rebuild("A", text_year=2019, extra_filter=lambda t: t["filing_date"] < "2020-03-01"), y)
        else:
            rob(ep, "FY2021 text filed before 24 February 2022",
                rebuild("B", text_year=2021, extra_filter=lambda t: t["filing_date"] < "2022-02-24"), y)
        raw = add(episode_frame(ty, by, ep))
        du = D.copy()
        du[y] = raw[y]
        rob(ep, "Unwinsorised outcome", du, y)
        for div in sorted(D["division"].dropna().unique()):
            sub = D[D["division"] != div]
            if len(D) - len(sub) >= 10:
                rob(ep, f"Dropping {div}", sub, y)
robust = pd.DataFrame(ROB)
robust.to_csv(RES / "Robustness Grid.csv", index=False)
OUT["robustness"] = robust.to_dict(orient="records")

# ------------------------------------------------------------------ panel models
Q = P.copy()
Q["prior_growth"] = Q.groupby("cik")["rev_growth"].shift(1)
lagged = INTS + ["breadth", "coverage", "linkage", "diversity", "updating", "ln_item1a_words",
                 "ln_assets", "leverage", "cash_ratio", "roa", "prior_growth", "reconfiguration"]
for c in lagged:
    Q[f"L_{c}"] = Q.groupby("cik")[c].shift(1).where(Q.groupby("cik")["fiscal_year"].shift(1) == Q["fiscal_year"] - 1)
Q = Q[(Q["fiscal_year"] >= 2019) & (Q["fiscal_year"] <= 2025)]
for c in ["rev_growth", "d_op_margin", "L_leverage", "L_cash_ratio", "L_roa", "L_prior_growth"]:
    Q[c] = winsor(Q[c])
for c in ["L_breadth", "L_coverage", "L_linkage", "L_diversity", "L_updating"]:
    Q[c + "_z"] = z(Q[c])
Q["L_bxc"] = Q["L_breadth_z"] * Q["L_coverage_z"]
panel_rows, panel_meta = [], {}
pctrl = [f"L_{c}" for c in INTS + ["ln_item1a_words", "ln_assets", "leverage", "cash_ratio", "roa"]]
for y in ["rev_growth", "d_op_margin", "adverse"]:
    for lab, rhs in {"H1": ["L_breadth_z"], "H2": ["L_coverage_z"], "H3": ["L_breadth_z", "L_coverage_z", "L_bxc"],
                     "E2": ["L_breadth_z", "L_updating_z"]}.items():
        cols = [y] + rhs + pctrl
        dd = Q.dropna(subset=cols).set_index(["cik", "fiscal_year"])
        mod = PanelOLS(dd[y], dd[rhs + pctrl], entity_effects=True, time_effects=True)
        r = mod.fit(cov_type="clustered", cluster_entity=True)
        key = f"Panel|{lab}|{y}"
        for t in rhs:
            ci = r.conf_int().loc[t]
            panel_rows.append({"model": key, "term": t, "coef": r.params[t], "se": r.std_errors[t], "t": r.tstats[t],
                               "p": r.pvalues[t], "ci_low": ci.iloc[0], "ci_high": ci.iloc[1]})
        panel_meta[key] = {"n": int(r.nobs), "firms": int(dd.index.get_level_values(0).nunique()),
                           "r2_within": float(r.rsquared_within)}
pd.DataFrame(panel_rows).to_csv(RES / "Panel Models.csv", index=False)
OUT["panel_coefficients"] = panel_rows
OUT["panel_meta"] = panel_meta

# exposure-by-shock interactions with predetermined FY2018 exposure
base18 = P[P["fiscal_year"] == 2018].set_index("cik")[INTS]
S = P[(P["fiscal_year"] >= 2019) & (P["fiscal_year"] <= 2025)].copy()
S = S.join(base18.add_suffix("_18"), on="cik")
S["rev_growth"] = winsor(S["rev_growth"])
S["d_op_margin"] = winsor(S["d_op_margin"])
shock_map = {"geopolitical": "fy_gpr", "supply": "fy_gscpi", "trade": "fy_epu_trade",
             "regulatory": "fy_epu_regulation", "macro": "fy_epu_us"}
inter_rows, inter_meta = [], {}
for c, m in shock_map.items():
    S[f"x_{c}"] = z(S[f"int_{c}_18"]) * z(S[m])
S["x_pandemic"] = z(S["int_pandemic_18"]) * (S["fiscal_year"] == 2020).astype(float)
xs = [f"x_{c}" for c in list(shock_map) + ["pandemic"]]
S["n_material_18"] = S["cik"].map(P[P["fiscal_year"] == 2018].set_index("cik")["breadth"])
S["shock_count"] = sum((z(S[m]) > 1).astype(int) for m in shock_map.values()) + (S["fiscal_year"] == 2020).astype(int)
S["x_breadth_shocks"] = z(S["n_material_18"]) * S["shock_count"]
for y in ["rev_growth", "d_op_margin"]:
    for lab, rhs in {"Separate exposures": xs, "With convergence": xs + ["x_breadth_shocks"]}.items():
        dd = S.dropna(subset=[y] + rhs).set_index(["cik", "fiscal_year"])
        r = PanelOLS(dd[y], dd[rhs], entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
        key = f"Shock|{lab}|{y}"
        for t in rhs:
            ci = r.conf_int().loc[t]
            inter_rows.append({"model": key, "term": t, "coef": r.params[t], "se": r.std_errors[t], "p": r.pvalues[t],
                               "ci_low": ci.iloc[0], "ci_high": ci.iloc[1]})
        inter_meta[key] = {"n": int(r.nobs), "firms": int(dd.index.get_level_values(0).nunique())}
pd.DataFrame(inter_rows).to_csv(RES / "Shock Exposure Models.csv", index=False)
OUT["shock_coefficients"] = inter_rows
OUT["shock_meta"] = inter_meta

# ------------------------------------------------------------------ predictive check
Qp = Q.dropna(subset=["adverse", "rev_growth"] + pctrl + ["L_breadth_z", "L_coverage_z", "L_linkage_z"]).copy()
train, test = Qp[Qp["fiscal_year"] <= 2022], Qp[Qp["fiscal_year"] >= 2023]
basef = ["L_ln_assets", "L_leverage", "L_cash_ratio", "L_roa", "L_ln_item1a_words"]
fullf = basef + ["L_breadth_z", "L_coverage_z", "L_linkage_z"] + [f"L_{c}" for c in INTS]
pred = {}
for name, feats in {"controls": basef, "controls plus text": fullf}.items():
    mu, sd = train[feats].mean(), train[feats].std()
    lr = LogisticRegression(max_iter=2000).fit((train[feats] - mu) / sd, train["adverse"])
    auc = roc_auc_score(test["adverse"], lr.predict_proba((test[feats] - mu) / sd)[:, 1])
    o = smf.ols("rev_growth ~ " + " + ".join(feats), data=train).fit()
    yhat = o.predict(test)
    oos = 1 - ((test["rev_growth"] - yhat) ** 2).sum() / ((test["rev_growth"] - train["rev_growth"].mean()) ** 2).sum()
    pred[name] = {"auc_adverse": auc, "oos_r2_growth": oos, "n_train": len(train), "n_test": len(test),
                  "adverse_rate_test": float(test["adverse"].mean())}
OUT["prediction"] = pred

# ------------------------------------------------------------------ descriptive trends for figures
trend = P[(P["fiscal_year"] >= 2017) & (P["fiscal_year"] <= 2025) & P["n_sent_1a"].notna()]
tr = trend.groupby("fiscal_year").agg(firms=("cik", "nunique"), breadth=("breadth", "mean"),
                                      linkage=("linkage", "mean"), coverage=("coverage", "mean"),
                                      item1a_words=("item1a_words", "median"),
                                      **{f"share_material_{c}": (f"mat_{c}", "mean") for c in CATS},
                                      **{f"intensity_{c}": (f"int_{c}", "mean") for c in CATS})
tr.to_csv(RES / "Disclosure Trends.csv")
OUT["trends"] = tr.round(6).to_dict(orient="index")
sec = trend.groupby(["division", "fiscal_year"])["breadth"].mean().unstack()
sec.to_csv(RES / "Breadth by Division.csv")
OUT["breadth_by_division"] = sec.round(4).to_dict(orient="index")

(RES / "Model Results.json").write_text(json.dumps(OUT, indent=1, default=float))
print("episode A n:", {k: v["n"] for k, v in metaA.items() if "|H3|" in k})
print(episode[episode["term"].isin(["breadth_z", "coverage_z", "breadth_z:coverage_z"])].round(4).to_string())
print(pd.DataFrame(panel_rows).round(4).to_string())
print(pd.DataFrame(inter_rows).round(4).to_string())
print(json.dumps(pred, indent=1))
