# Dataset feasibility assessment
Date: 15 November 2026
Author: Imo J. Enang

This is a desk assessment of dataset suitability, not a completed download, audit or licence clearance.

| Dataset | Candidate measures | Access | Principal limitations | Decision |
|---|---|---|---|---|
| SEC EDGAR annual 10-K filings | Digital exploration/exploitation narratives, AI mentions, restructuring and business-model change | Public; SEC fair-access rules and identification requirements | Disclosure bias, changing vocabulary, reporting incentives, text is not proof of realised capabilities | Core pilot; validate against observable events |
| SEC Company Facts / XBRL | Revenue, assets, R&D where reported, capital expenditures, operating income | Public API | Taxonomy inconsistency, fiscal-year alignment, incomplete R&D, restatements, sector-specific accounting | Core pilot financial controls and outcomes |
| USPTO PatentsView | Technology patent portfolios, IPC/CPC diversity, new-class entry, citation patterns | Public bulk/API subject to current terms and availability | Grant/publication lag, assignee-name disambiguation, acquisition effects, patents weak in service sectors | Conditional core; construct crosswalk and test match quality |
| USPTO assignment data | Ownership transfers and portfolio reconfiguration | Public | Transfers do not necessarily imply strategic renewal; entity matching | Optional triangulation |
| Compustat North America | Standardised firm financial panel and industry controls | Licensed institutional access | Subscription and redistribution restrictions; survivorship and identifier matching | Preferred if authorised access exists; not assumed |
| CRSP | Security returns and risk-adjusted market outcomes | Licensed institutional access | Financial market coverage only; share-class complexity | Optional; no assumed access |
| Orbis / Capital IQ / Refinitiv | Ownership, financial and corporate events | Licensed | Inconsistent historical coverage and redistribution limits | Alternative licensed data |
| FRED | Interest rates, inflation, business cycle variables | Public API/download | Macro data vary by frequency; firm exposure not identified | Supplementary macro controls |
| BEA / BLS | Industry trends, productivity, labour-market controls | Public | NAICS revisions and coarse aggregation | Supplementary controls |
| OpenAlex / Crossref | Scientific publication activity and firm collaboration | Public subject to terms | Affiliation disambiguation and incomplete company attribution | Optional innovation validation |
| Company press releases / investor presentations | Verifiable strategic renewal events, acquisitions, product launches, market exits | Often public | Selection and promotional bias, costly event coding | Triangulation with dated independent evidence |
| Earnings-call transcripts | Strategic narrative, AI deployment and management commitments | Often licensed or fragmented public availability | Licensing and selection biases, time-consuming cleaning | Optional, not required for pilot |
| Job postings / occupational AI measures | AI talent demand and implementation proxy | Mostly licensed or platform-specific | Posting intensity not capability, historical coverage varies | Optional external validation |

## Construct-by-source feasibility
1. Digital exploration: new technology-domain entry, novel digital patent categories and validated investment/launch events; disclosure-language indicators only as secondary proxies.
2. Digital exploitation: evidence of digitisation of existing operations, efficiency-oriented investments and deployment; requires careful differentiation from generic digital mentions.
3. AI capability: combine AI-relevant innovation and documented deployment with organisational evidence; AI keyword frequency alone is insufficient.
4. Strategic renewal: independently dated resource reconfiguration, strategic business entry/exit, major operating-segment shifts or business-model changes. Text similarity or word frequency alone is not a valid measure.
5. Sustained competitive advantage: persistence of industry-adjusted operating performance or market measures across subsequent years; avoid claiming sustainable advantage from short-term accounting returns.

## Identification and measurement risks
- Endogeneity: successful firms may invest more in AI and disclose more; panel fixed effects alone do not establish causality.
- Temporal ordering: predictor at t, renewal at t+1, performance persistence at t+2 or later; patent grant dates are not invention dates.
- Survivorship: include delisted firms where feasible and document exclusions.
- Sample bias: SEC reporting firms are predominantly public US issuers and are not representative of all firms.
- Sector differences: patent propensities and financial reporting vary substantially.
- Construct overlap: distinguish AI capability from exploration and exploitation and strategic renewal from outcome performance.
- Measurement validation: manual blinded coding sample, inter-coder agreement where possible, convergent/discriminant validity and negative controls.

## Feasibility verdict
**Feasible as a staged archival research programme, not yet validated as an executable full panel.** Public SEC, PatentsView and FRED sources can support a pilot, subject to actual access, coverage and entity-matching checks. AI capability, digital exploitation and strategic renewal are the main construct-validity bottlenecks. Compustat and CRSP cannot be assumed available.

## Decision gates
Proceed to full collection only if pilot shows acceptable firm-identifier matching, longitudinal coverage, construct discrimination, temporal variation and auditable event coding. If these fail, revise to a narrower sample or alternative mixed-method research design. No invented thresholds or empirical results.
