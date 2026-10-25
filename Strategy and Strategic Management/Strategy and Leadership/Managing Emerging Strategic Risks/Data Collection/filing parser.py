"""Convert a 10-K primary document to plain text and extract Items 1, 1A and 7.

Section boundaries are located by heading patterns. Because tables of contents
repeat the headings, every start match is paired with the first later end match
and the longest plausible span is kept. Extraction quality flags are returned
with the text so that failures are visible rather than silent.
"""
from __future__ import annotations

import html as htmlmod
import re
import unicodedata

from lxml import etree, html

BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "section", "ul", "ol", "dt", "dd"}
SEP = r"[\s\.\:\-–—‒ ]*"

ITEM = {
    "item1": (rf"item{SEP}1{SEP}(?:and{SEP}2{SEP})?business\b",
              [rf"item{SEP}1a{SEP}risk", rf"item{SEP}1b{SEP}unresolved", rf"item{SEP}2{SEP}(?:description{SEP}of{SEP})?propert"]),
    "item1a": (rf"item{SEP}1a{SEP}risk{SEP}factors",
               [rf"item{SEP}1b{SEP}unresolved", rf"item{SEP}1c{SEP}cyber", rf"item{SEP}2{SEP}(?:description{SEP}of{SEP})?propert",
                rf"item{SEP}3{SEP}legal"]),
    "item7": (rf"item{SEP}7{SEP}management.{{0,3}}s{SEP}discussion",
              [rf"item{SEP}7a{SEP}quantitative", rf"item{SEP}8{SEP}(?:consolidated{SEP})?financial{SEP}statements"]),
    "item1a_alt": (rf"risk{SEP}factors\s*\n",
                   [rf"unresolved{SEP}staff{SEP}comments", rf"item{SEP}2{SEP}propert", rf"properties\s*\n", rf"legal{SEP}proceedings\s*\n"]),
    "mdna_exhibit": (rf"management.{{0,3}}s{SEP}discussion{SEP}and{SEP}analysis",
                     [rf"report{SEP}of{SEP}independent{SEP}registered", rf"consolidated{SEP}statements?{SEP}of{SEP}(?:income|operations|earnings)",
                      rf"management.{{0,3}}s{SEP}report{SEP}on{SEP}internal"]),
}
LIMITS = {"item1": (1500, 900_000), "item1a": (2000, 900_000), "item7": (2000, 1_500_000),
          "item1a_alt": (5000, 900_000), "mdna_exhibit": (5000, 1_500_000)}


def to_text(raw: bytes) -> str:
    """Plain text with line breaks at block elements; numeric tables removed."""
    head = raw[:2000].lower()
    if b"<html" not in head and b"<body" not in head and b"<div" not in raw[:20000].lower():
        text = raw.decode("utf-8", "ignore")
        return normalise(text)
    try:
        doc = html.fromstring(raw)
    except (etree.ParserError, ValueError):
        return normalise(re.sub(r"<[^>]+>", " ", raw.decode("utf-8", "ignore")))
    for bad in doc.xpath("//script|//style|//*[local-name()='header']|//*[local-name()='hidden']"):
        bad.drop_tree()
    for el in doc.xpath("//*[contains(translate(@style,'DISPLAY:NOE','display:noe'),'display:none')]"):
        el.drop_tree()
    for tbl in doc.xpath("//table"):
        t = tbl.text_content()
        letters = sum(ch.isalpha() for ch in t)
        digits = sum(ch.isdigit() for ch in t)
        if digits > 0.25 * max(letters, 1) or (len(t) > 0 and letters < 40 and digits > 10):
            tbl.drop_tree()
    for el in doc.iter():
        if isinstance(el.tag, str) and el.tag.split("}")[-1].lower() in BLOCK:
            el.tail = "\n" + (el.tail or "")
    return normalise(doc.text_content())


def normalise(text: str) -> str:
    text = htmlmod.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[ \t\r\f\v ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def extract(text: str, item: str) -> tuple[str, dict]:
    start_pat, end_pats = ITEM[item]
    lo, hi = LIMITS[item]
    lead = r"(?:^|\n)[ \t]*(?:part[ \t]+i{1,2}[\s,\.\-]*)?"
    starts = [m for m in re.finditer(lead + "(" + start_pat + ")", text, flags=re.I)]
    ends = sorted({m.start(1) for p in end_pats for m in re.finditer(lead + "(" + p + ")", text, flags=re.I)})
    best = (0, None, None)
    for s in starts:
        nxt = [e for e in ends if e > s.end(1)]
        if not nxt:
            continue
        span = nxt[0] - s.start(1)
        if lo <= span <= hi and span > best[0]:
            best = (span, s.start(1), nxt[0])
    info = {"starts": len(starts), "ends": len(ends), "ok": best[1] is not None}
    if best[1] is None:
        return "", info
    section = text[best[1]:best[2]]
    # sections that only point elsewhere
    if len(section) < 4000 and re.search(r"incorporated (?:herein )?by reference", section, re.I):
        info["by_reference"] = True
    return section, info


SENT_SPLIT = re.compile(r"(?<=[\.\?\!])\s+(?=[A-Z\"\(])|\n+")


def sentences(section: str) -> list[str]:
    out = []
    for s in SENT_SPLIT.split(section):
        s = s.strip()
        if len(s) >= 25 and sum(ch.isalpha() for ch in s) >= 20:
            out.append(s)
    return out
