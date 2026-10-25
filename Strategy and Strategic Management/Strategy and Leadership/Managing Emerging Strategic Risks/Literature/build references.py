"""Format the reference list in Emerald Harvard style from verified bibliographic records.

Every entry is built from the Crossref record retrieved by DOI, with missing
author or pagination fields completed from the OpenAlex record for the same DOI.
Entries without a verified record are not formatted; they are listed as
unverified so they can be removed from the text.

Usage: python "build references.py" <file with one citation key per line> <output json>
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REC = json.loads((HERE / "Crossref Records" / "Candidate Reference Records.json").read_text())
EXTRA = HERE / "Manual Verified References.json"
MANUAL = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}


def initials(given: str) -> str:
    parts = re.split(r"[\s\-]+", given.strip())
    return "".join(p[0] + "." for p in parts if p)


def clean(t: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    t = re.sub(r"\s+", " ", t)
    return t.rstrip("*")


def authors_from(m: dict, oa: dict | None) -> list[tuple[str, str]]:
    out = [(a.get("family", ""), a.get("given", "")) for a in (m.get("author") or []) if a.get("family")]
    if not out and oa:
        for au in oa.get("authorships", []):
            name = au["author"]["display_name"].split()
            out.append((name[-1], " ".join(name[:-1])))
    return out


def fmt_authors(auths: list[tuple[str, str]]) -> str:
    names = [f"{fam.title() if fam.isupper() else fam}, {initials(giv)}" for fam, giv in auths]
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def year_of(m: dict) -> int:
    for k in ("published-print", "issued", "published-online"):
        if m.get(k) and m[k].get("date-parts") and m[k]["date-parts"][0][0]:
            return m[k]["date-parts"][0][0]
    return 0


def entry(key: str) -> dict:
    if key in MANUAL:
        return MANUAL[key]
    r = REC.get(key)
    if not r or not r.get("message"):
        return {"key": key, "verified": False}
    m, oa = r["message"], r.get("openalex")
    auths = authors_from(m, oa)
    yr = year_of(m)
    title = clean(m.get("title", [""])[0])
    venue = clean((m.get("container-title") or [""])[0])
    vol, iss = m.get("volume", ""), m.get("issue", "")
    page = m.get("page", "") or m.get("article-number", "")
    if oa and (not vol or not page):
        b = oa.get("biblio", {})
        vol = vol or (b.get("volume") or "")
        iss = iss or (b.get("issue") or "")
        if not page and b.get("first_page"):
            page = b["first_page"] + ("-" + b["last_page"] if b.get("last_page") else "")
    doi = m.get("DOI", "").lower()
    kind = m.get("type")
    if kind == "journal-article" and venue:
        bits = [f"{fmt_authors(auths)} ({yr}), \"{title}\", {venue}"]
        if vol:
            bits.append(f"Vol. {vol}" + (f" No. {iss}" if iss else ""))
        if page:
            bits.append(("pp. " if "-" in page else "") + page.replace("--", "-"))
        text = ", ".join(bits) + f", doi: {doi}."
    else:
        pub = clean(m.get("publisher", ""))
        series = venue or pub
        num = re.search(r"w(\d+)$", doi)
        series_txt = f"NBER Working Paper No. {num.group(1)}" if "10.3386" in doi and num else series
        text = f"{fmt_authors(auths)} ({yr}), \"{title}\", {series_txt}, doi: {doi}."
    surname_key = auths[0][0] if auths else ""
    return {"key": key, "verified": True, "text": text, "year": yr, "first_author": surname_key,
            "n_authors": len(auths), "doi": doi, "authors": [a[0] for a in auths]}


def in_text(e: dict) -> str:
    a = e["authors"]
    fix = lambda s: s.title() if s.isupper() else s
    if len(a) == 1:
        return f"{fix(a[0])}, {e['year']}"
    if len(a) == 2:
        return f"{fix(a[0])} and {fix(a[1])}, {e['year']}"
    return f"{fix(a[0])} et al., {e['year']}"


if __name__ == "__main__":
    keys = [k.strip() for k in open(sys.argv[1]) if k.strip()]
    out = [entry(k) for k in keys]
    for e in out:
        if e.get("verified"):
            e["cite"] = in_text(e)
    out.sort(key=lambda e: (e.get("first_author", "").lower(), e.get("year", 0)))
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    for e in out:
        print(e.get("cite"), "|", e.get("text", "UNVERIFIED " + e["key"])[:160])
