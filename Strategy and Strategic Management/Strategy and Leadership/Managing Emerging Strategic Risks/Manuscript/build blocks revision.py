"""Assemble Manuscript Blocks Revision.json for the revised manuscript.

Text comes from manuscript content revision.py, tables from Revision Numbers.json and the
original Numbers.json, references from verified Crossref, OpenAlex and manual records through
Literature/build references revision.py. The script stops if any in-text citation lacks a
verified reference, so no unverified source can reach the reference list. Tables are numbered
in the order the text first refers to them.
"""
import importlib.util
import json
import math
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
LIT = PROJ / "Literature"
FIG = PROJ / "Figures and Tables" / "Revision"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C = load("content", HERE / "manuscript content revision.py")
REF = load("refs", LIT / "build references revision.py")
N, O = C.N, C.O
f2, f3, pv, MINUS = C.f2, C.f3, C.pv, C.MINUS


def p3(x):
    return "<0.001" if x < 0.001 else f"{x:.3f}"


def bp(r):
    return f"{f3(r['coef'])} ({p3(r['p'])})"


# ------------------------------------------------------------------ references
keys = []
for f in ("Candidate References.csv", "Revision Candidate References.csv"):
    keys += [r.split(",")[0] for r in (LIT / f).read_text().splitlines()[1:] if r.strip()]
DO_NOT_CITE = {"Brown Tian Tucker CAR"}   # Crossref returned a different paper for the remembered DOI
entries = {}
for k in dict.fromkeys(keys + list(REF.MANUAL.keys())):
    if k in DO_NOT_CITE:
        continue
    e = REF.entry(k)
    if e.get("verified"):
        e["cite"] = e.get("cite") or REF.in_text(e)
        entries[k] = e
text_all = " ".join(v for k, v in C.BLOCKS if k == "p") + " " + " ".join(v for _, v in C.ABSTRACT)


def variants(e):
    name, yr = e["cite"].rsplit(", ", 1)
    return [e["cite"], f"{name} ({yr})"]


cited = {k: e for k, e in entries.items() if any(v in text_all for v in variants(e))}
seen, uniq = set(), {}
for k, e in cited.items():
    if e["doi"] not in seen:
        uniq[k] = e
        seen.add(e["doi"])
cited = uniq
tokens = set()
for grp in re.findall(r"\(([^()]*\d{4}[^()]*)\)", text_all):
    for part in grp.split(";"):
        m = re.search(r"([A-Z][A-Za-z'\-À-ſ ]+(?: et al\.)?(?: and [A-Z][A-Za-z'\-À-ſ]+)?), (\d{4})$", part.strip())
        if m:
            tokens.add(f"{m.group(1).strip()}, {m.group(2)}")
for m in re.finditer(r"([A-Z][A-Za-z'\-]+(?: et al\.| and [A-Z][A-Za-z'\-]+)?) \((\d{4})\)", text_all):
    tokens.add(f"{m.group(1)}, {m.group(2)}")
known = {e["cite"] for e in cited.values()}
missing = sorted(t for t in tokens if t not in known and not t.startswith(("Table", "Figure")))
if missing:
    raise SystemExit(f"Citations without verified reference: {missing}")
# two works with the same in-text form would need a and b suffixes
dup = [c for c in known if sum(e["cite"] == c for e in cited.values()) > 1]
if dup:
    raise SystemExit(f"Ambiguous in-text citations: {dup}")
refs = sorted(cited.values(), key=lambda e: (e["first_author"].lower().replace("‐", "-"), e["year"], e["text"]))

# ------------------------------------------------------------------ tables
T = {}
T["one"] = {
    "caption": "Table 1. Data sources, content and coverage",
    "header": ["Source", "Content used", "Coverage", "Role in the study"],
    "widths": [22, 32, 22, 24],
    "rows": [
        ["SEC EDGAR submissions and 10-K filings", "Items 1, 1A and 7 of the latest original 10-K for each fiscal year",
         f"{O['sample_final']} firms; {O['filings']:,} filings; fiscal 2017 to 2025", "Disclosed exposure, convergence, documented response"],
        ["SEC XBRL company facts", f"{O['xbrl_fact_rows']:,} fact rows; first-reported annual values", "Fiscal 2013 to 2026",
         "Revenue, cost, margins, inventory, controls"],
        ["SEC XBRL frames (public float)", "Entity public float reported for 2018", f"{O['frame_float_entities']:,} entities", "Sampling frame"],
        ["Geopolitical Risk index (Caldara and Iacoviello)", "Monthly global index", "1985 to September 2026", "Geopolitical shock"],
        ["Economic Policy Uncertainty (Baker, Bloom and Davis)", "US index with trade policy and regulation components", "1985 to September 2026", "Policy, trade and regulatory shocks"],
        ["Global Supply Chain Pressure Index (Federal Reserve Bank of New York)", "Monthly standardised index", "1998 to September 2026", "Supply-chain shock"],
        ["World Uncertainty Index (Ahir, Bloom and Furceri)", "Quarterly global and US indices", "1952 to 2026 third quarter", "Supplementary uncertainty measure"],
        ["US Bureau of Labor Statistics price indices", "CPI-U all items (seasonally adjusted); PPI final demand", "January 2012 to September 2026",
         "Deflating revenue; inflation context"],
    ],
    "note": "Note: Indices were averaged over the twelve months ending in each firm's fiscal year-end month in the primary models. "
            f"A second download of all {N['macro_version_check']['files']} macro files on 25 October 2026 returned byte-identical files. "
            "The October 2025 CPI value is missing in the BLS file and was interpolated. Retrieval dates and checksums are held in the project repository. Source: author's compilation.",
}

log = pd.read_csv(PROJ / "Datasets" / "Sampling Frame" / "Sample Selection Log.csv")
d = O["episodeA_desc"]
labels = {"severity": "Revenue severity, ln(FY2020/FY2019)", "margin_change": "Operating-margin change, FY2020 minus FY2019",
          "recovery": "Revenue recovery, ln(FY2022/FY2019)", "breadth": "Convergence breadth, FY2018 (0 to 9)",
          "coverage": "Response coverage, revised rules, FY2018 (share)", "linkage": "Linkage density, FY2018 (share of sentences)"}
rows = [[s, "", f"{int(v):,}", ""] for s, v in zip(log["step"], log["firms remaining"])]
ar = N["any_response_pct"]
resp_rows = [["Firms with any documented response, FY2018 and FY2025", "", "", ""]] + [
    [f"{lab}", f"{ar[k]['2018']:.1f}% / {ar[k]['2025']:.1f}%", "", ""] for k, lab in
    [("original", "Original rules"), ("revised", "Revised rules"), ("high", "High-confidence rules"), ("lm", "Language model")] if k in ar]
T["two"] = {
    "caption": "Table 2. Sample selection, pandemic-episode variables and prevalence of documented response",
    "header": ["Step or variable", "Mean [SD] or share", "Firms or n", "Median"],
    "widths": [52, 18, 15, 15],
    "rows": [["Panel A. Sample selection", "", "", ""]] + rows + [["Panel B. Pandemic episode variables", "", "", ""]] +
            [[labels[k], f"{d[k]['mean']:.3f} [{d[k]['sd']:.3f}]", f"{d[k]['n']:,}", f"{d[k]['median']:.3f}"] for k in labels] +
            [["Panel C. " + resp_rows[0][0], "", "", ""]] + resp_rows[1:],
    "bold_rows": [0, len(rows) + 1, len(rows) + 2 + len(labels)],
    "note": "Note: Outcomes winsorised at the 1st and 99th percentiles. Breadth counts categories with at least three Item 1A sentences. "
            "Panel C gives the share of sample firms filing in that year with at least one documented response under each rule. Source: SEC EDGAR filings and XBRL company facts; author's analysis.",
}

# Table 3: validation
vrows = []
order = [("Original rules", "Original rules"), ("Revised rules", "Revised rules"), ("High-confidence rules", "High-confidence rules"),
         (C.LMCAND if f"{C.LMCAND}|All reference items" in N["validation"] else C.LMNAME, "Language model on candidates"),
         ("Revised rules confirmed by language model", "Revised rules confirmed by language model")]
for key, lab in order:
    if f"{key}|All reference items" not in N["validation"]:
        continue
    v = N["validation"][f"{key}|All reference items"]
    vrows.append([lab, f"{int(v['items_flagged'])}", f"{int(v['items_flagged_qualifying'])}",
                  f"{v['precision_unweighted']:.2f} [{v['precision_unweighted_wilson_low']:.2f}, {v['precision_unweighted_wilson_high']:.2f}]",
                  f"{v['precision_weighted']:.2f} [{v['precision_ci_low']:.2f}, {v['precision_ci_high']:.2f}]",
                  f"{v['recall_weighted']:.2f} [{v['recall_ci_low']:.2f}, {v['recall_ci_high']:.2f}]",
                  f"{v['f1_weighted']:.2f} [{v['f1_ci_low']:.2f}, {v['f1_ci_high']:.2f}]",
                  f"{v['estimated_population_flagged']:,.0f}"])
vs = N["validation_sample"]
T["three"] = {
    "caption": "Table 3. Validation of four documented-response measures against the coding manual",
    "header": ["Rule", "Flagged in sample", "Of which qualify", "Precision, sample [Wilson 95%]", "Precision, weighted [95%]",
               "Recall, weighted [95%]", "F1, weighted [95%]", "Pairs flagged in population"],
    "widths": [22, 9, 9, 13, 13, 13, 12, 9], "rows": vrows,
    "note": f"Note: {vs['items']} sentence-category pairs drawn by stratified random sampling across rule strata, nine categories, "
            f"{vs['divisions']} SIC divisions and {vs['years']} fiscal years; {vs['qualifying']} qualify. Weighted figures apply design weights and "
            "give population estimates; intervals for weighted figures come from 2,000 stratified bootstrap draws. Recall is estimated within candidate pairs. "
            "Reference labels were assigned by an AI assistant applying the written coding manual and are not independent human annotation; "
            "the blank sheets for two human coders are released with the data. Source: author's analysis.",
}

# Table 4: hypothesis tests across measures
P = C.P
cols4 = [("A", "severity", "Revenue fall FY2020"), ("A", "margin_change", "Margin change FY2020"), ("A", "recovery", "Recovery FY2022"),
         ("B", "margin_change", "Margin change FY2022"), ("B", "margin_change_two", "Margin change FY2023"), ("B", "severity", "Revenue FY2021 to FY2023")]
rows4 = [["H1. Convergence breadth (primary)"] + [""] * 6]
rows4.append(["Breadth, b (p)"] + [bp(P(e, "H1", y, "breadth_z")) for e, y, _ in cols4])
rows4.append(["Wild bootstrap p"] + [p3(P(e, "H1", y, "breadth_z")["p_wild"]) if P(e, "H1", y, "breadth_z").get("p_wild") is not None else "" for e, y, _ in cols4])
rows4.append(["Holm p or BH q"] + [(p3(r["p_holm"]) if r.get("p_holm") is not None else (f"q {r['q_bh']:.3f}" if r.get("q_bh") is not None else ""))
                                   for r in (P(e, "H1", y, "breadth_z") for e, y, _ in cols4)])
meas = [("Original rules", "Original rules"), ("Revised rules", "Revised rules (primary)"), ("High-confidence rules", "High-confidence rules")]
if C.HAS_LM:
    meas.append((C.LMNAME, "Language model"))


def rvcell(ep, m, mod, y, t):
    k = f"{ep}|{m}|{mod}|{y}|{t}"
    return bp(N["response_variants"][k]) if k in N["response_variants"] else "n.e."


rows4.append(["H2. Response coverage, b (p)"] + [""] * 6)
for m, lab in meas:
    rows4.append([lab] + [rvcell(e, m, "H2", y, "cv_z") for e, y, _ in cols4])
rows4.append(["H3. Breadth x coverage, b (p)"] + [""] * 6)
for m, lab in meas:
    rows4.append([lab] + [rvcell(e, m, "H3", y, "bxcv") for e, y, _ in cols4])
s3 = P("A", "H3", "severity", "bxc")
rows4.append(["Revised rules: wild bootstrap p; Holm p", f"{p3(s3['p_wild'])}; {p3(s3['p_holm'])}"] + [""] * 5)
nobs = [P(e, "H1", y, "breadth_z")["n"] for e, y, _ in cols4]
rows4.append(["Firms (H1)"] + [f"{int(n):,}" for n in nobs])
T["four"] = {
    "caption": "Table 4. Hypothesis tests under four response measures in two shock episodes",
    "header": ["Test and measure"] + [c[2] for c in cols4], "widths": [25, 12.5, 12.5, 12.5, 12.5, 12.5, 12.5], "rows": rows4,
    "bold_rows": [i for i, r in enumerate(rows4) if r[0].startswith(("H1.", "H2.", "H3."))],
    "note": f"Note: Coefficients per standard deviation of the predictor; p-values from errors clustered by two-digit SIC with a t({C.cl['clusters'] - 1}) reference. "
            "Wild bootstrap: restricted wild cluster bootstrap, Rademacher weights, 4,999 draws. Holm adjustment across the three confirmatory tests on pandemic revenue severity; "
            "BH q is the Benjamini-Hochberg adjustment across exploratory tests. Predictors from fiscal 2018 (pandemic) and fiscal 2020 (2022 episode). All models include the nine "
            "category intensities, log assets, leverage, cash to assets, return on assets, prior two-year revenue growth, log Item 1A words and two-digit SIC and fiscal year-end "
            "month fixed effects. n.e.: not estimated because fewer than ten firms had a non-zero value. Source: author's analysis.",
}

# Table 5: recovery and interaction scrutiny
rows5 = [["Panel A. Breadth and pandemic recovery", "", "", ""]]
for spec in ["Primary specification", "Three-digit SIC fixed effects", "Peer recovery (industry leave-one-out mean)", "Pandemic demand shock (peer severity)",
             "Foreign income share (geographic diversification)", "Revenue size and share of industry revenue (market position)",
             "R&D intensity, capex rate and inventory (strategic flexibility)", "Pandemic category material in FY2018", "All of the above jointly"]:
    r = C.RI("recovery", spec)
    rows5.append([spec, f3(r["coef"]), p3(r["p"]), f"{int(r['n'])}"])
rs = C.RIT("recovery", "Material-category indicators in place of breadth", "mat_supply")
rows5.append(["Supply-chain category material (category indicators in place of breadth)", f3(rs["coef"]), p3(rs["p"]), f"{int(rs['n'])}"])
rows5.append(["Panel B. Breadth x revised-rule coverage", "Revenue fall", "Recovery", "Firms"])
for spec in ["Primary specification", "Firms with any revised-rule response only", "Excluding distressed firms (negative ROA or top-quintile leverage)",
             "Manufacturing only", "Excluding manufacturing", "Control for peer severity", "FY2019 text filed before 1 March 2020"]:
    a, b = C.II("severity", spec), C.II("recovery", spec)
    rows5.append([spec, bp(a), bp(b), f"{int(a['n'])}"])
T["five"] = {
    "caption": "Table 5. Scrutiny of the recovery association and the breadth-by-coverage interaction, pandemic episode",
    "header": ["Specification", "b", "p", "Firms"], "widths": [52, 16, 16, 16], "rows": rows5,
    "bold_rows": [0, 11],
    "note": "Note: Panel A: coefficient on breadth (per standard deviation) for revenue recovery from fiscal 2019 to 2022, adding each alternative explanation in turn to the primary model. "
            "Panel B: interaction coefficient with p-values in brackets. Errors clustered by two-digit SIC. Source: author's analysis.",
}

# Table 6: shock channels
SH = C.SH
terms6 = [("x_geopolitical", "Geopolitical exposure x GPR"), ("x_supply", "Supply-chain exposure x GSCPI"), ("x_trade", "Trade exposure x trade policy uncertainty"),
          ("x_regulatory", "Regulatory exposure x regulation uncertainty"), ("x_macro", "Macro-financial exposure x EPU"),
          ("x_pandemic", "Pandemic exposure x fiscal 2020"), ("x_breadth_shocks", "Breadth x number of high indices")]
specs6 = [("rev_growth", {}, "Revenue growth"), ("rev_growth", {"cluster": "industry"}, "Revenue growth, industry clusters"),
          ("rev_growth", {"effects": "firm and industry-by-year"}, "Revenue growth, industry-by-year effects"),
          ("cost_growth", {}, "Cost of revenue growth"), ("d_gross_margin", {}, "Gross margin change"), ("d_op_margin", {}, "Operating margin change")]


def star(p):
    return "**" if p < 0.01 else ("*" if p < 0.05 else "")


rows6 = []
for t, lab in terms6:
    rows6.append([lab] + [f"{f3(SH(y, t, **kw)['coef'])}{star(SH(y, t, **kw)['p'])}" for y, kw, _ in specs6])
rows6.append(["Firm-years"] + [f"{int(SH(y, 'x_geopolitical', **kw)['n']):,}" for y, kw, _ in specs6])
T["six"] = {
    "caption": "Table 6. Pre-shock exposure and realised sensitivity by channel, fiscal 2019 to 2025",
    "header": ["Interaction"] + [s[2] for s in specs6], "widths": [28, 12, 12, 12, 12, 12, 12], "rows": rows6,
    "note": "Note: Exposure is the fiscal 2018 category intensity, standardised; each index is the fiscal-year average, standardised. Firm and year fixed effects "
            "unless stated; errors clustered by firm unless stated; * p < 0.05, ** p < 0.01. Lagged convergence, coverage and controls included. "
            "Alternative index timings (year-end month, within-year peak, year-on-year change) and two-way clustering are reported in the workbook. Source: author's analysis.",
}

# Table 7: cases with the coding-manual verdict
cases = json.loads((PROJ / "Results" / "Illustrative Cases.json").read_text())
RM = pd.read_csv(PROJ / "Datasets" / "Derived" / "Revision" / "Response Measures.csv")
RM18 = RM[RM["fiscal_year"] == 2018].set_index("cik")
CATS = ["geopolitical", "trade", "regulatory", "cyber", "technology", "supply", "climate", "macro", "pandemic"]
short = {"geopolitical": "Geo", "trade": "Trade", "regulatory": "Reg", "cyber": "Cyber", "technology": "Tech", "supply": "Supply",
         "climate": "Climate", "macro": "Macro", "pandemic": "Pandemic"}
names = {"Ford Motor Co": "Ford Motor", "AMAZON.COM, INC.": "Amazon.com", "Marathon Petroleum Corporation": "Marathon Petroleum",
         "United Parcel Service, Inc.": "United Parcel Service", "GENERAL MOTORS COMPANY": "General Motors", "Walmart Inc.": "Walmart",
         "CATERPILLAR INC": "Caterpillar", "McKESSON CORPORATION": "McKesson"}
verdict = {"Marathon Petroleum Corporation": "Routine (asset transfer to affiliate; logistics)", "United Parcel Service, Inc.": "Routine (acquisitions)",
           "CATERPILLAR INC": "Routine (standing currency hedging)", "McKESSON CORPORATION": "Routine (outsourcing for efficiency)"}
rows7 = []
for c in cases:
    hi = [short[k] for k in CATS if c["cik"] in RM18.index and RM18.loc[c["cik"], f"act_high_{k}"] > 0]
    rows7.append([names.get(c["name"], c["name"]), c["breadth_group"], ", ".join(short[x] for x in c["material"]),
                  ", ".join(short[x] for x in c["actions"]) or "None", verdict.get(c["name"], "No action counted"), ", ".join(hi) or "None",
                  f"{100 * (math.exp(c['severity']) - 1):.1f}%", f"{100 * (math.exp(c['recovery']) - 1):.1f}%"])
T["seven"] = {
    "caption": "Table 7. Illustrative cases from the pandemic episode",
    "header": ["Firm", "Breadth group", "Material categories, FY2018", "Actions counted, revised rules", "Coding-manual verdict",
               "High-confidence actions", "Revenue FY2019 to FY2020", "Revenue FY2022 vs FY2019"],
    "widths": [13, 11, 20, 11, 17, 10, 9, 9], "rows": rows7,
    "note": "Note: Within each breadth group the rule selects the largest firm by fiscal 2019 revenue whose revenue fell by more than ten per cent and the largest whose "
            "revenue did not fall, with and without a counted action. The verdict applies the coding manual to the sentences the revised rules counted. "
            "Source: SEC EDGAR 10-K filings and XBRL company facts; author's analysis.",
}

# Table 8: executive diagnostic
T["eight"] = {
    "caption": "Table 8. An executive diagnostic for converging strategic risks",
    "header": ["Stage", "What the evidence shows", "Question for the board", "Evidence to request", "Owner and timing"],
    "widths": [11, 27, 21, 23, 18],
    "rows": [
        ["Identify", f"Risk lists rose to {f2(O['breadth_mean']['2025'])} of nine categories; dispersion fell under every count and more than half of Item 1A text sat in boilerplate sentences from fiscal 2019",
         "Which of our risk statements would read the same for a competitor?", "Item 1A changes against last year; firm-specific risks separated from shared text", "General counsel and chief risk officer; annual"],
        ["Quantify", "Geopolitical and supply-chain exposure moved revenue and cost together; macro-financial exposure reduced operating margin; combined exposure added nothing measurable",
         "Through which channel would each risk reach the accounts, and how much?", "Revenue, cost and asset share exposed per channel; contractual ability to pass costs into prices", "Chief financial officer; annual and after each shock"],
        ["Respond", f"Rules counting response had precision near {f2(N['validation']['Revised rules|All reference items']['precision_weighted'])}; threat-linked responses were rare and none protected performance",
         "What have we completed for each material risk, with what resources?", "Register of completed actions tied to a named threat, with cost, owner and date", "Executive owner for each risk; quarterly"],
        ["Validate", "Disclosure did not predict who lost most; realised sensitivity by channel did",
         "Did our exposure behave as estimated in the last shock?", "Variance analysis of revenue and margin by channel in the shock year", "Audit or risk committee; after each shock"],
    ],
    "note": "Note: The four stages map to sensing (Identify, Quantify), seizing (Respond) and reconfiguring and learning (Validate). Source: author's design based on the study's findings.",
}

# Appendix tables
au0, au1 = O["audit_original"], O["audit_revised"]
anames = {"geopolitical": "Geopolitical", "trade": "Trade policy", "regulatory": "Regulatory change", "cyber": "Cybersecurity", "technology": "AI and technology",
          "supply": "Supply chain", "climate": "Climate and environment", "macro": "Macro-financial", "pandemic": "Pandemic",
          "none": "Unclassified sentences with category content"}
T["appA"] = {
    "caption": "Table A1. Audit of dictionary classifications",
    "header": ["Category", "Original dictionary: correct of audited", "Revised dictionary, fresh sample: correct of audited"],
    "widths": [36, 32, 32],
    "rows": [[anames[k], f"{au0[k]['correct']} of {au0[k]['n']}", f"{au1[k]['correct']} of {au1[k]['n']}"] for k in anames] +
            [["Pooled category precision", f"{O['audit_pooled_original']:.2f}", f"{O['audit_pooled_revised']:.2f}"]],
    "note": "Note: Sentences drawn by stratified random sampling with different seeds for the two audits and coded by an AI assistant against written category definitions; "
            "not independent human annotation. For unclassified sentences the figure counts misses. Source: author's analysis.",
}
corr = pd.read_csv(PROJ / "Results" / "Correlations Episode A.csv", index_col=0)
cv_ = ["severity", "recovery", "breadth", "coverage", "linkage", "ln_assets", "leverage", "cash_ratio", "roa"]
cn = {"severity": "1 Severity", "recovery": "2 Recovery", "breadth": "3 Breadth", "coverage": "4 Coverage", "linkage": "5 Linkage",
      "ln_assets": "6 Log assets", "leverage": "7 Leverage", "cash_ratio": "8 Cash to assets", "roa": "9 Return on assets"}
T["appB"] = {"caption": "Table A2. Correlations among pandemic-episode variables", "header": ["Variable"] + [str(i + 1) for i in range(len(cv_))],
             "widths": [19] + [9] * len(cv_),
             "rows": [[cn[a]] + [(f"{corr.loc[a, b]:.2f}" if j < i else "") for j, b in enumerate(cv_)] for i, a in enumerate(cv_)],
             "note": "Note: Pearson correlations, pairwise complete observations, winsorised variables; coverage under the revised rules. Source: author's analysis."}
AC = N["alternative_convergence"]
acm = [m for m in dict.fromkeys(r["measure"] for r in AC) if not m.startswith("Joint")]
rowsC = []
for m in acm:
    def g(ep, y):
        r = [x for x in AC if x["episode"] == ep and x["outcome"] == y and x["measure"] == m]
        return bp(r[0]) if r else ""
    rowsC.append([m, g("A", "severity"), g("A", "margin_change"), g("A", "recovery"), g("B", "margin_change"), g("B", "margin_change_two")])
T["appC"] = {"caption": "Table A3. Alternative convergence measures", "header": ["Measure, standardised", "Revenue fall FY2020", "Margin change FY2020",
             "Recovery FY2022", "Margin change FY2022", "Margin change FY2023"], "widths": [30, 14, 14, 14, 14, 14], "rows": rowsC,
             "note": "Note: Each measure replaces breadth in the H1 model; b (p). Boilerplate sentences contain a four-word sequence shared by 30 to 75 per cent of that year's filings. "
                     "Industry adjustment subtracts the two-digit SIC mean. Source: author's analysis."}
RS = O["robustness_summary"]
grid = pd.DataFrame(N["grid_h1"])
rowsD = []
for k, lab in [("A|severity|breadth_z", "Breadth on revenue fall (original grid, H1 model)"), ("A|recovery|breadth_z", "Breadth on recovery (original grid)"),
               ("A|severity|breadth_z:coverage_z", "Breadth x coverage on revenue fall (original grid)"),
               ("A|recovery|breadth_z:coverage_z", "Breadth x coverage on recovery (original grid)"),
               ("B|margin_change_two|breadth_z", "Breadth on FY2023 margin change (original grid)")]:
    r = RS[k]
    rowsD.append([lab, str(r["checks"]), str(r["same_sign"]), str(r["p05"]), str(r["p05_hc1"]), f"{f3(r['min'])} to {f3(r['max'])}"])
for y, lab in [("severity", "Breadth on revenue fall (revision grid, breadth alone)"), ("recovery", "Breadth on recovery (revision grid, breadth alone)")]:
    g_ = grid[(grid["outcome"] == y) & (grid["check"] != "Primary specification")]
    base = grid[(grid["outcome"] == y) & (grid["check"] == "Primary specification")]["coef"].iloc[0]
    rowsD.append([lab, str(len(g_)), str(int((g_["coef"] * base > 0).sum())), str(int((g_["p"] < 0.05).sum())),
                  str(int((g_["p_hc1"] < 0.05).sum())), f"{f3(g_['coef'].min())} to {f3(g_['coef'].max())}"])
T["appD"] = {"caption": "Table A4. Summary of the robustness grids", "header": ["Association", "Checks", "Same sign", "p < 0.05, clustered", "p < 0.05, HC1", "Range of b"],
             "widths": [40, 10, 10, 13, 13, 14], "rows": rowsD,
             "note": "Note: The original grid has 23 pre-specified checks per association (thresholds, diversity, sample restrictions, added controls, timing, unwinsorised outcome "
                     "and dropping each SIC division) and was reproduced from the raw data. The revision grid adds hazard-catalogue exclusion and non-boilerplate breadth. Source: author's analysis."}

FIGS = {
    "one": ("Figure One Constructs and Tests.png", "Figure 1. Constructs, hypotheses and tests", "Source: author's design."),
    "two": ("Figure Two Category Prevalence.png", "Figure 2. Share of firms with each emerging risk category material in Item 1A, fiscal 2017 to 2025",
            f"Note: Material means at least three Item 1A sentences in the category. Source: SEC EDGAR 10-K filings of {O['sample_final']} sampled US non-financial firms; author's analysis."),
    "three": ("Figure Three Convergence and Homogenisation.png", "Figure 3. Convergence breadth and dispersion across firms under alternative counts, fiscal 2017 to 2025",
              "Note: Dispersion is the coefficient of variation across firms. Source: SEC EDGAR 10-K filings; author's analysis."),
    "four": ("Figure Four Breadth by Division.png", "Figure 4. Mean convergence breadth by SIC division, fiscal 2017 to 2025",
             "Note: Divisions with at least 15 sampled firms; n = firms in fiscal 2018. Source: SEC EDGAR 10-K filings; author's analysis."),
    "five": ("Figure Five Hypothesis Estimates.png", "Figure 5. Hypothesis tests with 95 per cent confidence intervals under four response measures",
             f"Note: Cross-sectional OLS with two-digit SIC and fiscal year-end month fixed effects, category intensities and controls; errors clustered by two-digit SIC; t({C.cl['clusters'] - 1}) intervals. Source: author's analysis."),
    "six": ("Figure Six Executive Diagnostic.png", "Figure 6. Identify, Quantify, Respond, Validate: an executive diagnostic for converging risks", "Source: author's design."),
}

# numbering check: tables and figures must first appear in numerical order
seq = [(k, v) for k, v in C.BLOCKS if k in ("table", "figure")]
word = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
for kind in ("table", "figure"):
    nums = [word[v] for k, v in seq if k == kind]
    if nums != sorted(nums):
        raise SystemExit(f"{kind}s out of order: {nums}")
body_text = " ".join(v for k, v in C.BLOCKS if k == "p")
for kind, lab in (("table", "Table"), ("figure", "Figure")):
    for k, v in seq:
        if k == kind and not re.search(rf"\b{lab}s? [^.]*\b{word[v]}\b", body_text):
            raise SystemExit(f"{lab} {word[v]} never referred to in text")

blocks = {"title": C.TITLE, "abstract": C.ABSTRACT, "keywords": C.KEYWORDS, "body": [{"kind": k, "value": v} for k, v in C.BLOCKS],
          "tables": T, "figures": {k: {"file": str(FIG / v[0]), "caption": v[1], "note": v[2]} for k, v in FIGS.items()},
          "appendix": ["appA", "appB", "appC", "appD"], "references": [e["text"] for e in refs]}


def minus(o):
    if isinstance(o, str):
        return re.sub(r"(?<![A-Za-z0-9])-(?=\d)", MINUS, o)
    if isinstance(o, list):
        return [minus(x) for x in o]
    if isinstance(o, dict):
        return {k: (minus(v) if k != "file" else v) for k, v in o.items()}
    return o


blocks["tables"] = minus(blocks["tables"])
(HERE / "Manuscript Blocks Revision.json").write_text(json.dumps(blocks, indent=1, ensure_ascii=False))
words = sum(len(v.split()) for k, v in C.BLOCKS if k == "p")
abs_words = sum(len((a + " " + b).split()) for a, b in C.ABSTRACT)
print("body words", words, "abstract words", abs_words, "references", len(refs))
(HERE / "Manuscript Text Revision.txt").write_text("\n\n".join([C.TITLE] + [f"{a}. {b}" for a, b in C.ABSTRACT] + [v for k, v in C.BLOCKS if k in ("p", "h1")]))
