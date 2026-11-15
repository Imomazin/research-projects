#!/usr/bin/env python3
"""Collect SEC submissions and XBRL coverage for a pilot sample.

Run: SEC_CONTACT_EMAIL=research@example.org python collect_sec.py
Outputs only source-derived coverage diagnostics, not empirical findings.
"""
import csv
import json
import os
import pathlib
import time
import requests

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
email = os.getenv("SEC_CONTACT_EMAIL", "").strip()
if not email or "@" not in email:
    raise SystemExit("Set SEC_CONTACT_EMAIL to a valid researcher contact email.")
session = requests.Session()
session.headers.update({"User-Agent": f"LongRangePlanningResearch {email}", "Accept-Encoding": "gzip, deflate"})
last_request = [0.0]

def get_json(url):
    delta = time.monotonic() - last_request[0]
    if delta < 0.35:
        time.sleep(0.35 - delta)
    response = session.get(url, timeout=40)
    last_request[0] = time.monotonic()
    response.raise_for_status()
    return response.json()

def iter_filings(sub):
    recent = sub.get("filings", {}).get("recent", {})
    keys = list(recent)
    for row in zip(*(recent.get(k, []) for k in keys)):
        yield dict(zip(keys, row))
    for f in sub.get("filings", {}).get("files", []):
        extra = get_json("https://data.sec.gov/submissions/" + f["name"])
        keys = list(extra)
        for row in zip(*(extra.get(k, []) for k in keys)):
            yield dict(zip(keys, row))

def annual_usd_facts(facts, concepts):
    us = facts.get("facts", {}).get("us-gaap", {})
    for label, tags in concepts.items():
        for tag in tags:
            if tag not in us:
                continue
            for row in us[tag].get("units", {}).get("USD", []):
                if row.get("form") not in ("10-K", "10-K/A"):
                    continue
                fy = row.get("fy")
                if fy not in range(2016, 2026):
                    continue
                if row.get("fp") != "FY":
                    continue
                yield {"metric": label, "tag": tag, "fiscal_year": fy,
                       "value": row.get("val"), "start": row.get("start", ""),
                       "end": row.get("end", ""), "filed": row.get("filed", ""),
                       "accession": row.get("accn", "")}

concepts = {
    "assets": ["Assets"],
    "revenues": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "research_development": ["ResearchAndDevelopmentExpense"],
}
with (ROOT / "companies.csv").open(newline="") as f:
    companies = list(csv.DictReader(f))
mapping = get_json("https://www.sec.gov/files/company_tickers.json")
by_ticker = {x["ticker"].upper(): x for x in mapping.values()}
coverage = []
facts_rows = []
filing_rows = []
errors = []
for firm in companies:
    ticker = firm["ticker"].upper()
    item = by_ticker.get(ticker)
    if not item:
        errors.append({"ticker": ticker, "error": "Ticker absent from current SEC map; verify historical entity"})
        continue
    cik = str(item["cik_str"]).zfill(10)
    try:
        sub = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        filings = list(iter_filings(sub))
        annual = [x for x in filings if x.get("form") in ("10-K", "10-K/A") and 2016 <= int(x.get("filingDate", "0000")[:4]) <= 2026]
        years = sorted(set(x["filingDate"][:4] for x in annual))
        for x in annual:
            filing_rows.append({"ticker": ticker, "cik": cik, "form": x.get("form"), "filing_date": x.get("filingDate"), "accession": x.get("accessionNumber"), "primary_document": x.get("primaryDocument")})
        data = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")
        rows = list(annual_usd_facts(data, concepts))
        for x in rows:
            facts_rows.append({"ticker": ticker, "cik": cik, **x})
        coverage.append({"ticker": ticker, "cik": cik, "sec_name": sub.get("name", ""), "sector_group": firm["sector_group"], "filing_years": ";".join(years), "annual_filings": len(annual), "raw_annual_financial_facts": len(rows)})
    except (requests.RequestException, ValueError, KeyError) as exc:
        errors.append({"ticker": ticker, "cik": cik, "error": str(exc)[:300]})

def write_csv(filename, rows, columns):
    with (OUT / filename).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
write_csv("filing_coverage.csv", coverage, ["ticker", "cik", "sec_name", "sector_group", "filing_years", "annual_filings", "raw_annual_financial_facts"])
write_csv("annual_filings.csv", filing_rows, ["ticker", "cik", "form", "filing_date", "accession", "primary_document"])
write_csv("financial_facts_raw.csv", facts_rows, ["ticker", "cik", "metric", "tag", "fiscal_year", "value", "start", "end", "filed", "accession"])
write_csv("errors.csv", errors, ["ticker", "cik", "error"])
(OUT / "manifest.json").write_text(json.dumps({"sample_requested": len(companies), "firms_with_coverage": len(coverage), "errors": len(errors), "source": "SEC EDGAR", "years": "2016-2025", "warning": "Raw facts include duplicates and amendments; not analysis-ready. No financial effects estimated."}, indent=2))
print(f"Firms with coverage: {len(coverage)}/{len(companies)}; errors: {len(errors)}")
