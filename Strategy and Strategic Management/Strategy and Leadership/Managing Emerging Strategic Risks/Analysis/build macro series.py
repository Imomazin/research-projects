"""Assemble the monthly macro-uncertainty series from the raw provider files.

Output: Datasets/Derived/Macro Monthly.csv with one row per month from January
2014 and the columns below. Quarterly World Uncertainty Index values are
assigned to each month of their quarter; no other transformation is applied.
"""
from pathlib import Path
import warnings

import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "Datasets" / "Raw Macro"
OUT = HERE.parent / "Datasets" / "Derived"
OUT.mkdir(parents=True, exist_ok=True)


def month_index(y, m):
    return pd.PeriodIndex.from_fields(year=y.astype(int), month=m.astype(int), freq="M")


gpr = pd.read_excel(RAW / "Geopolitical Risk Monthly.xls")
gpr["month"] = pd.to_datetime(gpr["month"]).dt.to_period("M")
gpr = gpr.set_index("month")[["GPR", "GPRT", "GPRA", "GPRC_USA"]].rename(
    columns={"GPR": "gpr", "GPRT": "gpr_threats", "GPRA": "gpr_acts", "GPRC_USA": "gpr_usa"})

epu = pd.read_excel(RAW / "Economic Policy Uncertainty United States.xlsx", sheet_name="Main News Index")
epu = epu[pd.to_numeric(epu["Month"], errors="coerce").notna() & pd.to_numeric(epu["Year"], errors="coerce").notna()]
epu.index = month_index(epu["Year"], epu["Month"])
epu = epu[["News_Based_Policy_Uncert_Index"]].rename(columns={"News_Based_Policy_Uncert_Index": "epu_us"})

cat = pd.read_excel(RAW / "Economic Policy Uncertainty Categorical.xlsx")
cat = cat[pd.to_numeric(cat["Month"], errors="coerce").notna() & pd.to_numeric(cat["Year"], errors="coerce").notna()]
cat.index = month_index(cat["Year"], cat["Month"])
cat = cat[["9. Trade policy", "8. Regulation", "6. National security"]].rename(
    columns={"9. Trade policy": "epu_trade", "8. Regulation": "epu_regulation", "6. National security": "epu_national_security"})

gs = pd.read_excel(RAW / "Global Supply Chain Pressure Index.xlsx", sheet_name="GSCPI Monthly Data", header=None)
gs = gs[[0, 1]].iloc[5:].dropna()
gs.index = pd.to_datetime(gs[0], format="%d-%b-%Y").dt.to_period("M")
gs = gs[[1]].rename(columns={1: "gscpi"}).astype(float)

wui = pd.read_excel(RAW / "World Uncertainty Index.xlsx", sheet_name="T1")
wui = wui[wui["Year"].astype(str).str.match(r"^\d{4}q\d$")]
wuc = pd.read_excel(RAW / "World Uncertainty Index.xlsx", sheet_name="T2")
wuc = wuc[wuc["year"].astype(str).str.match(r"^\d{4}q\d$")]
rows = []
for (_, r), (_, c) in zip(wui.iterrows(), wuc.iterrows()):
    y, q = int(str(r["Year"])[:4]), int(str(r["Year"])[-1])
    for m in range(3 * q - 2, 3 * q + 1):
        rows.append({"month": pd.Period(year=y, month=m, freq="M"),
                     "wui_global": r["Global (GDP weighted average)"], "wui_usa": c["USA"]})
wui = pd.DataFrame(rows).set_index("month")

macro = gpr.join([epu, cat, gs, wui], how="outer").sort_index()
macro = macro[macro.index >= pd.Period("2014-01", freq="M")]
macro.index.name = "month"
macro.to_csv(OUT / "Macro Monthly.csv")
print(macro.tail(3).to_string())
print(macro.loc["2018-01":"2025-12"].describe().round(2).to_string())
