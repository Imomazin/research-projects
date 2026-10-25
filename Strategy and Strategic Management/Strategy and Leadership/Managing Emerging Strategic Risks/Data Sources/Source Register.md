# Source register

| Source | Data | Access | Use | Status |
|---|---|---|---|---|
| SEC EDGAR submissions and Archives | 10-K primary documents, filing dates, accession numbers | https://data.sec.gov/submissions/ and https://www.sec.gov/Archives/edgar/ | Items 1, 1A and 7 text; sampling | Collected 25 Oct 2026 (6,301 filings for 800 firms; 6,214 after validation exclusions) |
| SEC XBRL company facts | Annual and quarterly facts for 50 concepts | https://data.sec.gov/api/xbrl/companyfacts/ | Revenue, margins, controls, resource commitments | Collected 25 Oct 2026 (2,240,714 rows) |
| SEC XBRL frames | dei:EntityPublicFloat, 2018 quarters | https://data.sec.gov/api/xbrl/frames/ | Sampling frame | Collected 25 Oct 2026 (5,720 entities) |
| Geopolitical Risk Index | Monthly GPR, threats, acts, country series | https://www.matteoiacoviello.com/gpr.htm | Geopolitical shock, tracking validity | Collected (data to September 2026) |
| Economic Policy Uncertainty | US monthly, categorical (trade, regulation), global | https://www.policyuncertainty.com/ | Policy shocks, tracking validity | Collected |
| World Uncertainty Index | Quarterly global and country | https://worlduncertaintyindex.com/data/ | Supplementary | WUI collected; pandemic and spillover files refused with HTTP 429 |
| NY Fed GSCPI | Monthly index | https://www.newyorkfed.org/research/policy/gscpi | Supply-chain shock | Collected (data to September 2026) |
| Crossref and OpenAlex | Bibliographic metadata | api.crossref.org, api.openalex.org | Reference verification | Collected |
| World Bank Enterprise Surveys | Firm survey microdata | https://www.enterprisesurveys.org/ | Considered | Not used: different units (non-US firms, survey waves) |
| AI Incident Database | AI incidents | https://incidentdatabase.ai/ | Considered | Not used: no firm-level link to the sample |
| WEF Global Risks Report | Risk perceptions | https://www.weforum.org/publications/ | Context only | Not used as data |

Licensing: SEC filings are public records. GPR, EPU and WUI are published for research use with citation; GSCPI is published by the Federal Reserve Bank of New York under its terms of use with attribution. Retrieval manifests: Datasets/Raw Macro/Macro Retrieval Manifest.csv and Datasets/Filings Index.csv (document SHA-256 per filing).
