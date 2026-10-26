"""Retrieve and audit small original UCI datasets.

Install: python -m pip install ucimlrepo pandas
Use: python "Download Datasets.py" --dataset "RT IoT"
     python "Download Datasets.py" --dataset "All Small"
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from ucimlrepo import fetch_ucirepo

CATALOGUE = {
    "Maintenance": (601, "Manufacturing Maintenance.csv"),
    "SECOM": (179, "Semiconductor Manufacturing.csv"),
    "Steel": (198, "Steel Quality Faults Original.csv"),
    "RT IoT": (942, "Real Time IoT Security.csv"),
}

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def fetch(key, directory):
    identifier, filename = CATALOGUE[key]
    dataset = fetch_ucirepo(id=identifier)
    features, targets = dataset.data.features, dataset.data.targets
    if features is None or features.empty:
        raise ValueError("Feature table missing: " + key)
    frame = pd.concat([features.reset_index(drop=True), targets.reset_index(drop=True)], axis=1) if targets is not None else features
    path = directory / filename
    frame.to_csv(path, index=False)
    return dict(dataset=key, uci_id=identifier, rows=len(frame),
                columns=len(frame.columns), filename=filename,
                sha256=sha256(path), utc=datetime.now(timezone.utc).isoformat(),
                source=f"https://archive.ics.uci.edu/dataset/{identifier}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=[*CATALOGUE, "All Small"], default="All Small")
    parser.add_argument("--output", default="Local Data")
    args = parser.parse_args()
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    selection = ["Maintenance", "SECOM", "Steel"] if args.dataset == "All Small" else [args.dataset]
    audit = [fetch(key, folder) for key in selection]
    (folder / "Download Audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    main()
