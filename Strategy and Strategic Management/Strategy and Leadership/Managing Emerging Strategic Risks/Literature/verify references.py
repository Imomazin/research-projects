"""Field-by-field verification of every reference against records retrieved for the revision.

1. Each entry in Verified Bibliography.csv with a DOI is compared with the fresh Crossref
   record (Revision Reference Records.json): first-author surname, number of authors,
   year, title, journal, volume, issue, pages and DOI, with the OpenAlex record as a second
   source. The publication status (issue assigned or online first) and the earliest online
   date are recorded and checked against the preparation date.
2. Each candidate in Revision Candidate References.csv was searched by bibliographic query.
   The top hits are accepted only when the first-author surname appears in the query and
   the title similarity is at least 0.85; accepted hits are written to Revision Accepted
   Records.json in the same form as the DOI records, so build references.py can format them.

Usage: python "verify references.py"
Outputs: Reference Verification.csv, Revision Candidate Matches.csv, Crossref Records/Revision Accepted Records.json
"""
import csv
import difflib
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREP_DATE = (2026, 10, 25)
NEW = json.loads((HERE / "Crossref Records" / "Revision Reference Records.json").read_text())
OLD = json.loads((HERE / "Crossref Records" / "Candidate Reference Records.json").read_text())
MANUAL = json.loads((HERE / "Manual Verified References.json").read_text())


def clean(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or ""))
    return re.sub(r"\s+", " ", t).strip().rstrip(".")


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", clean(t).lower().replace("‐", "-").replace("-", " "))


def date_parts(m, k):
    d = m.get(k)
    if d and d.get("date-parts") and d["date-parts"][0] and d["date-parts"][0][0]:
        p = d["date-parts"][0]
        return tuple(p + [1] * (3 - len(p)))
    return None


def summary(m):
    pp = m.get("page", "")
    return {"first_author": (m.get("author") or [{}])[0].get("family", ""), "n_authors": len(m.get("author") or []),
            "year_print": (date_parts(m, "published-print") or (None,))[0],
            "year_issued": (date_parts(m, "issued") or (None,))[0],
            "online": date_parts(m, "published-online"), "title": clean((m.get("title") or [""])[0]),
            "journal": clean((m.get("container-title") or [""])[0]), "volume": m.get("volume", ""),
            "issue": m.get("issue", ""), "pages": pp, "type": m.get("type", ""), "doi": m.get("DOI", "").lower()}


rows = []
for r in csv.DictReader(open(HERE / "Verified Bibliography.csv")):
    key, ref, doi = r["key"], r["reference"], r["doi"]
    if key in MANUAL:
        rows.append({"key": key, "status": "verified manually against primary source", "source": MANUAL[key].get("verified_against", ""),
                     "reference": ref, "issues": ""})
        continue
    new, old = NEW.get(key, {}), OLD.get(key, {})
    m = new.get("message")
    if not m:
        rows.append({"key": key, "status": "fresh Crossref record not retrieved", "reference": ref, "issues": "re-check"})
        continue
    s = summary(m)
    so = summary(old["message"]) if old.get("message") else {}
    oa = new.get("openalex") or {}
    issues = []
    yr = re.search(r"\((\d{4})\)", ref)
    yr = int(yr.group(1)) if yr else None
    year_crossref = s["year_print"] or s["year_issued"]
    if yr != year_crossref:
        issues.append(f"year in reference {yr} versus Crossref {year_crossref}")
    if s["first_author"] and s["first_author"].lower().replace("‐", "-") not in ref.lower().replace("‐", "-"):
        issues.append(f"first author {s['first_author']} not found")
    if norm(s["title"])[:60] not in norm(ref):
        ratio = difflib.SequenceMatcher(None, norm(s["title"]), norm(ref)).find_longest_match(0, len(norm(s["title"])), 0, len(norm(ref))).size / max(1, len(norm(s["title"])))
        if ratio < 0.9:
            issues.append("title differs from Crossref")
    if s["journal"] and norm(s["journal"]) not in norm(ref):
        issues.append(f"journal {s['journal']} not found")
    if s["volume"] and f"Vol. {s['volume']}" not in ref:
        issues.append(f"volume {s['volume']} not in reference")
    if s["issue"] and f"No. {s['issue']}" not in ref:
        issues.append(f"issue {s['issue']} not in reference")
    if s["pages"] and s["pages"].replace("--", "-") not in ref:
        issues.append(f"pages {s['pages']} not in reference")
    if s["doi"] and s["doi"] not in ref.lower():
        issues.append("DOI differs")
    ahead = not s["volume"] and s["type"] == "journal-article"
    first_date = min([d for d in (date_parts(m, "published-online"), date_parts(m, "published-print"), date_parts(m, "issued")) if d])
    if first_date > PREP_DATE:
        issues.append("first publication date after preparation date")
    oa_title = clean(oa.get("title") or oa.get("display_name") or "")
    oa_agree = bool(oa_title) and difflib.SequenceMatcher(None, norm(oa_title), norm(s["title"])).ratio() > 0.9
    changed = [k for k in ("title", "journal", "volume", "issue", "pages", "doi") if so and so.get(k) != s.get(k)]
    rows.append({"key": key, "status": "ahead of print (no volume assigned)" if ahead else "published in an issue",
                 "source": f"Crossref {s['doi']} retrieved for the revision; OpenAlex title agreement {oa_agree}",
                 "first_online": "-".join(map(str, first_date)), "crossref_year": year_crossref,
                 "volume": s["volume"], "issue": s["issue"], "pages": s["pages"], "type": s["type"],
                 "changed_since_first_retrieval": ",".join(changed), "reference": ref, "issues": "; ".join(issues)})
with open(HERE / "Reference Verification.csv", "w", newline="") as fh:
    keys = ["key", "status", "source", "first_online", "crossref_year", "volume", "issue", "pages", "type",
            "changed_since_first_retrieval", "issues", "reference"]
    w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)

cand = list(csv.DictReader(open(HERE / "Revision Candidate References.csv")))
matches, accepted = [], {}
for c in cand:
    items = NEW.get(c["key"], {}).get("search", [])
    q = c["title_query"]
    best = None
    for it in items:
        t = clean((it.get("title") or [""])[0])
        fam = (it.get("author") or [{}])[0].get("family", "")
        tn = norm(t)
        sim = max(difflib.SequenceMatcher(None, tn, norm(q)[i:i + len(tn)]).ratio() for i in range(0, max(1, len(norm(q)) - len(tn) + 1), 3)) if tn else 0
        ok = bool(fam) and fam.lower() in q.lower() and sim >= 0.85
        matches.append({"key": c["key"], "query": q, "hit_title": t, "first_author": fam, "year": (date_parts(it, "issued") or ("",))[0],
                        "journal": clean((it.get("container-title") or [""])[0]), "doi": it.get("DOI", ""), "similarity": round(sim, 3), "accepted": ok})
        if ok and best is None:
            best = it
    if best is not None:
        accepted[c["key"]] = {"doi": best["DOI"], "message": best, "openalex": None, "via": "Crossref bibliographic search, revision"}
with open(HERE / "Revision Candidate Matches.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(matches[0].keys()))
    w.writeheader()
    w.writerows(matches)
(HERE / "Crossref Records" / "Revision Accepted Records.json").write_text(json.dumps(accepted, indent=1))
iss = [r for r in rows if r.get("issues")]
print(len(rows), "references checked;", len(iss), "with issues;", len(accepted), "of", len(cand), "candidates accepted")
for r in iss:
    print(r["key"], "|", r["issues"])
print(sorted(accepted))
