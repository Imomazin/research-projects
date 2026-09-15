#!/usr/bin/env python3
"""Supplementary checks for the Strategic Organization capability-asymmetry study.

Place this file at
    Strategic Organization/04 Analysis/Supplementary Checks/supplementary-checks.py

Run it inside the private repository
    python "Strategic Organization/04 Analysis/Supplementary Checks/supplementary-checks.py"

Run it anywhere on synthetic data with the same schema
    python supplementary-checks.py --demo

The script reads the two participant files used by
04 Analysis/Reproducible Analysis/analysis_pipeline.py. It writes aggregate tables only,
with no participant IDs and no participant rows, to
04 Analysis/Supplementary Checks/Outputs/ and it never modifies the validated
04 Analysis/Statistical Modeling/ outputs.

Checks
    S1  Score distributions and domain profile diagnostics
    S2  Screening rules for implausibly low assessments
    S3  Psychometrics under each screening rule
    S4  Core models M1 to M3 under each screening rule
    S5  Exposure-group medians and trimmed means
    S6  Occupation cluster structure and effective number of clusters
    S7  Wild cluster restricted bootstrap for M1 to M3
    S8  Occupation-level randomisation inference for M1 and M2
    S9  Career-interest mapping sensitivity
    S10 Comparison within ICT professional occupations
    S11 Measurement-error sensitivity for the conventional control

Methods follow Iglewicz and Hoaglin (1993) for modified z-scores, Carter, Schnepel and Steigerwald
(2017) for the effective number of clusters, Cameron, Gelbach and Miller (2008), MacKinnon and Webb (2017),
Roodman et al. (2019) and Webb (2023) for the wild cluster restricted bootstrap and MacKinnon, Nielsen and
Webb (2023) for cluster-robust practice.

Tested with Python 3.12, numpy 2.4, scipy 1.17, pandas 3.0 and statsmodels 0.15.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

SEED = 20260915
B_WILD = 9999
B_PARALLEL = 1000
B_PAIRS = 1999
LEVEL = 0.95

CONV_ITEMS = ["Strategic Thinking Pre", "Problem Solving Pre", "Decision Making Pre",
              "Leadership Pre", "Adaptability Pre", "Digital Capability Pre"]
AI_ITEMS = ["AI Knowledge Pre", "AI Application Pre", "AI Judgement Pre", "Data Literacy Pre"]
ALL_ITEMS = CONV_ITEMS + AI_ITEMS

CATEGORY_ORDER = ["Minimal Exposure", "Exposed: Gradient 2", "Exposed: Gradient 3", "Exposed: Gradient 4"]
EXPOSURE_ORDINAL = {"Not Exposed": 0, "Minimal Exposure": 1, "Exposed: Gradient 1": 2,
                    "Exposed: Gradient 2": 3, "Exposed: Gradient 3": 4, "Exposed: Gradient 4": 5}

# ILO 2025 categories for alternative ISCO-08 codes, read from
# https://github.com/pgmyrek/2025_GenAI_scores_ISCO08 (output_data.json)
ALTERNATIVE_CODES = {
    "2120": ("Mathematicians, actuaries and statisticians", "Exposed: Gradient 3"),
    "2432": ("Public relations professionals", "Exposed: Gradient 2"),
    "2513": ("Web and multimedia developers", "Exposed: Gradient 4"),
    "1219": ("Business services and administration managers not elsewhere classified", "Exposed: Gradient 2"),
    "2641": ("Authors and related writers", "Exposed: Gradient 3"),
}
SCENARIOS = {
    "A Data analysis interests coded 2120": {"data analysis": "2120", "data analyst": "2120", "data science": "2120"},
    "B Social media interests coded 2432": {"social media management": "2432", "social media manager": "2432"},
    "C UX/UI design interests coded 2513": {"product (ux/ui) design": "2513", "ux/ui designer": "2513"},
    "D Project and product management coded 1219": {"project management": "1219", "product management": "1219",
                                                    "product manager": "1219"},
    "E Technical writing coded 2641": {"technical writing": "2641"},
}


# Paths and loading

def resolve_root(arg_root: str | None) -> Path:
    candidates = []
    if arg_root:
        candidates.append(Path(arg_root))
    if os.environ.get("SO_PROJECT_ROOT"):
        candidates.append(Path(os.environ["SO_PROJECT_ROOT"]))
    here = Path(__file__).resolve()
    if len(here.parents) > 2:
        candidates.append(here.parents[2])
    candidates += [Path.cwd(), Path.cwd() / "Strategic Organization"]
    for c in candidates:
        if (c / "01 Primary Data").exists() and (c / "03 Data Integration").exists():
            return c
    raise FileNotFoundError("Could not find the Strategic Organization project root. "
                            "Pass --project-root or set SO_PROJECT_ROOT.")


def to_num(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def load_data(root: Path) -> tuple[pd.DataFrame, dict]:
    primary_path = root / "01 Primary Data" / "Compiled Participants Data_v2.csv"
    ready_path = root / "03 Data Integration" / "Strategic_Organization_Analysis_Ready.csv"
    for p in (primary_path, ready_path):
        if not p.exists():
            raise FileNotFoundError(f"Missing input file: {p}")
    primary = pd.read_csv(primary_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    ready = pd.read_csv(ready_path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    for name, frame in (("primary", primary), ("analysis-ready", ready)):
        if frame["Participant ID"].duplicated().any():
            raise ValueError(f"Duplicate Participant ID values in the {name} file")
    mapped = ready[ready["ISCO-08"].astype(str).str.strip() != ""].copy()
    keep = ["Participant ID", "Overall Baseline Score", "Assessment Date"] + ALL_ITEMS
    df = mapped.merge(primary[keep], on="Participant ID", how="left", validate="one_to_one")
    data = pd.DataFrame({
        "isco": df["ISCO-08"].astype(str).str.strip(),
        "title": df["ISCO Title"].astype(str).str.strip(),
        "category": df["ILO GenAI Exposure Category"].astype(str).str.strip(),
        "ordinal": to_num(df["Exposure Ordinal (Analytical Recode)"]),
        "confidence": df["Mapping Confidence"].astype(str).str.strip(),
        "interest": df["Career Interest"].astype(str).str.strip(),
        "conv": to_num(df["Conventional Capability Index"]),
        "ai": to_num(df["AI/Data Capability Index"]),
        "overall": to_num(df["Overall Baseline Score"]),
    })
    for item in ALL_ITEMS:
        data[item] = to_num(df[item]).to_numpy()
    required = ["ordinal", "conv", "ai"] + ALL_ITEMS
    if data[required].isna().any().any():
        bad = data[required].isna().sum()
        raise ValueError(f"Missing numeric values in mapped rows:\n{bad[bad > 0]}")
    data["gap"] = data["conv"] - data["ai"]
    data["high"] = (data["ordinal"] >= 4).astype(float)
    info = {
        "n_baseline": int(len(primary)),
        "n_mapped": int(len(data)),
        "index_check_conv_max_abs_diff": float(np.max(np.abs(data[CONV_ITEMS].mean(axis=1) - data["conv"]))),
        "index_check_ai_max_abs_diff": float(np.max(np.abs(data[AI_ITEMS].mean(axis=1) - data["ai"]))),
    }
    return data.reset_index(drop=True), info


# Statistical helpers

def cronbach(X: np.ndarray) -> float:
    X = np.asarray(X, float)
    k = X.shape[1]
    return k / (k - 1) * (1 - X.var(axis=0, ddof=1).sum() / X.sum(axis=1).var(ddof=1))


def codes(labels) -> tuple[np.ndarray, int]:
    g, uniques = pd.factorize(pd.Series(list(labels)), sort=True)
    return np.asarray(g), len(uniques)


def cluster_matrix(g: np.ndarray, G: int) -> np.ndarray:
    C = np.zeros((G, len(g)))
    C[g, np.arange(len(g))] = 1.0
    return C


def cr1_constant(n: int, k: int, G: int) -> float:
    return (G / (G - 1)) * ((n - 1) / (n - k))


def cr1_fit(y: np.ndarray, X: np.ndarray, g: np.ndarray, G: int):
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    u = y - X @ beta
    S = np.zeros((G, X.shape[1]))
    np.add.at(S, g, X * u[:, None])
    V = cr1_constant(len(y), X.shape[1], G) * XtX_inv @ (S.T @ S) @ XtX_inv
    return beta, np.sqrt(np.diag(V)), XtX_inv


def design(*cols: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(cols[0]))] + [np.asarray(c, float) for c in cols])


def statsmodels_cluster(y, X, labels):
    g, _ = codes(labels)
    return sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g, "use_correction": True}, use_t=True)


def effective_clusters(X: np.ndarray, g: np.ndarray, G: int, k: int, rho: float) -> float:
    """Carter, Schnepel and Steigerwald (2017) effective number of clusters for coefficient k."""
    a = X @ np.linalg.inv(X.T @ X)[k]
    sum_a = np.bincount(g, weights=a, minlength=G)
    sum_a2 = np.bincount(g, weights=a ** 2, minlength=G)
    gamma = (1 - rho) * sum_a2 + rho * sum_a ** 2
    gbar = gamma.mean()
    return float(G / (1 + np.mean((gamma - gbar) ** 2) / gbar ** 2))


def kish_clusters(sizes) -> float:
    s = np.asarray(sizes, float)
    return float(s.sum() ** 2 / (s ** 2).sum())


def draw_weights(kind: str, B: int, G: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "Rademacher":
        return rng.choice(np.array([-1.0, 1.0]), size=(B, G))
    if kind == "Webb":
        vals = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
        return rng.choice(vals, size=(B, G))
    raise ValueError(kind)


class WildClusterBootstrap:
    """Wild cluster restricted (WCR) bootstrap-t for one coefficient with CR1 standard errors."""

    def __init__(self, y, X, labels, k, kind, B, seed):
        self.y = np.asarray(y, float)
        self.X = np.asarray(X, float)
        self.k = k
        self.g, self.G = codes(labels)
        self.C = cluster_matrix(self.g, self.G)
        self.n, self.K = self.X.shape
        self.c = cr1_constant(self.n, self.K, self.G)
        self.beta, self.se, XtX_inv = cr1_fit(self.y, self.X, self.g, self.G)
        self.P = XtX_inv @ self.X.T
        self.a = self.X @ XtX_inv[k]
        self.Xr = np.delete(self.X, k, axis=1)
        self.Pr = np.linalg.pinv(self.Xr)
        self.W = draw_weights(kind, B, self.G, np.random.default_rng(seed))

    def pvalue(self, b0: float) -> float:
        xk = self.X[:, self.k]
        fitted = self.Xr @ (self.Pr @ (self.y - b0 * xk)) + b0 * xk
        resid = self.y - fitted
        t_obs = (self.beta[self.k] - b0) / self.se[self.k]
        Ystar = fitted[None, :] + resid[None, :] * self.W[:, self.g]
        betas = Ystar @ self.P.T
        U = Ystar - betas @ self.X.T
        se = np.sqrt(self.c * np.sum(((U * self.a) @ self.C.T) ** 2, axis=1))
        tstar = (betas[:, self.k] - b0) / se
        return float(np.mean(np.abs(tstar) >= abs(t_obs)))

    def interval(self, level: float = LEVEL) -> tuple[float, float]:
        alpha = 1 - level
        b, se = self.beta[self.k], self.se[self.k]
        tol = 1e-4 * max(se, 1e-12)

        def bound(direction: int) -> float:
            inner, outer = b, b + direction * 2.5 * se
            for _ in range(16):
                if self.pvalue(outer) <= alpha:
                    break
                inner, outer = outer, b + direction * 2 * abs(outer - b)
            else:
                return float("nan")
            for _ in range(60):
                mid = 0.5 * (inner + outer)
                if self.pvalue(mid) > alpha:
                    inner = mid
                else:
                    outer = mid
                if abs(outer - inner) < tol:
                    break
            return 0.5 * (inner + outer)

        return bound(-1), bound(+1)


def batch_cluster_t(y, H, conv, C, G):
    """Coefficient and CR1 t statistic on the exposure column for many exposure assignments H (m x n)."""
    m, n = H.shape
    s_h = H.sum(axis=1)
    if conv is None:
        det = n * s_h - s_h ** 2
        inv01, inv11, inv00 = -s_h / det, n / det, s_h / det
        sy, shy = y.sum(), H @ y
        b0 = inv00 * sy + inv01 * shy
        b1 = inv01 * sy + inv11 * shy
        U = y[None, :] - b0[:, None] - b1[:, None] * H
        a = inv01[:, None] + inv11[:, None] * H
        K, beta_k = 2, b1
    else:
        XtX = np.empty((m, 3, 3))
        XtX[:, 0, 0] = n
        XtX[:, 0, 1] = XtX[:, 1, 0] = XtX[:, 1, 1] = s_h
        XtX[:, 0, 2] = XtX[:, 2, 0] = conv.sum()
        XtX[:, 1, 2] = XtX[:, 2, 1] = H @ conv
        XtX[:, 2, 2] = conv @ conv
        Xty = np.stack([np.full(m, y.sum()), H @ y, np.full(m, conv @ y)], axis=1)
        inv = np.linalg.inv(XtX)
        beta = np.einsum("mij,mj->mi", inv, Xty)
        U = y[None, :] - beta[:, [0]] - beta[:, [1]] * H - beta[:, [2]] * conv[None, :]
        a = inv[:, 1, 0][:, None] + inv[:, 1, 1][:, None] * H + inv[:, 1, 2][:, None] * conv[None, :]
        K, beta_k = 3, beta[:, 1]
    se = np.sqrt(cr1_constant(n, K, G) * np.sum(((U * a) @ C.T) ** 2, axis=1))
    return beta_k, beta_k / se


def randomisation_inference(y, high, conv, labels, batch=4096):
    g, G = codes(labels)
    C = cluster_matrix(g, G)
    high_by_cluster = np.zeros(G)
    for j in range(G):
        vals = np.unique(high[g == j])
        if len(vals) != 1:
            raise ValueError("Exposure varies within an occupation cluster")
        high_by_cluster[j] = vals[0]
    n_high = int(high_by_cluster.sum())
    obs_b, obs_t = batch_cluster_t(y, high[None, :], conv, C, G)
    total, extreme_t, extreme_b = 0, 0, 0
    combos = itertools.combinations(range(G), n_high)
    while True:
        chunk = list(itertools.islice(combos, batch))
        if not chunk:
            break
        A = np.zeros((len(chunk), G))
        A[np.repeat(np.arange(len(chunk)), n_high), np.asarray(chunk).ravel()] = 1.0
        b, t = batch_cluster_t(y, A[:, g], conv, C, G)
        extreme_t += int(np.sum(np.abs(t) >= abs(obs_t[0]) - 1e-12))
        extreme_b += int(np.sum(np.abs(b) >= abs(obs_b[0]) - 1e-12))
        total += len(chunk)
    return {"Clusters": G, "High-exposure clusters": n_high, "Assignments enumerated": total,
            "Observed B": float(obs_b[0]), "Observed t": float(obs_t[0]),
            "Randomisation p [|t|]": extreme_t / total, "Randomisation p [|B|]": extreme_b / total}


def parallel_analysis(items: np.ndarray, B: int, seed: int):
    rng = np.random.default_rng(seed)
    n, p = items.shape
    observed = np.linalg.eigvalsh(np.corrcoef(items, rowvar=False))[::-1]
    sims = np.array([np.linalg.eigvalsh(np.corrcoef(rng.normal(size=(n, p)), rowvar=False))[::-1]
                     for _ in range(B)])
    threshold = np.quantile(sims, 0.95, axis=0)
    retained = 0
    for i in range(p):
        if observed[i] > threshold[i]:
            retained += 1
        else:
            break
    return observed, threshold, retained


def modified_z(x: np.ndarray) -> np.ndarray:
    """Iglewicz and Hoaglin (1993) modified z-score."""
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    return np.zeros_like(x) if mad == 0 else 0.6745 * (x - med) / mad


def eiv_high(ai, high, conv, conv_items):
    """Method-of-moments errors-in-variables correction for the conventional control using alpha."""
    alpha_c = cronbach(conv_items)
    Z = np.column_stack([high, conv])
    Zc = Z - Z.mean(axis=0)
    yc = ai - ai.mean()
    S = Zc.T @ Zc / (len(ai) - 1)
    s = Zc.T @ yc / (len(ai) - 1)
    S[1, 1] -= (1 - alpha_c) * conv.var(ddof=1)
    if np.any(np.linalg.eigvalsh(S) <= 0) or np.ptp(high) == 0:
        return float("nan"), float("nan"), alpha_c
    b = np.linalg.solve(S, s)
    return float(b[0]), float(b[1]), float(alpha_c)


# Individual checks

def s1_distributions(d: pd.DataFrame):
    rows = []
    variables = [(v, d[v].to_numpy()) for v in ALL_ITEMS] + [
        ("Conventional Capability Index", d["conv"].to_numpy()), ("AI/Data Capability Index", d["ai"].to_numpy()),
        ("Capability Gap", d["gap"].to_numpy())]
    overall = d["overall"].dropna().to_numpy()
    if len(overall):
        variables.append(("Overall Baseline Score", overall))
    for name, x in variables:
        rows.append({"Variable": name, "N": len(x), "Mean": x.mean(), "SD": x.std(ddof=1), "Median": np.median(x),
                     "Min": x.min(), "Max": x.max(), "% at or above 90": 100 * np.mean(x >= 90),
                     "% equal to 100": 100 * np.mean(x == 100), "Skewness": stats.skew(x, bias=False),
                     "Distinct values": len(np.unique(x))})
    conv, ai = d["conv"].to_numpy(), d["ai"].to_numpy()
    ten = d[ALL_ITEMS].mean(axis=1).to_numpy()
    profile = [
        {"Statistic": "Participants with AI/data index above conventional index", "Value": int(np.sum(ai > conv))},
        {"Statistic": "Maximum AI/data index", "Value": float(ai.max())},
        {"Statistic": "Maximum conventional index", "Value": float(conv.max())},
        {"Statistic": "% with conventional index above the maximum AI/data index", "Value": 100 * np.mean(conv > ai.max())},
    ]
    mask = d["overall"].notna().to_numpy()
    if mask.sum() > 3:
        ov = d.loc[mask, "overall"].to_numpy()
        fit = sm.OLS(ov, design(conv[mask], ai[mask])).fit()
        profile += [
            {"Statistic": "Pearson r overall baseline with ten-dimension mean", "Value": np.corrcoef(ov, ten[mask])[0, 1]},
            {"Statistic": "Pearson r overall baseline with conventional index", "Value": np.corrcoef(ov, conv[mask])[0, 1]},
            {"Statistic": "Pearson r overall baseline with AI/data index", "Value": np.corrcoef(ov, ai[mask])[0, 1]},
            {"Statistic": "OLS weight of conventional index in overall baseline", "Value": fit.params[1]},
            {"Statistic": "OLS weight of AI/data index in overall baseline", "Value": fit.params[2]},
            {"Statistic": "Mean overall baseline minus ten-dimension mean", "Value": float(np.mean(ov - ten[mask]))},
        ]
    return pd.DataFrame(rows), pd.DataFrame(profile)


def screening_rules(d: pd.DataFrame) -> dict[str, np.ndarray]:
    items = d[ALL_ITEMS].to_numpy()
    rules = {
        "Full mapped sample": np.ones(len(d), bool),
        "Exclude overall baseline score of zero": (d["overall"] > 0).to_numpy(),
        "Exclude any dimension score below 10": (items >= 10).all(axis=1),
        "Exclude modified z below -3.5 on either index": (modified_z(d["conv"].to_numpy()) >= -3.5)
                                                          & (modified_z(d["ai"].to_numpy()) >= -3.5),
    }
    rules["Exclude participants flagged by any rule"] = (rules["Exclude overall baseline score of zero"]
                                                         & rules["Exclude any dimension score below 10"]
                                                         & rules["Exclude modified z below -3.5 on either index"])
    return rules


def s2_s3_s4(d: pd.DataFrame, rules: dict, B: int):
    s2, s3, s4 = [], [], []
    high = d["high"].to_numpy().astype(bool)
    for i, (name, keep) in enumerate(rules.items()):
        s2.append({"Rule": name, "Excluded": int((~keep).sum()), "Excluded low exposure": int((~keep & ~high).sum()),
                   "Excluded high exposure": int((~keep & high).sum()), "Retained": int(keep.sum()),
                   "Retained low exposure": int((keep & ~high).sum()), "Retained high exposure": int((keep & high).sum())})
        sub = d[keep].reset_index(drop=True)
        conv, ai, gap, hi = (sub[c].to_numpy() for c in ("conv", "ai", "gap", "high"))
        a_c, a_a = cronbach(sub[CONV_ITEMS].to_numpy()), cronbach(sub[AI_ITEMS].to_numpy())
        r = np.corrcoef(conv, ai)[0, 1]
        sc, sa = conv.std(ddof=1), ai.std(ddof=1)
        rel_gap = (a_c * sc ** 2 + a_a * sa ** 2 - 2 * r * sc * sa) / (sc ** 2 + sa ** 2 - 2 * r * sc * sa)
        obs, thr, retained = parallel_analysis(sub[ALL_ITEMS].to_numpy(), B_PARALLEL, SEED + 10 + i)
        s3.append({"Rule": name, "N": len(sub), "Alpha conventional": a_c, "Alpha AI/data": a_a,
                   "Alpha all ten": cronbach(sub[ALL_ITEMS].to_numpy()), "Pearson r indices": r,
                   "Spearman rho indices": stats.spearmanr(conv, ai).statistic,
                   "Disattenuated r [Pearson over root alpha product]": r / math.sqrt(a_c * a_a),
                   "Gap SD": gap.std(ddof=1), "Difference-score reliability of gap": rel_gap,
                   "Eigenvalue 1": obs[0], "Eigenvalue 2": obs[1], "Parallel analysis threshold 2": thr[1],
                   "Components retained": retained,
                   "Mean gap": gap.mean(), "Median gap": np.median(gap)})
        for model, y, X, k in (("M1 AI/data on high exposure", ai, design(hi), 1),
                               ("M2 AI/data on high exposure and conventional", ai, design(hi, conv), 1),
                               ("M3 gap on high exposure", gap, design(hi), 1)):
            res = statsmodels_cluster(y, X, sub["isco"])
            wcr = WildClusterBootstrap(y, X, sub["isco"], k, "Webb", B, SEED + 100 + i)
            ci = res.conf_int(alpha=1 - LEVEL)[k]
            s4.append({"Rule": name, "Model": model, "N": len(sub), "Clusters": wcr.G, "B": res.params[k],
                       "CR1 SE": res.bse[k], "CR1 CI lower": ci[0], "CR1 CI upper": ci[1], "CR1 p": res.pvalues[k],
                       "WCR Webb p": wcr.pvalue(0.0), "R-squared": res.rsquared})
    return pd.DataFrame(s2), pd.DataFrame(s3), pd.DataFrame(s4)


def s5_group_medians(d: pd.DataFrame, rules: dict):
    rows = []
    for rule in ("Full mapped sample", "Exclude participants flagged by any rule"):
        sub = d[rules[rule]]
        groups = [(c, sub[sub["category"] == c]) for c in CATEGORY_ORDER]
        groups += [("Low exposure [Minimal and Gradient 2]", sub[sub["high"] == 0]),
                   ("High exposure [Gradients 3 and 4]", sub[sub["high"] == 1])]
        for label, grp in groups:
            if len(grp) == 0:
                continue
            row = {"Rule": rule, "Group": label, "N": len(grp)}
            for col, nice in (("conv", "Conventional"), ("ai", "AI/data"), ("gap", "Gap")):
                x = grp[col].to_numpy()
                row.update({f"{nice} median": np.median(x), f"{nice} Q1": np.quantile(x, .25),
                            f"{nice} Q3": np.quantile(x, .75), f"{nice} 10% trimmed mean": stats.trim_mean(x, 0.1)})
            rows.append(row)
    return pd.DataFrame(rows)


def s6_clusters(d: pd.DataFrame):
    table = (d.groupby(["isco", "title", "category"], as_index=False)
               .agg(N=("ai", "size"), High=("high", "max"))
               .sort_values(["High", "N"], ascending=[False, False]))
    table["Share of mapped sample %"] = 100 * table["N"] / len(d)
    table = table.rename(columns={"isco": "ISCO-08", "title": "ISCO title", "category": "ILO category",
                                  "High": "High exposure"})
    g, G = codes(d["isco"])
    hi, conv = d["high"].to_numpy(), d["conv"].to_numpy()
    summary = [{"Statistic": "Occupation clusters", "Value": G},
               {"Statistic": "High-exposure clusters", "Value": int(table["High exposure"].sum())},
               {"Statistic": "Largest cluster share %", "Value": float(table["Share of mapped sample %"].max())},
               {"Statistic": "Kish effective clusters, all", "Value": kish_clusters(table["N"])},
               {"Statistic": "Kish effective clusters, high exposure",
                "Value": kish_clusters(table.loc[table["High exposure"] == 1, "N"])},
               {"Statistic": "Kish effective clusters, low exposure",
                "Value": kish_clusters(table.loc[table["High exposure"] == 0, "N"])}]
    for model, X in (("M1", design(hi)), ("M2", design(hi, conv))):
        for rho in (0.0, 0.5, 1.0):
            summary.append({"Statistic": f"G* for high exposure in {model}, rho {rho:.1f}",
                            "Value": effective_clusters(X, g, G, 1, rho)})
    return table, pd.DataFrame(summary)


def s7_wild(d: pd.DataFrame, B: int):
    rows = []
    hi, conv, ai, gap = (d[c].to_numpy() for c in ("high", "conv", "ai", "gap"))
    for j, (model, y, X) in enumerate((("M1 AI/data on high exposure", ai, design(hi)),
                                       ("M2 AI/data on high exposure and conventional", ai, design(hi, conv)),
                                       ("M3 gap on high exposure", gap, design(hi)))):
        res = statsmodels_cluster(y, X, d["isco"])
        ci = res.conf_int(alpha=1 - LEVEL)[1]
        for kind in ("Rademacher", "Webb"):
            wcr = WildClusterBootstrap(y, X, d["isco"], 1, kind, B, SEED + 200 + j)
            if abs(wcr.se[1] - res.bse[1]) > 1e-8 * max(1.0, res.bse[1]):
                raise AssertionError("Custom CR1 standard error does not match statsmodels")
            lo, up = wcr.interval()
            rows.append({"Model": model, "Weights": kind, "Bootstrap draws": B, "B": res.params[1],
                         "CR1 SE": res.bse[1], "CR1 t CI lower": ci[0], "CR1 t CI upper": ci[1],
                         "CR1 t p": res.pvalues[1], "WCR p": wcr.pvalue(0.0), "WCR CI lower": lo, "WCR CI upper": up})
    return pd.DataFrame(rows)


def s8_randomisation(d: pd.DataFrame):
    hi, conv, ai = (d[c].to_numpy() for c in ("high", "conv", "ai"))
    rows = []
    for model, cv in (("M1 AI/data on high exposure", None), ("M2 AI/data on high exposure and conventional", conv)):
        out = randomisation_inference(ai, hi, cv, d["isco"])
        rows.append({"Model": model, **out})
    return pd.DataFrame(rows)


def recode(d: pd.DataFrame, overrides: dict) -> tuple[pd.DataFrame, int]:
    out = d.copy()
    key = out["interest"].str.lower().str.strip()
    changed = key.isin(overrides.keys())
    for label, code in overrides.items():
        m = key == label
        title, category = ALTERNATIVE_CODES[code]
        out.loc[m, ["isco", "title", "category"]] = [code, title, category]
        out.loc[m, "ordinal"] = EXPOSURE_ORDINAL[category]
    out["high"] = (out["ordinal"] >= 4).astype(float)
    return out, int(changed.sum())


def s9_mapping(d: pd.DataFrame, B: int):
    combined = {}
    for mapping in SCENARIOS.values():
        combined.update(mapping)
    scenarios = [("Original mapping", d, 0)]
    for name, mapping in SCENARIOS.items():
        recoded, n_changed = recode(d, mapping)
        if n_changed == 0:
            print(f"Warning: {name} matched no career-interest labels. Check the label spelling in SCENARIOS.")
        scenarios.append((name, recoded, n_changed))
    scenarios.append(("F All alternatives A to E",) + recode(d, combined))
    hc = d[d["confidence"] == "High"].reset_index(drop=True)
    scenarios.append(("G High-confidence mappings only", hc, int(len(d) - len(hc))))
    rows = []
    for j, (name, sub, n_changed) in enumerate(scenarios):
        hi, conv, ai = (sub[c].to_numpy() for c in ("high", "conv", "ai"))
        g, G = codes(sub["isco"])
        switched = int(np.sum(sub["high"].to_numpy() != d["high"].to_numpy())) if len(sub) == len(d) else np.nan
        m1 = statsmodels_cluster(ai, design(hi), sub["isco"])
        X2 = design(hi, conv)
        m2 = statsmodels_cluster(ai, X2, sub["isco"])
        ci = m2.conf_int(alpha=1 - LEVEL)[1]
        wcr = WildClusterBootstrap(ai, X2, sub["isco"], 1, "Webb", B, SEED + 300 + j)
        rows.append({"Scenario": name, "Participants recoded or removed": n_changed,
                     "Participants switching exposure group": switched, "N": len(sub),
                     "High exposure N": int(hi.sum()), "Clusters": G,
                     "High-exposure clusters": int(sub.loc[sub["high"] == 1, "isco"].nunique()),
                     "M1 B": m1.params[1], "M1 CR1 SE": m1.bse[1], "M1 CR1 p": m1.pvalues[1],
                     "M2 B": m2.params[1], "M2 CR1 SE": m2.bse[1], "M2 CR1 CI lower": ci[0],
                     "M2 CR1 CI upper": ci[1], "M2 CR1 p": m2.pvalues[1], "M2 WCR Webb p": wcr.pvalue(0.0),
                     "M2 G* rho 1": effective_clusters(X2, g, G, 1, 1.0)})
    return pd.DataFrame(rows)


def s10_ict(d: pd.DataFrame, B: int):
    sub = d[d["isco"].str.startswith("25")].reset_index(drop=True)
    hi, conv, ai = (sub[c].to_numpy() for c in ("high", "conv", "ai"))
    rows = []
    for model, X in (("M1 AI/data on high exposure", design(hi)),
                     ("M2 AI/data on high exposure and conventional", design(hi, conv))):
        hc3 = sm.OLS(ai, X).fit(cov_type="HC3")
        cr1 = statsmodels_cluster(ai, X, sub["isco"])
        wcr = WildClusterBootstrap(ai, X, sub["isco"], 1, "Webb", B, SEED + 400)
        rows.append({"Model": model, "N": len(sub), "High exposure N": int(hi.sum()),
                     "Clusters": int(sub["isco"].nunique()),
                     "Codes": " ".join(f"{c}={n}" for c, n in sub["isco"].value_counts().sort_index().items()),
                     "B": hc3.params[1], "HC3 SE": hc3.bse[1], "HC3 p": hc3.pvalues[1], "CR1 SE": cr1.bse[1],
                     "CR1 p": cr1.pvalues[1], "WCR Webb p": wcr.pvalue(0.0),
                     "Low exposure AI/data median": np.median(ai[hi == 0]),
                     "High exposure AI/data median": np.median(ai[hi == 1]),
                     "Low exposure conventional median": np.median(conv[hi == 0]),
                     "High exposure conventional median": np.median(conv[hi == 1])})
    return pd.DataFrame(rows)


def s11_measurement(d: pd.DataFrame, rules: dict):
    rows = []
    rng = np.random.default_rng(SEED + 500)
    for rule in ("Full mapped sample", "Exclude participants flagged by any rule"):
        sub = d[rules[rule]].reset_index(drop=True)
        hi, conv, ai = (sub[c].to_numpy() for c in ("high", "conv", "ai"))
        items = sub[CONV_ITEMS].to_numpy()
        ols = sm.OLS(ai, design(hi, conv)).fit()
        b_hi, b_conv, alpha_c = eiv_high(ai, hi, conv, items)
        g, G = codes(sub["isco"])
        members = [np.where(g == j)[0] for j in range(G)]
        draws, skipped = [], 0
        for _ in range(B_PAIRS):
            idx = np.concatenate([members[j] for j in rng.integers(0, G, G)])
            est = eiv_high(ai[idx], hi[idx], conv[idx], items[idx])[0]
            if np.isfinite(est):
                draws.append(est)
            else:
                skipped += 1
        draws = np.array(draws)
        rows.append({"Rule": rule, "N": len(sub), "Alpha conventional": alpha_c, "OLS B high exposure": ols.params[1],
                     "OLS B conventional": ols.params[2], "EIV B high exposure": b_hi, "EIV B conventional": b_conv,
                     "Cluster pairs bootstrap draws used": len(draws), "Draws skipped": skipped,
                     "EIV B high exposure percentile CI lower": np.quantile(draws, .025) if len(draws) else np.nan,
                     "EIV B high exposure percentile CI upper": np.quantile(draws, .975) if len(draws) else np.nan})
    return pd.DataFrame(rows)


# Reconciliation, synthetic data and reporting

def reconcile(root: Path, d: pd.DataFrame) -> list[dict]:
    manifest = root / "04 Analysis" / "Statistical Modeling" / "analysis_manifest.json"
    if not manifest.exists():
        return []
    ref = json.loads(manifest.read_text(encoding="utf-8"))
    hi, conv, ai = (d[c].to_numpy() for c in ("high", "conv", "ai"))
    m1 = statsmodels_cluster(ai, design(hi), d["isco"])
    m2 = statsmodels_cluster(ai, design(hi, conv), d["isco"])
    checks = [("n_mapped", len(d)), ("conv_mean", conv.mean()), ("ai_mean", ai.mean()),
              ("high_exposure_ai_unadjusted_B", m1.params[1]), ("high_exposure_ai_adjusted_B", m2.params[1]),
              ("high_exposure_ai_adjusted_p", m2.pvalues[1]), ("unique_isco", d["isco"].nunique())]
    return [{"Manifest key": k, "Validated value": ref.get(k), "Reproduced value": float(v),
             "Absolute difference": abs(float(v) - float(ref[k])) if k in ref else None} for k, v in checks]


def build_demo_project(root: Path) -> None:
    rng = np.random.default_rng(SEED)
    G2, G3, G4, MIN = "Exposed: Gradient 2", "Exposed: Gradient 3", "Exposed: Gradient 4", "Minimal Exposure"
    labels = [  # synthetic stand-ins for the real crosswalk labels, with the real code frequencies
        ("Backend Development", 46, "2512", "Software developers", "High", G3),
        ("Software Engineering", 3, "2512", "Software developers", "High", G3),
        ("Backend Developer", 2, "2512", "Software developers", "High", G3),
        ("AI Engineering", 1, "2512", "Software developers", "Medium", G3),
        ("Frontend Development", 41, "2513", "Web and multimedia developers", "High", G4),
        ("Full-stack Development", 7, "2513", "Web and multimedia developers", "High", G4),
        ("Web Developer", 4, "2513", "Web and multimedia developers", "High", G4),
        ("Frontend Developer", 3, "2513", "Web and multimedia developers", "High", G4),
        ("Web Development", 2, "2513", "Web and multimedia developers", "High", G4),
        ("Financial Analysis", 1, "2413", "Financial analysts", "High", G4),
        ("Social Media Management", 7, "2431", "Advertising and marketing professionals", "Medium", G3),
        ("Social Media Manager", 1, "2431", "Advertising and marketing professionals", "Medium", G3),
        ("Technical Writing", 2, "2642", "Journalists", "Medium", G3),
        ("Accounting", 2, "2411", "Accountants", "High", G3),
        ("Mobile Development", 1, "2514", "Applications programmers", "High", G3),
        ("Content Creation", 1, "2641", "Authors and related writers", "Low", G3),
        ("Customer Service", 1, "4225", "Enquiry clerks", "High", G3),
        ("Product (UX/UI) Design", 15, "2166", "Graphic and multimedia designers", "Medium", G2),
        ("UX/UI Designer", 2, "2166", "Graphic and multimedia designers", "Medium", G2),
        ("Graphic Design", 3, "2166", "Graphic and multimedia designers", "High", G2),
        ("Motion Graphics", 1, "2166", "Graphic and multimedia designers", "High", G2),
        ("Business Analysis", 14, "2421", "Management and organization analysts", "High", G2),
        ("Business Analyst", 6, "2421", "Management and organization analysts", "High", G2),
        ("Data Analysis", 9, "2511", "Systems analysts", "Medium", G2),
        ("Data Analyst", 5, "2511", "Systems analysts", "Medium", G2),
        ("Data Science", 1, "2511", "Systems analysts", "Medium", G2),
        ("AI Consulting", 1, "2511", "Systems analysts", "Medium", G2),
        ("Systems Analysis", 1, "2511", "Systems analysts", "High", G2),
        ("Cybersecurity", 4, "2529", "Database and network professionals not elsewhere classified", "High", G2),
        ("Operations Management", 1, "1219", "Business services and administration managers not elsewhere classified", "High", G2),
        ("Business Administration", 1, "1219", "Business services and administration managers not elsewhere classified", "High", G2),
        ("Project Management", 4, "2422", "Policy administration professionals", "Medium", MIN),
        ("Product Management", 1, "1223", "Research and development managers", "Medium", MIN),
        ("Product Manager", 1, "1223", "Research and development managers", "Medium", MIN),
        ("Industrial Design", 1, "2163", "Product and garment designers", "High", MIN),
        ("Academic Researcher", 1, "2310", "University and higher education teachers", "Medium", MIN),
        ("Small Business Owner", 1, "1120", "Managing directors and chief executives", "Low", MIN),
    ]
    people = [lab for lab in labels for _ in range(lab[1])] + [("", 0, "", "", "", "")] * 2
    n = len(people)
    high = np.array([1.0 if p[5] in (G3, G4) else 0.0 for p in people])
    general = rng.normal(0, 1, n) + 0.35 * high
    conv_items = np.clip(88 + 9 * general[:, None] + rng.normal(0, 6, (n, 6)), 0, 100)
    ai_items = np.clip(70 + 7 * general[:, None] + rng.normal(0, 4, (n, 4)), 0, 98)
    low_pool, high_pool = np.where(high == 0)[0], np.where(high == 1)[0]
    tail = np.concatenate([rng.choice(low_pool, 13, replace=False), rng.choice(high_pool, 6, replace=False)])
    factor = rng.uniform(0.3, 0.85, len(tail))
    conv_items[tail] *= factor[:, None]
    ai_items[tail] *= factor[:, None]
    zero = tail[0]
    conv_items[zero] = rng.uniform(0, 5, 6)
    ai_items[zero] = rng.uniform(0, 1.5, 4)
    conv_items, ai_items = np.round(conv_items, 1), np.round(ai_items, 1)
    overall = np.round(np.c_[conv_items, ai_items].mean(axis=1), 1)
    overall[zero] = 0.0
    primary_cols = ["Participant ID", "Assessment Date", "Age Group", "Gender", "Country", "Highest Education Level",
                    "Employment Status", "Career Stage", "Years of Experience", "Current Job Function",
                    "Industry / Sector", "Current Role Level", "Career Interest", "Previous AI Exposure",
                    "TG Nexus Cohort", "Overall Baseline Score"] + ALL_ITEMS + [
                    "Primary Gap Identified", "Intervention Type", "Personalised Intervention",
                    "AI-Supported Recommendation", "Intervention Start Date", "Intervention End Date",
                    "Learning / Contact Hours", "Completion Rate %", "Engagement Level", "Reassessment Date",
                    "Overall Post Score"] + [i.replace(" Pre", " Post") for i in ALL_ITEMS] + [
                    "Outcome / Progression", "Notes"]
    primary, ready = [], []
    for i, p in enumerate(people):
        pid = f"DEMO-{i + 1:03d}"
        rec = {c: "" for c in primary_cols}
        rec.update({"Participant ID": pid, "Assessment Date": str(date(2026, 5, 22) + timedelta(days=int(rng.integers(0, 90)))),
                    "Country": "Nigeria", "Career Interest": p[0], "Overall Baseline Score": f"{overall[i]:.1f}",
                    "Current Job Function": "Technology & Digital"})
        for j, item in enumerate(CONV_ITEMS):
            rec[item] = f"{conv_items[i, j]:.1f}"
        for j, item in enumerate(AI_ITEMS):
            rec[item] = f"{ai_items[i, j]:.1f}"
        primary.append(rec)
        ready.append({"Participant ID": pid, "Career Interest": p[0], "ISCO-08": p[2], "ISCO Title": p[3],
                      "Mapping Confidence": p[4], "ILO GenAI Exposure Category": p[5],
                      "Exposure Ordinal (Analytical Recode)": str(EXPOSURE_ORDINAL[p[5]]) if p[5] else "",
                      "Conventional Capability Index": f"{conv_items[i].mean():.4f}",
                      "AI/Data Capability Index": f"{ai_items[i].mean():.4f}",
                      "Capability Gap": f"{conv_items[i].mean() - ai_items[i].mean():.4f}"})
    (root / "01 Primary Data").mkdir(parents=True, exist_ok=True)
    (root / "03 Data Integration").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(primary, columns=primary_cols).to_csv(root / "01 Primary Data" / "Compiled Participants Data_v2.csv", index=False)
    pd.DataFrame(ready).to_csv(root / "03 Data Integration" / "Strategic_Organization_Analysis_Ready.csv", index=False)


def fmt(x, d=2):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"


def write_summary(out: Path, info: dict, results: dict, demo: bool) -> None:
    s3, s4, s7, s8, s9, s10, s11 = (results[k] for k in ("S3", "S4", "S7", "S8", "S9", "S10", "S11"))
    s2, s6b, profile = results["S2"], results["S6b"], results["S1b"]
    full, screened = "Full mapped sample", "Exclude participants flagged by any rule"
    p3 = s3.set_index("Rule")
    m = s4.set_index(["Rule", "Model"])
    m1, m2 = "M1 AI/data on high exposure", "M2 AI/data on high exposure and conventional"
    wild = s7.set_index(["Model", "Weights"])
    effective = s6b.set_index("Statistic")["Value"]
    prof = profile.set_index("Statistic")["Value"]
    lines = ["# Supplementary Checks Summary", ""]
    if demo:
        lines += ["These outputs come from synthetic demonstration data. None of the numbers describe the study.", ""]
    lines += [f"Generated {time.strftime('%d %B %Y %H:%M')} from {info['n_mapped']} mapped participants "
              f"[{info['n_baseline']} in the baseline file].", ""]
    if results.get("Reconciliation"):
        worst = max((r["Absolute difference"] or 0) for r in results["Reconciliation"])
        lines += ["## Reconciliation", "",
                  f"The script reproduced the validated manifest values with a largest absolute difference of {worst:.2e}.", ""]
    lines += ["## Domain profile", "",
              f"The highest AI/data index in the sample was {fmt(prof['Maximum AI/data index'])} while "
              f"{fmt(prof['% with conventional index above the maximum AI/data index'], 1)}% of participants had a "
              f"conventional index above that value. The number of participants scoring higher on AI/data than on "
              f"conventional capability was {int(prof['Participants with AI/data index above conventional index'])}.", ""]
    excl = s2.set_index("Rule").loc[screened]
    lines += ["## Screening and psychometrics", "",
              f"The combined screening rule excluded {int(excl['Excluded'])} participants "
              f"[{int(excl['Excluded low exposure'])} low exposure and {int(excl['Excluded high exposure'])} high exposure]. "
              f"The Pearson correlation between the indices moved from {fmt(p3.loc[full, 'Pearson r indices'], 3)} to "
              f"{fmt(p3.loc[screened, 'Pearson r indices'], 3)} and the Spearman correlation from "
              f"{fmt(p3.loc[full, 'Spearman rho indices'], 3)} to {fmt(p3.loc[screened, 'Spearman rho indices'], 3)}. "
              f"The difference-score reliability of the gap was {fmt(p3.loc[full, 'Difference-score reliability of gap'], 3)} "
              f"in the full sample and {fmt(p3.loc[screened, 'Difference-score reliability of gap'], 3)} after screening. "
              f"Parallel analysis retained {int(p3.loc[screened, 'Components retained'])} "
              f"{'component' if int(p3.loc[screened, 'Components retained']) == 1 else 'components'} after screening.", ""]
    lines += ["## Core models after screening", "",
              f"M1 gave B = {fmt(m.loc[(full, m1), 'B'])} in the full sample and {fmt(m.loc[(screened, m1), 'B'])} after "
              f"screening [WCR Webb p = {fmt(m.loc[(screened, m1), 'WCR Webb p'], 3)}]. M2 gave B = "
              f"{fmt(m.loc[(full, m2), 'B'])} in the full sample and {fmt(m.loc[(screened, m2), 'B'])} after screening "
              f"[WCR Webb p = {fmt(m.loc[(screened, m2), 'WCR Webb p'], 3)}].", ""]
    lines += ["## Cluster structure and inference", "",
              f"The effective number of clusters for the M1 exposure coefficient was "
              f"{fmt(effective['G* for high exposure in M1, rho 1.0'], 1)} at rho 1 and "
              f"{fmt(effective['G* for high exposure in M1, rho 0.0'], 1)} at rho 0. For M2 the WCR Webb interval ran from "
              f"{fmt(wild.loc[(m2, 'Webb'), 'WCR CI lower'])} to {fmt(wild.loc[(m2, 'Webb'), 'WCR CI upper'])} against a CR1 t "
              f"interval of {fmt(wild.loc[(m2, 'Webb'), 'CR1 t CI lower'])} to {fmt(wild.loc[(m2, 'Webb'), 'CR1 t CI upper'])}. "
              f"For M1 the WCR Webb p-value was {fmt(wild.loc[(m1, 'Webb'), 'WCR p'], 4)}.", ""]
    ri = s8.set_index("Model")
    lines += [f"Occupation-level randomisation inference over {int(ri.loc[m1, 'Assignments enumerated'])} assignments gave "
              f"p = {fmt(ri.loc[m1, 'Randomisation p [|t|]'], 4)} for M1 and p = {fmt(ri.loc[m2, 'Randomisation p [|t|]'], 4)} "
              f"for M2.", ""]
    lines += ["## Mapping sensitivity", ""]
    for _, r in s9.iterrows():
        lines.append(f"{r['Scenario']}: {int(r['Participants recoded or removed'])} participants recoded or removed, "
                     f"high exposure n = {int(r['High exposure N'])}, M2 B = {fmt(r['M2 B'])} [CR1 CI "
                     f"{fmt(r['M2 CR1 CI lower'])} to {fmt(r['M2 CR1 CI upper'])}] with WCR Webb p = "
                     f"{fmt(r['M2 WCR Webb p'], 3)}.")
        lines.append("")
    ict = s10.set_index("Model")
    lines += ["## Within ICT professional occupations", "",
              f"Among {int(ict.loc[m2, 'N'])} participants targeting ISCO-08 sub-major group 25 across "
              f"{int(ict.loc[m2, 'Clusters'])} occupations, M1 gave B = {fmt(ict.loc[m1, 'B'])} and M2 gave "
              f"B = {fmt(ict.loc[m2, 'B'])} [HC3 p = {fmt(ict.loc[m2, 'HC3 p'], 3)}]. Cluster-based inference with this "
              f"few clusters is not reliable and the HC3 figures are descriptive.", ""]
    me = s11.set_index("Rule")
    lines += ["## Measurement error in the conventional control", "",
              f"Correcting for alpha = {fmt(me.loc[full, 'Alpha conventional'], 3)} moved the M2 exposure coefficient "
              f"from {fmt(me.loc[full, 'OLS B high exposure'])} to {fmt(me.loc[full, 'EIV B high exposure'])} "
              f"[cluster pairs bootstrap {fmt(me.loc[full, 'EIV B high exposure percentile CI lower'])} to "
              f"{fmt(me.loc[full, 'EIV B high exposure percentile CI upper'])}].", ""]
    (out / "Supplementary Checks Summary.md").write_text("\n".join(lines), encoding="utf-8")


def run(root: Path, B: int, demo: bool) -> Path:
    t0 = time.time()
    out = root / "04 Analysis" / "Supplementary Checks" / "Outputs"
    out.mkdir(parents=True, exist_ok=True)
    d, info = load_data(root)
    print(f"Loaded {info['n_mapped']} mapped participants from {root}")
    results = {"Reconciliation": reconcile(root, d)}
    results["S1"], results["S1b"] = s1_distributions(d)
    rules = screening_rules(d)
    print("S2 to S4 screening, psychometrics and core models")
    results["S2"], results["S3"], results["S4"] = s2_s3_s4(d, rules, B)
    results["S5"] = s5_group_medians(d, rules)
    results["S6"], results["S6b"] = s6_clusters(d)
    print("S7 wild cluster bootstrap")
    results["S7"] = s7_wild(d, B)
    print("S8 randomisation inference")
    results["S8"] = s8_randomisation(d)
    print("S9 mapping sensitivity")
    results["S9"] = s9_mapping(d, B)
    results["S10"] = s10_ict(d, B)
    print("S11 measurement error")
    results["S11"] = s11_measurement(d, rules)
    names = {"S1": "S1 Score Distributions", "S1b": "S1b Domain Profile", "S2": "S2 Screening Rules",
             "S3": "S3 Psychometrics by Screening Rule", "S4": "S4 Core Models by Screening Rule",
             "S5": "S5 Exposure Group Medians", "S6": "S6 Occupation Cluster Structure",
             "S6b": "S6b Effective Clusters", "S7": "S7 Wild Cluster Bootstrap",
             "S8": "S8 Occupation Randomisation Inference", "S9": "S9 Mapping Sensitivity",
             "S10": "S10 Within ICT Comparison", "S11": "S11 Measurement Error Sensitivity"}
    for key, name in names.items():
        results[key].to_csv(out / f"{name}.csv", index=False, float_format="%.6f")
    if results["Reconciliation"]:
        pd.DataFrame(results["Reconciliation"]).to_csv(out / "S0 Reconciliation With Validated Manifest.csv",
                                                       index=False, float_format="%.8f")
    manifest = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "synthetic_demo": demo, "seed": SEED,
                "wild_bootstrap_draws": B, "parallel_analysis_draws": B_PARALLEL, "cluster_pairs_draws": B_PAIRS,
                "index_check": {k: v for k, v in info.items() if k.startswith("index_check")},
                "python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__,
                "statsmodels": sm.__version__, "runtime_seconds": round(time.time() - t0, 1)}
    (out / "Supplementary Checks Manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_summary(out, info, results, demo)
    n_files = len(names) + 2 + (1 if results["Reconciliation"] else 0)
    print(f"Wrote {n_files} files to {out} in {time.time() - t0:.0f} seconds")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", help="Path to the Strategic Organization folder")
    parser.add_argument("--demo", action="store_true", help="Run on synthetic data in a temporary folder")
    parser.add_argument("--bootstrap", type=int, default=B_WILD, help="Wild bootstrap draws (default 9999)")
    args = parser.parse_args()
    if args.demo:
        root = Path(tempfile.mkdtemp(prefix="so-supplementary-demo-"))
        build_demo_project(root)
        out = run(root, args.bootstrap, demo=True)
        print((out / "Supplementary Checks Summary.md").read_text(encoding="utf-8"))
    else:
        run(resolve_root(args.project_root), args.bootstrap, demo=False)


if __name__ == "__main__":
    main()
