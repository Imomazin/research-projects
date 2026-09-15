# Model Specification and Claim Discipline

## Primary empirical objects

1. **Conventional capability index:** equal-weight mean of six baseline dimensions.
2. **AI/Data capability index:** equal-weight mean of AI Knowledge, AI Application, AI Judgement and Data Literacy.
3. **Raw domain contrast:** conventional minus AI/data score within participant. Use this descriptively as a within-instrument profile difference, not as a stable individual-difference construct. Difference-score reliability is approximately 0.022 in the full mapped sample and -0.058 after the combined sensitivity screen.
4. **ILO occupational exposure:** official 2025 occupation-level task-exposure category linked through ISCO-08 coding of career interest. This is exposure of the targeted occupation, not participant-level AI use or current-job exposure.
5. **High exposure:** ILO Gradient 3 or Gradient 4. Low exposure is Minimal Exposure or Gradient 2 in the observed sample.
6. **Ordinal exposure recode:** project-created 0-5 scale, where Not Exposed = 0, Minimal = 1, Gradient 1 = 2, Gradient 2 = 3, Gradient 3 = 4 and Gradient 4 = 5. Only 1, 3, 4 and 5 occur in the mapped sample. Use the ordinal recode for robustness only.

## Primary tests

- Descriptive paired comparison of conventional and AI/data raw domain scores.
- **M1:** AI/data capability on high occupational exposure.
- **M2:** AI/data capability on high occupational exposure plus conventional capability.
- Primary exposure inference must use occupation-aware procedures. Report wild cluster restricted bootstrap inference with Webb weights and occupation-level randomisation inference alongside conventional clustered estimates.

The adjusted gap model and residual-readiness model are not independent confirmatory tests. With conventional capability included, the adjusted gap exposure coefficient is algebraically the adjusted AI/data exposure coefficient with the sign reversed. The residual-readiness coefficient is another transformation of the adjusted relationship. These equivalences belong in a table note, not as separate headline tests.

## Prespecified sensitivity checks

Use the supplementary S1-S11 checks for:

- low-score screening rules without assuming the records are incomplete;
- psychometrics before and after screening;
- exposure-group medians and trimmed means;
- effective occupation-cluster counts;
- wild cluster restricted bootstrap inference;
- occupation-level randomisation inference;
- occupation-mapping alternatives and High-confidence-only mappings;
- within-ICT professional occupation comparison;
- measurement-error sensitivity for the conventional capability control.

Existing checks for assessment date, current job function, HC3 errors, complete-case demographics, Huber regression and influence diagnostics remain secondary robustness analyses.

## Claim boundaries

- Repository materials do not document whether conventional and AI/data scores are calibrated to a common proficiency metric. Therefore the 16.63-point raw difference is a within-instrument domain profile unless common scaling is documented by the assessment owner.
- Cross-sectional baseline analyses support association and readiness-alignment language, not causality or temporal sequencing.
- Career interest is an aspirational targeted occupation. Do not describe occupational exposure as participants' current work exposure.
- ILO exposure is occupation-level task exposure, not AI adoption, use or individual competence.
- Full-sample unadjusted sorting is sensitive to the low-score tail. M1 falls from B = 7.21 to B = 2.55 after the combined sensitivity screen, with WCR Webb p = .067 after screening.
- The adjusted exposure effect is the core inferential result. M2 is B = 0.11 in the full sample, remains near zero after screening and remains statistically indistinguishable from zero under WCR, occupation randomisation, mapping and measurement-error sensitivity checks.
- The ten assessment dimensions show a dominant general factor, including after low-score screening. Treat domain averages as theory-defined indices rather than clean latent constructs.
- The raw gap is not a reliable person-level trait and should not be the primary dependent variable.
- The post-score n = 12 sample cannot identify intervention effects.
- Do not use wording that capability development 'lags' occupational demand. The design cannot establish a sequence over time.

## Sample scope

The paper should describe the sample narrowly as early-career, degree-educated digital talent concentrated in Nigeria. Demographic controls have substantial missingness and belong in supplementary analysis rather than the main identification strategy.

## Authoritative post-audit sources

For manuscript drafting, use `../Supplementary Checks/Outputs/` together with the validated `analysis_manifest.json`. Where an earlier narrative conflicts with the S1-S11 results, the post-audit supplementary results take precedence.