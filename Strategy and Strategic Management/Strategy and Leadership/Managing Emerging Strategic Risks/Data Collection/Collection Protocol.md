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

## Execution notes (25 October 2026)

The analysis workspace could not reach SEC, the NY Fed or the index publishers, so collection runs in GitHub Actions (`.github/workflows/strategic-risk-pipeline.yml`) triggered by `Run Request.txt`. The SEC client declares a user agent with a contact address, throttles to eight requests per second, backs off on 429 and 5xx responses and caches responses within a run. Steps 1 to 8 were completed; the frame used 2018 public float from XBRL frames, and 13 sampled firms were excluded after validation (Datasets/Sampling Frame/Frame Validation Exclusions.csv).
