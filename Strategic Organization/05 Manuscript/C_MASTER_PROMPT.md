# MASTER INSTRUCTION TO C — STRATEGIC ORGANIZATION MANUSCRIPT

You are taking over a fully prepared research project for submission to **Strategic Organization (SAGE)**. Work as a senior strategy and organization scholar preparing a paper capable of surviving a demanding top-journal review process. Do not treat this as a generic drafting task. The empirical work, claim boundaries, journal requirements and style benchmarks are already defined in the repository. Your job is to build the strongest defensible manuscript around them.

## 1. Repository and project location

GitHub repository: `Imomazin/research-projects`

Project root: `Strategic Organization/`

Do not use, edit, move or cite files from `ppdl-cross-org-intelligence`. That is an unrelated project.

Start by reading the project folders in this order:

1. `Strategic Organization/README.md`
2. `Strategic Organization/05 Manuscript/JOURNAL_REQUIREMENTS.md`
3. `Strategic Organization/05 Manuscript/WORLD_CLASS_MANUSCRIPT_STRATEGY.md`
4. `Strategic Organization/04 Analysis/Statistical Modeling/STATISTICAL_MODELING_REPORT.md`
5. `Strategic Organization/04 Analysis/Statistical Modeling/MODEL_SPECIFICATION_AND_CLAIM_DISCIPLINE.md`
6. `Strategic Organization/05 Manuscript/Exemplar Paper/Writing Style Blueprint.md`
7. the exemplar manuscripts in `Strategic Organization/05 Manuscript/Exemplar Paper/`
8. the data-integration documentation in `Strategic Organization/03 Data Integration/README.md`
9. the ILO secondary-data documentation in `Strategic Organization/02 Secondary Data/`
10. the detailed statistical tables in `Strategic Organization/04 Analysis/Statistical Modeling/`

Do not draft the article until you have read those materials.

## 2. Target journal

Target: **Strategic Organization**

Submission type: **Research Article**, not SOapbox.

Official page: https://journals.sagepub.com/home/SOQ

Official guidelines: https://journals.sagepub.com/author-instructions/soq

Strategic Organization requires the paper to make a clear conceptual or empirical contribution at the intersection of strategic management and organization theory. The manuscript must therefore read as a strategy/organization paper. It must not read as a training report, employability study, HR analytics paper or generic AI-skills survey.

Current formal requirements include:

- generally no more than 12,000 words inclusive of abstract, references and tables;
- double-spaced, 12-point font;
- preferred manuscript format: Word;
- unstructured abstract of 100–150 words;
- minimum five keywords;
- SAGE Harvard referencing;
- separate title page and fully anonymised review manuscript;
- all figures numbered consecutively and prepared at 300 dpi;
- tables and figures on separate pages at the end of the initial submission file, with placement markers in the text;
- cover letter encouraged;
- data-availability statement encouraged subject to ethical/legal constraints.

Our internal target is 10,800–11,500 total words inclusive of references and tables. Do not exceed the journal limit.

## 3. Folder map and what each folder contains

### `01 Primary Data/`

Contains the participant-level source data in CSV and Excel form.

- `Compiled Participants Data_v2.csv`
- `Compiled Participants Data_v2.xlsx`

Baseline dataset: n=200, 49 fields. The primary baseline dimensions are complete. Some demographic fields are incomplete. Only 12 participants have an overall post score. Component post scores and most intervention fields are absent.

Treat participant-level data as confidential. The repository is private for a reason.

### `02 Secondary Data/`

Contains documentation and the exact ILO occupation-exposure lookup used in this study.

- `ILO GenAI Occupational Exposure 2025 - SOURCE.md`
- `ILO_Exposure_Lookup_Used.csv`

Authoritative external source: ILO 2025, *Generative AI and Jobs: A Refined Global Index of Occupational Exposure* and its ISCO-08 exposure dataset.

The ILO measure is occupation-level GenAI exposure. It is not individual AI usage, adoption, skill or performance.

### `03 Data Integration/`

Contains the coded ISCO-08 mappings and the merged analysis-ready data.

- `ISCO08_Career_Interest_Crosswalk.csv`
- `ISCO08_Current_Function_Crosswalk.csv`
- `Strategic_Organization_Analysis_Ready.csv`
- `Strategic_Organization_Analysis_Ready.xlsx`
- `Strategic_Organization_Integrated_Dataset.xlsx`
- `README.md`

Career Interest is available for 198 of 200 participants and all 198 non-missing career interests have been mapped to ISCO-08 and the ILO exposure taxonomy.

Mapping confidence:

- High: 145
- Medium: 51
- Low: 2

Career interest represents a target/aspirational occupation. Do not present it as the participant's observed current occupation.

### `04 Analysis/`

This is the authoritative source for all statistical claims.

Use `04 Analysis/Statistical Modeling/` for the completed outputs and `04 Analysis/Reproducible Analysis/analysis_pipeline.py` for the reproducible code.

The Statistical Modeling folder contains:

- `STATISTICAL_MODELING_REPORT.md`
- `MODEL_SPECIFICATION_AND_CLAIM_DISCIPLINE.md`
- `analysis_manifest.json`
- sample-flow, missingness, descriptive and psychometric tables;
- exposure-group tests;
- correlation tables;
- core clustered regressions;
- robustness analyses;
- influence diagnostics;
- robust and quantile regressions;
- exploratory post-score appendix tables;
- publication-resolution figures.

Never type a numerical result from memory if the exact value can be read from the analysis files.

### `05 Manuscript/`

Contains the manuscript strategy, journal requirements and style exemplars.

Read:

- `JOURNAL_REQUIREMENTS.md`
- `WORLD_CLASS_MANUSCRIPT_STRATEGY.md`
- `Exemplar Paper/Writing Style Blueprint.md`

The Exemplar Paper folder contains a full accepted Strategic Organization manuscript by Lin & Corley (2026), its Markdown source and CC BY 4.0 licence. Use it to study argument architecture, scholarly pacing, transitions, paragraph density, theoretical positioning and discussion structure. Do not copy sentences, distinctive phrases or rhetorical constructions.

The folder also contains a link to Figge, Anderson & Lewis (2026), *AI-human learning systems: Investigating the strategic role of AI for organizational learning*, Strategic Organization 24(2): 307–342. This is the closest conceptual comparator for the present AI/capability argument and should inform how the paper enters the journal's current conversation.

### `06 Submission/`

Use this for the final submission package only after the manuscript is internally approved.

## 4. Study identity

This is a **cross-sectional multi-source capability-demand alignment study** linking participant capability assessments to an external occupation-level GenAI exposure taxonomy through ISCO-08 career-interest coding.

The core phenomenon is **strategic capability asymmetry under occupational GenAI exposure**.

Preferred research question:

**Do individuals targeting more AI-exposed occupations possess AI/data capability commensurate with their general strategic capability, and what does this reveal about strategic human-capital readiness in an emerging digital economy?**

Secondary formulation:

**How does the relationship between conventional strategic capability and AI/data capability vary across occupational GenAI exposure?**

Do not use causal wording.

## 5. Constructs and operationalisation

Use these terms exactly and consistently.

**Conventional strategic capability**
Equal-weight baseline average of:
- Strategic Thinking
- Problem Solving
- Decision Making
- Leadership
- Adaptability
- Digital Capability

**AI/data capability**
Equal-weight baseline average of:
- AI Knowledge
- AI Application
- AI Judgement
- Data Literacy

**Capability asymmetry**
Conventional strategic capability minus AI/data capability within the same individual.

**Occupational GenAI exposure**
ILO 2025 occupation-level exposure category after ISCO-08 mapping.

**High exposure**
An analytical grouping of ILO Gradient 3 and Gradient 4. Mapped n=125, 63.13% of n=198.

**Relative AI readiness**
AI/data capability considered conditional on conventional capability. This is an analytical interpretation. Do not call it a validated scale.

The ordinal 0–5 exposure recode is our analytical robustness variable. It is not an official continuous ILO score.

## 6. Measurement evidence and boundary

Internal consistency is high:

- conventional six-item alpha ≈ .883;
- AI/data four-item alpha ≈ .945;
- all ten items alpha ≈ .943.

However:

- conventional and AI/data indices correlate ≈ .919;
- PCA first eigenvalue ≈ 7.142;
- second eigenvalue ≈ .658;
- parallel analysis retains one component.

Therefore, the paper must describe the two indices as **theory-defined domain averages**, not empirically established independent latent constructs. Capability asymmetry is a within-person contrast between two theoretically defined capability domains.

Several conventional dimensions also have strong ceiling effects. Acknowledge this.

## 7. Completed empirical results

Mapped analytic sample: n=198 across 19 ISCO-08 occupation clusters.

### Core result A: large within-person asymmetry

- mean conventional capability = 86.43;
- mean AI/data capability = 69.80;
- mean capability gap = 16.63 points;
- bootstrap 95% CI = 15.80 to 17.43;
- median gap = 17.48;
- paired t(197) = 39.58, p < .001;
- Wilcoxon p < .001;
- Cohen dz = 2.81, bootstrap 95% CI approximately 2.47 to 3.27.

This is a large, pervasive within-person asymmetry.

### Core result B: absolute capability sorts with exposure

Exposure-group means:

- Minimal, n=9: conventional 72.04; AI/data 59.84; gap 12.19.
- Gradient 2, n=64: conventional 81.91; AI/data 66.00; gap 15.91.
- Gradient 3, n=67: conventional 89.32; AI/data 72.10; gap 17.22.
- Gradient 4, n=58: conventional 90.30; AI/data 72.87; gap 17.44.

In the unadjusted occupation-clustered model, high exposure predicts higher absolute AI/data capability:

- B = 7.21, SE = 1.01, p < .001.

### Core result C: no relative AI/data advantage once general capability is controlled

Occupation-clustered OLS with small-cluster t inference:

- adjusted high-exposure effect on AI/data capability: B = 0.11, SE = 1.12, p = .921;
- conventional capability coefficient ≈ .782, p < .001;
- model R² ≈ .844.

Capability-gap models:

- high exposure unadjusted B ≈ 1.87, p ≈ .218;
- high exposure adjusted B ≈ -0.11, p ≈ .921.

Residual relative-readiness model:

- high exposure B ≈ 0.10, p ≈ .930.

The substantive conclusion is **selective sorting on general capability without a commensurate relative AI/data advantage**.

This is the key result. Do not rewrite it as “AI exposure causes a capability gap.” The data do not support that claim.

## 8. Robustness completed

The adjusted exposure effect remains substantively null when:

- only High-confidence mappings are retained;
- the baseline-zero participant is removed;
- assessment date is controlled;
- current job function controls are included;
- HC3 standard errors are used;
- ordinal exposure replaces the binary high-exposure measure;
- complete-case demographic controls are used;
- Huber robust regression is used;
- median quantile regression is used;
- nonlinear conventional capability is allowed;
- high-exposure × conventional-capability interaction is tested.

Influence diagnostics identify a small set of influential observations but robust estimators do not change the conclusion.

Assessment date does not show meaningful temporal drift in exposure or capability outcomes.

## 9. Post-assessment evidence

Only 12 participants have an overall post score. No ten-component post profile exists. Most intervention fields are blank. Three reassessments occur on the same day and one baseline score is zero.

Observed descriptive follow-up:

- mean gain ≈ 27.63;
- median gain ≈ 27.56;
- all 12 observed gains are positive;
- Wilcoxon p ≈ .00049.

Sensitivity analyses remain positive after exclusions.

This is **appendix-only exploratory evidence**. It cannot support intervention effectiveness. Do not put an intervention claim in the title, abstract, contribution or main conclusion. If the paper becomes cleaner without the follow-up analysis, omit it from the main text.

## 10. Theoretical strategy

Build the paper around three connected literatures.

### Strategic human capital and capability portfolios

The theoretical issue is not simply whether individuals are capable, but whether the composition of their capabilities is aligned with strategically changing demand environments.

### Human-AI complementarity, organizational learning and technology-enabled knowing

Explain why AI knowledge, application, judgement and data literacy can become complements to conventional strategic capability. Connect to current Strategic Organization work on AI-human learning and machine/human knowing.

### Occupational exposure and capability-demand alignment

Use ILO exposure as an external demand-context measure. Ask whether people targeting more exposed occupations exhibit capability portfolios commensurate with that environment.

Do not claim observed firm-level performance, organizational transformation or causal microfoundational mechanisms.

## 11. Contribution strategy

The introduction and discussion should make two or three precise contributions.

1. **Strategic capability asymmetry**: high conventional capability can coexist with materially weaker AI/data capability within the same talent pool.
2. **Capability-demand alignment**: highly exposed occupational aspirations attract stronger talent in absolute terms, yet the AI/data component does not scale disproportionately once general capability is considered.
3. **Human-AI capability development**: the findings refine strategy/organization discussions by showing that absolute capability sorting is not the same as domain-specific readiness for AI-exposed work.

Do not oversell novelty. Make each contribution relative to specific prior literature.

## 12. Writing architecture

Build the manuscript in this order:

1. Title
2. 100–150 word unstructured abstract
3. Minimum five keywords
4. Introduction
5. Theory / conceptual development
6. Data and methods
7. Results
8. Discussion
9. Limitations and future research integrated into discussion
10. Conclusion
11. References
12. Tables and figures on separate pages for the submission version
13. Supplementary-material references where necessary

Introduction sequence:

1. phenomenon;
2. strategic puzzle;
3. theoretical gap;
4. study design;
5. headline findings;
6. bounded contributions.

Do not start with generic AI hype.

Paragraph discipline: claim → evidence/literature → mechanism/logic → implication for this paper.

Use active, precise scholarly prose. Avoid formulaic prose, repetitive signposting, excessive headings, citation dumping and consultancy language.

## 13. Citation and reference strategy

Use SAGE Harvard exactly.

Prioritise:

- foundational strategic human-capital/capability scholarship;
- Strategic Organization papers relevant to AI, strategy, organization, learning and technology;
- Strategic Management Journal;
- Organization Science;
- Academy of Management Journal;
- Academy of Management Review;
- Administrative Science Quarterly;
- Journal of Management Studies;
- selected high-quality digital-strategy work;
- the official ILO 2025 source for occupational GenAI exposure.

Target a focused reference list, roughly 55–75 genuinely used high-quality sources. Maintain classic anchors while ensuring a strong 2020–2026 contemporary layer.

Rules:

- never invent a citation;
- verify every DOI, title, journal, volume, issue, year and page range;
- cite the published peer-reviewed version if one exists;
- do not cite a preprint when a published article is available;
- avoid consultancy reports/blogs for theoretical claims;
- do not cite sources merely to inflate the bibliography;
- all in-text citations must appear in the reference list and vice versa.

## 14. Tables

Design the main manuscript around approximately four tables.

**Table 1: Sample, measurement and mapping profile**

**Table 2: Descriptive statistics, reliability and correlations**

**Table 3: Capability profile by ILO GenAI exposure group**

**Table 4: Core occupation-clustered regression models**

Move psychometric diagnostics, mapping sensitivity, detailed robustness, influence diagnostics, robust/quantile regressions and post-score sensitivity to supplementary material.

Tables must be self-contained and reconcile exactly to `04 Analysis/Statistical Modeling/`.

## 15. Figures

Recommended main figures:

**Figure 1: Original conceptual/analytic model** showing capability portfolio alignment against occupational GenAI exposure.

**Figure 2: Within-person capability asymmetry** using the completed statistical figure as the empirical foundation.

**Figure 3: Capability sorting across occupational exposure** showing absolute capability differences while making the adjusted alignment result clear.

Supplementary figures may include exposure distribution and parallel analysis.

All figures must be publication-quality and 300 dpi. No chartjunk, 3-D effects or decorative AI imagery. Use consistent terminology and fonts. Make the meaning immediately clear.

## 16. Limitations and claim discipline

State explicitly:

- cross-sectional design;
- predominantly Nigerian sample;
- career interest is aspirational;
- ILO exposure is occupation-level;
- measurement ceiling effects;
- dominant general factor in the capability dimensions;
- incomplete demographic fields;
- only n=12 overall follow-up scores;
- no causal intervention design.

Never use causal verbs such as “causes,” “drives,” “leads to” or “results in” for the occupational-exposure models unless clearly describing theory rather than empirical identification.

## 17. Data governance

The repository is private and includes participant-level data. Do not place raw participant data in a public repository.

Draft a data-availability statement that explains that participant-level data are restricted because of confidentiality/governance constraints, while analysis code and non-disclosive aggregate outputs may be made available subject to approval.

## 18. Files you must produce

Work inside `Strategic Organization/05 Manuscript/` and `Strategic Organization/06 Submission/` only. Do not overwrite raw data or analysis outputs.

Create:

### In `05 Manuscript/`
- `Strategic_Organization_Manuscript_Draft.md`
- final working Word manuscript when ready
- `REFERENCE_AUDIT.md` documenting bibliographic verification
- `TABLES_FIGURES_PLAN.md`
- `THEORY_CONTRIBUTION_MAP.md`
- `REVIEWER_RISK_REGISTER.md`
- `DATA_AVAILABILITY_AND_ETHICS.md`
- `TITLE_ABSTRACT_KEYWORDS_OPTIONS.md`

### In `06 Submission/`
- anonymised final manuscript
- separate title page
- cover letter
- supplementary appendix
- final tables/figures package as required
- submission checklist

Do not create multiple uncontrolled manuscript versions. Use clear versioning.

## 19. Quality-control gates before you call the manuscript complete

Check every item:

- Is this visibly a Strategic Organization paper?
- Is the strategy/organization contribution clear within the first two pages?
- Are the two or three contributions specific and non-overlapping?
- Are all numerical claims traceable to `04 Analysis/Statistical Modeling/`?
- Is the adjusted null exposure effect represented accurately?
- Have all causal intervention claims been removed?
- Is the psychometric one-factor result disclosed honestly?
- Are all references real, verified and SAGE Harvard compliant?
- Is every citation in the reference list and vice versa?
- Is the abstract 100–150 words?
- Are there at least five specific keywords?
- Is the manuscript under the journal's 12,000-word guidance inclusive of abstract, references and tables?
- Are figures at least 300 dpi and analytically necessary?
- Do tables avoid redundancy with the prose?
- Is the review manuscript fully anonymised?
- Is participant confidentiality protected?
- Have you avoided copying any wording from the exemplar papers?
- Does the discussion explain the theoretical meaning of the null adjusted exposure effect instead of hiding it?

## 20. Final instruction

Do not simply “write up the results.” Build a coherent theoretical argument around the observed capability asymmetry and the distinction between **absolute capability sorting** and **relative AI/data readiness**.

The paper succeeds if a Strategic Organization reviewer can see why this empirical pattern changes or sharpens how strategy and organization scholars think about human capability portfolios under AI-exposed work environments.

Before drafting, read every specified repository file. During drafting, verify every statistical number against the analysis folder and every citation against an authoritative bibliographic source. Do not introduce new empirical claims that are not supported by the repository.
