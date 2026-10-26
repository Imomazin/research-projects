"""Download, validate and preserve the UCI gas-turbine annual files.

Source: UCI Machine Learning Repository dataset 551, DOI 10.24432/C5WC95.
Licence: Creative Commons Attribution 4.0. This is an observed single-site
turbine dataset, NOT an observed multi-factory federation.
"""
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATASET = "https://archive.ics.uci.edu/static/public/551/gas+turbine+co+and+nox+emission+data+set.zip"
ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "Datasets" / "Gas Turbine Annual Records"
YEARS = {
    "2011": "Gas Turbine First Year.csv",
    "2012": "Gas Turbine Second Year.csv",
    "2013": "Gas Turbine Third Year.csv",
    "2014": "Gas Turbine Fourth Year.csv",
    "2015": "Gas Turbine Fifth Year.csv",
}
EXPECTED = {"AT", "AP", "AH", "AFDP", "GTEP", "TIT", "TAT", "TEY", "CDP", "CO", "NOX"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    request = urllib.request.Request(DATASET, headers={"User-Agent": "IndustryResearch/1.0 (data-acquisition)"})
    with urllib.request.urlopen(request, timeout=150) as response:
        downloaded = response.read()
    if not zipfile.is_zipfile(io.BytesIO(downloaded)):
        raise ValueError("UCI response is not an expected ZIP archive")
    audit = {
        "dataset": "Gas Turbine CO and NOx Emission Data Set",
        "reference": "10.24432/C5WC95",
        "license": "CC BY 4.0",
        "source": DATASET,
        "archive_sha256": sha(downloaded),
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "annual_files": [],
        "industrial_client_partition": "single-site, no independent factories",
        "temporal_partition": "source annual files preserved separately",
    }
    years = {}
    with zipfile.ZipFile(io.BytesIO(downloaded)) as archive:
        files = [f for f in archive.namelist() if not f.endswith("/")]
        for year, name in YEARS.items():
            candidates = [p for p in files if Path(p).name.lower() == f"gt_{year}.csv"]
            if len(candidates) != 1:
                raise ValueError(f"Expected one original annual CSV for {year}, got {candidates}")
            original = archive.read(candidates[0])
            frame = pd.read_csv(io.BytesIO(original))
            if set(frame.columns) != EXPECTED or frame.isna().all(axis=0).any():
                raise ValueError(f"Unexpected sensor schema in {year}: {frame.columns.tolist()}")
            if not all(pd.api.types.is_numeric_dtype(frame[c]) for c in frame.columns):
                raise ValueError(f"Nonnumeric features in year {year}")
            years[year] = {"original_name": candidates[0], "file_name": name,
                           "rows": len(frame), "columns": list(frame.columns),
                           "sha256": sha(original), "bytes": len(original), "content": original}
    total = sum(v["rows"] for v in years.values())
    if total != 36733:
        raise ValueError(f"Unexpected total UCI row count: {total}")
    DEST.mkdir(parents=True, exist_ok=True)
    for year, item in years.items():
        path = DEST / item["file_name"]
        path.write_bytes(item["content"])
        audit["annual_files"].append({k: v for k, v in item.items() if k != "content"} | {"year": year})
    audit["total_observations"] = total
    (DEST / "Acquisition Audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verified": True, "total_observations": total,
                      "years": {k: item["rows"] for k, item in years.items()},
                      "source_archive_sha256": audit["archive_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
