"""Merge text measures, accounting panel, sample attributes and macro series
into the firm-year research panel and derive every analysis variable.

Inputs (Datasets/Derived): Text Measures.csv, Financial Panel.csv, Macro Monthly.csv
and Datasets/Sampling Frame/Sample Firms.csv.
Output: Datasets/Derived/Research Panel.csv and Variable Coverage.csv.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DER = HERE.parent / "Datasets" / "Derived"
CATS = list(json.loads((HERE / "Risk Taxonomy Dictionary.json").read_text())["categories"].keys())
EMERGING = CATS  # all nine categories enter the convergence count
MATERIAL = 3


def entropy_exp(counts: np.ndarray) -> float:
    tot = counts.sum()
    if tot == 0:
        return np.nan
    p = counts[counts > 0] / tot
    return float(np.exp(-(p * np.log(p)).sum()))


def text_variables(t: pd.DataFrame, threshold: int = MATERIAL) -> pd.DataFrame:
    t = t.copy()
    cnt = t[[f"cnt_{c}" for c in CATS]].to_numpy(dtype=float)
    act = t[[f"act_{c}" for c in CATS]].to_numpy(dtype=float)
    n = t["n_sent_1a"].replace(0, np.nan).to_numpy(dtype=float)
    for i, c in enumerate(CATS):
        t[f"int_{c}"] = cnt[:, i] / n
        t[f"mat_{c}"] = (cnt[:, i] >= threshold).astype(int)
    mat = cnt >= threshold
    t["breadth"] = mat.sum(axis=1)
    t["linkage"] = t["n_linked"] / t["n_sent_1a"].replace(0, np.nan)
    t["catalogue_share"] = t["n_catalogue"] / t["n_sent_1a"].replace(0, np.nan)
    t["diversity"] = [entropy_exp(r) for r in cnt]
    covered = (mat & (act > 0)).sum(axis=1)
    t["coverage"] = np.where(mat.sum(axis=1) > 0, covered / np.maximum(mat.sum(axis=1), 1), np.nan)
    norm = np.linalg.norm(cnt, axis=1) * np.linalg.norm(act, axis=1)
    t["alignment"] = np.where(norm > 0, (cnt * act).sum(axis=1) / np.where(norm > 0, norm, 1), np.nan)
    t["any_action"] = (act.sum(axis=1) > 0).astype(int)
    t["ln_item1a_words"] = np.log1p(t["item1a_words"])
    t["ln_response_sent"] = np.log1p(t["n_sent_response"])
    return t


def fiscal_macro(panel: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    """Average of each macro series over the twelve months ending in the fiscal year-end month."""
    macro = macro.copy()
    macro.index = pd.PeriodIndex(macro["month"], freq="M")
    macro = macro.drop(columns="month")
    roll = macro.rolling(12, min_periods=12).mean()
    key = pd.PeriodIndex(pd.to_datetime(panel["fy_end"]), freq="M")
    vals = roll.reindex(key)
    vals.index = panel.index
    return panel.join(vals.add_prefix("fy_"))


def main():
    text = pd.read_csv(DER / "Text Measures.csv")
    fin = pd.read_csv(DER / "Financial Panel.csv", parse_dates=["fy_end"])
    firms = pd.read_csv(HERE.parent / "Datasets" / "Sampling Frame" / "Sample Firms.csv")
    macro = pd.read_csv(DER / "Macro Monthly.csv")
    text = text_variables(text)
    excl = pd.read_csv(HERE.parent / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")
    firms = firms[~firms["cik"].isin(excl["cik"])]
    firms = firms[["cik", "name", "sic", "division", "state_incorporation", "sampling_weight", "float"]]
    firms["sic2"] = (firms["sic"] // 100).astype(int)
    firms["us_incorporated"] = firms["state_incorporation"].astype(str).str.match(r"^[A-Z]{2}$").astype(int)
    p = fin.merge(firms, on="cik", how="inner").merge(text, on=["cik", "fiscal_year"], how="left")
    p = p.sort_values(["cik", "fiscal_year"]).reset_index(drop=True)
    g = p.groupby("cik")
    # accounting variables
    p["ln_assets"] = np.log(p["assets"].where(p["assets"] > 0))
    p["leverage"] = p["liabilities"] / p["assets"]
    p["cash_ratio"] = p["cash"] / p["assets"]
    p["roa"] = p["net_income"] / p["assets"]
    fallback = p["revenue"] - p["costs_and_expenses"]
    p["op_income_source"] = np.where(p["operating_income"].notna(), "OperatingIncomeLoss",
                                     np.where(fallback.notna(), "revenue less costs and expenses", ""))
    p["op_income"] = p["operating_income"].fillna(fallback)
    p["op_margin"] = p["op_income"] / p["revenue"].where(p["revenue"] > 0)
    p["ln_revenue"] = np.log(p["revenue"].where(p["revenue"] > 0))
    lag = lambda col, k=1: g[col].shift(k).where(g["fiscal_year"].shift(k) == p["fiscal_year"] - k)
    p["rev_growth"] = p["ln_revenue"] - lag("ln_revenue")
    p["d_op_margin"] = p["op_margin"] - lag("op_margin")
    p["lag_assets"] = lag("assets")
    for col in ["capex", "rnd", "acquisitions", "restructuring"]:
        p[f"{col}_rate"] = p[col].fillna(0) / p["lag_assets"]
    p["reconfiguration"] = p[["capex_rate", "rnd_rate", "acquisitions_rate"]].sum(axis=1, min_count=1)
    p["rnd_intensity"] = p["rnd"].fillna(0) / p["revenue"].where(p["revenue"] > 0)
    p["foreign_share"] = (p["pretax_foreign"] / p["pretax_income"].abs()).clip(-2, 2)
    p["adverse"] = ((p["rev_growth"] <= np.log(0.9)) | (p["d_op_margin"] <= -0.05)).astype(float)
    p.loc[p["rev_growth"].isna() & p["d_op_margin"].isna(), "adverse"] = np.nan
    p["fye_month"] = p["fy_end"].dt.month
    p["filing_date"] = pd.to_datetime(p["filing_date"])
    p = fiscal_macro(p, macro)
    p.to_csv(DER / "Research Panel.csv", index=False)
    cov = p.groupby("fiscal_year").agg(firms=("cik", "nunique"), revenue=("revenue", "count"),
                                       item1a=("n_sent_1a", "count"), op_margin=("op_margin", "count"),
                                       response=("n_sent_response", "count"))
    cov.to_csv(DER / "Variable Coverage.csv")
    print(p.shape)
    print(cov)


if __name__ == "__main__":
    main()
