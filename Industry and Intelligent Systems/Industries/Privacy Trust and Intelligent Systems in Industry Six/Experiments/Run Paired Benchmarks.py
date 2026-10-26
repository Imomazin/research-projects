"""Run paired, versioned federated-learning experiments and summarise uncertainty.

Each configuration is exploratory. Report every result, including failed trials.
Never pick a publication claim based on the repeated test-set rankings.
"""
import argparse
import csv
import itertools
import json
import math
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scipy.stats import t

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "Industrial Federated Benchmark.py"
DEFAULT_OUTPUT = HERE / "Results" / "Repeated Benchmarks"
MODELS = ("linear_baseline", "pooled_mlp", "fedavg", "federated_dp_sgd")


def words(value):
    """Use words in generated filenames and folder names."""
    mapping = dict(enumerate("zero one two three four five six seven eight nine".split()))
    s = format(float(value), ".4f").rstrip("0").rstrip(".")
    return " ".join("point" if x == "." else "minus" if x == "-" else mapping[int(x)] for x in s)


def trial_name(dataset, seed, alpha, noise):
    return (dataset.title() + " Seed " + words(seed) + " Alpha " + words(alpha)
            + " Noise " + words(noise) + ".json")


def flatten_trial(record, source_name):
    config = record["parameters"]
    outcome = []
    for model in MODELS:
        m = record["models"][model]
        for split in ("validation", "test"):
            for metric, result in m[split].items():
                outcome.append({
                    "dataset": config["dataset"],
                    "seed": config["seed"],
                    "alpha": config["alpha"],
                    "noise": config["noise"],
                    "clients": config["clients"],
                    "rounds": config["rounds"],
                    "max_rows": config["max_rows"],
                    "model": model,
                    "evaluation_split": split,
                    "metric": metric,
                    "value": float(result),
                    "source_result": source_name,
                    "epsilon_max": (
                        m["protocol"].get("epsilon_max", "")
                        if model == "federated_dp_sgd" else ""
                    ),
                })
    return outcome


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def group_summary(rows):
    groups = {}
    for row in rows:
        key = (row["dataset"], row["alpha"], row["noise"], row["model"],
               row["evaluation_split"], row["metric"])
        groups.setdefault(key, []).append(row["value"])
    summary = []
    for key in sorted(groups):
        values = groups[key]
        n = len(values)
        mean = statistics.mean(values)
        sd = statistics.stdev(values) if n > 1 else float("nan")
        half = t.ppf(0.975, n - 1) * sd / math.sqrt(n) if n > 1 else float("nan")
        summary.append(dict(
            zip(("dataset", "alpha", "noise", "model", "evaluation_split", "metric"), key),
            seeds=n, mean=mean, standard_deviation=sd,
            confidence_interval_lower=mean - half,
            confidence_interval_upper=mean + half,
            interval_method="t interval across paired seeds; exploratory",
        ))
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", choices=[
        "maintenance", "steel", "semiconductor", "power", "gas", "iot"
    ], default=["maintenance", "steel"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 23, 37, 47, 59])
    parser.add_argument("--alphas", nargs="+", type=float, default=[0.1, 0.5, 2.0])
    parser.add_argument("--noises", nargs="+", type=float, default=[0.8, 1.2, 2.0])
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--clients", type=int, default=4)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--participation", type=float, default=0.75)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--mode", choices=["smoke", "exploratory"], default="exploratory")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    opts = parser.parse_args()
    if opts.mode == "smoke":
        opts.seeds, opts.alphas, opts.noises = [11], [0.5], [1.2]
        opts.rounds, opts.clients, opts.max_rows = 1, 2, 500
    if any(v <= 0 for v in opts.alphas + opts.noises) or opts.rounds < 1:
        parser.error("Positive alphas, noises and rounds are required")
    if opts.clients < 2 or not (0 < opts.participation <= 1):
        parser.error("Invalid client participation")
    out = Path(opts.output_dir)
    runs = out / "Runs"
    runs.mkdir(parents=True, exist_ok=True)
    planned = list(itertools.product(opts.datasets, opts.seeds, opts.alphas, opts.noises))
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": opts.mode,
        "planned_trials": len(planned),
        "datasets": opts.datasets,
        "seeds": opts.seeds,
        "alphas": opts.alphas,
        "noises": opts.noises,
        "client_partitions": "simulated Dirichlet, not actual organisations",
        "privacy": "Opacus per-record DP-SGD without cryptographic secure aggregation",
        "study_status": "Exploratory pilot; not confirmatory publication findings",
    }
    (out / "Experiment Plan.json").write_text(json.dumps(manifest, indent=2) + "\n")
    observations, failures = [], []
    for dataset, seed, alpha, noise in planned:
        destination = runs / trial_name(dataset, seed, alpha, noise)
        command = [
            sys.executable, str(ENGINE),
            "--dataset", dataset, "--seed", str(seed),
            "--alpha", str(alpha), "--noise", str(noise),
            "--clients", str(opts.clients), "--rounds", str(opts.rounds),
            "--epochs", str(opts.epochs), "--max-rows", str(opts.max_rows),
            "--participation", str(opts.participation),
            "--batch", str(opts.batch), "--output", str(destination),
        ]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            failures.append({"dataset": dataset, "seed": seed,
                             "alpha": alpha, "noise": noise,
                             "returncode": result.returncode,
                             "stderr_tail": result.stderr[-4000:]})
            print("FAILED", dataset, seed, alpha, noise, file=sys.stderr)
            continue
        try:
            record = json.loads(destination.read_text(encoding="utf-8"))
            observations.extend(flatten_trial(record, str(destination.relative_to(out))))
        except Exception as exc:
            failures.append({"dataset": dataset, "seed": seed,
                             "alpha": alpha, "noise": noise, "parsing_error": str(exc)})
            continue
        print("PASS", dataset, seed, alpha, noise, flush=True)
    (out / "Failures.json").write_text(json.dumps(failures, indent=2) + "\n")
    if observations:
        write_csv(out / "Trial Metrics.csv", observations, list(observations[0]))
        summaries = group_summary(observations)
        write_csv(out / "Seed Summary.csv", summaries, list(summaries[0]))
    manifest.update({"completed_trials": len(set(r["source_result"] for r in observations)),
                     "failed_trials": len(failures), "generated_utc": datetime.now(timezone.utc).isoformat()})
    (out / "Experiment Plan.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"completed": manifest["completed_trials"],
                      "failed": len(failures), "out": str(out)}, indent=2))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
