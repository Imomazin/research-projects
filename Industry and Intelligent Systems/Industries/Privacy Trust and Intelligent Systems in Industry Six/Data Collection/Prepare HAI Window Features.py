"""Derive 30-second window features from the HAI 21.03 attack sessions.

Source: https://github.com/icsdataset/hai (commit recorded in the audit), HAI 21.03 files
test1.csv.gz to test5.csv.gz. Licence CC BY-SA 4.0; the derived table inherits it.
Citation: Shin, Lee, Yun and Min, CSET 2021, doi:10.1145/3474718.3474719.

Each window aggregates 30 consecutive one-second records. Features per sensor are the mean,
standard deviation and last-minus-first change. A window is labelled as attack when any of
its seconds carries the source attack flag. Event identifiers mark contiguous attack runs so
that detection delay can be measured. No raw HAI records are written by this script.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW = 30


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def windows(frame, session):
    labels = ["attack", "attack_P1", "attack_P2", "attack_P3"]
    sensors = [c for c in frame.columns if c not in labels + ["time"]]
    attack = frame["attack"].to_numpy()
    starts = np.flatnonzero((attack == 1) & (np.r_[0, attack[:-1]] == 0))
    event = np.full(len(frame), -1)
    for e, s in enumerate(starts):
        end = s
        while end < len(attack) and attack[end] == 1:
            end += 1
        event[s:end] = e
    n = len(frame) // WINDOW
    values = frame[sensors].to_numpy(float)[: n * WINDOW].reshape(n, WINDOW, len(sensors))
    out = pd.DataFrame(np.hstack([values.mean(axis=1), values.std(axis=1),
                                  values[:, -1, :] - values[:, 0, :]]),
                       columns=[f"{s} Mean" for s in sensors] + [f"{s} Std" for s in sensors]
                       + [f"{s} Change" for s in sensors])
    att = attack[: n * WINDOW].reshape(n, WINDOW)
    ev = event[: n * WINDOW].reshape(n, WINDOW)
    out.insert(0, "Session", session)
    out.insert(1, "Window Start", frame["time"].to_numpy()[: n * WINDOW: WINDOW])
    out.insert(2, "Window Index", np.arange(n))
    out.insert(3, "Attack", (att.max(axis=1) > 0).astype(int))
    out.insert(4, "Attack Seconds", att.sum(axis=1))
    out["Event ID"] = [int(r[r >= 0].min()) if (r >= 0).any() else -1 for r in ev]
    out["Event First Second"] = [int(np.argmax(r >= 0)) if (r >= 0).any() else -1 for r in ev]
    return out, len(starts)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--hai-root", required=True, help="Folder holding hai-21.03 from the official repository")
    cli.add_argument("--source-commit", required=True)
    cli.add_argument("--output-dir", required=True)
    args = cli.parse_args()
    folder = Path(args.hai_root) / "hai-21.03"
    tables, audit_files, events = [], {}, {}
    for i in range(1, 6):
        path = folder / f"test{i}.csv.gz"
        frame = pd.read_csv(path)
        table, count = windows(frame, f"test{i}")
        tables.append(table)
        audit_files[path.name] = {"sha256": digest(path), "rows": int(len(frame)),
                                  "attack_seconds": int(frame["attack"].sum()),
                                  "first_time": str(frame["time"].iloc[0]),
                                  "last_time": str(frame["time"].iloc[-1])}
        events[f"test{i}"] = count
    data = pd.concat(tables, ignore_index=True)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / "HAI Window Features.csv.gz"
    data.to_csv(target, index=False, compression={"method": "gzip", "mtime": 0})
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": "https://github.com/icsdataset/hai",
        "source_commit": args.source_commit,
        "version": "HAI 21.03",
        "licence": "CC BY-SA 4.0 (derived table shares the licence)",
        "citation_doi": "10.1145/3474718.3474719",
        "window_seconds": WINDOW,
        "windows": int(len(data)), "attack_windows": int(data["Attack"].sum()),
        "events_by_session": events, "source_files": audit_files,
        "feature_columns": int(data.shape[1] - 7),
        "derived_table_sha256": digest(target),
        "notes": "Sessions are recording periods of one testbed, not independent plants.",
    }
    (out / "HAI Acquisition Audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({k: audit[k] for k in ("windows", "attack_windows", "events_by_session")}, indent=2))


if __name__ == "__main__":
    main()
