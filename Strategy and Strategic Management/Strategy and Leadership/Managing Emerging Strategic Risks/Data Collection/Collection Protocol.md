# Collection protocol

1. Freeze sampling frame, years, filing date cutoff and eligible CIKs.
2. Download SEC submissions and companyfacts with a descriptive User-Agent, caching, backoff and SEC fair-access compliance.
3. Collect full 10-K documents, record accession number, filing date and Item 1A text extraction quality.
4. Retrieve and archive dated GPR, WUI, EPU and GSCPI series from their official distribution channels.
5. Standardise calendar/fiscal timing, geographical exposures, sector definitions and units.
6. Save raw data outside Git if licensing or size requires; store checksums and immutable manifests in Git.
7. Validate completeness, duplicates, fiscal-year overlaps, missingness and text extraction against manually inspected filings.
8. Create frozen derived firm-year panel with reproducible code and a data dictionary.

No synthetic observations may be presented as empirical evidence.
