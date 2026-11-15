# External dataset acquisition register
Checked: 15 November 2026. Sole author: Imo J. Enang.

## Acquired and committed
1. SEC company ticker-to-CIK registry: pilot/data/sec-cik-crosswalk.csv. 30 current-listed company mappings. Source https://www.sec.gov/files/company_tickers.json. Historical identifiers remain to be audited.
2. SEC XBRL financial facts: pilot/data/sec-financial-facts-part1.csv and sec-financial-facts-part2.csv. Extracted from official per-company companyfacts endpoints. 1,026 selected metric-year records from 26 firms, including missing metrics. Four firms (META, CRM, V, COST) could not be parsed reliably via the extraction intermediary and require re-fetch. Selected records are provisional: fiscal-year comparability, amendments, duplicate facts and sector-specific reporting must be audited. These are source observations, not estimated results.
3. FRED original time-series CSV: pilot/data/fred-GDP.csv, fred-UNRATE.csv, fred-FEDFUNDS.csv, fred-CPIAUCSL.csv, fred-INDPRO.csv. Source https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIESID. Full available series stored; restrict to analysis years in transformations. Vintage/revision handling remains outstanding.

## Identified but not yet acquired
4. USPTO PatentsView 2025 annualized patent datasets and disambiguated assignee/CPC records. Official source https://www.uspto.gov/ip-policy/economic-research/patentsview and https://data.uspto.gov/ . 2025 coverage confirmed; bulk download and firm matching outstanding.
5. Public patent-to-firm research linkage, https://github.com/songma/patent-firm-link-share ; firm_year_panel_public.csv (50,862,003 bytes; 593,488 firm-year observations described by publisher). Do not claim its panel has been downloaded or validated. Requires GVKEY-to-CIK crosswalk and independent licence/provenance review.
6. SEC 10-K full-text filing sections for event-coded strategic renewal; filing indexes and text extraction outstanding.
7. BEA/BLS sector controls; relevant series selection and download outstanding.
8. Compustat/CRSP/Capital IQ/Orbis; institutional licence not established and no data obtained.

## Restrictions
Do not commit restricted microdata, private interviews or licensed datasets. Preserve original source URLs, dates, identifiers, selection rules and hashes where available. Public data can be stored as narrow research extracts with provenance, subject to source terms.

## Next blockers
- Recover and verify four failed SEC companyfacts JSON parses.
- Complete firm-year completeness and fiscal-year/metric validation.
- Acquire patent-to-firm linkage and check GVKEY-CIK matching.
- Extract strategic-renewal events and manually validate coding.
- Establish whether Warwick DBA survey microdata can be lawfully reused.
