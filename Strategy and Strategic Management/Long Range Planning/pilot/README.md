# SEC data coverage pilot

30 purposively selected listed firms across technology, finance, retail, health and industrial sectors. This is a feasibility sample, not a representative or randomly drawn sample.

## Run
Install Python 3.10+ and `pip install -r requirements.txt`.
Set `SEC_CONTACT_EMAIL` to a real contact address for compliant SEC access.
Run `python collect_sec.py`.

Outputs: `output/filing_coverage.csv`, `output/annual_filings.csv`, `output/financial_facts_raw.csv`, `output/errors.csv`, `output/manifest.json`.

The SEC limits automated request rates and requires a declared User-Agent. This script throttles requests to fewer than 3 per second. API access and entity matching must be verified during execution.

## Interpretation cautions
The SEC's current ticker mapping is not historical and may misrepresent reorganised or delisted entities. Raw XBRL entries may include restatements, overlapping tags, repeated fiscal years, alternative durations and amended filings. A single firm-year financial observation requires a documented selection protocol. 10-K availability is counted by filing year, not automatically the corresponding fiscal year. This pilot does not yet extract annual-report text, patent records or strategic-renewal events.

Do not treat these files as final research findings.
