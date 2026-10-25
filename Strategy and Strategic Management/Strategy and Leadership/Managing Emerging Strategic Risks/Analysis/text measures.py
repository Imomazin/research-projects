"""Sentence-level risk taxonomy classification and documented-response detection."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAXONOMY = json.loads((HERE / "Risk Taxonomy Dictionary.json").read_text())
CATS = list(TAXONOMY["categories"].keys())
PATTERNS = {c: re.compile(r"(?:%s)" % "|".join(v["patterns"]), re.I) for c, v in TAXONOMY["categories"].items()}
ACT = TAXONOMY["action_sentence"]
SUBJECT = re.compile(ACT["subject"], re.I)
VERBS = re.compile(r"\b(?:%s)\b" % "|".join(ACT["verbs"]), re.I)
MODALS = re.compile(ACT["exclude_modals"], re.I)
ACCOUNTING = re.compile(ACT["exclude_accounting"], re.I)
WINDOW = ACT["proximity_words"]
CATALOGUE = TAXONOMY["hazard_catalogue_threshold"]
WORD = re.compile(r"[a-z][a-z\-']+")


def classify(sentence: str) -> list[str]:
    return [c for c in CATS if PATTERNS[c].search(sentence)]


def is_action(sentence: str) -> bool:
    return bool(SUBJECT.search(sentence) and VERBS.search(sentence)
                and not MODALS.search(sentence) and not ACCOUNTING.search(sentence))


def action_categories(sentence: str) -> list[str]:
    """Categories named within WINDOW words of a realised action verb."""
    if not is_action(sentence):
        return []
    def word_index(pos):
        return len(sentence[:pos].split())
    verb_pos = [word_index(m.start()) for m in VERBS.finditer(sentence)]
    found = []
    for c in CATS:
        for m in PATTERNS[c].finditer(sentence):
            w = word_index(m.start())
            if any(abs(w - v) <= WINDOW for v in verb_pos):
                found.append(c)
                break
    return found


def risk_profile(sents: list[str]) -> dict:
    counts = Counter()
    linked = catalogue = 0
    pairs = Counter()
    for s in sents:
        cs = classify(s)
        counts.update(cs)
        if 2 <= len(cs) < CATALOGUE:
            linked += 1
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    pairs[(cs[i], cs[j])] += 1
        elif len(cs) >= CATALOGUE:
            catalogue += 1
    n = len(sents)
    out = {"n_sent": n, "n_linked": linked, "n_catalogue": catalogue}
    for c in CATS:
        out[f"cnt_{c}"] = counts[c]
    out["pairs"] = {f"{a}|{b}": v for (a, b), v in pairs.items()}
    return out


def response_profile(sents: list[str]) -> dict:
    counts = Counter()
    n_act = 0
    for s in sents:
        if not is_action(s):
            continue
        n_act += 1
        counts.update(action_categories(s))
    out = {"n_action": n_act}
    for c in CATS:
        out[f"act_{c}"] = counts[c]
    return out


def term_vector(text: str) -> Counter:
    return Counter(WORD.findall(text.lower()))


def cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return float("nan")
    common = set(a) & set(b)
    num = sum(a[k] * b[k] for k in common)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else float("nan")
