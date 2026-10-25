"""Format the reference list in Emerald Harvard style from verified bibliographic records (revision).

Differences from build references.py: records are the fresh Crossref and OpenAlex records
retrieved for the revision (Revision Reference Records.json, Revision Candidate Records.json)
with the bibliographic-search matches in Revision Accepted Records.json as a fallback, and
articles published online without a volume are formatted as ahead of print.

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
REC = {}
for fn in ("Candidate Reference Records.json", "Revision Accepted Records.json", "Revision Reference Records.json",
           "Revision Candidate Records.json"):
    p = HERE / "Crossref Records" / fn
    if p.exists():
        for k, v in json.loads(p.read_text()).items():
            if v.get("message"):
                REC[k] = v
EXTRA = HERE / "Manual Verified References.json"
MANUAL = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}


SMALL = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with", "versus", "vs"}


def initials(given: str) -> str:
    given = re.sub(r"\(.*?\)", "", given)
    parts = [p for p in re.split(r"[\s\-\.]+", given.strip()) if p and p[0].isalpha()]
    return "".join(p[0].upper() + "." for p in parts)


def fix_case(name: str) -> str:
    if not name.isupper():
        return name
    n = name.title()
    return re.sub(r"\bMc([a-z])", lambda m: "Mc" + m.group(1).upper(), n)


def title_case_if_upper(t: str) -> str:
    letters = [c for c in t if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
        words = t.lower().split()
        return " ".join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))
    return t


def clean(t: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    t = re.sub(r"\s+", " ", t).replace("\u2729", "").replace("\u2010", "-").strip()
    return t.rstrip("*").rstrip(".").strip()


def authors_from(m: dict, oa: dict | None) -> list[tuple[str, str]]:
    out = [(a.get("family", "").replace(" Jr.", "").replace("\u2010", "-"), a.get("given", "")) for a in (m.get("author") or []) if a.get("family")]
    if not out and oa:
        for au in oa.get("authorships", []):
            name = au["author"]["display_name"].split()
            out.append((name[-1], " ".join(name[:-1])))
    return out


def fmt_authors(auths: list[tuple[str, str]]) -> str:
    names = [f"{fix_case(fam).replace(chr(0x2010), '-')}, {initials(giv)}" for fam, giv in auths]
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
    title = title_case_if_upper(clean(m.get("title", [""])[0]))
    sub = clean((m.get("subtitle") or [""])[0])
    if sub and sub.lower() not in title.lower():
        title = f"{title}: {sub[0].lower() + sub[1:] if sub[:1].isupper() and not sub[:2].isupper() else sub}"
    venue = clean((m.get("container-title") or [""])[0])
    if venue.startswith("The Stata Journal"):
        venue = "The Stata Journal"
    vol, iss = m.get("volume", ""), m.get("issue", "")
    page = m.get("page", "") or m.get("article-number", "")
    if oa and (not vol or not page or "-" not in page):
        b = oa.get("biblio", {})
        vol = vol or (b.get("volume") or "")
        iss = iss or (b.get("issue") or "")
        if b.get("first_page") and b.get("last_page") and (not page or "-" not in page) \
                and (not page or b["first_page"] == page):
            page = b["first_page"] + "-" + b["last_page"]
        elif not page and b.get("first_page"):
            page = b["first_page"]
    if m.get("article-number"):
        page = str(m["article-number"])            # article number, not a page range
    elif "-" in page and len(set(page.split("-"))) == 1:
        page = page.split("-")[0]
    title = re.sub(r"\s+:", ":", title)
    doi = m.get("DOI", "").lower()
    kind = m.get("type")
    if kind == "proceedings-article" and venue:
        text = f"{fmt_authors(auths)} ({yr}), \"{title}\", {venue}, " + (f"pp. {page}, " if page else "") + f"doi: {doi}."
        return {"key": key, "verified": True, "text": text.replace("\u2010", "-"), "year": yr,
                "first_author": auths[0][0] if auths else "", "n_authors": len(auths), "doi": doi, "authors": [a[0] for a in auths]}
    if kind == "journal-article" and venue:
        bits = [f"{fmt_authors(auths)} ({yr}), \"{title}\", {venue}"]
        if vol:
            bits.append(f"Vol. {vol}" + (f" No. {iss}" if iss else ""))
            if page:
                bits.append(("pp. " if "-" in page else "") + page.replace("--", "-"))
        else:
            bits.append("Vol. ahead-of-print No. ahead-of-print")
        text = ", ".join(bits) + f", doi: {doi}."
    else:
        pub = clean(m.get("publisher", ""))
        series = venue or pub
        num = re.search(r"w(\d+)$", doi)
        series_txt = f"NBER Working Paper No. {num.group(1)}" if "10.3386" in doi and num else series
        text = f"{fmt_authors(auths)} ({yr}), \"{title}\", {series_txt}, doi: {doi}."
    surname_key = auths[0][0] if auths else ""
    text = text.replace("\u2010", "-")
    return {"key": key, "verified": True, "text": text, "year": yr, "first_author": surname_key,
            "n_authors": len(auths), "doi": doi, "authors": [a[0] for a in auths]}


def in_text(e: dict) -> str:
    a = [x.replace("\u2010", "-").replace(" Jr.", "") for x in e["authors"]]
    fix = fix_case
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
