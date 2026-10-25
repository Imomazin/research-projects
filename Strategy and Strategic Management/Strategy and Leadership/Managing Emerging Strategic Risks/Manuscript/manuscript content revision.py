"""Text of the revised manuscript. Every number is read from Revision Numbers.json.

BLOCKS is a list of (kind, value) pairs consumed by build blocks revision.py.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = json.loads((HERE / "Revision Numbers.json").read_text())
O = N["original"]
MINUS = "−"


def f2(x):
    return f"{x:.2f}".replace("-", MINUS)


def f3(x):
    return f"{x:.3f}".replace("-", MINUS)


def pv(x):
    return "p < 0.001" if x < 0.001 else f"p = {x:.3f}"


def pct(x, d=1):
    return f"{x:.{d}f} per cent"


def n0(x):
    return f"{int(round(x)):,}"


def ppt(x):
    """log or share change to per cent"""
    return f"{100 * (math.exp(x) - 1):.1f}".replace("-", MINUS)


def P(ep, model, outcome, term):
    return N["principal"][f"{ep}|{model}|{outcome}|{term}"]


def PL(model, outcome, term):
    return N["placebo"][f"{model}|{outcome}|{term}"]


def RV(ep, measure, model, outcome, term):
    return N["response_variants"][f"{ep}|{measure}|{model}|{outcome}|{term}"]


def V(rule, sample="All reference items"):
    return N["validation"][f"{rule}|{sample}"]


def SH(outcome, term, timing="fy", effects="firm and year", cluster="firm"):
    return N["shock"][f"{outcome}|{timing}|{effects}|{cluster}|{term}"]


def RI(outcome, spec):
    return next(r for r in N["recovery_investigation"] if r["outcome"] == outcome and r["specification"] == spec)


def RIT(outcome, spec, term):
    return next(r for r in N["recovery_investigation"] if r["outcome"] == outcome and r["specification"] == spec and r["term"] == term)


def II(outcome, spec):
    return next(r for r in N["interaction_investigation"] if r["outcome"] == outcome and r["specification"] == spec)


def AC(ep, outcome, measure, term=None):
    return next(r for r in N["alternative_convergence"] if r["episode"] == ep and r["outcome"] == outcome and r["measure"] == measure
                and (term is None or r["term"] == term))


def MT(measure, year):
    return next(r for r in N["measure_trends"] if r["measure"] == measure and r["fiscal_year"] == year)


def ME(measure, outcome, cov):
    return next(r for r in N["marginal"] if r["measure"] == measure and r["outcome"] == outcome and abs(r["coverage"] - cov) < 1e-9)


def DET(year, predictors):
    return next(r for r in N["determinants"] if r["fiscal_year"] == year and r["predictors"] == predictors)


def CMP(outcome):
    return next(c for c in N["compounding"] if c["outcome"] == outcome)


bm, cv, mp = O["breadth_mean"], O["breadth_cv"], O["material_pct"]
ar = N["any_response_pct"]
LMNAME = "Language model (entailment at least 0.5)"
LMCAND = "Language model on candidate pairs (measure used in the models)"
HAS_LM = any(k.startswith(f"A|{LMNAME}|") for k in N["response_variants"])
REP = N.get("reproduction", {})
rep_counts = REP.get("status_counts", {})
rep_match = rep_counts.get("match", 0) + rep_counts.get("match to rounding", 0)
rep_total = REP.get("numbers_compared", 0)
sev1, mar1, rec1 = P("A", "H1", "severity", "breadth_z"), P("A", "H1", "margin_change", "breadth_z"), P("A", "H1", "recovery", "breadth_z")
sev2, rec2 = P("A", "H2", "severity", "coverage_z"), P("A", "H2", "recovery", "coverage_z")
sev3, rec3 = P("A", "H3", "severity", "bxc"), P("A", "H3", "recovery", "bxc")
b1, b2, b3 = P("B", "H1", "margin_change", "breadth_z"), P("B", "H1", "margin_change_two", "breadth_z"), P("B", "H1", "severity", "breadth_z")
bc = P("B", "H2", "margin_change", "coverage_z")
pls, plm = PL("H1", "severity", "breadth_z"), PL("H1", "margin_change", "breadth_z")
vo, vr, vh = V("Original rules"), V("Revised rules"), V("High-confidence rules")
vl = V(LMCAND) if f"{LMCAND}|All reference items" in N["validation"] else V(LMNAME)
cl = N["clusters"]
cg, cm = CMP("rev_growth"), CMP("d_op_margin")
grid_rev = next(r for r in N["grid_h1"] if r.get("check") == "Base-year revenue of at least 100 million US dollars" and r.get("outcome") == "margin_change_two") \
    if any(r.get("check") == "Base-year revenue of at least 100 million US dollars" and r.get("outcome") == "margin_change_two" for r in N["grid_h1"]) else None

TITLE = "When every risk is material: disclosed risk convergence, documented response and organisational resilience in US firms, 2017 to 2025"

ABSTRACT_FN = lambda: [
    ("Purpose", "This study examines whether the number of emerging strategic risks a firm discloses and the responses it documents identify which firms lose most when systemic shocks arrive."),
    ("Design/methodology/approach", f"A stratified random sample of {n0(O['sample_final'])} US non-financial firms supplied {n0(O['filings'])} annual reports for fiscal 2017 to 2025. Nine risk categories were measured in Item 1A and documented responses in Items 1 and 7 under four classifiers audited against a coding manual. Disclosure was linked to SEC financial data and to uncertainty indices. Pre-registered models with small-cluster inference examine the pandemic and the 2022 shocks; the first version's results were reproduced from the raw filings."),
    ("Findings", f"Mean convergence breadth rose from {f2(bm['2017'])} to {f2(bm['2025'])} of nine categories while dispersion across firms fell under every alternative count. Breadth did not predict the pandemic revenue fall; the interval excludes falls above {ppt(abs(sev1['ci_low_t']))} per cent per standard deviation. Rule-based response measures had precision near {f2(vr['precision_weighted'])}; threat-linked responses were rare and no measure protected performance. Geopolitical and supply-chain exposure moved revenue and cost together in high-index years while macro-financial exposure lowered margins. Combined exposure added nothing measurable."),
    ("Research limitations/implications", "Validation labels come from AI coding that awaits human double-coding. Outcomes are nominal and the evidence is associational."),
    ("Practical implications", "Boards should treat the risk-factor list as a compliance record and assess exposure by transmission channel and by completed action."),
    ("Originality/value", "The study separates disclosed exposure, documented response and realised sensitivity and shows that disclosure saturation has removed the information in aggregate risk counts."),
]
KEYWORDS = "Strategic risk, Risk disclosure, Disclosure saturation, Organisational resilience, Dynamic capabilities, Enterprise risk management, Polycrisis"

BLOCKS = []
add = lambda k, v: BLOCKS.append((k, v))

# ---------------------------------------------------------------- introduction
add("h1", "Introduction")
add("p", f"Boards now read annual reports in which almost every emerging risk is listed as material. In fiscal 2017 the typical sampled US firm discussed {f2(bm['2017'])} of nine emerging risk categories at length in its risk factors; by fiscal 2025 the figure was {f2(bm['2025'])} with {pct(O['share_nine_pct']['2025'])} of firms covering all nine. The period behind this change brought a pandemic and three extreme index readings: the highest global supply-chain pressure since the index begins in 1998 (December 2021), the highest geopolitical risk since March 2003 (March 2022) and the highest US trade policy uncertainty since 1985 (April 2025) (Benigno et al., 2022; Caldara and Iacoviello, 2022; Baker et al., 2016). Scholars of systemic risk describe such periods as a polycrisis in which crises in different systems entangle and intensify each other (Lawrence et al., 2024; Helbing, 2013; Renn et al., 2019) and survey evidence suggests that firms in global production networks respond mostly with cautious measures such as buffers and scanning (Pedersen et al., 2026; Bag, 2026). Executives face the practical version of the problem when they decide how many risks deserve attention and what to do about each (Day and Dennis, 2022; Sheehan, 2020; Soleimani and Stauffer, 2026).")
add("p", "Two assumptions sit behind current practice. The first holds that firms exposed to several emerging risks at once are more fragile, because shocks that arrive together exhaust attention and slack (Ocasio, 1997; Bourgeois, 1981; Lawrence et al., 2024). The second holds that a firm which documents responses to the risks it discloses is better prepared (Nocco and Stulz, 2006; Hoyt and Liebenberg, 2011). Recent work supports versions of both. Pre-crisis disclosure of slack, learning and innovation capabilities in 10-K filings was associated with investor recognition of resilience during the pandemic (Neunsinger et al., 2026); among Chinese listed firms a closer match between disclosed risks and disclosed responses predicted better subsequent performance (Zhang et al., 2026). Text-based research has otherwise measured one risk at a time: political risk (Hassan et al., 2019), epidemic exposure (Hassan et al., 2023), climate exposure (Sautner et al., 2023; Wang and Li, 2026) or cyber risk (Florackis et al., 2022). Two questions remain open: whether the number and combination of disclosed risks still separate firms once nearly all firms list nearly all risks and whether the responses that classification rules find in annual reports are in fact responses to those risks.")
add("p", f"This study addresses both questions with {n0(O['filings'])} annual reports filed by a stratified random sample of {n0(O['sample_final'])} US non-financial firms between fiscal 2017 and 2025, linked to SEC financial statement data and to four public uncertainty indices. It asks how far emerging risks co-occur in disclosure, whether pre-shock convergence predicts losses and recovery in the pandemic and the 2022 shocks and whether firms whose documented actions cover their disclosed risks fare better. Hypotheses, measures and decision rules were committed to the project repository before outcomes were merged with text measures and all later changes are dated. Because the response measure carries the second assumption, it was rebuilt from a written coding manual and audited under four classification rules; the whole pipeline was also rerun from the raw filings to confirm every reported number.")
add("p", "The findings challenge both assumptions. Disclosure saturated. Breadth rose towards its ceiling, dispersion across firms fell under every way of counting risks and breadth carried no information about who fell furthest in either shock. Rule-based response measures mostly captured routine treasury, contracting and acquisition activity; responses explicitly tied to a disclosed threat were rare and did not protect performance. Realised sensitivity followed specific channels: geopolitical and supply-chain exposure moved revenue and cost together, macro-financial exposure lowered margins and combined exposure added nothing measurable. The paper contributes to strategic risk management and dynamic capabilities research by separating disclosed exposure, documented response and realised sensitivity and by showing which kinds of risk information remain useful once aggregate counts have saturated. It gives boards a four-stage diagnostic built on that distinction.")

# ---------------------------------------------------------------- theory
add("h1", "Disclosed exposure, documented response and realised sensitivity")
add("p", "Strategic management has long treated environmental uncertainty as a set of separable conditions to be judged one at a time, each with its own likely effect and response (Rindova and Courtney, 2020; Bundy et al., 2017; Dess and Beard, 1984). Enterprise risk management inherited that separability. Its frameworks ask firms to list risks, score each on likelihood and impact and aggregate the scores into a portfolio view (Nocco and Stulz, 2006; Bromiley et al., 2015; Andersen, 2008). Systemic-risk scholars argue that separability misses the defining feature of the current period, in which shocks interact through shared infrastructure, supply networks and policy responses (Helbing, 2013; Renn et al., 2019; Lawrence et al., 2024). Climate science uses the term compound events for hazards whose joint impact exceeds the sum of their parts (Zscheischler et al., 2018) and supply-network studies find that disruption travels through linked suppliers so that losses exceed the direct shock (Carvalho et al., 2021; Elliott et al., 2022; Baldwin and Freeman, 2022). Firm-level evidence on spillovers in the same period points the same way (Tao et al., 2026).")
add("p", "Dynamic capabilities theory explains why firms facing the same shocks perform differently. Firms sense threats and opportunities, seize them through investment and reconfigure assets as conditions change (Teece et al., 1997; Teece, 2007; Eisenhardt and Martin, 2000), with managerial cognition shaping each step (Helfat and Peteraf, 2015; Schilke et al., 2018). Strategic foresight specifies sensing: firms can act on weak signals before threats take full form; mature foresight practice predicts later profitability (Ansoff, 1975; Rohrbeck and Kum, 2018; Vecchiato, 2012). The attention-based view adds that what executives notice and write about shapes what the organisation does (Ocasio, 1997; Eggers and Kaplan, 2009; Nadkarni and Barr, 2008) and recent contributions to this journal describe the loop from signal to recalibrated decision and the selective reconfiguration it requires (Enang, 2026; Hussain, 2026; Huang, 2026). Organisational ambidexterity explains how firms protect current operations while exploring new positions (March, 1991; O'Reilly and Tushman, 2013; Raisch and Birkinshaw, 2008), which matters when several threats demand defence of the core and renewal at once. The data contain no valid measure of ambidexterity, so it serves here as an explanation and is not tested.")
add("p", "Three constructs follow from this view and much of the literature treats them as one. Disclosed exposure is the set of threats a firm states in its risk factors and how much it says about each; it is the public record of sensing. Documented response is a completed or ongoing action that the firm reports and ties to a named threat; it is the public record of seizing and reconfiguring. Realised sensitivity is the change in performance when a shock arrives through a given channel; it reflects both actual exposure and the capabilities the firm brought to the shock. Disclosed exposure can depart from actual exposure because risk reporting answers litigation, regulatory and lender incentives as well as economic risk (Cazier et al., 2020; Dai et al., 2024; Leuz and Wysocki, 2016) and documented response can depart from action because statements and practice are often decoupled (Meyer and Rowan, 1977; Westphal and Zajac, 2001; Bromley and Powell, 2012; Power, 2009).")
add("p", "These departures imply a saturation mechanism. When the cost of omitting a risk that later materialises exceeds the cost of listing it, each firm adds categories as peers and regulators draw attention to them, so the list ratchets upward (Campbell et al., 2014; Dyer et al., 2017; Hope et al., 2016). As counts approach their ceiling, the variation between firms that could carry information shrinks and repeated language grows (Lang and Stice-Lawrence, 2015; Cohen et al., 2020). Saturation need not remove all information. Which channels a firm emphasises, how intensely and how its emphasis changes from year to year can still reveal exposure and management attention (Kravet and Muslu, 2013; Muslu et al., 2015; Hirshleifer and Teoh, 2003). The theory therefore predicts that aggregate counts lose informational value first while channel-specific information keeps it. H1 tests whether convergence still carries information about losses, as the polycrisis argument implies.")
add("p", "Convergence should make each capability harder to exercise if it reflects real exposure. When several categories are material at once, executive attention is divided across more domains (Ocasio, 1997; Cho and Hambrick, 2006) and responses compete for the same slack (Bourgeois, 1981). Protection against one threat can raise exposure to another, as when a firm concentrates sourcing to cut cost and so becomes more exposed to trade and geopolitical disruption (Baldwin and Freeman, 2022; Ivanov and Dolgui, 2020). Resilience research shows that slack, prior practices and financial flexibility shape both the depth of the fall and the speed of recovery (Ortiz-de-Mandojana and Bansal, 2016; DesJardine et al., 2019; Fahlenbrach et al., 2021; Ding et al., 2021; de Waal et al., 2025).")
add("p", "H1. In a systemic shock, firms with greater pre-shock convergence of emerging risk exposures experience greater performance loss after accounting for the intensity of each risk category.")
add("p", "The dynamic capabilities view predicts that a firm which has acted on its disclosed threats will absorb a shock better than one which has only described them (Teece, 2007; Wenzel et al., 2021). The closest empirical construct is the alignment between disclosed risks and disclosed responses, which Zhang et al. (2026) relate to performance and which this study first labelled strategic risk-response alignment. Whether such alignment can be measured from US annual reports depends on whether sentences that look like responses describe actions taken because of the threat. The study therefore measures response coverage, the share of a firm's material risk categories for which its business description or management discussion reports a completed action. It tests coverage under classification rules of increasing strictness. Figure 1 summarises the model.")
add("p", "H2. In a systemic shock, firms with greater pre-shock response coverage experience smaller performance loss and stronger recovery.")
add("p", "H3. Response coverage weakens the association between pre-shock risk convergence and performance loss.")
add("figure", "one")

# ---------------------------------------------------------------- data and method
add("h1", "Data and method")
add("p", f"The sampling frame started from the {n0(O['frame_float_entities'])} entities that reported a 2018 public float in SEC XBRL data. Of these, {n0(O['frame_float_half_bn'])} reported a float of at least 0.5 billion US dollars. Excluding finance and real estate together with utilities and unclassified entities and requiring a 10-K for fiscal 2018 left {n0(O['frame_eligible'])} eligible firms. A proportional stratified random sample of {n0(O['sample_drawn'])} was drawn by SIC division with a fixed seed. Before estimation {O['validation_excluded']} sampled firms were removed because their reported public float was implausible for their size, because they report in Canadian dollars or because they are blank-check companies, leaving {n0(O['sample_final'])} firms. Firms were not required to survive to 2025, so the panel is unbalanced and keeps firms that were acquired or delisted. Table 1 lists the data sources and Table 2 the sample.")
add("table", "one")
add("p", f"Filings were retrieved from the SEC EDGAR submissions interface under its fair-access rules. For each firm and fiscal year from 2017 to 2025 the latest original 10-K was converted to text and Items 1, 1A and 7 were located by heading patterns; Item 1A was extracted from {pct(O['filings_item1a_ok_pct'])} and the management discussion from {pct(O['filings_item7_ok_pct'])} of the {n0(O['filings'])} filings. Financial data come from {n0(O['xbrl_fact_rows'])} XBRL fact rows, using values as first reported so that later restatements cannot leak into the analysis. The Geopolitical Risk index, the US economic and trade policy uncertainty indices, the World Uncertainty Index and the Global Supply Chain Pressure Index were downloaded from their publishers (Caldara and Iacoviello, 2022; Baker et al., 2016; Ahir et al., 2022; Benigno et al., 2022); a second download on 25 October 2026 returned byte-identical files for all {N['macro_version_check']['files']} series. Consumer and producer price indices came from the Bureau of Labor Statistics. To confirm the evidence base the full pipeline was rerun from the raw filings and financial facts at the commit of the first version: {n0(rep_match)} of {n0(rep_total)} reported quantities were reproduced {'exactly' if not rep_counts.get('match to rounding') else 'exactly or to rounding'}; a separate re-implementation of the sample draw, panel construction and principal regressions, written without the analysis code, matched all {N['independent_checks']['match']} values it checked.")
add("p", f"Each Item 1A sentence was assigned to any of nine categories using a dictionary of phrase patterns. The categories are geopolitical conflict, trade policy, regulatory change, cybersecurity, artificial intelligence and technology, supply chain, climate and environment, macro-financial instability and pandemic. A transparent dictionary was preferred to a trained classifier because its errors can be inspected sentence by sentence (Loughran and McDonald, 2011; Loughran and McDonald, 2016; Gentzkow et al., 2019). Across fiscal years mean geopolitical intensity tracked the Geopolitical Risk index (r = {O['tracking']['geopolitical']['r']:.2f}), trade intensity tracked trade policy uncertainty (r = {O['tracking']['trade']['r']:.2f}) and regulatory intensity tracked regulatory policy uncertainty (r = {O['tracking']['regulatory']['r']:.2f}), whereas supply-chain intensity did not fall back when supply pressure eased (r = {O['tracking']['supply']['r']:.2f}). Geopolitical, trade and macro-financial intensity rose with the foreign share of pre-tax income (Spearman correlations of {O['foreign_share_rho']['int_geopolitical']['rho']:.2f} to {O['foreign_share_rho']['int_macro']['rho']:.2f}, n = {O['foreign_share_n']}). An audit of classified sentences found low precision for some patterns. After one revision of the dictionary, pooled category precision on a fresh sample rose from {f2(O['audit_pooled_original'])} to {f2(O['audit_pooled_revised'])} (Table A1). A category is material for a firm-year when it accounts for at least three sentences. Convergence breadth counts material categories from zero to nine. Because breadth may reflect disclosure conventions it was compared with twelve alternatives (Table A3). Four change the count: one- and five-sentence thresholds, breadth counted only from sentences free of boilerplate (sentences without four-word sequences shared by 30 to 75 per cent of that year's filings, after Lang and Stice-Lawrence, 2015) and industry-adjusted breadth. Five describe the mix and links between categories: the total share of category sentences, an entropy-based diversity index, the number of linked category pairs, the share of sentences linking categories and the share stating that one category causes or worsens another. Three describe change and repetition: the turnover of material categories from the previous year, the number of newly material categories and the share of Item 1A text in boilerplate sentences.")
add("p", f"Documented response was measured from Items 1 and 7 under four rules. The original and revised rules of the first version flag a sentence when an organisational subject, a realised action verb and a category term occur together without conditional wording. High-confidence rules add the conditions of a written coding manual: an explicit link between the action and the threat, no future or aspirational wording, no standing treasury instruments and no descriptions of products sold to customers. The fourth rule is a zero-shot natural language inference model ({N['lm_version'].get('model', '')}) that scores whether a sentence states that the company has already acted to reduce or manage its exposure to the category (Yin et al., 2019; Laurer et al., 2024), applied with a fixed threshold of 0.5 to candidate sentences. The coding manual separates risk recognition, disclosure, anticipation, routine activity, reactive management, proactive adaptation and resource reconfiguration and counts a pair as a documented response only when the action is reactive or proactive, completed or ongoing and tied to the threat. A stratified sample of {N['validation_sample']['items']} sentence-category pairs drawn across rule strata and categories, {N['validation_sample']['divisions']} industry divisions and {N['validation_sample']['years']} fiscal years was coded against the manual. Design weights give population precision, recall and F1 with bootstrap intervals (Wilson, 1927). The reference labels were assigned by an AI assistant applying the manual. They are not independent human annotation. The coding sheets, manual and agreement code (Cohen, 1960; Hayes and Krippendorff, 2007) are released for two human coders.")
add("p", f"The hypotheses were tested in two shock episodes. In the pandemic episode severity is the log change in revenue from fiscal 2019 to fiscal 2020, margin change is the change in operating margin over the same years and recovery is the log ratio of fiscal 2022 to fiscal 2019 revenue; predictors come from the fiscal 2018 10-K, filed before the pandemic by every firm. In the 2022 episode outcomes compare fiscal 2022 and 2023 with fiscal 2021 and predictors come from the fiscal 2020 10-K. A placebo episode uses fiscal 2017 predictors and the fiscal 2018 to 2019 change, a period without a systemic shock. The models are ordinary least squares with two-digit SIC and fiscal year-end month fixed effects, controlling for the nine category intensities and for log assets, liabilities to assets, cash to assets, return on assets, prior two-year revenue growth and log Item 1A length. Errors are clustered by two-digit SIC. Because the {cl['clusters']} clusters are uneven (the largest holds {pct(100 * cl['largest_share'])} of firms and the effective number is about {cl['effective_clusters_herfindahl']:.0f}), the principal tests also report t({cl['clusters'] - 1}) reference p-values and restricted wild cluster bootstrap p-values from 4,999 draws (Cameron et al., 2008; MacKinnon and Webb, 2017; MacKinnon et al., 2023). The three pre-registered confirmatory tests on pandemic severity are adjusted with the Holm procedure and the exploratory tests with the Benjamini-Hochberg false discovery rate (Holm, 1979; Benjamini and Hochberg, 1995). Null results are read through confidence intervals and equivalence tests (Lakens, 2017).")
add("p", "A firm-year panel for fiscal 2019 to 2025 adds firm and year fixed effects with lagged predictors. Macro indices are common to all firms in a year, so their direct effects are absorbed by year effects; they enter only as interactions with each firm's fiscal 2018 category intensity, in the spirit of exposure-by-shift designs (Goldsmith-Pinkham et al., 2020; Borusyak et al., 2022). The shock models were re-estimated with indices measured at the fiscal year-end month, at their peak within the fiscal year and as year-on-year changes, with industry-by-year fixed effects and with errors clustered by industry. Revenue was deflated by the consumer price index. Cost of revenue, gross margin and inventory were added as outcomes to examine how revenue changes arose. None of these models identifies causal effects of disclosure. They test whether disclosed convergence and documented response carry information about subsequent performance.")


# ---------------------------------------------------------------- helpers for results
def ci(r):
    lo, hi = (r["ci_low_t"], r["ci_high_t"]) if r.get("ci_low_t") is not None else (r["ci_low"], r["ci_high"])
    return f"[{f3(lo)}, {f3(hi)}]"


def est(r, p_key="p"):
    return f"b = {f3(r['coef'])}, 95 per cent CI {ci(r)}, {pv(r[p_key])}"


def short(r):
    b = f"{r['coef']:.4f}".replace("-", MINUS) if abs(r["coef"]) < 0.0005 else f3(r["coef"])
    return f"b = {b}, {pv(r['p'])}"


def wilson_upper(k, n, z=1.96):
    ph = k / n
    return (ph + z * z / (2 * n) + z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def mtr(m, y):
    return MT(m, y)["cv"]


def det_r2(y, p):
    return DET(y, p)["r2"]


mp_ = O["material_pct"]
U = N["universe"]
vs_ = N["validation_sample"]
rem_n = vs_["strata"].get("other", 0)
rem_up = wilson_upper(0, rem_n) if rem_n else float("nan")
cand_total = sum(v for k, v in U.items() if k != "other")
rc = vs_["response_class"]
rc = {int(k): v for k, v in rc.items()}
hi_rv = lambda ep, y, t, m="High-confidence rules", mod="H3": RV(ep, m, mod, y, t)
sat = N["saturation"]
sb = {r["fiscal_year"]: r for r in N["below_ceiling"]}
me_rev_025 = ME("Revised rules", "severity", 0.25)
me_rev_0 = ME("Revised rules", "recovery", 0.0)
me_rev_050r = ME("Revised rules", "recovery", 0.5)
ii = lambda y, s: II(y, s)
pre_sev, pre_rec = ii("severity", "FY2019 text filed before 1 March 2020"), ii("recovery", "FY2019 text filed before 1 March 2020")
resp_sev, resp_rec = ii("severity", "Firms with any revised-rule response only"), ii("recovery", "Firms with any revised-rule response only")
nm_sev, nm_rec = ii("severity", "Excluding manufacturing"), ii("recovery", "Excluding manufacturing")
dist_rec, peer_sev = ii("recovery", "Excluding distressed firms (negative ROA or top-quintile leverage)"), ii("severity", "Control for peer severity")
ri3 = RI("recovery", "Three-digit SIC fixed effects")
rij = RI("recovery", "All of the above jointly")
risup = RIT("recovery", "Material-category indicators in place of breadth", "mat_supply")
nov = AC("A", "recovery", "Novelty (newly material categories)")
iab = AC("A", "recovery", "Industry-adjusted breadth")
nbp = AC("A", "recovery", "Breadth from non-boilerplate sentences")
alt_sev = [r for r in N["alternative_convergence"] if r["episode"] == "A" and r["outcome"] == "severity"]
alt_sev_minp = min(r["p"] for r in alt_sev)
alt_measures = len({r["measure"] for r in N["alternative_convergence"] if not r["measure"].startswith(("Joint", "Breadth, threshold three"))})
pa = {r["check"] + "|" + r["outcome"] + "|" + r["term"]: r for r in N["preregistered_added"]}
surv = N["survival_logit"]
geo_r, sup_r, mac_r = SH("rev_growth", "x_geopolitical"), SH("rev_growth", "x_supply"), SH("rev_growth", "x_macro")
geo_c, sup_c = SH("cost_growth", "x_geopolitical"), SH("cost_growth", "x_supply")
geo_g, sup_g = SH("d_gross_margin", "x_geopolitical"), SH("d_gross_margin", "x_supply")
sup_i = SH("inventory_growth", "x_supply")
mac_m = SH("d_op_margin", "x_macro")
mac_ri, mac_mi = SH("rev_growth", "x_macro", cluster="industry"), SH("d_op_margin", "x_macro", cluster="industry")
mac_ry = SH("rev_growth", "x_macro", effects="firm and industry-by-year")
geo_2w, sup_ind = SH("rev_growth", "x_geopolitical", cluster="two-way"), SH("rev_growth", "x_supply", cluster="industry")
real_geo = SH("real_growth", "x_geopolitical")
hc_any = 100 - 100 * RV("A", "High-confidence rules", "H2", "severity", "cv_z")["share_zero"]
hcB_any = 100 - 100 * RV("B", "High-confidence rules", "H2", "severity", "cv_z")["share_zero"]
hr_b = RV("B", "High-confidence with resource commitment", "H2", "severity", "cv_z")
rv_family = int(next(iter(N["response_variants"].values())).get("family_size") or 0)

# ---------------------------------------------------------------- results
add("h1", "Results")
add("p", f"Emerging risk disclosure converged steadily over the nine years (Figures 2 and 3). Mean breadth rose from {f2(bm['2017'])} categories in fiscal 2017 to {f2(bm['2025'])} in fiscal 2025 and the share of firms with all nine categories material rose from {pct(O['share_nine_pct']['2017'])} to {pct(O['share_nine_pct']['2025'])}. Geopolitical risk was material for {pct(mp_['geopolitical']['2017'])} of firms in fiscal 2017 and {pct(mp_['geopolitical']['2025'])} in fiscal 2025; trade policy rose from {pct(mp_['trade']['2017'])} to {pct(mp_['trade']['2025'])}. Dispersion across firms fell as the mean rose. The coefficient of variation of breadth fell from {f3(mtr('breadth', 2017))} to {f3(mtr('breadth', 2025))} and the decline appears under counts that are far from their ceiling: from {f3(mtr('breadth_t5', 2017))} to {f3(mtr('breadth_t5', 2025))} with a five-sentence threshold, from {f3(mtr('breadth_specific', 2017))} to {f3(mtr('breadth_specific', 2025))} when only sentences free of shared boilerplate are counted and from {f3(sb[2017]['cv'])} to {f3(sb[2025]['cv'])} among the {n0(sat['below_ceiling_firms'])} firms that never reached nine categories. Over the same years the share of Item 1A text in boilerplate sentences rose from {pct(100 * sat['boilerplate_share_mean']['2017'])} to {pct(100 * sat['boilerplate_share_mean']['2025'])}, while sentences linking two categories rose only from {pct(O['linkage_pct']['2017'], 2)} to {pct(O['linkage_pct']['2025'], 2)} of risk sentences. Breadth rose in every SIC division with at least 15 sampled firms (Figure 4).")
add("figure", "two")
add("figure", "three")
add("p", f"Breadth reflects reporting practice as much as exposure. Item 1A length alone explained {pct(100 * det_r2(2018, 'Item 1A length'))} of the variance in breadth in fiscal 2018 and {pct(100 * det_r2(2025, 'Item 1A length'))} in fiscal 2025, whereas firm size explained at most {pct(100 * max(det_r2(y, 'Firm size') for y in (2018, 2021, 2025)))} in the three years tested. Length, size and foreign income share together explained {pct(100 * det_r2(2018, 'Length, size and foreign share'))} in fiscal 2018 and {pct(100 * det_r2(2025, 'Length, size and foreign share'))} in fiscal 2025; adding two-digit industry raised the figures to {pct(100 * det_r2(2018, 'All including industry'))} and {pct(100 * det_r2(2025, 'All including industry'))}. More than half the variation in breadth is therefore unrelated to observable size, international exposure, industry or document length.")
add("figure", "four")
add("p", f"The validation of the response measures changed what the first version could claim (Table 3). Of {n0(cand_total + U.get('other', 0))} sentence-category pairs in the management discussion and business description of the sampled firms, {n0(cand_total)} were candidates flagged by a rule or close to one. Of the {vs_['items']} audited pairs, {rc.get(0, 0)} recorded no organisational action, {rc.get(1, 0)} described routine activity, {rc.get(4, 0)} stated plans, {rc.get(2, 0)} described reactive risk management and {rc.get(3, 0)} proactive adaptation; {vs_['qualifying']} met every condition for a documented response. The original rules reached a weighted precision of {f2(vo['precision_weighted'])} and the revised rules {f2(vr['precision_weighted'])}, so roughly three of every four sentences they counted were not responses to the threat. The main errors were sentences with no organisational action, categories that were not relevant to the sentence, products sold to customers and standing treasury instruments. The high-confidence rules reached a precision of {f2(vh['precision_weighted'])} with recall of {f2(vh['recall_weighted'])}; the language model reached precision of {f2(vl['precision_weighted'])} with recall of {f2(vl['recall_weighted'])} and the highest F1 ({f2(vl['f1_weighted'])}). Recall is measured within the candidate pairs. None of the {rem_n} audited pairs outside the candidates qualified, but with a Wilson upper bound of {pct(100 * rem_up)} the audit cannot rule out documented responses that no rule detects.")
add("table", "three")
add("p", f"Measured strictly, documented response was rare before the pandemic. In fiscal 2018 {pct(ar['revised']['2018'])} of firms reported at least one response under the revised rules but only {pct(ar['high']['2018'])} under the high-confidence rules" + (f" and {pct(ar['lm']['2018'])} under the language model" if 'lm' in ar else "") + f". By fiscal 2020 the high-confidence share had risen to {pct(ar['high']['2020'])}, almost entirely through pandemic responses; it stood at {pct(ar['high']['2025'])} in fiscal 2025. The response variable used in H2 and H3 therefore has little variation in the pandemic test: {pct(100 - hc_any)} of firms have zero high-confidence coverage in fiscal 2018.")
add("p", f"H1 is not supported (Table 4 and Figure 5). In the pandemic episode a one standard deviation increase in fiscal 2018 breadth was associated with a change in fiscal 2020 revenue of {est(sev1)}; the wild bootstrap p-value is {sev1['p_wild']:.3f} and the Holm-adjusted p-value {sev1['p_holm']:.3f}. The interval rules out a fall in revenue of more than {ppt(abs(sev1['ci_low_t']))} per cent per standard deviation, which is small beside the standard deviation of the outcome ({f3(sev1['sd_y'])} log points). Breadth was also unrelated to the change in operating margin ({short(mar1)}). None of the {alt_measures} alternative convergence measures predicted the pandemic revenue fall; the smallest p-value among them was {alt_sev_minp:.3f}. Breadth did not predict which firms were still filing in fiscal 2022 (logit {pv(surv['p']['breadth_z'])}); the estimate barely moved when the sample was limited to survivors or reweighted for attrition ({short(pa['Survivors to FY2022 only|severity|breadth_z'])}; {short(pa['Inverse-probability attrition weights|severity|breadth_z'])}). In the placebo period from fiscal 2018 to 2019 breadth was not associated with revenue change at conventional levels ({short(pls)}).")
add("p", f"The 2022 episode gives the same answer. Breadth in fiscal 2020 was unrelated to the change in operating margin in fiscal 2022 ({short(b1)}) and to revenue growth from fiscal 2021 to 2023 ({short(b3)}). The association with the fiscal 2023 margin change ({est(b2)}) is the only H1 estimate in this episode with a conventional p-value below 0.05. It does not survive the wild bootstrap (p = {b2['p_wild']:.3f}) or the false discovery rate adjustment (q = {b2['q_bh']:.2f}). It reappears with the five-sentence threshold ({short(AC('B', 'margin_change_two', 'Breadth, threshold five'))}) but not with the one-sentence threshold ({short(AC('B', 'margin_change_two', 'Breadth, threshold one'))}) or the non-boilerplate count ({short(AC('B', 'margin_change_two', 'Breadth from non-boilerplate sentences'))}) (Table A3). It is reported as unconfirmed.")
add("table", "four")
add("figure", "five")
add("p", f"One exploratory association runs against the polycrisis argument. Firms with greater fiscal 2018 breadth recovered more revenue by fiscal 2022 ({est(rec1)}; wild bootstrap p = {rec1['p_wild']:.3f}; q = {rec1['q_bh']:.3f}). Table 5 shows why it should not be read as evidence that wider disclosure aids recovery. With three-digit industry fixed effects the estimate falls to {f3(ri3['coef'])} (p = {ri3['p']:.3f}) and with all alternative explanations entered together (peer recovery, peer pandemic severity, geographic and acquisition-based diversification, business scope, reporting length, market position, strategic flexibility and prior pandemic disclosure) it falls to {f3(rij['coef'])} (p = {rij['p']:.3f}; wild bootstrap p = {rij['p_wild']:.3f}). When each category enters separately only supply-chain materiality is associated with recovery ({short(risup)}). Among the alternative measures only industry-adjusted breadth ({short(iab)}) and the number of newly material categories ({short(nov)}) carry a similar association; breadth counted from non-boilerplate sentences does not ({short(nbp)}). The association is better explained by finer industry composition and supply-chain exposure than by the number of risks disclosed.")
add("table", "five")

# H2
h2m = [("original rules", "Original rules"), ("revised rules", "Revised rules"), ("high-confidence rules", "High-confidence rules")] + \
      ([("language model", LMNAME)] if HAS_LM else [])
h2_txt = "; ".join(f"{lab} {short(RV('A', m, 'H2', 'severity', 'cv_z'))}" for lab, m in h2m)
h2r_txt = "; ".join(f"{lab} {short(RV('A', m, 'H2', 'recovery', 'cv_z'))}" for lab, m in h2m)
h2_all = [RV(ep, m, "H2", y, "cv_z") for ep, ys in (("A", ["severity", "margin_change", "recovery"]), ("B", ["margin_change", "margin_change_two", "severity"]))
          for _, m in h2m for y in ys]
h2_sig = [r for r in h2_all if r["p"] < 0.05]
add("p", f"H2 is not supported under any response measure. Coverage measured in fiscal 2018 was unrelated to the pandemic revenue fall ({h2_txt}) and to recovery ({h2r_txt}). " + (f"None of the {len(h2_all)} H2 estimates across measures, outcomes and the two episodes had a p-value below 0.05." if not h2_sig else f"Of the {len(h2_all)} H2 estimates across measures, outcomes and the two episodes, {len(h2_sig)} had a p-value below 0.05" + ("; none survived the false discovery rate adjustment." if all((r.get('q_bh') or 1) >= 0.05 for r in h2_sig) else ".")) + f" The one coverage measure that requires a stated resource commitment had non-zero values for too few firms in fiscal 2018 to be estimated in the pandemic episode; in the 2022 episode it was associated with higher revenue growth from fiscal 2021 to 2023 ({short(hr_b)}, q = {hr_b['q_bh']:.2f}). Within categories, firms that documented a high-confidence pandemic response by fiscal 2020 had higher revenue growth from fiscal 2021 to 2023 than other firms for which pandemic risk was material, but the estimate is imprecise ({short(next(r for r in N['category_response'] if r['episode'] == 'B' and r['category'] == 'pandemic' and r['rule'] == 'high-confidence' and r['outcome'] == 'severity'))}).")

# H3
h3_hi_s, h3_hi_r = RV("A", "High-confidence rules", "H3", "severity", "bxcv"), RV("A", "High-confidence rules", "H3", "recovery", "bxcv")
h3_lm = (RV("A", LMNAME, "H3", "severity", "bxcv"), RV("A", LMNAME, "H3", "recovery", "bxcv")) if HAS_LM else None
add("p", f"H3 predicted that coverage would weaken the association between breadth and loss. The confirmatory estimate has the opposite sign: among firms with higher revised-rule coverage, breadth was associated with a larger pandemic revenue fall ({est(sev3)}; wild bootstrap p = {sev3['p_wild']:.3f}; Holm-adjusted p = {sev3['p_holm']:.3f}); the same pattern appears for recovery ({short(rec3)}; q = {rec3['q_bh']:.3f}). The marginal effects show where the interaction comes from. At zero coverage, which describes {pct(100 * ME('Revised rules', 'severity', 0.0)['share_at_or_below'])} of firms, breadth was unrelated to the revenue fall and positively associated with recovery (b = {f3(me_rev_0['effect'])}, {pv(me_rev_0['p'])}). The negative association appears only at a coverage of one quarter or more ({f3(me_rev_025['effect'])} at 0.25), a level that {pct(100 * (1 - me_rev_025['share_at_or_below']))} of firms exceeded.")
anyh_s, anyh_r = RV("A", "Any high-confidence response (indicator)", "H3", "severity", "bxanyh"), RV("A", "Any high-confidence response (indicator)", "H3", "recovery", "bxanyh")
anyh_firms = int(round((1 - anyh_s["share_zero"]) * anyh_s["n"]))
add("p", f"Table 5 asks whether the interaction reflects response at all. Among the firms with any revised-rule response it vanished for both the revenue fall ({short(resp_sev)}) and recovery ({short(resp_rec)}). The recovery interaction was confined to manufacturing ({short(nm_rec)} outside it), while the severity interaction outside manufacturing had a similar size but was imprecise ({short(nm_sev)}). With predictors taken from fiscal 2019 reports filed before 1 March 2020 the recovery interaction fell to {f3(pre_rec['coef'])} (p = {pre_rec['p']:.2f}) and the severity interaction to {f3(pre_sev['coef'])} (p = {pre_sev['p']:.2f}). In the placebo period without a systemic shock the interaction was small ({short(PL('H3', 'severity', 'bxc'))}). It persisted when distressed firms were excluded ({short(dist_rec)} for recovery) and when peer severity was controlled ({short(peer_sev)} for severity). The more accurate measures point the same way with less precision. The high-confidence severity interaction was {f3(h3_hi_s['coef'])} (p = {h3_hi_s['p']:.3f}) and the recovery interaction {f3(h3_hi_r['coef'])} (p = {h3_hi_r['p']:.3f})" + (f"; under the language model they were {f3(h3_lm[0]['coef'])} (p = {h3_lm[0]['p']:.3f}) and {f3(h3_lm[1]['coef'])} (p = {h3_lm[1]['p']:.3f})" if h3_lm else "") + f". For the {anyh_firms} firms with any high-confidence response in fiscal 2018 the interaction with breadth was {f3(anyh_s['coef'])} for severity (p = {anyh_s['p']:.3f}) and {f3(anyh_r['coef'])} for recovery (p = {anyh_r['p']:.3f}).")
add("p", "No measure shows documented response weakening the link between breadth and loss. The opposite pattern is fragile because it rests on few firms, disappears within responders and changes with the reporting year. A plausible explanation that the data cannot test is that firms documenting responses before the pandemic were those whose threats had already materialised. A documented response would then mark realised exposure more than protection.")

# shocks
add("p", f"The firm-year panel shows where realised sensitivity came from (Table 6). In years of high geopolitical risk, firms with greater fiscal 2018 geopolitical intensity had higher nominal revenue growth ({short(geo_r)} per standard deviation of both exposure and index) and higher cost-of-revenue growth ({short(geo_c)}), with no change in gross margin ({short(geo_g)}). Supply-chain exposure in years of high supply-chain pressure shows the same pattern for revenue ({short(sup_r)}) and cost ({short(sup_c)}), with faster inventory growth ({short(sup_i)}). These high-index years were also years of high inflation. The pattern is consistent with exposed firms passing higher input costs into prices. The data contain no firm-level prices, so pass-through is a plausible explanation that the study does not test. Deflating revenue by the consumer price index cannot separate price from volume because a common deflator is absorbed by the year effects ({short(real_geo)} for real growth).")
add("p", f"Macro-financial exposure is the only channel associated with lower performance. In years of high US policy uncertainty, firms with greater macro-financial intensity had lower revenue growth ({short(mac_r)}) and lower operating-margin change ({short(mac_m)}). The association remained with industry-by-year fixed effects ({short(mac_ry)}) but not with errors clustered by industry ({short(mac_ri)} for revenue; {short(mac_mi)} for margin). The geopolitical association lost conventional significance under two-way clustering ({short(geo_2w)}) and the supply-chain association under industry clustering ({short(sup_ind)}). Combined exposure added nothing measurable. The interaction between breadth and the number of indices at high levels was {f3(cg['coef'])} for revenue growth, with a 95 per cent interval of [{f3(cg['ci95'][0])}, {f3(cg['ci95'][1])}] that excludes the smallest single-channel effect in the model ({f3(cg['bound_smallest_significant_single_effect'])}; equivalence test {pv(cg['tost_p'])}); for operating margin the interval was [{f3(cm['ci95'][0])}, {f3(cm['ci95'][1])}] against a bound of {f3(cm['bound_smallest_significant_single_effect'])} ({pv(cm['tost_p'])}).")
add("table", "six")

# cases
CASES = json.loads((HERE.parent / "Results" / "Illustrative Cases.json").read_text())
cs = {c["name"]: c for c in CASES}
ford, gm, cat, mpc = cs["Ford Motor Co"], cs["GENERAL MOTORS COMPANY"], cs["CATERPILLAR INC"], cs["Marathon Petroleum Corporation"]
chg = lambda x: f"{100 * (math.exp(x) - 1):.1f}".replace("-", MINUS)
add("p", f"Table 7 sets the statistical results beside eight large firms chosen by rule from the pandemic episode. Firms with similar breadth fared very differently. Ford Motor disclosed {ford['breadth']} material categories and lost {chg(ford['severity']).lstrip(MINUS)} per cent of revenue in fiscal 2020; General Motors disclosed {gm['breadth']} and lost {chg(gm['severity']).lstrip(MINUS)} per cent. Every action that the first version counted as a documented response for these firms was routine under the coding manual. Marathon Petroleum's counted actions were the transfer of logistics assets to its affiliate and lower crude acquisition costs; Caterpillar's included its standing currency hedging programme; neither firm had a high-confidence response in fiscal 2018. Marathon Petroleum lost {chg(mpc['severity']).lstrip(MINUS)} per cent of revenue and Caterpillar {chg(cat['severity']).lstrip(MINUS)} per cent. The cases illustrate the two central findings: the number of disclosed risks did not separate firms facing the same shock and the activity that rules record as response was largely the ordinary conduct of the business.")
add("table", "seven")

# ---------------------------------------------------------------- discussion
add("h1", "Discussion")
add("p", f"The study set out to test two assumptions behind current risk practice. The first, that firms disclosing more converging risks are more fragile, finds no support in either shock. The evidence is consistent with disclosure saturation. Risk lists grew towards their ceiling and became more alike under every way of counting categories, boilerplate grew faster than firm-specific text and the remaining variation in breadth followed document length and industry more than size or international exposure. Breadth then carried no information about who lost most in either shock; the interval for the pandemic estimate excludes effects of a size that would matter to a board. This extends work on the informativeness of risk factors (Campbell et al., 2014; Hope et al., 2016; Dyer et al., 2017) by showing that the aggregate count loses its information as disclosure saturates while channel-specific intensity keeps it. The panel models show that geopolitical, supply-chain and macro-financial intensity each tracked realised sensitivity in the years when its index was high.")
add("p", "The second assumption, that documented response indicates preparedness, depends on a measurement problem that the validation exposed. Rules that pair an organisational subject, an action verb and a risk term mostly record routine activity: acquisitions, hedging programmes, supply contracts and products sold to customers. Once the coding manual's conditions were applied, responses explicitly tied to a disclosed threat were rare before the pandemic and did not protect performance under any of the four measures. Two readings remain open. Firms may act on threats without writing about the action in the business description or management discussion, so the filings understate response. Statements and practice may also be decoupled in the other direction (Meyer and Rowan, 1977; Westphal and Zajac, 2001; Bromley and Powell, 2012). The data cannot separate these readings; either one implies that annual-report text is a weak basis for measuring seizing and reconfiguring.")
add("p", "Zhang et al. (2026) found that closer coordination between the risks and the response measures that Chinese A-share firms reported from 2014 to 2023 predicted better subsequent performance, through lower financing constraints and greater institutional attention. Three differences may explain why the result does not carry over. Their measure takes the reported responses as given, whereas this study audited the sentences that rules classify as responses and found that most described routine activity. Their outcome is performance in ordinary years, which can reflect how investors read the disclosure, whereas this study asks whether responses absorbed two systemic shocks. The disclosure regimes and markets also differ. The two studies agree that the match between threat and action is the construct of interest; they differ on whether the text of US annual reports measures it.")
add("p", "For dynamic capabilities research the results separate three things that are often treated as one (Teece, 2007; Schilke et al., 2018). Disclosed exposure records sensing, but once disclosure saturates the record says more about reporting incentives than about the firm's attention (Ocasio, 1997; Eggers and Kaplan, 2009). Documented response is meant to record seizing and reconfiguring, but the filings record little of either. Realised sensitivity, estimated channel by channel, carries the information about exposure that the aggregate counts lost. Ambidexterity offers one explanation of why firms with similar disclosure fared differently, since protecting the core while repositioning requires separate structures or leadership attention (O'Reilly and Tushman, 2013; Raisch and Birkinshaw, 2008), but the filings contain no measure of it and the study does not test it. Researchers who build capability measures from annual reports should validate them against coded samples before testing performance effects and should report precision and recall alongside the estimates.")

# ---------------------------------------------------------------- implications
add("h1", "Implications for boards and executive teams")
add("p", f"Boards receive risk lists that now look alike across firms. The evidence here suggests that the length of the list says little about how much a firm stands to lose. Table 8 and Figure 6 turn the findings into a four-stage diagnostic for the annual risk review. Identify separates the threats specific to the firm from the boilerplate that peers share; a director can ask which Item 1A paragraphs changed this year and why. Quantify attaches each threat to the channel through which it would reach the accounts. The panel results suggest that geopolitical and supply-chain shocks moved revenue and cost together while macro-financial uncertainty reduced operating margin, so the board needs the revenue, cost and asset share exposed in each channel and an estimate of the firm's ability to pass costs into prices. Scenario work that combines two or three named channels serves this stage better than a register that lists everything (Schoemaker, 2022; Mortlock and Osiyevskyy, 2023; Calandro, 2020).")
add("p", "Respond records completed actions tied to a named threat, with the resources committed and an accountable owner. The validation shows how easily routine activity is mistaken for response, so the register should state which threat each action addresses, what changed and when. Validate compares realised revenue and margin changes in the last shock with the channel estimates and revises the first three stages. A chief risk officer can run the diagnostic within the existing annual cycle using segment data, supplier and contract records and the variance analysis that finance already prepares. The study's own measures suggest a test for the board: if the firm's risk factors would read the same with a competitor's name on them, they record compliance rather than exposure.")
add("table", "eight")
add("figure", "six")

# ---------------------------------------------------------------- limitations
add("h1", "Limitations")
add("p", f"Several limitations qualify these conclusions. The reference labels for the response validation and the dictionary audit were assigned by an AI assistant applying the written manual. They are not independent human annotation. The precision and recall figures should be treated as provisional until two human coders have coded the released sample and agreement has been reported. Recall is estimated within candidate sentences, so responses phrased in ways no rule detects would be missed. The language model was applied without training on this corpus and its errors may differ by category and year. Disclosure measures what firms choose to report and Item 1A answers legal as well as economic incentives, so disclosed exposure may differ from actual exposure. Outcomes are nominal accounting figures; revenue changes mix price and volume and the pass-through explanation for the channel results is untested.")
add("p", f"The sample covers {n0(O['sample_final'])} large US non-financial firms, so the results may not hold for smaller firms or for jurisdictions with prescribed response disclosure. Inference rests on {cl['clusters']} industry clusters of uneven size; the wild bootstrap and t references address this, but the macro-financial channel loses statistical significance when errors are clustered by industry. The study tests associations between disclosure and later performance and identifies no causal effect of disclosure or response. The pandemic was a single shock with sector-specific effects and the 2022 episode overlaps with recovery from it.")

# ---------------------------------------------------------------- conclusion
add("h1", "Conclusion")
add("p", f"US firms now disclose almost every emerging risk as material. The number they list no longer identifies which firms lose most when shocks arrive. Measured carefully, responses tied to a disclosed threat were rare in annual reports before the pandemic and none of the response measures protected performance. What remains informative is channel-specific: the intensity of geopolitical, supply-chain and macro-financial exposure tracked realised sensitivity in the years those shocks were strong. Risk practice should therefore move from counting risks to estimating channels and recording completed actions. The most useful next step for research is human double-coding of the released response sample, followed by tests of response measures built from internal action registers rather than public text.")

ABSTRACT = ABSTRACT_FN()
