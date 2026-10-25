"""Intercoder agreement for the human coding of documented strategic response.

Usage: python "compute agreement.py" "<coder one sheet.csv>" "<coder two sheet.csv>"
Writes Intercoder Agreement.csv next to this script. Both sheets must have the
columns of Response Human Coding Sheet.csv with every item coded.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FIELDS = ["category_relevant", "response_class", "threat_link", "status", "reconfiguration", "resource_commitment", "qualifies"]


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    po = np.mean(a == b)
    pe = sum(np.mean(a == c) * np.mean(b == c) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def alpha_nominal(a, b):
    vals = np.concatenate([a, b])
    cats = sorted(set(vals))
    n = len(vals)
    do = np.mean(a != b)
    freq = np.array([np.sum(vals == c) for c in cats])
    de = 1 - (freq * (freq - 1)).sum() / (n * (n - 1))
    return 1 - do / de if de > 0 else np.nan


def main(p1, p2):
    a, b = pd.read_csv(p1).set_index("item_id"), pd.read_csv(p2).set_index("item_id")
    b = b.reindex(a.index)
    rows = []
    for f in FIELDS:
        x, y = a[f].astype(str).str.strip(), b[f].astype(str).str.strip()
        ok = (x != "") & (y != "") & (x != "nan") & (y != "nan")
        if ok.sum() == 0:
            rows.append({"field": f, "items": 0})
            continue
        x, y = x[ok].to_numpy(), y[ok].to_numpy()
        rows.append({"field": f, "items": int(ok.sum()), "raw_agreement": float(np.mean(x == y)),
                     "cohen_kappa": kappa(x, y), "krippendorff_alpha": alpha_nominal(x, y)})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "Intercoder Agreement.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
