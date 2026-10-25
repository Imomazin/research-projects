"""Write the analysis workbook: every table and figure source dataset from the Results files."""
import json
import subprocess
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
DER = PROJ / "Datasets" / "Derived"
OUT = HERE / "Managing Emerging Strategic Risks Analysis Workbook.xlsx"
M = json.loads((HERE / "Model Results.json").read_text())
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PROJ, capture_output=True, text=True).stdout.strip()

sheets = {}
meta = pd.DataFrame([
    ["Title", "When every risk is material: disclosed risk convergence, documented response and organisational resilience in US firms, 2017 to 2025"],
    ["Target journal", "Strategy & Leadership (Emerald), research paper"],
    ["Author", "Imo J. Enang"],
    ["Sample", "787 US non-financial firms, stratified random sample from 1,597 eligible firms; 6,214 10-K filings, fiscal 2017 to 2025"],
    ["Sources", "SEC EDGAR submissions, 10-K filings and XBRL company facts; Geopolitical Risk index; Economic Policy Uncertainty indices; World Uncertainty Index; NY Fed Global Supply Chain Pressure Index"],
    ["Retrieval", "25 October 2026 through the project's GitHub Actions pipeline; manifests and checksums in the repository"],
    ["Code version", f"Repository Imomazin/research-projects, branch research/strategic-risk, commit {commit} at workbook build"],
    ["Numbers", "All values are outputs of Analysis/estimate models.py, Analysis/validate measures.py and related scripts; none are typed by hand"],
    ["Sheet: Data Dictionary", "Variable definitions, sources and timing"],
    ["Sheet: Sample and Descriptives", "Sample selection log (Table 2 Panel A), pandemic-episode descriptives (Table 2 Panel B) and correlations (Table A2)"],
    ["Sheet: Hypothesis Tests", "Episode models for H1 to H3 and exploratory E1 (Table 3, Figure 5) and marginal effects of breadth by coverage"],
    ["Sheet: Robustness", "Pre-specified robustness grid for both episodes (Table 4) and the original-dictionary re-estimation"],
    ["Sheet: Panel and Shock Models", "Firm fixed-effects panel models, exposure-by-shock models (Table 5) and out-of-sample prediction"],
    ["Sheet: Disclosure Trends", "Category prevalence and breadth by year and division (Figures 2 to 4), dispersion, tracking and known-group validity"],
    ["Sheet: Validation and Cases", "AI-assisted audit of dictionary classifications (Table A1) and illustrative cases (Table 7)"],
], columns=["Item", "Description"])
sheets["Contents and Metadata"] = [("Workbook contents and provenance", meta)]
sheets["Data Dictionary"] = [("Variable definitions", pd.read_csv(PROJ / "Datasets" / "Data Dictionary.csv"))]
desc = pd.read_csv(HERE / "Descriptives Episode A.csv").rename(columns={"Unnamed: 0": "Variable"})
descB = pd.read_csv(HERE / "Descriptives Episode B.csv").rename(columns={"Unnamed: 0": "Variable"})
corr = pd.read_csv(HERE / "Correlations Episode A.csv").rename(columns={"Unnamed: 0": "Variable"})
sheets["Sample and Descriptives"] = [
    ("Sample selection log", pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Selection Log.csv")),
    ("Sample allocation by SIC division", pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Allocation.csv").rename(columns={"Unnamed: 0": "Division"})),
    ("Frame validation exclusions", pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Frame Validation Exclusions.csv")),
    ("Pandemic episode descriptive statistics (winsorised)", desc),
    ("2022 episode descriptive statistics (winsorised)", descB),
    ("Pandemic episode correlations", corr),
]
ep = pd.read_csv(HERE / "Episode Models.csv")
epm = pd.DataFrame([{"model": k, **v} for k, v in M["episode_meta"].items() if not isinstance(v, (int, float))]).drop(columns=["hc3_p"])
sheets["Hypothesis Tests"] = [
    ("Episode models: coefficients per standard deviation, errors clustered by two-digit SIC; p_hc1 from HC1 errors", ep),
    ("Episode models: fit and sample", epm),
    ("Marginal effect of breadth at levels of coverage", pd.read_csv(HERE / "Marginal Effects of Breadth.csv")),
]
alt = pd.read_csv(HERE / "Alternative Original Dictionary" / "Episode Models.csv")
sheets["Robustness"] = [
    ("Robustness grid (23 checks per outcome)", pd.read_csv(HERE / "Robustness Grid.csv")),
    ("Re-estimation with the original (pre-audit) dictionary", alt),
]
pm = pd.DataFrame([{"model": k, **v} for k, v in M["panel_meta"].items()])
sm = pd.DataFrame([{"model": k, **v} for k, v in M["shock_meta"].items()])
pr = pd.DataFrame([{"model": k, **v} for k, v in M["prediction"].items()])
sheets["Panel and Shock Models"] = [
    ("Firm and year fixed-effects panel models, fiscal 2019 to 2025 (errors clustered by firm)", pd.read_csv(HERE / "Panel Models.csv")),
    ("Panel model samples", pm),
    ("Exposure-by-shock models (fiscal 2018 exposure x standardised index)", pd.read_csv(HERE / "Shock Exposure Models.csv")),
    ("Exposure-by-shock samples", sm),
    ("Out-of-sample prediction: trained on outcome years to FY2022, tested on FY2023 to FY2025", pr),
]
sheets["Disclosure Trends"] = [
    ("Disclosure trends by fiscal year (Figure 2 source)", pd.read_csv(HERE / "Disclosure Trends.csv")),
    ("Breadth dispersion and linkage by fiscal year (Figure 3 source)", pd.read_csv(HERE / "Breadth Dispersion.csv")),
    ("Mean breadth by SIC division and fiscal year (Figure 4 source)", pd.read_csv(HERE / "Breadth by Division.csv")),
    ("Category intensity by SIC division, FY2018, per cent of Item 1A sentences (known-group validity)", pd.read_csv(HERE / "Known Groups Intensity.csv")),
    ("Category intensity against matching macro index by fiscal year (tracking validity)", pd.read_csv(HERE / "Category Tracking.csv")),
    ("Monthly macro index series, January 2014 to September 2026", pd.read_csv(DER / "Macro Monthly.csv")),
]
cases = json.loads((HERE / "Illustrative Cases.json").read_text())
cdf = pd.DataFrame([{**{k: v for k, v in c.items() if k not in ("material", "actions", "action_sentences")},
                     "material": ", ".join(c["material"]), "actions": ", ".join(c["actions"]),
                     "action sentences": " | ".join(a["sentence"] for a in c["action_sentences"])} for c in cases])
sheets["Validation and Cases"] = [
    ("AI-assisted audit, original dictionary (not human coding)", pd.read_csv(HERE / "Validation Audit Original Dictionary.csv").rename(columns={"dictionary_label": "category", "mean": "precision", "sum": "correct", "count": "audited"})),
    ("AI-assisted audit, revised dictionary on a fresh sample (not human coding)", pd.read_csv(HERE / "Validation Audit Revised Dictionary Holdout.csv").rename(columns={"dictionary_label": "category", "mean": "precision", "sum": "correct", "count": "audited"})),
    ("Illustrative cases selected by the outcome-balanced rule in Analysis/select cases.py", cdf),
]

with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
    for name, blocks in sheets.items():
        row = 0
        for title, df in blocks:
            pd.DataFrame([[title]]).to_excel(xw, sheet_name=name, startrow=row, header=False, index=False)
            df.to_excel(xw, sheet_name=name, startrow=row + 1, index=False)
            row += len(df) + 4

wb = load_workbook(OUT)
hdr_fill = PatternFill("solid", fgColor="E8EBF0")
thin = Side(style="thin", color="B8BDC6")
for ws in wb.worksheets:
    blocks = sheets[ws.title]
    row = 1
    for title, df in blocks:
        ws.cell(row, 1).font = Font(name="Calibri", bold=True, size=12, color="1F2A44")
        for j in range(1, df.shape[1] + 1):
            c = ws.cell(row + 1, j)
            c.font = Font(name="Calibri", bold=True, size=10)
            c.fill = hdr_fill
            c.border = Border(bottom=thin)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        for i in range(row + 2, row + 2 + len(df)):
            for j in range(1, df.shape[1] + 1):
                c = ws.cell(i, j)
                c.font = Font(name="Calibri", size=10)
                if isinstance(c.value, float):
                    c.number_format = "0.0000" if abs(c.value) < 1000 else "#,##0"
        row += len(df) + 4
    for j in range(1, ws.max_column + 1):
        width = max(len(str(ws.cell(i, j).value or "")) for i in range(1, min(ws.max_row, 400) + 1))
        ws.column_dimensions[get_column_letter(j)].width = min(max(10, width * 0.9), 70)
    ws.sheet_view.showGridLines = False
ws = wb["Contents and Metadata"]
ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 120
for r in range(3, ws.max_row + 1):
    ws.cell(r, 2).alignment = Alignment(wrap_text=True, vertical="top")
wb.save(OUT)
print("written", OUT, [ws.title for ws in wb.worksheets])
