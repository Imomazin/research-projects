"""Collection stages executed in GitHub Actions. Each stage takes
(client, project_dir, data_dir, log, **kwargs)."""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import json
import random
import re
import time
import zipfile
from pathlib import Path
from urllib.parse import quote

MAILTO = "imomazin.ae@gmail.com"
SL_ISSN = "1087-8572"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------- literature

def stage_literature(client, proj: Path, data: Path, log: list, **kw):
    out_dir = proj / "Literature" / "Crossref Records"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(proj / "Literature" / "Candidate References.csv")))
    records = {}
    for r in rows:
        if r["doi"]:
            url = f"https://api.crossref.org/works/{quote(r['doi'], safe='')}?mailto={MAILTO}"
            body = client.get(url, sec=False)
            records[r["key"]] = {"doi": r["doi"],
                                 "message": json.loads(body)["message"] if body else None}
        if r["title_query"]:
            url = ("https://api.crossref.org/works?rows=5&mailto=" + MAILTO +
                   "&query.bibliographic=" + quote(r["title_query"]))
            body = client.get(url, sec=False)
            items = json.loads(body)["message"]["items"] if body else []
            records.setdefault(r["key"], {})["search"] = items
    (out_dir / "Candidate Reference Records.json").write_text(json.dumps(records, indent=1))
    log.append(f"crossref candidates: {len(records)}; doi hits "
               f"{sum(1 for v in records.values() if v.get('message'))}")
    # Strategy & Leadership corpus on the study's themes
    sl = {}
    for term in ["risk", "uncertainty", "resilience", "scenario", "foresight", "crisis", "disruption",
                 "geopolitical", "agility", "ambidexterity", "dynamic capabilities", "supply chain",
                 "cyber", "artificial intelligence", "volatility", "turbulence"]:
        url = (f"https://api.crossref.org/journals/{SL_ISSN}/works?rows=100&mailto={MAILTO}"
               f"&filter=from-pub-date:2016-01-01&query.bibliographic={quote(term)}")
        body = client.get(url, sec=False)
        if body:
            for it in json.loads(body)["message"]["items"]:
                sl[it["DOI"]] = it
    (out_dir / "Strategy and Leadership Corpus.json").write_text(json.dumps(list(sl.values()), indent=1))
    log.append(f"S&L corpus records: {len(sl)}")
    # Wider searches for competing studies
    wide = {}
    for term in ["risk factor disclosure co-occurrence multiple risks firm",
                 "compound risks firms strategic response resilience",
                 "polycrisis organisations strategy",
                 "interconnected risks enterprise risk management firm performance",
                 "textual risk disclosure organizational resilience covid",
                 "risk disclosure boilerplate versus substantive action firms",
                 "emerging risks 10-K textual analysis",
                 "strategic risk management dynamic capabilities empirical",
                 "organizational resilience accounting performance recovery shock",
                 "supply chain risk disclosure firm performance pandemic",
                 "geopolitical risk exposure firm level text",
                 "corporate foresight firm performance longitudinal"]:
        url = ("https://api.crossref.org/works?rows=25&mailto=" + MAILTO +
               "&filter=from-pub-date:2012-01-01,type:journal-article&query.bibliographic=" + quote(term))
        body = client.get(url, sec=False)
        if body:
            wide[term] = json.loads(body)["message"]["items"]
    (out_dir / "Competing Study Searches.json").write_text(json.dumps(wide, indent=1))
    log.append(f"wide searches: {len(wide)}")




# --------------------------------------------------------------------- sampling frame

def fiscal_year(period_end: str) -> int:
    """Compustat convention: fiscal years ending January to May belong to the prior year."""
    y, m = int(period_end[:4]), int(period_end[5:7])
    return y if m >= 6 else y - 1


def submissions_full(client, cik: int) -> dict | None:
    body = client.get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    if not body:
        return None
    data = json.loads(body)
    recent = data["filings"]["recent"]
    cols = list(recent.keys())
    rows = [dict(zip(cols, vals)) for vals in zip(*[recent[c] for c in cols])]
    for f in data["filings"].get("files", []):
        extra = client.get(f"https://data.sec.gov/submissions/{f['name']}")
        if extra:
            ex = json.loads(extra)
            rows += [dict(zip(ex.keys(), vals)) for vals in zip(*[ex[c] for c in ex.keys()])]
    data["all_filings"] = rows
    return data


def stage_frame(client, proj: Path, data: Path, log: list, **kw):
    out = proj / "Datasets" / "Sampling Frame"
    out.mkdir(parents=True, exist_ok=True)
    floats = {}
    for q in ("CY2018Q1I", "CY2018Q2I", "CY2018Q3I", "CY2018Q4I"):
        body = client.get(f"https://data.sec.gov/api/xbrl/frames/dei/EntityPublicFloat/USD/{q}.json")
        if not body:
            log.append(f"public float frame missing {q}")
            continue
        for d in json.loads(body)["data"]:
            prev = floats.get(d["cik"])
            if prev is None or d["end"] > prev["end"]:
                floats[d["cik"]] = {"cik": d["cik"], "name": d["entityName"], "float": d["val"],
                                    "float_date": d["end"], "float_accn": d["accn"]}
    log.append(f"entities with 2018 public float: {len(floats)}")
    cand = [v for v in floats.values() if v["float"] >= 500_000_000]
    log.append(f"public float >= 0.5bn: {len(cand)}")
    rows = []
    for v in cand:
        sub = submissions_full(client, v["cik"])
        if not sub:
            v["submissions"] = "missing"
            rows.append(v)
            continue
        tenks = [f for f in sub["all_filings"] if f["form"] in ("10-K", "10-K405")
                 and f.get("reportDate")]
        fys = sorted({fiscal_year(f["reportDate"]) for f in tenks})
        v.update({
            "sic": sub.get("sic"), "sic_description": sub.get("sicDescription"),
            "state_incorporation": sub.get("stateOfIncorporation"),
            "entity_type": sub.get("entityType"), "category": sub.get("category"),
            "fiscal_year_end": sub.get("fiscalYearEnd"),
            "exchanges_now": "|".join(x for x in (sub.get("exchanges") or []) if x),
            "tickers_now": "|".join(sub.get("tickers") or []),
            "tenk_fiscal_years": "|".join(str(y) for y in fys),
            "has_fy2018_tenk": int(2018 in fys),
            "foreign_filer_forms": int(any(f["form"] in ("20-F", "40-F") for f in sub["all_filings"])),
        })
        rows.append(v)
    keys = sorted({k for r in rows for k in r})
    with open(out / "Frame Candidates.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    log.append(f"frame candidates written: {len(rows)}")


STAGES = {"literature": stage_literature, "frame": stage_frame}
