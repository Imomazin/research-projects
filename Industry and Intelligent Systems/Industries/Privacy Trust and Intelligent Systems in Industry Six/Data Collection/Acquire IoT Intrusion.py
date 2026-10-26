"""Acquire full UCI real-time IoT intrusion data with original archive provenance.

UCI dataset 942, DOI: 10.24432/C5P338, CC BY 4.0.
This is an IoT intrusion benchmark; it is NOT a factory field dataset.
"""
import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SOURCE = "https://archive.ics.uci.edu/static/public/942/rt-iot2022.zip"
BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "Datasets" / "IoT Intrusion Source"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    request = urllib.request.Request(SOURCE, headers={"User-Agent": "IndustryResearch/1.0 (academic-data)"})
    with urllib.request.urlopen(request, timeout=180) as response:
        original = response.read()
    if not zipfile.is_zipfile(io.BytesIO(original)):
        raise ValueError("Invalid original UCI IoT source archive")
    with zipfile.ZipFile(io.BytesIO(original)) as archive:
        entries = [m for m in archive.namelist() if not m.endswith("/")]
        candidate_names = [e for e in entries if e.lower().endswith(".csv")]
        if not candidate_names:
            candidate_names = [e for e in entries if "rt_iot" in Path(e).name.lower()]
        if not candidate_names:
            raise ValueError("UCI archive does not contain an identifiable data table")
        matches = []
        for e in candidate_names:
            raw = archive.read(e)
            try:
                head = pd.read_csv(io.BytesIO(raw), nrows=2)
                if "Attack_type" in head.columns:
                    matches.append((e, raw))
            except Exception:
                continue
        if len(matches) != 1:
            raise ValueError(f"Expected one class-labelled UCI table; found {[m[0] for m in matches]}")
        raw_name, payload = matches[0]
        frame = pd.read_csv(io.BytesIO(payload), low_memory=False)
        if len(frame) != 123117 or "Attack_type" not in frame.columns:
            raise ValueError(f"Unexpected IoT dataset structure: {frame.shape}")
        if frame.shape[1] < 80 or frame["Attack_type"].isna().any():
            raise ValueError("Missing or incomplete label information")
        distribution = {str(k): int(v) for k,v in frame["Attack_type"].value_counts().items()}
        audit = {
            "dataset": "RT-IoT2022 original source",
            "source_url": SOURCE,
            "citation": "10.24432/C5P338",
            "license": "CC BY 4.0",
            "acquired_utc": datetime.now(timezone.utc).isoformat(),
            "source_archive_sha256": sha(original),
            "data_file_inside_archive": raw_name,
            "uncompressed_data_sha256": sha(payload),
            "rows": int(len(frame)),
            "columns": list(frame.columns),
            "class_distribution": distribution,
            "scope": "IoT devices and simulated attacks; security transfer evaluation, not manufacturing field measurements",
            "federated_sites_confirmed": False,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "Real Time IoT Traffic.zip").write_bytes(original)
    (OUT / "Acquisition Audit.json").write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"verified": True, "rows": audit["rows"], "n_columns": len(audit["columns"]),
                      "n_classes": len(distribution), "archive_sha256": sha(original),
                      "source_csv": raw_name}, indent=2))


if __name__ == "__main__":
    main()
