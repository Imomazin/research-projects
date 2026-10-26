"""Prepare a labelled, machine-aware feature table from Bosch CNC vibration data.

Source: https://github.com/boschresearch/CNC_Machining
Original data: Tnani, Feil and Diepold, Procedia CIRP (2022).
Data licensed CC BY 4.0. Original HDF5 recordings remain external.
This is a deterministic feature-extraction utility, not a completed experiment.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy.signal import welch
from scipy.stats import kurtosis


def source_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def axis_features(signal, prefix, sample_rate):
    sample = np.asarray(signal, dtype=np.float64)
    if sample.size < 16 or not np.all(np.isfinite(sample)):
        raise ValueError("Nonfinite or too short vibration signal")
    power = float(np.mean(sample ** 2))
    f, density = welch(sample, fs=sample_rate, nperseg=min(2048, len(sample)))
    idx = int(np.argmax(density[1:]) + 1) if len(density) > 1 else 0
    excess_kurtosis = float(kurtosis(sample, fisher=True, bias=False))
    return {
        prefix + " Mean": float(sample.mean()),
        prefix + " Standard Deviation": float(sample.std(ddof=0)),
        prefix + " Root Mean Square": float(np.sqrt(power)),
        prefix + " Peak Amplitude": float(np.max(np.abs(sample))),
        prefix + " Peak To Peak": float(np.ptp(sample)),
        prefix + " Kurtosis": excess_kurtosis if np.isfinite(excess_kurtosis) else 0.0,
        prefix + " Dominant Frequency Hz": float(f[idx]),
    }


def transform(path, root, sample_rate):
    parts = path.relative_to(root).parts
    if len(parts) != 4 or parts[0] not in {"M01", "M02", "M03"}:
        raise ValueError("Unexpected source directory: " + str(path))
    machine, operation, condition, _ = parts
    if condition not in {"good", "bad"}:
        raise ValueError("Expected good or bad condition")
    filename_parts = path.stem.split("_")
    if len(filename_parts) < 5 or filename_parts[0] != machine:
        raise ValueError("Unexpected source filename: " + str(path))
    with h5py.File(path, "r") as file:
        values = file["vibration_data"][:]
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("Expected three sensor axes")
    record = {
        "Machine": machine,
        "Operation": operation,
        "Condition": condition,
        "Anomaly": int(condition == "bad"),
        "Timeframe": "_".join(filename_parts[1:3]),
        "Source File": str(path.relative_to(root)),
        "Source SHA": source_digest(path),
        "Samples": int(values.shape[0]),
    }
    for col, axis in zip(("X", "Y", "Z"), values.T):
        record.update(axis_features(axis, col, sample_rate))
    return record


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--data-root", required=True,
                     help="Path to official Bosch repo data folder (M01, M02, M03).")
    cli.add_argument("--output-dir", default="Local Data")
    cli.add_argument("--sample-rate", type=int, default=2000)
    cli.add_argument("--max-files", type=int, default=0,
                     help="Optional code smoke subset, explicitly reported as incomplete.")
    args = cli.parse_args()
    root = Path(args.data_root).resolve()
    sources = sorted(root.glob("M*/OP*/*/*.h5"))
    if not sources:
        raise SystemExit("No Bosch source recordings found")
    if args.max_files:
        sources = sources[:args.max_files]
    records = [transform(p, root, args.sample_rate) for p in sources]
    frame = pd.DataFrame.from_records(records)
    if frame["Source File"].duplicated().any():
        raise ValueError("Duplicate source observations")
    if not bool((frame["Anomaly"] == (frame["Condition"] == "bad").astype(int)).all()):
        raise ValueError("Label inconsistency")
    directory = Path(args.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    table = directory / "Bosch CNC Derived Features.csv"
    frame.to_csv(table, index=False)
    audit = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": "https://github.com/boschresearch/CNC_Machining",
        "source_publication": "https://doi.org/10.1016/j.procir.2022.04.022",
        "data_license": "CC BY 4.0",
        "rows_processed": int(len(frame)),
        "machines": frame["Machine"].value_counts().to_dict(),
        "conditions": frame["Condition"].value_counts().to_dict(),
        "operations": int(frame["Operation"].nunique()),
        "sample_rate_hz": args.sample_rate,
        "truncated_by_max_files": bool(args.max_files),
        "machine_identifiers": "Natural recorded machines, not independent companies.",
        "feature_table_sha256": source_digest(table),
    }
    (directory / "Bosch CNC Acquisition Audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
