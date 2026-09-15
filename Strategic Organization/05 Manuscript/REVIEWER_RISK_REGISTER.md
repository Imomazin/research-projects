# Reviewer Risk Register

Audited against repository commit bb0acd6 on 15 September 2026. Numbers come from 04 Analysis/Statistical Modeling unless another source is named. S1 to S11 refer to the checks in 04 Analysis/Supplementary Checks/supplementary-checks.py.

| Risk | Claim at stake | Settled by |
|---|---|---|
| Domain scores may not share a metric | The 16.63-point asymmetry | Instrument documentation and S1 |
| A low-scoring tail drives the correlations | One-factor result, alphas and sorting | S2 to S5 and completion records |
| Two occupations carry the exposure contrast | Every exposure estimate and its inference | S6 to S8 and S10 |
| Medium-confidence mappings move people across the exposure line | The adjusted null | S9 |
| Table 4 repeats one comparison | Presentation of the adjusted null | Drafting |
| The robustness record is described as stable | Robustness paragraph | Drafting |
| Career interest is aspirational | Scope of exposure claims | Drafting |
| Exposure is an occupation-level task measure | Construct definitions | Drafting |
| Sample coverage and missing demographics | Generalisation and controls | Table 1 |
| Data provenance, ethics and related work | Eligibility for submission | Author input |
| Outputs that identify participants | Data availability statement | Governance |
| Figures and exemplar calibration | Presentation | Redraw after S1 to S5 |

## Domain scores may not share a metric

Challenge: a reviewer can argue that the gap reflects how the two domains are scored rather than what participants can do.

Evidence: No participant reached 90 on the AI/data index, whose maximum was 88.5, while 53.0% reached 90 on the conventional index. Between 5.6% and 20.7% of participants scored exactly 100 on each conventional dimension and nobody scored 100 on any AI/data dimension, where the highest single score was 98.0. The gap was positive for all but one or two participants [Wilcoxon W = 4]. The repository holds no description of the assessment items, response formats or scoring rules.

Response: Methods must describe the instrument and state whether both domains are scored against the same proficiency standard. If they are not, the asymmetry becomes a within-instrument profile and the paper should drop language about weaker AI/data capability. Report the gap in raw points first. Treat dz = 2.81 as secondary because it is large mainly through the small spread of the gap [SD 5.91].

## A low-scoring tail drives the correlations

Challenge: the one-factor structure, the high alphas and part of the sorting difference may rest on a small group of very low scores.

Evidence: The Pearson correlation between the indices was .919 and the Spearman correlation was .835. The gap correlated +.167 with AI/data capability under Pearson and −.128 under Spearman. Dimension minima between 0 and 5.7 and index minima of 2.22 and 0.58 sit far below the index medians of 90.8 and 72.7. The Minimal exposure group [n = 9] had a conventional SD of 29.58 against 9.32 and 10.34 in Gradients 4 and 3. The figure_04 scatter places most low scores in the low-exposure group. Removing the single baseline-zero case lowered R² in the adjusted model from .844 to .816. The observed correlation also exceeds the ceiling implied by the two alphas [.919 against .914], which puts the disattenuated correlation at 1.006 and leaves the gap with little reliable individual variance on these Pearson-based figures.

Response: Fix the rule for identifying implausibly low assessments before interpreting results, preferably from completion records held by the assessment owner. Report the psychometrics and core models under that rule and add group medians to Table 3. If sorting weakens after screening, the paper should present it as conditional on that rule.

## Two occupations carry the exposure contrast

Challenge: the high-versus-low comparison is close to a comparison of occupational fields. Its 19 nominal clusters also overstate the information available for inference.

Evidence: Web and multimedia developers [2513, n = 57] and software developers [2512, n = 52] account for 109 of the 125 high-exposure participants. The low-exposure group is led by graphic and multimedia designers [2166, n = 21], management and organization analysts [2421, n = 20] and systems analysts [2511, n = 17]. Eleven of the 19 clusters hold one or two participants. The Kish effective number of clusters is 5.4. The Carter, Schnepel and Steigerwald (2017) measure for the unadjusted exposure coefficient is 4.1 under perfect within-cluster correlation and 7.1 under none, so CR1 intervals with 18 degrees of freedom can be too narrow (MacKinnon and Webb, 2017; MacKinnon, Nielsen and Webb, 2023). Frontend and full-stack interests reach Gradient 4 through 2513 while backend interests sit in Gradient 3 through 2512, which makes the split between the two high gradients a split between kinds of development work.

Response: Describe the contrast as participants targeting software and web development against participants targeting design, business analysis and data analysis roles. Base exposure inference on wild cluster restricted bootstrap intervals with Webb weights and report occupation-level randomisation inference beside them. Add the comparison within ICT professional occupations [2511 and 2529 against 2512, 2513 and 2514; n = 131 across five occupations] as a boundary check with descriptive standard errors. Any statement that the data rule out a relative advantage above a given size should rest on the bootstrap interval.

## Medium-confidence mappings move people across the exposure line

Challenge: plausible alternative codes for a few career-interest labels change who counts as high exposure.

Evidence: Of the 198 mappings, 53 are Medium or Low confidence. Data analysis, data analyst and data science interests [15 participants] are coded 2511 Systems analysts in Gradient 2, which the crosswalk justifies as ESCO-aligned, while 2120 Mathematicians, actuaries and statisticians and 3314 Statistical, mathematical and related associate professionals both sit in Gradient 3 of the ILO 2025 scores. UX/UI design interests [17] are coded 2166 in Gradient 2 with 2513 in Gradient 4 as an alternative. Social media interests [8] are coded 2431 in Gradient 3 with 2432 Public relations professionals in Gradient 2 as an alternative. Project management [4] is coded 2422 Policy administration professionals on the basis of one national implementation. Technical writing [2] is coded 2642 Journalists although the ISCO-08 definition of 2641 Authors and related writers lists technical writers among its examples; both codes are Gradient 3. Several mapping sources are Wikidata entries or a commercial careers site. Restricting the adjusted model to High-confidence mappings moved the exposure coefficient from 0.11 to 1.89 [95% CI −1.11 to 4.88, n = 145].

Response: Add a mapping sensitivity table to the supplement. Recode technical writing to 2641, document a defensible basis for project management and cite ESCO or the ILO ISCO-08 documentation for every code.

## Table 4 repeats one comparison

Evidence: In analysis_pipeline.py the adjusted gap model is the adjusted AI/data model with the sign reversed on the exposure term [0.11 and −0.11 with p = .921 in both]. The residual model residualises only the outcome, so its coefficient of 0.10 is the adjusted coefficient shrunk by the share of exposure variance that conventional capability explains.

Response: Report the unadjusted and adjusted AI/data models in Table 4 with the unadjusted gap model if space allows. State the equivalences in the table note so that a reviewer does not read five columns as five tests.

## The robustness record is described as stable

Evidence: Across specifications with the binary exposure term the adjusted coefficient ranged from −0.85 under median regression to 1.89 with High-confidence mappings without any specification reaching conventional significance. The median and Huber models used non-clustered standard errors. The modelling report ends by saying that capability development appears to lag occupational demand, which implies a sequence the cross-sectional design cannot observe.

Response: Describe the adjusted exposure coefficient as indistinguishable from zero in every specification, give the range of estimates and remove the lag wording.

## Career interest is aspirational

Evidence: Career Interest records a target occupation for 198 participants. Current job function could be coded to ISCO-08 for only 26 of 200.

Response: Use targeted occupation consistently and keep every exposure claim at the level of occupational aspiration.

## Exposure is an occupation-level task measure

Evidence: The ILO 2025 index scores tasks within ISCO-08 unit groups (Gmyrek et al., 2025). The analytical recode runs from 0 to 5 in the integration README and the brief but appears as 1 to 5 in MODEL_SPECIFICATION_AND_CLAIM_DISCIPLINE.md. Only codes 1, 3, 4 and 5 occur in the sample.

Response: Define the recode once as 0 to 5 with four categories observed. Keep exposure distinct from AI use, adoption and competence in every section.

## Sample coverage and missing demographics

Evidence: Of the 200 participants, 195 were in Nigeria once state and city entries in the Country field are harmonised [186 recorded as Nigeria and nine as Nigerian locations], with two in Ghana and one each in Kenya, Egypt and Ethiopia. Age group was missing for 61.0% and gender and employment status for 33.0% each, while a further 37.0% recorded employment status as Other. The complete-case control model retained 106 participants. Bachelor's degrees accounted for 78.0% of the sample, early-career participants for 84.5% and Technology & Digital current functions for 56.0%.

Response: Harmonise the Country field before building Table 1. Describe the sample as early-career degree-educated digital talent in Nigeria and keep the demographic model in the supplement.

## Data provenance, ethics and related work

Evidence: The participant file carries TG Nexus Cohort, Primary Gap Identified and intervention fields, which matches the TG Nexus assessment dataset planned for the deferred empirical Strategy and Leadership paper. Strategic Organization requires the ethics committee name and approval number with consent statements on the title page and an EQUATOR reporting checklist at upload. Sage requires disclosure of generative AI use that produces text or references.

Response: Confirm the data access agreement and the legal basis for research use of the assessment records. Obtain the ethics approval or waiver details. Decide authorship or acknowledgement for the data owner and the TG Nexus co-author. Disclose the related manuscript and any commercial relationship at submission. Describe the setting without naming TG Nexus in the anonymised manuscript.

## Outputs that identify participants

Evidence: table_13_influence_diagnostics.csv lists Participant IDs with scores for the 15 most influential cases and table_A1_post_cases.csv lists Participant IDs with baseline and post scores.

Response: Exclude both files from the supplement and any release. The data availability statement should describe only aggregate outputs as shareable.

## Figures and exemplar calibration

Evidence: figure_01 shows two bars with separate confidence intervals, which hides the paired structure. Every figure also carries an in-plot title. The fitted line in figure_04 includes the low-scoring tail. The stored exemplar is an essay of about 7,800 words with no empirical tables and Figge, Anderson and Lewis (2026) is a system dynamics model.

Response: Redraw the empirical figures after S1 to S5 with a paired display of the within-person gap and captions in place of titles. Use one recent quantitative Strategic Organization research article to calibrate the Methods and Results sections.
