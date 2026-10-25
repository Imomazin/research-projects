"""Apply the inclusion criteria to the frame candidates and draw the study sample.

Criteria: operating company; SIC outside finance (6000-6999), utilities (4900-4999)
and public administration or unclassified (9000 and above); a 10-K for fiscal year
2018; public float of at least 0.5 billion US dollars in 2018. From the eligible
frame a proportional stratified random sample of 800 firms is drawn by SIC division
with a fixed seed. The exclusion log records every step.
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FRAME = HERE.parent / "Datasets" / "Sampling Frame"
SEED = 20181231
N = 800


def division(sic: float) -> str:
    if 1000 <= sic < 1500: return "Mining"
    if 1500 <= sic < 1800: return "Construction"
    if 2000 <= sic < 4000: return "Manufacturing"
    if 4000 <= sic < 4900: return "Transportation and communications"
    if 5000 <= sic < 5200: return "Wholesale trade"
    if 5200 <= sic < 6000: return "Retail trade"
    if 7000 <= sic < 9000: return "Services"
    if 100 <= sic < 1000: return "Agriculture"
    return "Other"


f = pd.read_csv(FRAME / "Frame Candidates.csv")
f["sic"] = pd.to_numeric(f["sic"], errors="coerce")
log = [("Entities with 2018 public float in SEC XBRL frames (from frame stage log)", 5720), ("Public float of at least 0.5 billion US dollars", len(f))]
steps = [
    ("Operating company", f["entity_type"] == "operating"),
    ("SIC code present", f["sic"].notna()),
    ("Excluding finance, insurance and real estate (SIC 6000-6999)", ~f["sic"].between(6000, 6999)),
    ("Excluding utilities (SIC 4900-4999)", ~f["sic"].between(4900, 4999)),
    ("Excluding public administration and unclassified (SIC 9000 and above)", f["sic"] < 9000),
    ("Filed a 10-K for fiscal year 2018", f["has_fy2018_tenk"] == 1),
]
mask = pd.Series(True, index=f.index)
for label, m in steps:
    mask &= m
    log.append((label, int(mask.sum())))
elig = f[mask].copy()
elig["division"] = elig["sic"].apply(division)
share = elig["division"].value_counts() / len(elig)
alloc = np.floor(share * N).astype(int)
rem = (share * N - alloc).sort_values(ascending=False)
for d in rem.index[: N - alloc.sum()]:
    alloc[d] += 1
rng = np.random.default_rng(SEED)
picked = []
for d, k in alloc.items():
    pool = elig[elig["division"] == d].sort_values("cik")
    idx = rng.choice(len(pool), size=k, replace=False)
    picked.append(pool.iloc[np.sort(idx)])
sample = pd.concat(picked).sort_values("cik")
sample["sampling_weight"] = sample["division"].map(elig["division"].value_counts() / alloc)
log.append((f"Proportional stratified random sample by SIC division (seed {SEED})", len(sample)))
elig.to_csv(FRAME / "Eligible Frame.csv", index=False)
sample.to_csv(FRAME / "Sample Firms.csv", index=False)
pd.DataFrame(log, columns=["step", "firms remaining"]).to_csv(FRAME / "Sample Selection Log.csv", index=False)
pd.DataFrame({"eligible": elig["division"].value_counts(), "sampled": alloc}).to_csv(FRAME / "Sample Allocation.csv")
print(pd.DataFrame(log)); print(pd.DataFrame({"eligible": elig["division"].value_counts(), "sampled": alloc}))
