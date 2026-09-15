# Post-Audit Claim Resolution

**Status:** Authoritative for manuscript drafting after the 15 September 2026 reviewer-risk audit.

This note supersedes any earlier wording in `C_MASTER_PROMPT.md`, `WORLD_CLASS_MANUSCRIPT_STRATEGY.md` or the statistical-modeling narrative where those files conflict with the supplementary S1-S11 checks.

## Definitive empirical story

The paper should not lead with a claim that participants have an objectively weaker AI/data capability because the repository does not contain instrument documentation establishing that the conventional and AI/data domains share a common proficiency metric. The observed 16.63-point difference is therefore reported first as a **within-instrument domain profile or raw-score asymmetry**. It becomes evidence of weaker AI/data capability only if the assessment owner confirms common scaling and proficiency standards.

The stronger inferential result concerns alignment with occupational demand. Participants targeting occupations with higher ILO GenAI exposure have higher AI/data scores in the unadjusted full-sample comparison, but that sorting is sensitive to the low-score tail. The unadjusted coefficient falls from 7.21 points in the full sample to 2.55 after the prespecified sensitivity screen, with WCR Webb p = .067 after screening.

Once conventional capability is included, there is no distinguishable relative AI/data advantage for participants targeting high-exposure occupations. The full-sample adjusted coefficient is 0.11 points. The WCR Webb interval is approximately -2.40 to 3.30. Occupation-level randomisation inference gives p = .962. After low-score screening the adjusted coefficient is 0.27 with WCR Webb p = .897. Restricting to High-confidence occupation mappings gives B = 1.89 with CR1 95% CI -1.11 to 4.88 and WCR Webb p = .536. Correcting the conventional control for measurement error moves the coefficient to -0.93 with a cluster-pairs bootstrap interval of -4.25 to 1.51. Within ICT professional occupations the adjusted coefficient is -1.30 with HC3 p = .362; this five-cluster check is descriptive only.

The manuscript contribution is therefore a **strategic human-capital readiness alignment problem**: targeting more GenAI-exposed occupations is not associated with a distinctive AI/data readiness advantage once general capability and the main analytical fragilities are accounted for. This is an associational cross-sectional result. Do not use temporal wording such as capability development 'lags' occupational demand.

## Measurement rules

The conventional index is the equal-weight mean of six baseline dimensions. The AI/data index is the equal-weight mean of AI Knowledge, AI Application, AI Judgement and Data Literacy. The ten items retain a dominant general factor after sensitivity screening.

The gap score is useful as a descriptive within-person raw-score contrast but **must not be treated as a stable individual-difference construct or primary dependent variable**. Difference-score reliability is 0.022 in the full mapped sample and -0.058 after the combined sensitivity screen.

No scoring guide, item specification, response-format documentation or common-scale calibration is held in the repository. Until supplied, state this explicitly in Methods and Limitations. Do not infer common proficiency scaling from the fact that both domains use 0-100 scores.

The repository also does not establish whether very low scores are incomplete assessments. Refer to these records as a low-score tail or observations flagged by prespecified sensitivity rules. Do not label them incomplete, erroneous or invalid without assessment-owner evidence.

## Exposure rules

ILO exposure is an occupation-level task-exposure measure linked to **targeted occupation** through career-interest coding. It is not individual AI use, adoption, competence or current-job exposure.

The project-created ordinal recode is 0 to 5: Not Exposed = 0, Minimal Exposure = 1, Gradient 1 = 2, Gradient 2 = 3, Gradient 3 = 4 and Gradient 4 = 5. Only 1, 3, 4 and 5 occur in the mapped sample. Primary models use the official ILO categories collapsed to high exposure [Gradients 3-4] versus low exposure [Minimal and Gradient 2]. The ordinal recode is robustness-only.

Use `targeted occupation`, `occupational aspiration` or `career-interest occupation` consistently. Do not write as if the 198 participants currently work in those occupations.

## Inference and clustering

The 19 nominal ISCO-08 clusters overstate independent information because two occupations contain 109 of the 125 high-exposure participants. The effective cluster count for the unadjusted exposure coefficient is approximately 4.1 to 7.1 depending on within-cluster correlation assumptions.

Consequently, CR1 inference alone is insufficient. For exposure claims, report wild cluster restricted bootstrap results with Webb weights and occupation-level randomisation inference. The adjusted null is the core result because it survives these procedures. Any effect-size exclusion claim must use the WCR interval, not the narrower CR1 interval.

## Mapping sensitivity

Mapping uncertainty changes point estimates but does not overturn the adjusted result. The original adjusted coefficient is 0.11. Alternative recodes span approximately -0.07 to 1.03 and the High-confidence-only specification gives 1.89. None yields evidence of a nonzero adjusted exposure effect under the appropriate robustness inference.

Technical writing should be documented as 2641 Authors and related writers in the preferred sensitivity mapping. Project-management coding requires an explicit defensible source. Prefer ILO ISCO-08 or ESCO sources over Wikidata or commercial careers pages wherever a direct authoritative occupational definition is available.

## Table 4

Do not present algebraically repetitive models as independent tests. The main Table 4 should prioritise:

1. M1: AI/data capability on high exposure, unadjusted.
2. M2: AI/data capability on high exposure plus conventional capability.
3. A clearly labelled low-score-screening sensitivity for M1 and M2 if space permits.

The adjusted gap model is algebraically the adjusted AI/data model with the exposure coefficient sign reversed when conventional capability is included. The residual-readiness model is not an independent robustness test. Explain these equivalences in the table note instead of presenting five columns as five separate confirmations.

## Robustness wording

Do not say the unadjusted sorting result is simply 'stable'. State that full-sample unadjusted sorting is supported by WCR and randomisation inference but attenuates materially under low-score screening. State separately that the **adjusted exposure coefficient remains statistically indistinguishable from zero across the full set of screening, mapping, randomisation, within-ICT and measurement-error sensitivity checks**.

## Sample scope

Describe the study population narrowly. After harmonising country entries, 195 of 200 participants are in Nigeria. Bachelor's degrees account for 78.0%, early-career participants for 84.5% and Technology & Digital current functions for 56.0%. Age is missing for 61.0%; gender and employment status are each missing for 33.0%. The complete-case demographic model has n = 106 and belongs in the supplement.

A defensible description is **early-career, degree-educated digital talent concentrated in Nigeria**. Do not generalise the sample to African workers or the wider labour market.

## Figures

Replace the old two-bar asymmetry figure with a paired within-person display. Figures should use captions rather than in-plot titles. Any capability-sorting scatter should visibly identify or separately analyse the low-score tail so the fitted relationship is not presented as if it were insensitive to those observations.

## Items still requiring author input

Two substantive matters cannot be resolved from the repository and must remain explicit until evidence is supplied: the assessment scoring/calibration documentation and the ethics/data-provenance record, including approval or waiver details and the legal basis for research use. These are not statistical gaps and must not be filled by inference.

## Drafting rule

When an earlier project note conflicts with this file or with `04 Analysis/Supplementary Checks/Outputs/`, use the post-audit results. The paper should be written around the adjusted readiness-alignment finding, with the raw 16.63-point domain contrast presented cautiously and the unadjusted occupational sorting result explicitly qualified by the low-score sensitivity.