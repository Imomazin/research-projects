"""Build the firm by fiscal-year accounting panel from SEC XBRL company facts.

Annual flow values are facts reported in a 10-K (or 10-K/A) with a duration of
350 to 380 days. Balance-sheet values are instants at the fiscal year end.
For every concept and fiscal year two versions are kept: the value as first
reported (the earliest filing that reports that period) and the latest value.
Analyses use first-reported values so that later restatements do not leak
information that was unavailable at the time.

Usage: python "build financial panel.py" <facts csv.gz> <output csv>
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REVENUE_ORDER = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                 "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
                 "SalesRevenueGoodsNet", "RevenuesNetOfInterestExpense", "SalesRevenueServicesNet"]
FLOWS = {
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"],
    "pretax_income": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                      "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
    "pretax_foreign": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign"],
    "pretax_domestic": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic"],
    "cost_of_revenue": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "gross_profit": ["GrossProfit"],
    "sga": ["SellingGeneralAndAdministrativeExpense"],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"],
    "rnd": ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"],
    "acquisitions": ["PaymentsToAcquireBusinessesNetOfCashAcquired"],
    "restructuring": ["RestructuringCharges"],
    "buybacks": ["PaymentsForRepurchaseOfCommonStock"],
    "dividends": ["PaymentsOfDividends", "PaymentsOfDividendsCommonStock"],
    "interest_expense": ["InterestExpense"],
    "depreciation": ["DepreciationDepletionAndAmortization"],
    "costs_and_expenses": ["CostsAndExpenses", "OperatingExpenses"],
}
STOCKS = {
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "inventory": ["InventoryNet"],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
    "goodwill": ["Goodwill"],
}


def fiscal_year(end: pd.Series) -> pd.Series:
    return np.where(end.dt.month >= 6, end.dt.year, end.dt.year - 1)


def annual_facts(facts: pd.DataFrame) -> pd.DataFrame:
    f = facts[facts["form"].isin(["10-K", "10-K/A"]) & (facts["unit"] == "USD")].copy()
    f["end"] = pd.to_datetime(f["end"], errors="coerce")
    f["start"] = pd.to_datetime(f["start"], errors="coerce")
    f["filed"] = pd.to_datetime(f["filed"], errors="coerce")
    f = f.dropna(subset=["end", "filed"])
    f["days"] = (f["end"] - f["start"]).dt.days
    f["is_flow"] = f["start"].notna()
    f = f[(~f["is_flow"]) | f["days"].between(350, 380)]
    f["fiscal_year"] = fiscal_year(f["end"])
    return f


def fiscal_year_ends(facts: pd.DataFrame) -> pd.DataFrame:
    """The fiscal year end date of each firm-year, taken from annual revenue or net income facts."""
    f = facts[facts["is_flow"] & facts["concept"].isin(REVENUE_ORDER + ["NetIncomeLoss", "OperatingIncomeLoss"])]
    # the period end reported most often for that firm and fiscal year
    ends = (f.groupby(["cik", "fiscal_year", "end"]).size().reset_index(name="n")
            .sort_values(["cik", "fiscal_year", "n", "end"]).groupby(["cik", "fiscal_year"]).tail(1))
    return ends[["cik", "fiscal_year", "end"]].rename(columns={"end": "fy_end"})


def pick(facts: pd.DataFrame, concepts: list[str], ends: pd.DataFrame, flow: bool, name: str) -> pd.DataFrame:
    sub = facts[facts["concept"].isin(concepts) & (facts["is_flow"] == flow)]
    sub = sub.merge(ends, on=["cik", "fiscal_year"], how="inner")
    sub = sub[(sub["end"] - sub["fy_end"]).dt.days.abs() <= 7]
    sub = sub.assign(rank=sub["concept"].map({c: i for i, c in enumerate(concepts)}))
    # concept priority first, then filing order
    first = (sub.sort_values(["cik", "fiscal_year", "rank", "filed"])
             .groupby(["cik", "fiscal_year"]).head(1)[["cik", "fiscal_year", "val", "concept", "filed", "accn"]])
    last = (sub.sort_values(["cik", "fiscal_year", "rank", "filed"])
            .groupby(["cik", "fiscal_year", "rank"]).tail(1)
            .sort_values(["cik", "fiscal_year", "rank"]).groupby(["cik", "fiscal_year"]).head(1)[["cik", "fiscal_year", "val"]])
    out = first.rename(columns={"val": name, "concept": f"{name}_concept", "filed": f"{name}_filed", "accn": f"{name}_accn"})
    out = out.merge(last.rename(columns={"val": f"{name}_latest"}), on=["cik", "fiscal_year"], how="left")
    return out


def build(facts: pd.DataFrame) -> pd.DataFrame:
    f = annual_facts(facts)
    ends = fiscal_year_ends(f)
    panel = ends.copy()
    rev = pick(f, REVENUE_ORDER, ends, True, "revenue")
    panel = panel.merge(rev, on=["cik", "fiscal_year"], how="left")
    for name, cs in FLOWS.items():
        p = pick(f, cs, ends, True, name)[["cik", "fiscal_year", name, f"{name}_latest"]]
        panel = panel.merge(p, on=["cik", "fiscal_year"], how="left")
    for name, cs in STOCKS.items():
        p = pick(f, cs, ends, False, name)[["cik", "fiscal_year", name, f"{name}_latest"]]
        panel = panel.merge(p, on=["cik", "fiscal_year"], how="left")
    restated = (panel["revenue_latest"] - panel["revenue"]).abs() > 0.005 * panel["revenue"].abs()
    panel["revenue_restated"] = restated.astype(int)
    return panel.sort_values(["cik", "fiscal_year"])


if __name__ == "__main__":
    facts = pd.read_csv(sys.argv[1], dtype={"cik": int})
    out = build(facts)
    out.to_csv(sys.argv[2], index=False)
    print(out.shape)
