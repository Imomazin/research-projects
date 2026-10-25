# Analysis plan

This plan was committed to the research branch before any outcome variable was merged with the text measures. The Git commit that adds it is the time stamp. Any later deviation is recorded in the deviations section at the end with its reason.

## Research questions

How far do the emerging strategic risks that US firms disclose co-occur and become linked within the same disclosure, and how has this changed between fiscal years 2017 and 2025? Is greater pre-shock convergence of disclosed risk exposure associated with weaker performance during and after systemic shocks, beyond the separate effect of each risk category? Do firms whose documented actions cover the risks they disclose fare better, and does that coverage weaken any convergence penalty?

## Constructs and operational definitions

Risk exposure is measured from Item 1A of each 10-K. Each sentence is assigned to any of nine categories (geopolitical, trade policy, regulatory change, cybersecurity, artificial intelligence and technological disruption, supply chain, climate and environment, macro-financial and pandemic) using the frozen dictionary in Risk Taxonomy Dictionary.json. Category intensity is the share of Item 1A sentences assigned to the category.

A category is treated as material for a firm-year when it accounts for at least three Item 1A sentences. Convergence breadth is the number of material categories (zero to nine). Linkage density is the share of Item 1A sentences that name two or three categories; sentences naming four or more categories are classed as hazard catalogues and excluded from linkage density because they typically list generic perils. Diversity is the exponential of the Shannon entropy of the category sentence counts.

Documented response is measured from Items 1 and 7. A response sentence names a category, has an organisational first-person subject, contains a realised action verb and contains no conditional modal. Response coverage is the share of a firm-year's material categories with at least one response sentence. Profile alignment is the cosine similarity between the vector of Item 1A category sentence counts and the vector of response sentence counts. Resource reconfiguration is measured separately from XBRL facts as capital expenditure, research and development and acquisition outlays scaled by lagged total assets.

Disclosure updating is one minus the cosine similarity of the Item 1A term-frequency vector with the firm's previous Item 1A.

## Outcomes

Accounting outcomes come from SEC XBRL company facts, using as-first-reported annual values to avoid look-ahead from restatements. Fiscal years follow the Compustat convention (years ending January to May belong to the prior year).

Episode A (pandemic shock): revenue severity is ln(revenue FY2020 / revenue FY2019); operating-margin change is the FY2020 operating margin minus the FY2019 operating margin in percentage points; recovery is ln(revenue FY2022 / revenue FY2019) and an indicator that FY2021 revenue regained the FY2019 level. Predictors come from the FY2018 10-K, which every sample firm filed before 2020.

Episode B (2022 compound shock of war, inflation, rate rises and supply pressure): operating-margin change FY2022 and FY2023 relative to FY2021 and ln(revenue FY2023 / revenue FY2021). Predictors come from the FY2020 10-K, filed before February 2022 for December year-end firms.

Panel: firm-years with outcomes from FY2019 to FY2025, predictors from the 10-K of the previous fiscal year. Outcomes are revenue growth, change in operating margin and an adverse-performance indicator (revenue decline of at least ten percent or an operating-margin fall of at least five percentage points).

Continuous outcomes and ratios are winsorised at the 1st and 99th percentiles of the pooled distribution.

## Hypotheses

H1. In each shock episode, higher pre-shock convergence breadth is associated with greater severity (lower revenue growth and larger margin decline) after controlling for the intensity of each category.

H2. Higher pre-shock response coverage is associated with lower severity and stronger recovery.

H3. Response coverage weakens the association between convergence breadth and severity (positive breadth × coverage interaction for revenue severity).

Organisational ambidexterity is retained as a theoretical mechanism. It is not tested because no reliable firm-level measure is available in these data.

Exploratory analyses, reported as such: linkage density conditional on breadth (sign not predicted, because linkage may reflect either entangled exposure or better interpretation); disclosure updating as a sensing indicator; resource reconfiguration; panel interactions between predetermined category exposure (FY2018) and the matching macro index (geopolitical with the Geopolitical Risk index, supply chain with the Global Supply Chain Pressure Index, trade and regulatory with economic and trade policy uncertainty, pandemic with fiscal year 2020).

## Models

Episode models are cross-sectional OLS with two-digit SIC fixed effects, controls for ln total assets, leverage, cash to assets, prior return on assets, prior two-year revenue growth, ln Item 1A word count and fiscal year-end month. Standard errors are clustered by two-digit SIC; heteroskedasticity-robust (HC3) errors are reported as a check.

Panel models use firm fixed effects and year fixed effects (industry-by-year fixed effects as a check), the same controls lagged one year, and standard errors clustered by firm. Macro indices are entered only as interactions with predetermined firm exposure because their main effects are absorbed by year fixed effects.

Predictive check: models fitted on outcome years up to FY2022 are evaluated on FY2023 to FY2025, comparing a controls-only baseline with the addition of the convergence and response measures (out-of-sample R squared and, for the adverse indicator, area under the ROC curve).

## Decision rules

A hypothesis is supported when the primary coefficient has the predicted sign with p below 0.05 in the primary specification (Episode A revenue severity for H1 to H3) and keeps its sign in most pre-listed robustness checks. Results for every outcome and episode are reported whether or not they support the hypotheses. No hypothesis is reworded after the results are seen.

## Robustness checks fixed in advance

Alternative materiality threshold (one and five sentences); continuous intensities without thresholds; diversity in place of breadth; excluding hazard-catalogue sentences from all counts; FY2019 predictors restricted to 10-Ks filed before 1 March 2020; December year-end firms only; excluding firms with Item 1A shorter than 1,000 words; unwinsorised outcomes; dropping each industry division in turn; survivors-only and attrition-weighted samples.

## Deviations

None were recorded at the time of commit. The following were made afterwards, each for the reason given. None changes a hypothesis, an outcome definition or the primary specification.

Data construction (made while building the panel and before the first estimation). Total revenue is the largest revenue concept reported for the fiscal year, because some filers tag only part of revenue with the ASC 606 contract-revenue concept (Archer-Daniels-Midland reports 27.6 billion US dollars under that concept for fiscal 2022 against total revenue of 101.6 billion). Total liabilities are computed as assets minus equity where the total is not tagged, which applies to 2,358 firm-years. Operating income is computed as revenue minus total costs and expenses where it is not tagged (349 firm-years). Thirteen sampled firms were excluded before estimation because their XBRL public float was implausible for their size (more than twenty times the larger of fiscal 2018 assets and revenue, with both below 100 million US dollars), because they report in Canadian dollars or because they are blank-check companies; Frame Validation Exclusions.csv lists them.

Inference check. Heteroskedasticity-consistent HC1 errors replace HC3 as the secondary check because single-firm industry cells give HC3 leverage values of one, which returned p-values of exactly one.

Measurement revision (made after the first estimation). The updating measure was recomputed on content words with stop words removed because the original term vectors were dominated by function words and compressed the measure near zero. An AI-assisted precision audit of 520 dictionary-classified sentences, run after the first estimation, found low precision for geopolitical risk (bare 'sanctions' matched legal penalties), supply-chain risk (bare 'supplier' matched compliance and contracting text), climate (ESG investor-attention language) and documented responses (negations, self-descriptions and passive observations). The dictionary was revised once to remove those patterns. Results are reported with the revised dictionary and, as a robustness check, with the frozen original dictionary (Risk Taxonomy Dictionary Original.json). The revised dictionary was audited on a fresh sample drawn with a different random seed.

Additional checks. The robustness grid was extended from Episode A severity to every episode outcome on which breadth showed an association, with an added restriction to firms with base-year revenue of at least 100 million US dollars because operating-margin changes for very small revenue bases reach several hundred percentage points. The shock-exposure models add an industry-by-year fixed-effects check. The dispersion of breadth across firms by year was added after the null results, as an exploratory explanation, and is reported as exploratory.
