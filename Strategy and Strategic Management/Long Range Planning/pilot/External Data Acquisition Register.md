# External data acquisition register

Acquisition date: 16 November 2026. Researcher: Imo J. Enang.

## Acquired and committed
- SEC current CIK/ticker registry crosswalk for 30 pilot tickers.
- SEC Company Facts: 289 selected annual accounting observations for eight issuers (MSFT, AAPL, NVDA, AMZN, GOOGL, ORCL, IBM, ADBE) for candidate fiscal years 2016–2025. Source is the SEC's public XBRL API. This is an extracted subset, not the original full source archive.
- FRED original CSV time series: GDP, UNRATE, FEDFUNDS, CPIAUCSL and INDPRO. Data files retain the source observation dates and are not yet aligned to firm fiscal years.

## Interpretation and corrections required
The SEC selection uses fy, fp=FY, form=10-K and annual-duration filters, choosing the latest filing for each company/metric/year. This is preliminary and may select comparative observations or restatements, particularly where fiscal year and filing date differ. It must be revalidated against fiscal period end and reporting accession. Some metrics are missing because of taxonomy choices; missing does not imply zero. The current SEC ticker map excludes delisted firms and does not resolve historical restructurings. These data are not ready for regression.

## Not yet acquired
- Patent-level PatentsView records and validated patent-assignee-to-CIK crosswalk.
- Full 10-K text for event coding and independent strategic renewal indicators.
- Licensed Compustat, CRSP, Capital IQ or Orbis data.
- Original DBA respondent-level data, interview transcripts and codebook.

## DBA triangulation
The user's Warwick DBA thesis is *An Exploration of Organisational Ambidexterity Implementation*. The full thesis and original study datasets have not been retrieved into this research folder. Triangulation should distinguish theoretical and construct validation from independent empirical replication. Do not merge DBA respondent-level observations with US public-company firm-year data without compatible units, consent and data-governance clearance. Extract the original constructs, measurement instruments and qualitative themes only after reading the thesis and supporting materials.

## Next steps
1. Complete remaining 22 firms in small source batches, logging failures.
2. Audit annual-report year mapping and financial tags, then create a clean firm-year panel.
3. Acquire dated patent events and evaluate corporate ownership matches.
4. Collect annual filing text and manually verify strategic renewal events.
5. Recover DBA thesis and permissible underlying data for theory and construct triangulation.
