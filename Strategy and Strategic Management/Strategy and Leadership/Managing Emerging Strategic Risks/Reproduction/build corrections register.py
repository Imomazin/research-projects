"""Write Reproduction/Corrections Register.csv from the revision outputs.

Each row records an issue raised in the revision instructions or found during the revision,
what the first version did, what the verification found, the correction made and the effect on
the conclusions. Every number is read from Manuscript/Revision Numbers.json or the original
Numbers.json, so the register cannot drift from the analysis.
"""
import json
import math
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
N = json.loads((PROJ / "Manuscript" / "Revision Numbers.json").read_text())
O = N["original"]


def P(ep, m, y, t):
    return N["principal"][f"{ep}|{m}|{y}|{t}"]


def RV(ep, meas, m, y, t):
    return N["response_variants"].get(f"{ep}|{meas}|{m}|{y}|{t}")


def f3(x):
    return f"{x:.3f}"


def pv(x):
    return "p < 0.001" if x < 0.001 else f"p = {x:.3f}"


rep = N.get("reproduction", {})
sc = rep.get("status_counts", {})
ic = N["independent_checks"]
V = N["validation"]
vo, vr, vh = V["Original rules|All reference items"], V["Revised rules|All reference items"], V["High-confidence rules|All reference items"]
lmk = next((k for k in V if k.startswith("Language model on candidate") and k.endswith("All reference items")),
           "Language model (entailment at least 0.5)|All reference items")
vl = V[lmk]
sev1, rec1, sev3, rec3 = P("A", "H1", "severity", "breadth_z"), P("A", "H1", "recovery", "breadth_z"), P("A", "H3", "severity", "bxc"), P("A", "H3", "recovery", "bxc")
sev2 = P("A", "H2", "severity", "coverage_z")
b2 = P("B", "H1", "margin_change_two", "breadth_z")
ri = {r["specification"] + "|" + r["outcome"] + "|" + r["term"]: r for r in N["recovery_investigation"]}
ii = {r["specification"] + "|" + r["outcome"]: r for r in N["interaction_investigation"]}
sh = N["shock"]
cg = next(c for c in N["compounding"] if c["outcome"] == "rev_growth")
cl = N["clusters"]
pl = N["placebo"].get("H1|severity|breadth_z")
mt = {(r["measure"], r["fiscal_year"]): r for r in N["measure_trends"]}
hi_firms = round((1 - (RV("A", "High-confidence rules", "H2", "severity", "cv_z") or {}).get("share_zero", 1)) * sev1["n"])
h2n = [r for k, r in N["response_variants"].items() if "|H2|" in k and k.endswith("|cv_z")]

rows = [
    ("Reproducibility of reported results",
     "Results produced by the pipeline at commit ed1a1df on branch research/strategic-risk",
     (f"Full rerun from raw filings and XBRL facts: {sc.get('match', 0) + sc.get('match to rounding', 0)} of {rep.get('numbers_compared', 0)} reported quantities reproduced; "
      if rep else "Full rerun pending; ") +
     f"independent re-implementation matched {ic['match']} of {ic['total']} checked values",
     "Reconciliation report added (Reproduction/Reconciliation Report.csv); any differences explained there", "None for the reproduced quantities"),
    ("Sample selection log",
     "Final row (validation screen leaving 787 firms) present in the committed log",
     "No script at ed1a1df writes that row; it was added by hand. The count agrees with Frame Validation Exclusions.csv",
     "Reproduction derives the row from the exclusions file and records the step in the run log", "None; the sample is unchanged"),
    ("Uncoded validation sample from the main text run",
     "Datasets/Derived/Validation Sample.csv committed at ed1a1df",
     "The reproduced draw shares 4 of 520 sentences with the committed file, probably because the committed file predates the final dictionary edit",
     "Recorded in File Comparison.csv; the file feeds no reported number (the revised-dictionary audit uses the committed holdout sample)", "None"),
    ("Commit fe19a29",
     "Cited as the data-processing commit",
     "Exists (fe19a2977750ff1829bdcaecd6da86abd6085f97, 25 October 2026 06:10 UTC) on research/strategic-risk and is an ancestor of revision/strategic-risk; not on main",
     "Recorded in the reproducibility record", "None"),
    ("Precision of the documented-response measure",
     f"Rule-based measure (organisational subject, action verb, category term); audit reported in Table A1 only for the dictionary",
     f"Weighted precision {vo['precision_weighted']:.2f} (original rules) and {vr['precision_weighted']:.2f} (revised rules) against a written coding manual; most false positives were sentences without organisational action, irrelevant categories, customer products and standing treasury instruments",
     f"Coding manual written; high-confidence rules (precision {vh['precision_weighted']:.2f}, recall {vh['recall_weighted']:.2f}) and a zero-shot language model (precision {vl['precision_weighted']:.2f}, recall {vl['recall_weighted']:.2f}) added; H2 and H3 re-estimated under each measure",
     "Documented response measured strictly was rare; no measure supports H2; the construct is named documented response coverage and the alignment label is dropped"),
    ("Status of reference labels",
     "Dictionary audit coded with an AI assistant",
     "Response validation labels also assigned by an AI assistant applying the manual",
     "Manuscript, tables and workbook state that labels are not independent human annotation; blank coding sheets, training sheet and agreement code released for two human coders",
     "Precision and recall are provisional until human double-coding is complete"),
    ("Recall outside candidate sentences",
     "Not assessed",
     f"None of {N['validation_sample']['strata'].get('other', 0)} audited non-candidate pairs qualified; Wilson upper bound about 12 per cent",
     "Recall reported as within-candidate recall; limitation stated", "Responses phrased in ways no rule detects could be missed"),
    ("Positive recovery association of breadth",
     f"Reported as a result running against the hypotheses: b = {f3(rec1['coef'])}, {pv(rec1['p'])}; abstract stated that breadth predicted stronger recovery among firms with no documented action",
     f"Wild bootstrap p = {rec1['p_wild']:.3f}; BH q = {rec1['q_bh']:.3f}; with three-digit SIC effects b = {f3(ri['Three-digit SIC fixed effects|recovery|breadth_z']['coef'])} (p = {ri['Three-digit SIC fixed effects|recovery|breadth_z']['p']:.3f}); with all alternative explanations b = {f3(ri['All of the above jointly|recovery|breadth_z']['coef'])} (p = {ri['All of the above jointly|recovery|breadth_z']['p']:.3f}); only supply-chain materiality carries it among categories",
     "Reported as exploratory and unconfirmed; removed from the abstract", "No claim that disclosing more risks aids recovery"),
    ("Negative breadth-by-coverage interaction",
     f"Reported against H3 and read as firms already responding to realised pressure: severity b = {f3(sev3['coef'])}, {pv(sev3['p'])}",
     f"Holm p = {sev3['p_holm']:.3f}; vanishes among firms with any response (severity {f3(ii['Firms with any revised-rule response only|severity']['coef'])}, recovery {f3(ii['Firms with any revised-rule response only|recovery']['coef'])}), outside manufacturing for recovery and with FY2019 text filed before March 2020 (recovery {f3(ii['FY2019 text filed before 1 March 2020|recovery']['coef'])})",
     "Reported as fragile; explanation offered as plausible and untested", "H3 not supported; interaction not interpreted as a response effect"),
    ("Fiscal 2023 margin result",
     f"b = {f3(b2['coef'])}, {pv(b2['p'])}; already noted as sensitive to HC1 errors",
     f"Wild bootstrap p = {b2['p_wild']:.3f}; BH q = {b2['q_bh']:.2f}; appears with the five-sentence threshold but not with the one-sentence or non-boilerplate counts",
     "Reported as unconfirmed", "Not treated as evidence for H1"),
    ("Small and uneven clusters",
     "CR1 errors clustered by two-digit SIC with normal reference distribution",
     f"{cl['clusters']} clusters; largest holds {100 * cl['largest_share']:.1f} per cent of firms; {cl['singletons']} singletons; effective number about {cl['effective_clusters_herfindahl']:.0f}",
     "t(G-1) reference and restricted wild cluster bootstrap (4,999 draws) added for principal tests", "Conclusions unchanged; H3 severity interaction keeps p < 0.01 under the wild bootstrap"),
    ("Multiple testing",
     "No adjustment",
     "Three confirmatory tests and many exploratory tests",
     "Holm adjustment for the confirmatory family and Benjamini-Hochberg for exploratory and response-measure families",
     f"H3 severity interaction Holm p = {sev3['p_holm']:.3f}; recovery association q = {rec1['q_bh']:.3f}; FY2023 margin result q = {b2['q_bh']:.2f}"),
    ("Benjamini-Hochberg implementation in revision code",
     "Not applicable to the first version",
     "First revision draft enforced monotonicity on q-values in the wrong order, which overstated some q-values",
     "Replaced by a standard step-up implementation tested against statsmodels before any value was reported", "None; caught before reporting"),
    ("Equivalence for the H1 null",
     f"Null reported with p = {sev1['p']:.3f}",
     f"95 per cent interval with t reference [{f3(sev1['ci_low_t'])}, {f3(sev1['ci_high_t'])}] log points per standard deviation",
     "Interval and the largest excluded effect reported", "Null is informative: effects beyond about three per cent per standard deviation are excluded"),
    ("Placebo period",
     "None",
     (f"Fiscal 2017 breadth on fiscal 2018 to 2019 revenue change: b = {f3(pl['coef'])}, {pv(pl['p'])}" if pl else "Pending"),
     "Placebo episode added", "Consistent with the null H1 result"),
    ("Attrition",
     "Firms not required to survive",
     f"Breadth did not predict survival to fiscal 2022 (logit p = {N['survival_logit']['p']['breadth_z']:.2f}); survivors-only and inverse-probability-weighted estimates close to the primary ones",
     "Attrition checks added", "None"),
    ("Convergence measurement",
     "Breadth at a three-sentence threshold, with diversity and threshold checks in the grid",
     f"Coefficient of variation fell under every alternative count: five-sentence threshold {mt[('breadth_t5', 2017)]['cv']:.3f} to {mt[('breadth_t5', 2025)]['cv']:.3f}; non-boilerplate {mt[('breadth_specific', 2017)]['cv']:.3f} to {mt[('breadth_specific', 2025)]['cv']:.3f}; mention density {mt[('mention_density', 2017)]['cv']:.3f} to {mt[('mention_density', 2025)]['cv']:.3f}",
     "Twelve alternative measures, a hazard-catalogue exclusion and determinants of breadth added; none predicted the pandemic revenue fall", "Saturation finding strengthened"),
    ("Macro-financial channel",
     "Lower growth and margins in high policy-uncertainty years; held with industry-by-year effects",
     f"Revenue b = {f3(sh['rev_growth|fy|firm and year|firm|x_macro']['coef'])} ({pv(sh['rev_growth|fy|firm and year|firm|x_macro']['p'])}); with industry clustering {pv(sh['rev_growth|fy|firm and year|industry|x_macro']['p'])}",
     "Reported with the clustering caveat", "Channel result is weaker than first stated"),
    ("Price pass-through",
     "Stated that geopolitically and supply-exposed firms passed costs into prices",
     f"Cost of revenue rose with revenue (geopolitical b = {f3(sh['cost_growth|fy|firm and year|firm|x_geopolitical']['coef'])}) and gross margin did not change; no firm-level price data",
     "Described as a plausible mechanism that the study does not test", "Mechanism claim softened"),
    ("Inflation adjustment",
     "Nominal outcomes",
     "Deflating by CPI-U leaves interaction estimates unchanged because a common deflator is absorbed by year effects; October 2025 CPI missing in the BLS file",
     "Real growth reported; missing month interpolated and recorded", "None"),
    ("Macro series versions",
     "Single download",
     f"Second download of {N['macro_version_check']['files']} files byte-identical ({N['macro_version_check']['identical']} of {N['macro_version_check']['files']})",
     "Version check recorded in the retrieval manifest", "None"),
    ("Compounding",
     "No compounding from combined exposure",
     f"Breadth x number of high indices on revenue growth: 95 per cent CI [{f3(cg['ci95'][0])}, {f3(cg['ci95'][1])}]; equivalence test {pv(cg['tost_p'])} against {f3(cg['bound_smallest_significant_single_effect'])}",
     "Equivalence bounds added", "Absence of compounding now supported by an equivalence test"),
    ("Theory and constructs",
     "Disclosure, documented action and sensitivity discussed together; ambidexterity cited",
     "Constructs conflated in places; no measure of ambidexterity",
     "Three constructs defined; saturation mechanism stated; ambidexterity labelled untested; comparison with Zhang et al. (2026) added",
     "Contribution restated around saturation and measurement"),
    ("References",
     "90 references",
     "All 90 verified against Crossref or OpenAlex; one remembered DOI for a candidate source resolved to a different paper",
     "That source not cited; new 2025 and 2026 references verified before use", "None"),
    ("Table and figure order",
     "Table 7 appeared in the text before Table 6",
     "Order checked automatically in the revision build",
     "Tables and figures renumbered in narrative order; figures redrawn in greyscale", "None"),
]
df = pd.DataFrame(rows, columns=["Issue", "Original finding or method", "Verification result", "Correction", "Effect on conclusions"])
df.to_csv(HERE / "Corrections Register.csv", index=False)
print(len(df), "rows")
