"""Assemble Manuscript Blocks.json: text from manuscript content.py, tables from Results,
references from verified records. Fails if any in-text citation lacks a verified reference
or any reference is not cited."""
import importlib.util
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
LIT = PROJ / "Literature"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = load("content", HERE / "manuscript content.py")
REF = load("refs", LIT / "build references.py")
N = C.N
f3, pv = C.f3, C.pv

# ------------------------------------------------------------------ references
keys = [r.split(",")[0] for r in (LIT / "Candidate References.csv").read_text().splitlines()[1:] if r.strip()]
entries = {}
for k in keys + list(REF.MANUAL.keys()):
    e = REF.entry(k)
    if e.get("verified"):
        e["cite"] = REF.in_text(e) if "cite" not in e else e["cite"]
        entries[k] = e
text_all = " ".join(v for k, v in C.BLOCKS if k == "p") + " " + " ".join(v for _, v in C.ABSTRACT)


def variants(e):
    c = e["cite"]
    name, yr = c.rsplit(", ", 1)
    return [c, f"{name} ({yr})"]


cited = {k: e for k, e in entries.items() if any(v in text_all for v in variants(e))}
# duplicates of the same work under two keys
seen, uniq = set(), {}
for k, e in cited.items():
    if e["doi"] not in seen:
        uniq[k] = e
        seen.add(e["doi"])
cited = uniq
# every citation token in text must be matched
tokens = set()
for grp in re.findall(r"\(([^()]*\d{4}[^()]*)\)", text_all):
    for part in grp.split(";"):
        part = part.strip()
        m = re.search(r"([A-Z][A-Za-z'\-À-ſ ]+(?: et al\.)?(?: and [A-Z][A-Za-z'\-À-ſ]+)?), (\d{4})$", part)
        if m:
            tokens.add(f"{m.group(1).strip()}, {m.group(2)}")
for m in re.finditer(r"([A-Z][A-Za-z'\-]+(?: et al\.| and [A-Z][A-Za-z'\-]+)?) \((\d{4})\)", text_all):
    tokens.add(f"{m.group(1)}, {m.group(2)}")
known = {e["cite"] for e in cited.values()}
missing = sorted(t for t in tokens if t not in known)
if missing:
    raise SystemExit(f"Citations without verified reference: {missing}")
refs = sorted(cited.values(), key=lambda e: (e["first_author"].lower().replace("‐", "-"), e["year"], e["text"]))

# ------------------------------------------------------------------ tables
T = {}
T["one"] = {
    "caption": "Table 1. Data sources, content and coverage",
    "header": ["Source", "Content used", "Coverage", "Role in the study"],
    "widths": [22, 32, 22, 24],
    "rows": [
        ["SEC EDGAR submissions and 10-K filings", "Items 1, 1A and 7 of the latest original 10-K for each fiscal year", f"{N['sample_final']} firms; {N['filings']:,} filings; fiscal 2017 to 2025", "Risk exposure, convergence, documented response, updating"],
        ["SEC XBRL company facts", f"{N['xbrl_fact_rows']:,} fact rows from 10-K and 10-Q filings; first-reported annual values", "Fiscal 2013 to 2026", "Revenue, operating margin, controls, resource commitments"],
        ["SEC XBRL frames (public float)", "Entity public float reported for 2018", f"{N['frame_float_entities']:,} entities", "Sampling frame"],
        ["Geopolitical Risk index (Caldara and Iacoviello)", "Monthly global index with threats and acts components", "1985 to September 2026", "Geopolitical shock; tracking validity"],
        ["Economic Policy Uncertainty (Baker, Bloom and Davis)", "US news-based index; trade policy and regulation components", "1985 to September 2026", "Policy and trade shocks; tracking validity"],
        ["Global Supply Chain Pressure Index (Federal Reserve Bank of New York)", "Monthly standardised index", "1998 to September 2026", "Supply-chain shock; tracking validity"],
        ["World Uncertainty Index (Ahir, Bloom and Furceri)", "Quarterly global and US indices", "1952 to 2026 third quarter", "Supplementary uncertainty measure"],
    ],
    "note": "Note: Macro indices were averaged over the twelve months ending in each firm's fiscal year-end month. Retrieval dates, file checksums and collection code are held in the project repository. Source: author's compilation.",
}
log = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Selection Log.csv")
d = N["episodeA_desc"]
labels = {"severity": "Revenue severity, ln(FY2020/FY2019)", "margin_change": "Operating-margin change, FY2020 minus FY2019",
          "recovery": "Revenue recovery, ln(FY2022/FY2019)", "recovered": "Revenue regained by FY2021 (share)",
          "breadth": "Convergence breadth, FY2018 (0 to 9)", "coverage": "Response coverage, FY2018 (share)",
          "linkage": "Linkage density, FY2018 (share of sentences)", "updating": "Disclosure updating, FY2018"}
rows = [[s, "", f"{int(v):,}", ""] for s, v in zip(log["step"], log["firms remaining"])]
T["two"] = {
    "caption": "Table 2. Sample selection and descriptive statistics for the pandemic episode",
    "header": ["Step or variable", "Mean [SD]", "Firms or n", "Median"],
    "widths": [52, 18, 15, 15],
    "rows": [["Panel A. Sample selection", "", "", ""]] + rows + [["Panel B. Pandemic episode variables", "", "", ""]] +
            [[labels[k], f"{d[k]['mean']:.3f} [{d[k]['sd']:.3f}]", f"{d[k]['n']:,}", f"{d[k]['median']:.3f}"] for k in labels],
    "bold_rows": [0, len(rows) + 1],
    "note": "Note: Outcomes winsorised at the 1st and 99th percentiles. Breadth counts categories with at least three Item 1A sentences. Source: SEC EDGAR filings and XBRL company facts; author's analysis.",
}
E = N["episode"]
cols = [("A", "severity", "Pandemic revenue fall"), ("A", "margin_change", "Pandemic margin change"), ("A", "recovery", "Pandemic recovery"),
        ("B", "margin_change", "2022 margin, FY2022"), ("B", "margin_change_two", "2022 margin, FY2023"), ("B", "severity", "2022 revenue, FY2023")]


def cell(m, t):
    k = f"{m}|{t}"
    if k not in E:
        return ""
    r = E[k]
    star = "**" if r["p"] < 0.01 else ("*" if r["p"] < 0.05 else "")
    return f"{r['b']:.3f}{star} [{r['se']:.3f}]"


trow = []
for h, terms in [("H1", [("breadth_z", "Convergence breadth")]), ("H2", [("coverage_z", "Response coverage")]),
                 ("H3", [("breadth_z", "Convergence breadth"), ("coverage_z", "Response coverage"), ("breadth_z:coverage_z", "Breadth x coverage")])]:
    trow.append([f"Model {h}"] + [""] * len(cols))
    for t, lab in terms:
        trow.append([lab] + [cell(f"{e}|{h}|{y}", t) for e, y, _ in cols])
    trow.append(["Observations"] + [str(E[f"{e}|{h}|{y}|{terms[0][0]}"]["n"]) for e, y, _ in cols])
    trow.append(["R squared"] + [f"{E[f'{e}|{h}|{y}|{terms[0][0]}']['r2']:.3f}" for e, y, _ in cols])
T["three"] = {
    "caption": "Table 3. Convergence, response coverage and performance in two shock episodes",
    "header": ["Term"] + [c[2] for c in cols], "widths": [22, 13, 13, 13, 13, 13, 13],
    "rows": trow, "bold_rows": [i for i, r in enumerate(trow) if r[0].startswith("Model")],
    "note": "Note: Coefficients per standard deviation of the predictor with standard errors clustered by two-digit SIC in brackets; * p < 0.05, ** p < 0.01. All models include the nine category intensities, log assets, leverage, cash to assets, return on assets, prior two-year revenue growth, log Item 1A words and two-digit SIC and fiscal year-end month fixed effects. Predictors from fiscal 2018 (pandemic) and fiscal 2020 (2022 episode). Source: author's analysis.",
}
R = N["robustness_summary"]
rlab = [("A|severity|breadth_z", "Breadth on pandemic revenue fall"), ("A|recovery|breadth_z", "Breadth on pandemic recovery"),
        ("A|severity|breadth_z:coverage_z", "Breadth x coverage on revenue fall"), ("A|recovery|breadth_z:coverage_z", "Breadth x coverage on recovery"),
        ("B|margin_change|breadth_z", "Breadth on 2022 margin change"), ("B|margin_change_two|breadth_z", "Breadth on FY2023 margin change")]
rrows = []
for k, lab in rlab:
    ep_, y, t = k.split("|")
    hyp = "H3" if ":" in t else "H1"
    pr = E[f"{ep_}|{hyp}|{y}|{t}"] if f"{ep_}|{hyp}|{y}|{t}" in E else E[f"{ep_}|H3|{y}|{t}"]
    r = R[k]
    rrows.append([lab, f"{pr['b']:.3f}", pv(pr["p"]).replace("p ", ""), f"{r['same_sign']} of {r['checks']}", f"{r['p05']}", f"{r['p05_hc1']}"])
T["four"] = {
    "caption": "Table 4. Summary of the pre-specified robustness grid",
    "header": ["Association", "Primary b", "Primary p", "Same sign", "p < 0.05, clustered", "p < 0.05, HC1"],
    "widths": [34, 12, 12, 14, 14, 14], "rows": rrows,
    "note": "Note: Twenty-three checks per association: materiality thresholds of one and five sentences, diversity in place of breadth, no intensity controls, December year-end firms, Item 1A of at least 1,000 words, US-incorporated firms, base-year revenue of at least 100 million US dollars, manufacturing only and excluding manufacturing, reconfiguration, foreign income and updating controls, predictors filed before the shock, unwinsorised outcome and dropping each SIC division. Primary b for the breadth rows comes from the H1 model and for the interaction rows from the H3 model. Source: author's analysis.",
}
S = N["shock"]
srows = []
for t, lab in [("x_geopolitical", "Geopolitical exposure x GPR"), ("x_supply", "Supply-chain exposure x GSCPI"),
               ("x_trade", "Trade exposure x trade policy uncertainty"), ("x_regulatory", "Regulatory exposure x regulation uncertainty"),
               ("x_macro", "Macro-financial exposure x EPU"), ("x_pandemic", "Pandemic exposure x fiscal 2020"),
               ("x_breadth_shocks", "Breadth x number of high indices")]:
    row = [lab]
    for m in ["With convergence|rev_growth", "Industry-by-year effects|rev_growth", "With convergence|d_op_margin", "Industry-by-year effects|d_op_margin"]:
        r = S[f"Shock|{m}|{t}"]
        star = "**" if r["p"] < 0.01 else ("*" if r["p"] < 0.05 else "")
        row.append(f"{r['b']:.4f}{star} [{r['se']:.4f}]")
    srows.append(row)
sm = N["shock_meta"]
srows.append(["Firm-years"] + [f"{sm['Shock|' + m]['n']:,}" for m in ["With convergence|rev_growth", "Industry-by-year effects|rev_growth", "With convergence|d_op_margin", "Industry-by-year effects|d_op_margin"]])
srows.append(["Fixed effects", "Firm, year", "Firm, industry-year", "Firm, year", "Firm, industry-year"])
T["five"] = {
    "caption": "Table 5. Pre-shock exposure and realised sensitivity to macro shocks, fiscal 2019 to 2025",
    "header": ["Interaction", "Revenue growth", "Revenue growth", "Margin change", "Margin change"],
    "widths": [32, 17, 17, 17, 17], "rows": srows,
    "note": "Note: Exposure is the fiscal 2018 category intensity, standardised; each index is the fiscal-year average, standardised. The number of high indices counts GPR, GSCPI, trade and regulation uncertainty and EPU more than one standard deviation above their mean plus fiscal 2020. Standard errors clustered by firm in brackets; * p < 0.05, ** p < 0.01. Source: author's analysis.",
}
T["six"] = {
    "caption": "Table 6. A board diagnostic for converging strategic risks",
    "header": ["Capability", "What the evidence shows", "Question for the board", "Evidence to request"],
    "widths": [14, 30, 28, 28],
    "rows": [
        ["Anticipate", f"Risk lists grew to {C.f2(N['breadth_mean']['2025'])} of nine categories on average and stopped separating firms; updating peaked in fiscal 2020", "Which risks rose in our ranking this year and why?", "Exposure ranked by revenue, cost or assets at stake, with the change from last year"],
        ["Interpret", f"Only {C.pct(N['linkage_pct']['2025'],1)} of risk sentences linked categories; combined exposure added no measurable loss", "Which two or three links between risks would hurt us most?", "Two-channel scenarios with named transmission paths and pass-through assumptions"],
        ["Adapt", f"{C.pct(100*N['coverage_fy2018']['share_zero'],0)} of firms reported no completed action on material risks in fiscal 2018; reported actions were mostly hedges", "For each material risk, what have we changed in operations or contracts?", "Register of completed adaptive actions with dates, owners and cost"],
        ["Reinforce", "Disclosure ratcheted up after shocks and rarely fell back; losses ran through specific channels", "Which channels moved our income statement in the last shock?", "Post-shock review of realised sensitivity by channel, fed into next year's ranking"],
    ],
    "note": "Note: The diagnostic adapts the anticipate, interpret, adapt and reinforce sequence to the study's findings. Source: author's analysis.",
}
cases = json.loads((PROJ / "Results" / "Illustrative Cases.json").read_text())
short = {"geopolitical": "Geo", "trade": "Trade", "regulatory": "Reg", "cyber": "Cyber", "technology": "Tech", "supply": "Supply",
         "climate": "Climate", "macro": "Macro", "pandemic": "Pandemic"}
T["seven"] = {
    "caption": "Table 7. Illustrative cases from the pandemic episode",
    "header": ["Firm", "Breadth group; documented action", "Material categories, FY2018", "Documented actions, FY2018", "Revenue change FY2019 to FY2020", "Revenue FY2022 vs FY2019"],
    "widths": [16, 16, 24, 14, 15, 15],
    "rows": [[{"Ford Motor Co": "Ford Motor", "AMAZON.COM, INC.": "Amazon.com", "Marathon Petroleum Corporation": "Marathon Petroleum",
               "United Parcel Service, Inc.": "United Parcel Service", "GENERAL MOTORS COMPANY": "General Motors", "Walmart Inc.": "Walmart",
               "CATERPILLAR INC": "Caterpillar", "McKESSON CORPORATION": "McKesson"}.get(c["name"], c["name"]),
              f"{c['breadth_group']}; {c['documented_action']}", ", ".join(short[x] for x in c["material"]),
              ", ".join(short[x] for x in c["actions"]) or "None", f"{100 * (2.718281828459045 ** c['severity'] - 1):.1f}%",
              f"{100 * (2.718281828459045 ** c['recovery'] - 1):.1f}%"] for c in cases],
    "note": "Note: Within each group the rule selects the largest firm by fiscal 2019 revenue whose revenue fell by more than ten per cent and the largest whose revenue did not fall. Material means at least three Item 1A sentences. Source: SEC EDGAR 10-K filings and XBRL company facts; author's analysis.",
}
au0, au1 = N["audit_original"], N["audit_revised"]
names = {"geopolitical": "Geopolitical", "trade": "Trade policy", "regulatory": "Regulatory change", "cyber": "Cybersecurity", "technology": "AI and technology",
         "supply": "Supply chain", "climate": "Climate and environment", "macro": "Macro-financial", "pandemic": "Pandemic", "action": "Documented response", "none": "Unclassified sentences with category content"}
T["appA"] = {
    "caption": "Table A1. Audit of dictionary classifications",
    "header": ["Category", "Original dictionary: correct of audited", "Revised dictionary, fresh sample: correct of audited"],
    "widths": [36, 32, 32],
    "rows": [[names[k], f"{au0[k]['correct']} of {au0[k]['n']}", f"{au1[k]['correct']} of {au1[k]['n']}"] for k in names] +
            [["Pooled category precision", f"{N['audit_pooled_original']:.2f}", f"{N['audit_pooled_revised']:.2f}"]],
    "note": "Note: Sentences drawn by stratified random sampling with different seeds for the two audits and coded with an AI assistant against written category definitions. The coding sheets are released for human double-coding. For unclassified sentences the figure counts misses. Source: author's analysis.",
}
corr = pd.read_csv(PROJ / "Results" / "Correlations Episode A.csv", index_col=0)
cv_ = ["severity", "recovery", "breadth", "coverage", "linkage", "updating", "ln_assets", "leverage", "cash_ratio", "roa"]
cn = {"severity": "1 Severity", "recovery": "2 Recovery", "breadth": "3 Breadth", "coverage": "4 Coverage", "linkage": "5 Linkage",
      "updating": "6 Updating", "ln_assets": "7 Log assets", "leverage": "8 Leverage", "cash_ratio": "9 Cash to assets", "roa": "10 Return on assets"}
crow = [[cn[a]] + [(f"{corr.loc[a, b]:.2f}" if j < i else "") for j, b in enumerate(cv_)] for i, a in enumerate(cv_)]
T["appB"] = {"caption": "Table A2. Correlations among pandemic-episode variables", "header": ["Variable"] + [str(i + 1) for i in range(len(cv_))],
             "widths": [19] + [8.1] * 10, "rows": crow,
             "note": "Note: Pearson correlations, pairwise complete observations, winsorised variables. Source: author's analysis."}

FIGS = {
    "one": ("Figure One Research Model.png", "Figure 1. Research model", "Source: author's design."),
    "two": ("Figure Two Category Prevalence.png", "Figure 2. Share of firms with each emerging risk category material in Item 1A, fiscal 2017 to 2025", "Note: Material means at least three Item 1A sentences in the category. Source: SEC EDGAR 10-K filings of 787 sampled US non-financial firms; author's analysis."),
    "three": ("Figure Three Convergence and Homogenisation.png", "Figure 3. Convergence breadth, dispersion across firms and linked risk sentences, fiscal 2017 to 2025", f"Note: Firms present every year: n = {N['balanced_firms']}. Source: SEC EDGAR 10-K filings; author's analysis."),
    "four": ("Figure Four Breadth by Division.png", "Figure 4. Mean convergence breadth by SIC division, fiscal 2017 to 2025", "Note: Divisions with at least 15 sampled firms; n = firms in fiscal 2018. Source: SEC EDGAR 10-K filings; author's analysis."),
    "five": ("Figure Five Hypothesis Estimates.png", "Figure 5. Hypothesis tests with 95 per cent confidence intervals", "Note: Cross-sectional OLS with two-digit SIC and fiscal year-end month fixed effects, category intensities and controls; errors clustered by two-digit SIC. Source: author's analysis."),
}
blocks = {"title": C.TITLE, "abstract": C.ABSTRACT, "keywords": C.KEYWORDS, "body": [], "tables": T,
          "figures": {k: {"file": str(PROJ / "Figures and Tables" / v[0]), "caption": v[1], "note": v[2]} for k, v in FIGS.items()},
          "references": [e["text"] for e in refs]}
for k, v in C.BLOCKS:
    blocks["body"].append({"kind": k, "value": v})
def minus(o):
    if isinstance(o, str):
        return re.sub(r"(?<![A-Za-z0-9])-(?=\d)", "\u2212", o)
    if isinstance(o, list):
        return [minus(x) for x in o]
    if isinstance(o, dict):
        return {k: (minus(v) if k not in ("file",) else v) for k, v in o.items()}
    return o


blocks["tables"] = minus(blocks["tables"])
(HERE / "Manuscript Blocks.json").write_text(json.dumps(blocks, indent=1, ensure_ascii=False))
words = sum(len(v.split()) for k, v in C.BLOCKS if k == "p")
abs_words = sum(len((a + " " + b).split()) for a, b in C.ABSTRACT)
print("body words", words, "abstract words", abs_words, "references", len(refs))
print("uncited verified entries:", len(entries) - len(cited))
