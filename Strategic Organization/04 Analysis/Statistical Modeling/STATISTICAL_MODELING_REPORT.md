# Statistical Modeling Report: Strategic Organization

## Analytical sample

The baseline dataset contains 200 participants. Career-interest occupations could be mapped to ISCO-08 and the ILO 2025 GenAI exposure taxonomy for 198 participants. The occupational-exposure analyses therefore use n = 198 across 19 nominal ISCO-08 occupation clusters. Of these participants, 125 [63.1%] target occupations classified as ILO Gradient 3 or Gradient 4.

Career interest is an occupational aspiration. Every exposure statement in the paper must therefore refer to the **targeted occupation**. The ILO variable captures occupation-level task exposure to GenAI. It does not measure individual AI use, adoption, competence or current-job exposure.

## Measurement and composite construction

The six conventional dimensions are averaged a priori to form the conventional capability index. AI Knowledge, AI Application, AI Judgement and Data Literacy are averaged a priori to form the AI/data capability index. Internal consistency is high for the conventional domain [alpha = .883] and AI/data domain [alpha = .945]. Parallel analysis retains one dominant component.

The repository does not contain the assessment items, response formats, scoring rules or documentation establishing that the two domain scores share a common proficiency metric. This matters because the highest AI/data index is 88.53 while a large share of conventional scores occupy the upper end of the scale. The cross-domain raw-score difference is therefore interpreted as a **within-instrument domain profile** unless common calibration is documented by the assessment owner.

The conventional-minus-AI/data difference score is not suitable as a stable individual-difference construct. Its estimated reliability is 0.022 in the full mapped sample and -0.058 after the combined low-score sensitivity screen. It may be reported descriptively as a paired raw-score contrast but should not be the main dependent variable.

## Finding 1: within-instrument domain profile

Mean conventional capability is 86.43 and mean AI/data capability is 69.80. The mean raw within-person difference is 16.63 points [bootstrap 95% CI 15.80 to 17.43] and the median difference is 17.48. The paired t-test and Wilcoxon test show that this raw-score difference is systematic within the instrument.

Cohen dz = 2.81 is secondary evidence because the standardized effect is amplified by the relatively small variance of the difference score. Without documentation that both domains are calibrated to the same proficiency standard, do not translate the 16.63-point profile into a claim that objectively measured AI/data capability is 16.63 points weaker.

## Finding 2: unadjusted occupational sorting is real in the full sample but sensitive to the low-score tail

In the full sample, participants targeting high-exposure occupations score 7.21 points higher on AI/data capability in M1. Wild cluster restricted bootstrap inference with Webb weights gives p = .0016 and occupation-level randomisation inference over 92,378 assignments gives p = .0039.

This full-sample sorting result is not invariant to low-score screening. The combined prespecified sensitivity rule excludes 16 participants [12 low exposure and 4 high exposure]. Under that screen, M1 falls from B = 7.21 to B = 2.55 and WCR Webb p rises to .067. The conventional-AI/data Pearson correlation also falls from .919 to .775 while the Spearman correlation changes from .835 to .788.

The manuscript must therefore state that unadjusted occupational sorting is supported in the full sample but attenuates materially when the low-score tail is screened. The repository does not establish that those low observations are incomplete assessments, so they must not be labelled invalid or incomplete without documentation from the assessment owner.

## Finding 3: no distinctive relative AI/data advantage after conventional capability is accounted for

M2 conditions AI/data capability on conventional capability. In the full mapped sample, the high-exposure coefficient is B = 0.11. The WCR Webb 95% interval is approximately -2.40 to 3.30 and occupation-level randomisation inference gives p = .962. This result is the central inferential finding.

The adjusted result remains near zero across the supplementary checks:

- after the combined low-score screen, B = 0.27 with WCR Webb p = .897;
- under the High-confidence-only occupation mapping, B = 1.89 with CR1 95% CI -1.11 to 4.88 and WCR Webb p = .536;
- alternative plausible occupation recodes move the adjusted point estimate between approximately -0.07 and 1.03 without producing evidence of a nonzero effect;
- a measurement-error correction for the conventional control moves the exposure coefficient from 0.11 to -0.93 with a cluster-pairs bootstrap interval of -4.25 to 1.51;
- within ICT professional occupations [n = 131 across five ISCO occupations], the adjusted coefficient is -1.30 with HC3 p = .362. With only five occupation clusters this is a descriptive boundary check, not a cluster-inferential test.

The strongest defensible conclusion is that participants targeting more GenAI-exposed occupations do **not** show a distinctive relative AI/data readiness advantage once their conventional capability is taken into account.

## Cluster structure

The 19 nominal occupation clusters overstate the independent information in the exposure contrast. Web and multimedia developers [2513] and software developers [2512] together account for 109 of the 125 high-exposure participants. The effective number of clusters for the unadjusted exposure coefficient is approximately 4.1 under perfect within-cluster correlation and 7.1 under zero within-cluster correlation.

For this reason, CR1 intervals are not sufficient on their own. Exposure inference should rely on wild cluster restricted bootstrap results and occupation-level randomisation inference. Any statement that the data rule out an effect larger than a given magnitude must be based on the WCR interval.

## Mapping sensitivity

Occupation mapping uncertainty changes the point estimate but does not overturn the adjusted null. The High-confidence-only sample contains 145 participants and yields B = 1.89 with WCR Webb p = .536. Plausible alternative mappings for data analysis, social media, UX/UI, project/product management and technical writing likewise do not produce a distinguishable adjusted exposure effect.

Technical writing should be documented as 2641 Authors and related writers in the preferred sensitivity mapping. Project-management mapping requires an explicit authoritative occupational source. Direct ILO ISCO-08 or ESCO documentation should be preferred wherever available.

## Main-table discipline

Table 4 should not present algebraically repetitive specifications as separate confirmations. The main inferential table should prioritise M1 [unadjusted AI/data on high exposure] and M2 [AI/data on high exposure plus conventional capability], with the low-score-screening versions shown as sensitivity columns if space permits.

The adjusted gap specification is algebraically equivalent to M2 with the exposure coefficient sign reversed when conventional capability is included. The residual-readiness model is also a transformation of the same adjusted relationship. These equivalences should be disclosed in the table note.

## Sample scope and controls

After harmonising location entries, 195 of the 200 participants are in Nigeria. Bachelor's degrees account for 78.0%, early-career participants for 84.5% and Technology & Digital current functions for 56.0%. Age is missing for 61.0% while gender and employment status are each missing for 33.0%. The complete-case demographic model retains 106 participants.

The paper should therefore describe the setting as **early-career, degree-educated digital talent concentrated in Nigeria**. Demographic-control models belong in the supplement and should not drive the headline claims.

## Post-assessment data

Only 12 participants have an overall post score and there are no post scores for the ten component dimensions. Intervention fields are largely empty, three reassessments occur on the assessment day and one baseline score is zero. Post-score analyses remain Appendix-only and explicitly noncausal. They cannot support intervention-effectiveness claims.

## Publication interpretation

The defensible contribution is a strategic human-capital readiness-alignment result. Participants targeting occupations with greater GenAI task exposure do not display a distinctive relative AI/data readiness advantage once general capability and the principal analytical fragilities are accounted for. This finding is cross-sectional and associational.

Do not write that capability development 'lags' occupational demand because the design does not observe capability development over time. Do not equate occupational exposure with AI use. Do not describe the 16.63-point raw domain contrast as an objective deficit unless common score calibration is documented.

The authoritative robustness evidence is in `../Supplementary Checks/Outputs/`. Where the earlier validated headline estimates and the supplementary sensitivity results answer different questions, report both transparently.