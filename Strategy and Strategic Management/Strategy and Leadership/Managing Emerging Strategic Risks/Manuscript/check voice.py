"""Flag wording that breaks the manuscript style rules.

Usage: python "check voice.py" <text or markdown file>
"""
import re
import sys

BANNED = [
    "delve", "leverage", "harness", "unlock", "unleash", "elevate", "amplify", "reimagine", "revolutionis",
    "transformative", "game-chang", "game chang", "groundbreaking", "cutting-edge", "cutting edge", "trailblaz",
    "visionary", "vibrant", "compelling", "powerful", "profound", "remarkable", "exceptional", "unprecedented",
    "seamless", "holistic", "multifaceted", "pivotal", "crucial", "paramount", "cornerstone", "catalyst",
    "beacon", "tapestry", "journey", "landscape", "ecosystem", "paradigm", "new chapter", "at its core",
    "in today's", "against this backdrop", "it is worth noting", "it is important to note", "needless to say",
    "this underscores", "highlights the importance", "moving forward", "going forward", "in conclusion",
    "ultimately", "synergy", "best-in-class", "world-class", "future-proof", "next-generation", "drive value",
    "deliver value", "create value", "move the needle", "low-hanging", "quick wins", "strategic alignment",
    "in this context", "from a broader perspective", "it is evident", "a key takeaway", "one could argue",
    "generally speaking", "the literature suggests", "the findings highlight", "it becomes clear",
    "this demonstrates the significance", "dramatic", "substantial improvement", "significant increase",
    "numerous", "dynamic and", "robust framework", "robust", "intersection of", "where strategy meets",
]
CONTRAST = [r"\bnot (?:just|merely|simply|only)\b[^.]{0,80}\bbut\b", r"\bis not [^.]{1,60}\. it is\b",
            r"\bisn't [^.]{1,60}\. it's\b", r"\bmore than [^.]{1,40}, (?:it|this) is\b", r"\bthe question is not\b",
            r"\bthe issue is not\b", r"\brather than merely\b", r"\bbeyond [^.]{1,40} lies\b"]


def main(path):
    text = open(path, encoding="utf-8").read()
    problems = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if "—" in line or "– " in line:
            problems.append((i, "dash", line[:90]))
        if ", and " in line:
            problems.append((i, "comma before and", line[line.find(", and ") - 40: line.find(", and ") + 20]))
        if "  " in line.strip():
            problems.append((i, "double space", line[:60]))
        for w in BANNED:
            if w in low:
                if w == "robust" and ("robustness" in low and "robust " not in low.replace("robustness", "")):
                    continue
                problems.append((i, f"banned: {w}", line[max(0, low.find(w) - 30): low.find(w) + 40]))
        for c in CONTRAST:
            if re.search(c, low):
                problems.append((i, "contrast formula", line[:90]))
        for sent in re.split(r"(?<=[.!?])\s+", line):
            bare = re.sub(r"\([^()]*\)", "", sent)
            if bare.count(",") > 2 and not sent.startswith("|"):
                problems.append((i, f"{bare.count(',')} commas", sent[:90]))
    for p in problems:
        print(p)
    print(len(problems), "issues")


if __name__ == "__main__":
    main(sys.argv[1])
