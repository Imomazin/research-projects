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
            time.sleep(0.3)
            oa = client.get(f"https://api.openalex.org/works/doi:{quote(r['doi'], safe='/')}?mailto={MAILTO}", sec=False)
            records[r["key"]]["openalex"] = json.loads(oa) if oa else None
        if r["title_query"]:
            url = ("https://api.crossref.org/works?rows=5&mailto=" + MAILTO +
                   "&query.bibliographic=" + quote(r["title_query"]))
            time.sleep(1.0)
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
        time.sleep(1.0)
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
        time.sleep(1.0)
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
            end = d.get("end", q)
            if prev is None or end > prev["float_date"]:
                floats[d["cik"]] = {"cik": d["cik"], "name": d["entityName"], "float": d["val"],
                                    "float_date": end, "float_accn": d["accn"], "frame": q}
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


# --------------------------------------------------------------------- macro indices

MACRO_PAGES = {
    "Geopolitical Risk": "https://www.matteoiacoviello.com/gpr.htm",
    "Economic Policy Uncertainty": "https://www.policyuncertainty.com/us_monthly.html",
    "Economic Policy Uncertainty Categorical": "https://www.policyuncertainty.com/categorical_epu.html",
    "Economic Policy Uncertainty Global": "https://www.policyuncertainty.com/global_monthly.html",
    "World Uncertainty Index": "https://worlduncertaintyindex.com/data/",
}
MACRO_NAMES = {
    "data_gpr_export.xls": "Geopolitical Risk Monthly.xls",
    "data_gpr_daily_recent.xls": "Geopolitical Risk Daily.xls",
    "us_policy_uncertainty_data.xlsx": "Economic Policy Uncertainty United States.xlsx",
    "categorical_epu_data.xlsx": "Economic Policy Uncertainty Categorical.xlsx",
    "global_policy_uncertainty_data.xlsx": "Economic Policy Uncertainty Global.xlsx",
    "wui_data.xlsx": "World Uncertainty Index.xlsx",
    "wpui_data.xlsx": "World Pandemic Uncertainty Index.xlsx",
    "wusi_data.xlsx": "World Uncertainty Spillover Index.xlsx",
    "wtui_data.xlsx": "World Trade Uncertainty Index.xlsx",
    "gscpi_data.xlsx": "Global Supply Chain Pressure Index.xlsx",
    "gscpi_data.csv": "Global Supply Chain Pressure Index.csv",
}
GSCPI_URLS = ["https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx",
              "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.csv"]


def stage_macro(client, proj: Path, data: Path, log: list, **kw):
    import importlib
    from urllib.parse import urljoin
    out = proj / "Datasets" / "Raw Macro"
    out.mkdir(parents=True, exist_ok=True)
    targets = list(GSCPI_URLS)
    for name, page in MACRO_PAGES.items():
        body = client.get(page, sec=False)
        if not body:
            log.append(f"macro page failed {page}")
            continue
        for href in re.findall(r'href=["\']([^"\']+)["\']', body.decode("utf-8", "ignore"), flags=re.I):
            full = urljoin(page, href)
            base = full.split("?")[0].rsplit("/", 1)[-1].lower()
            if base in MACRO_NAMES and full not in targets:
                targets.append(full)
    manifest = []
    for url in targets:
        base = url.split("?")[0].rsplit("/", 1)[-1].lower()
        time.sleep(4)
        body = client.get(url, sec=False, use_cache=False)
        if not body:
            log.append(f"macro download failed {url}")
            manifest.append({"file": MACRO_NAMES[base], "url": url, "status": "failed", "retrieved": now()})
            continue
        fn = out / MACRO_NAMES[base]
        fn.write_bytes(body)
        import hashlib
        manifest.append({"file": fn.name, "url": url, "status": "downloaded", "bytes": len(body),
                         "sha256": hashlib.sha256(body).hexdigest(), "retrieved": now()})
        log.append(f"macro {fn.name} {len(body)} bytes")
    with open(out / "Macro Retrieval Manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "url", "status", "bytes", "sha256", "retrieved"])
        w.writeheader()
        w.writerows(manifest)


# --------------------------------------------------------------------- filings

FIRST_FY, LAST_FY = 2017, 2025
PART_LIMIT = 40_000_000


def load_module(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_FP = {}


def parser(parser_path: str):
    if "fp" not in _FP:
        _FP["fp"] = load_module("fp", parser_path)
    return _FP["fp"]


def parse_filing(raw: bytes, parser_path: str) -> dict:
    fp = parser(parser_path)
    text = fp.to_text(raw)
    out = {"text_chars": len(text)}
    for item in ("item1", "item1a", "item7"):
        sec, info = fp.extract(text, item)
        if item == "item1a" and not info["ok"]:
            sec, info2 = fp.extract(text, "item1a_alt")
            info = {**info2, "fallback": True}
        out[item] = sec
        out[item + "_info"] = info
    return out


def parse_exhibit(raw: bytes, parser_path: str) -> tuple[str, dict]:
    fp = parser(parser_path)
    return fp.extract(fp.to_text(raw), "mdna_exhibit")


def part_writer(folder: Path, prefix: str):
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(folder.glob(prefix + " Part *.jsonl.gz"))
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    names = [a + b for a in [""] + list(letters) for b in letters]
    idx = len(existing)
    state = {"fh": None, "size": 0, "idx": idx}

    def write(rec: dict):
        line = (json.dumps(rec) + "\n").encode()
        if state["fh"] is None or state["size"] > PART_LIMIT:
            if state["fh"]:
                state["fh"].close()
            path = folder / f"{prefix} Part {names[state['idx']]}.jsonl.gz"
            state["idx"] += 1
            state["fh"] = gzip.open(path, "wb", compresslevel=9)
            state["raw"] = path
            state["size"] = 0
        state["fh"].write(line)
        state["size"] = state["fh"].fileobj.tell()

    def close():
        if state["fh"]:
            state["fh"].close()
    return write, close


def stage_filings(client, proj: Path, data: Path, log: list, **kw):
    from concurrent.futures import ProcessPoolExecutor
    import hashlib
    t0 = time.time()
    budget = float(kw.get("budget_hours", 5.0)) * 3600
    sample = list(csv.DictReader(open(proj / "Datasets" / "Sampling Frame" / "Sample Firms.csv")))
    index_path = proj / "Datasets" / "Filings Index.csv"
    done = set()
    fields = ["cik", "fiscal_year", "form", "accession", "filing_date", "report_date", "primary_document", "url",
              "doc_bytes", "doc_sha256", "n_tenk_in_fy", "n_amendments_in_fy", "text_chars",
              "item1_chars", "item1a_chars", "item7_chars", "item1_ok", "item1a_ok", "item1a_fallback", "item7_ok",
              "item7_source", "item1a_by_reference", "item7_by_reference", "status"]
    if index_path.exists():
        for r in csv.DictReader(open(index_path)):
            done.add(r["cik"])
    new_file = not index_path.exists()
    idx_fh = open(index_path, "a", newline="")
    idx_w = csv.DictWriter(idx_fh, fieldnames=fields)
    if new_file:
        idx_w.writeheader()
    write, close = part_writer(data / "Filing Texts", "Filing Texts")
    parser_path = str(Path(__file__).resolve().parent / "filing parser.py")
    pool = ProcessPoolExecutor(max_workers=4)
    pending = []

    def drain(block=False):
        keep = []
        for meta, fut in pending:
            if not block and not fut.done():
                keep.append((meta, fut))
                continue
            try:
                res = fut.result()
            except Exception as exc:
                meta["status"] = f"parse error {type(exc).__name__}"
                idx_w.writerow({k: meta.get(k, "") for k in fields})
                continue
            i1, i1a, i7 = res["item1_info"], res["item1a_info"], res["item7_info"]
            meta.update({"text_chars": res["text_chars"], "item1_chars": len(res["item1"]),
                         "item1a_chars": len(res["item1a"]), "item7_chars": len(res["item7"]),
                         "item1_ok": int(i1["ok"]), "item1a_ok": int(i1a["ok"]),
                         "item1a_fallback": int(bool(i1a.get("fallback"))), "item7_ok": int(i7["ok"]),
                         "item7_source": "main" if i7["ok"] else "",
                         "item1a_by_reference": int(bool(i1a.get("by_reference"))),
                         "item7_by_reference": int(bool(i7.get("by_reference"))), "status": "parsed"})
            rec = {"cik": meta["cik"], "fiscal_year": meta["fiscal_year"], "accession": meta["accession"],
                   "filing_date": meta["filing_date"], "report_date": meta["report_date"],
                   "item1": res["item1"], "item1a": res["item1a"], "item7": res["item7"]}
            if (not i7["ok"] or i7.get("by_reference")) and meta.get("exhibit_raw"):
                sec, info = parse_exhibit(meta.pop("exhibit_raw"), parser_path)
                if info["ok"]:
                    rec["item7"] = sec
                    meta.update({"item7_chars": len(sec), "item7_ok": 1, "item7_source": "annual report exhibit"})
            meta.pop("exhibit_raw", None)
            write(rec)
            idx_w.writerow({k: meta.get(k, "") for k in fields})
        pending[:] = keep

    n_firms = 0
    for firm in sample:
        cik = int(firm["cik"])
        if str(cik) in done:
            continue
        if time.time() - t0 > budget:
            log.append(f"time budget reached after {n_firms} firms; resume required")
            break
        sub = submissions_full(client, cik)
        n_firms += 1
        if not sub:
            idx_w.writerow({"cik": cik, "status": "submissions missing"})
            continue
        by_fy = {}
        amend = {}
        for f in sub["all_filings"]:
            if not f.get("reportDate"):
                continue
            fy = fiscal_year(f["reportDate"])
            if not FIRST_FY <= fy <= LAST_FY:
                continue
            if f["form"] == "10-K/A":
                amend[fy] = amend.get(fy, 0) + 1
            if f["form"] == "10-K":
                by_fy.setdefault(fy, []).append(f)
        if not by_fy:
            idx_w.writerow({"cik": cik, "status": "no 10-K in window"})
        for fy, fl in sorted(by_fy.items()):
            fl.sort(key=lambda f: (f["reportDate"], f["filingDate"]))
            f = fl[-1]
            acc = f["accessionNumber"].replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{f['primaryDocument']}"
            meta = {"cik": cik, "fiscal_year": fy, "form": f["form"], "accession": f["accessionNumber"],
                    "filing_date": f["filingDate"], "report_date": f["reportDate"],
                    "primary_document": f["primaryDocument"], "url": url,
                    "n_tenk_in_fy": len(fl), "n_amendments_in_fy": amend.get(fy, 0)}
            raw = client.get(url)
            if raw is None:
                meta["status"] = "download failed"
                idx_w.writerow({k: meta.get(k, "") for k in fields})
                continue
            meta["doc_bytes"] = len(raw)
            meta["doc_sha256"] = hashlib.sha256(raw).hexdigest()
            # annual report exhibit for MD&A incorporated by reference
            ix = client.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/index.json")
            if ix:
                try:
                    items = json.loads(ix)["directory"]["item"]
                    ex13 = [it["name"] for it in items if re.search(r"ex(?:hibit)?[-_ ]?13", it["name"], re.I)
                            and it["name"].lower().endswith((".htm", ".html", ".txt"))]
                    if ex13:
                        meta["exhibit_raw"] = client.get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{ex13[0]}")
                except (KeyError, ValueError):
                    pass
            pending.append((meta, pool.submit(parse_filing, raw, parser_path)))
            if len(pending) > 24:
                drain(block=True)
            else:
                drain()
        idx_fh.flush()
    drain(block=True)
    pool.shutdown()
    close()
    idx_fh.close()
    remaining = sum(1 for f in sample if str(int(f["cik"])) not in done) - n_firms
    log.append(f"filings stage processed {n_firms} firms; remaining {remaining}; minutes {(time.time()-t0)/60:.1f}")


# --------------------------------------------------------------------- XBRL company facts

CONCEPTS = [
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet", "SalesRevenueGoodsNet", "SalesRevenueServicesNet", "RevenuesNetOfInterestExpense",
    "CostOfRevenue", "CostOfGoodsAndServicesSold", "GrossProfit", "OperatingIncomeLoss", "NetIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesForeign", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
    "Assets", "Liabilities", "StockholdersEquity", "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "LongTermDebtNoncurrent", "LongTermDebt",
    "InventoryNet", "NetCashProvidedByUsedInOperatingActivities", "PaymentsToAcquirePropertyPlantAndEquipment",
    "ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    "PaymentsToAcquireBusinessesNetOfCashAcquired", "RestructuringCharges", "SellingGeneralAndAdministrativeExpense",
    "PaymentsForRepurchaseOfCommonStock", "PaymentsOfDividends", "PaymentsOfDividendsCommonStock",
    "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic", "PaymentsToAcquireProductiveAssets",
    "InterestExpense", "IncomeTaxExpenseBenefit", "DepreciationDepletionAndAmortization", "OperatingExpenses",
    "CostsAndExpenses", "AssetsCurrent", "LiabilitiesCurrent", "Goodwill",
]


def stage_facts(client, proj: Path, data: Path, log: list, **kw):
    sample = list(csv.DictReader(open(proj / "Datasets" / "Sampling Frame" / "Sample Firms.csv")))
    out_dir = data / "Company Facts"
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = ["cik", "taxonomy", "concept", "unit", "start", "end", "val", "accn", "fy", "fp", "form", "filed", "frame"]
    path = out_dir / "Financial Facts Long.csv.gz"
    n = missing = 0
    with gzip.open(path, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for firm in sample:
            cik = int(firm["cik"])
            body = client.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
            if not body:
                missing += 1
                continue
            facts = json.loads(body).get("facts", {})
            for tax, concepts in facts.items():
                for concept, spec in concepts.items():
                    if tax == "us-gaap" and concept not in CONCEPTS:
                        continue
                    if tax == "dei" and concept not in ("EntityPublicFloat", "EntityCommonStockSharesOutstanding"):
                        continue
                    if tax not in ("us-gaap", "dei"):
                        continue
                    for unit, rows in spec.get("units", {}).items():
                        for r in rows:
                            if r.get("end", "") < "2014-01-01" or r.get("form") not in ("10-K", "10-K/A", "10-Q", "10-Q/A"):
                                continue
                            w.writerow({"cik": cik, "taxonomy": tax, "concept": concept, "unit": unit,
                                        **{k: r.get(k, "") for k in fields[4:]}})
                            n += 1
    log.append(f"company facts rows {n}; firms missing {missing}")


# --------------------------------------------------------------------- revision sources

FRED_SERIES = {"CPIAUCSL": "Consumer Price Index All Urban Consumers.csv",
               "PPIFIS": "Producer Price Index Final Demand.csv",
               "PCUOMFGOMFG": "Producer Price Index Total Manufacturing Industries.csv"}


def stage_revision(client, proj: Path, data: Path, log: list, **kw):
    """Price indices for deflation, a version check of the stored macro files, fresh Crossref
    and OpenAlex records for every cited and candidate reference, and searches for recent
    competing studies."""
    import hashlib
    out = proj / "Datasets" / "Raw Macro" / "Revision"
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for sid, name in FRED_SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        body = client.get(url, sec=False, use_cache=False)
        if body:
            (out / name).write_bytes(body)
        manifest.append({"file": name, "url": url, "status": "downloaded" if body else "failed",
                         "bytes": len(body) if body else "", "sha256": hashlib.sha256(body).hexdigest() if body else "",
                         "retrieved": now()})
        time.sleep(2)
    stored = list(csv.DictReader(open(proj / "Datasets" / "Raw Macro" / "Macro Retrieval Manifest.csv")))
    for r in stored:
        if r["status"] != "downloaded":
            continue
        time.sleep(4)
        body = client.get(r["url"], sec=False, use_cache=False)
        sha = hashlib.sha256(body).hexdigest() if body else ""
        local = proj / "Datasets" / "Raw Macro" / r["file"]
        manifest.append({"file": "version check: " + r["file"], "url": r["url"], "status": "downloaded" if body else "failed",
                         "bytes": len(body) if body else "", "sha256": sha, "retrieved": now(),
                         "stored_sha256": r["sha256"], "stored_file_present": local.exists(),
                         "identical_to_stored": bool(body) and sha == r["sha256"]})
    with open(out / "Revision Retrieval Manifest.csv", "w", newline="") as fh:
        keys = ["file", "url", "status", "bytes", "sha256", "retrieved", "stored_sha256", "stored_file_present", "identical_to_stored"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(manifest)
    log.append(f"revision macro files: {len(manifest)}")
    lit = proj / "Literature"
    recs = {}
    bib = list(csv.DictReader(open(lit / "Verified Bibliography.csv")))
    cand = list(csv.DictReader(open(lit / "Revision Candidate References.csv")))
    for r in bib + cand:
        key, doi, tq = r["key"], r.get("doi", ""), r.get("title_query", "")
        rec = {}
        if doi:
            body = client.get(f"https://api.crossref.org/works/{quote(doi, safe='')}?mailto={MAILTO}", sec=False, use_cache=False)
            rec["doi"] = doi
            rec["message"] = json.loads(body)["message"] if body else None
            oa = client.get(f"https://api.openalex.org/works/doi:{quote(doi, safe='/')}?mailto={MAILTO}", sec=False, use_cache=False)
            rec["openalex"] = json.loads(oa) if oa else None
            time.sleep(0.4)
        if tq:
            body = client.get("https://api.crossref.org/works?rows=5&mailto=" + MAILTO + "&query.bibliographic=" + quote(tq),
                              sec=False, use_cache=False)
            rec["search"] = json.loads(body)["message"]["items"] if body else []
            time.sleep(1.0)
        recs[key] = rec
    (lit / "Crossref Records" / "Revision Reference Records.json").write_text(json.dumps(recs, indent=1))
    log.append(f"revision reference records: {len(recs)}; doi hits {sum(1 for v in recs.values() if v.get('message'))}")
    wide = {}
    for term in ["risk factor disclosure boilerplate informativeness", "number of risk factors 10-K firm",
                 "risk disclosure similarity across firms homogeneity", "risk factor disclosure regulation S-K 2020 summary",
                 "textual risk disclosure organizational resilience", "multiple risks co-occurrence firm disclosure",
                 "polycrisis firms strategy", "strategic response crisis firms text analysis",
                 "supply chain risk disclosure pandemic performance", "documented risk mitigation disclosure firm actions",
                 "dynamic capabilities sensing seizing reconfiguring measurement text", "organisational resilience revenue recovery covid firms",
                 "inflation pass-through firms 2022 prices margins", "geopolitical risk firm exposure 2022 Russia Ukraine"]:
        body = client.get("https://api.crossref.org/works?rows=30&mailto=" + MAILTO +
                          "&filter=from-pub-date:2023-01-01,type:journal-article&query.bibliographic=" + quote(term),
                          sec=False, use_cache=False)
        if body:
            wide[term] = json.loads(body)["message"]["items"]
        time.sleep(1.0)
    sl = {}
    for term in ["risk", "uncertainty", "resilience", "crisis", "disruption", "geopolitical", "strategy", "leadership"]:
        body = client.get(f"https://api.crossref.org/journals/{SL_ISSN}/works?rows=100&mailto={MAILTO}"
                          f"&filter=from-pub-date:2024-01-01&query.bibliographic={quote(term)}", sec=False, use_cache=False)
        if body:
            for it in json.loads(body)["message"]["items"]:
                sl[it["DOI"]] = it
        time.sleep(1.0)
    (lit / "Crossref Records" / "Revision Literature Searches.json").write_text(json.dumps({"wide": wide, "strategy_and_leadership": list(sl.values())}, indent=1))
    log.append(f"revision searches: {len(wide)} terms; S&L records since 2024: {len(sl)}")


# --------------------------------------------------------------------- contextual language model comparator

NLI_MODEL = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
CAT_PHRASE = {"geopolitical": "geopolitical conflict or sanctions", "trade": "trade policy and tariffs",
              "regulatory": "regulatory change", "cyber": "cybersecurity threats", "technology": "technological disruption",
              "supply": "supply chain disruption", "climate": "climate and environmental risk",
              "macro": "macroeconomic and financial instability", "pandemic": "the pandemic"}


def stage_nli(client, proj: Path, data: Path, log: list, **kw):
    """Zero-shot natural language inference scores for the response validation sample."""
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "torch==2.5.1", "--index-url",
                    "https://download.pytorch.org/whl/cpu"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==4.46.3", "sentencepiece==0.2.0",
                    "protobuf==5.28.3"], check=True)
    import torch
    from huggingface_hub import model_info
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    info = model_info(NLI_MODEL)
    tok = AutoTokenizer.from_pretrained(NLI_MODEL, revision=info.sha)
    mod = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL, revision=info.sha).eval()
    labels = {v.lower(): k for k, v in mod.config.id2label.items()}
    rows = list(csv.DictReader(open(proj / "Validation" / "Response Validation Sample.csv")))
    out = []
    hyps = {"implemented": "The company has already taken an action to reduce or manage its exposure to {}.",
            "planned": "The company only plans or may take an action about {} in the future.",
            "routine": "The sentence describes a routine business activity unrelated to {}."}
    for r in rows:
        rec = {"item_id": r["item_id"]}
        for name, h in hyps.items():
            enc = tok(r["sentence"][:2000], h.format(CAT_PHRASE[r["category"]]), return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                pr = torch.softmax(mod(**enc).logits, dim=-1)[0]
            rec[f"entail_{name}"] = round(float(pr[labels["entailment"]]), 4)
        out.append(rec)
    with open(proj / "Validation" / "Response Validation Language Model Scores.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    (proj / "Validation" / "Language Model Version.txt").write_text(
        f"model {NLI_MODEL}\nrevision {info.sha}\ntorch 2.5.1 cpu; transformers 4.46.3\nrun {now()}\n")
    log.append(f"nli scored {len(out)} items with {NLI_MODEL}@{info.sha}")


def stage_convergence(client, proj: Path, data: Path, log: list, **kw):
    """Run the second text pass for the alternative convergence measures on the data-branch texts."""
    import subprocess, sys
    out = proj / "Datasets" / "Derived" / "Revision"
    out.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(proj / "Analysis" / "build convergence measures.py"), str(data / "Filing Texts"),
                        str(out / "Convergence Measures.csv")], capture_output=True, text=True)
    log.append(r.stdout[-3000:])
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])


BLS_SERIES = {"CUSR0000SA0": "Consumer Price Index All Urban Consumers Seasonally Adjusted BLS.csv",
              "WPSFD4": "Producer Price Index Final Demand Seasonally Adjusted BLS.csv"}


def stage_prices(client, proj: Path, data: Path, log: list, **kw):
    """Price indices from the Bureau of Labor Statistics public API (FRED timed out from the runner)."""
    import hashlib
    import requests
    out = proj / "Datasets" / "Raw Macro" / "Revision"
    out.mkdir(parents=True, exist_ok=True)
    man = []
    for sid, name in BLS_SERIES.items():
        rows = []
        for a, b in ((2012, 2020), (2021, 2026)):
            r = requests.post("https://api.bls.gov/publicAPI/v1/timeseries/data/",
                              json={"seriesid": [sid], "startyear": str(a), "endyear": str(b)},
                              headers={"User-Agent": "Imo Enang strategic risk research " + MAILTO}, timeout=90)
            js = r.json()
            log.append(f"BLS {sid} {a}-{b}: {js.get('status')} {js.get('message')}")
            for d in js.get("Results", {}).get("series", [{}])[0].get("data", []):
                if d["period"].startswith("M") and d["period"] != "M13":
                    rows.append({"year": int(d["year"]), "month": int(d["period"][1:]), "value": float(d["value"])})
            time.sleep(3)
        rows.sort(key=lambda x: (x["year"], x["month"]))
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["year", "month", "value"])
            w.writeheader()
            w.writerows(rows)
        body = (out / name).read_bytes()
        man.append({"file": name, "url": f"https://api.bls.gov/publicAPI/v1/timeseries/data/ series {sid}", "status": "downloaded" if rows else "failed",
                    "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "retrieved": now(), "rows": len(rows)})
    with open(out / "Price Index Retrieval Manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(man[0].keys()))
        w.writeheader()
        w.writerows(man)


def stage_references(client, proj: Path, data: Path, log: list, **kw):
    """Crossref and OpenAlex records (with abstracts) for the revision candidate references only."""
    lit = proj / "Literature"
    recs = {}
    for r in csv.DictReader(open(lit / "Revision Candidate References.csv")):
        rec = {}
        if r["doi"]:
            body = client.get(f"https://api.crossref.org/works/{quote(r['doi'], safe='')}?mailto={MAILTO}", sec=False, use_cache=False)
            rec["doi"], rec["message"] = r["doi"], (json.loads(body)["message"] if body else None)
            oa = client.get(f"https://api.openalex.org/works/doi:{quote(r['doi'], safe='/')}?mailto={MAILTO}", sec=False, use_cache=False)
            rec["openalex"] = json.loads(oa) if oa else None
            time.sleep(0.5)
        if r["title_query"]:
            body = client.get("https://api.crossref.org/works?rows=5&mailto=" + MAILTO + "&query.bibliographic=" + quote(r["title_query"]),
                              sec=False, use_cache=False)
            rec["search"] = json.loads(body)["message"]["items"] if body else []
            time.sleep(1.0)
        recs[r["key"]] = rec
    (lit / "Crossref Records" / "Revision Candidate Records.json").write_text(json.dumps(recs, indent=1))
    log.append(f"candidate records {len(recs)}; doi hits {sum(1 for v in recs.values() if v.get('message'))}")


STAGES = {"literature": stage_literature, "frame": stage_frame, "macro": stage_macro,
          "filings": stage_filings, "facts": stage_facts, "revision": stage_revision, "nli": stage_nli, "convergence": stage_convergence, "prices": stage_prices, "references": stage_references}
