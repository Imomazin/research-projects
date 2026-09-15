#!/usr/bin/env python3
"""P3-E3 randomized validation on the unbiased Criteo uplift benchmark.

This script estimates treatment effects within the released benchmark distribution.
It does NOT attempt to recover Criteo's original commercial incrementality level,
which the dataset documentation states cannot be inferred after privacy-preserving
subsampling.

Design:
- treatment is randomized in the source incrementality experiments
- propensity is therefore estimated by the training-fold treatment rate, not by a
  predictive propensity model
- nuisance outcome models are cross-fitted separately in treated and control arms
- the primary estimator is AIPW / doubly robust ATE
- the randomized difference in means is retained as the transparent benchmark
- predicted uplift is evaluated by randomized observed uplift within score deciles

Outputs contain only aggregate research results and provenance. Raw Criteo rows are
never written to this repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = [f"f{i}" for i in range(12)]
REQUIRED = FEATURES + ["treatment", "conversion", "visit", "exposure"]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_data(path: Path, max_rows: int | None) -> pd.DataFrame:
    frame = pd.read_csv(path, nrows=max_rows)
    missing = [column for column in REQUIRED if column not in frame.columns]
    if missing:
        raise ValueError(f"Criteo input is missing required columns: {missing}")

    frame = frame[REQUIRED].copy()
    frame[FEATURES] = frame[FEATURES].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=FEATURES + ["treatment", "conversion", "visit"])
    frame["treatment"] = frame["treatment"].astype(int)
    frame["conversion"] = frame["conversion"].astype(int)
    frame["visit"] = frame["visit"].astype(int)

    invalid_treatment = ~frame["treatment"].isin([0, 1])
    if invalid_treatment.any():
        raise ValueError("treatment must be binary 0/1")
    return frame.reset_index(drop=True)


def make_outcome_model(seed: int):
    # Scalable probabilistic linear nuisance model. We avoid class weighting because
    # AIPW needs probability estimates on the original released benchmark scale.
    return make_pipeline(
        StandardScaler(),
        SGDClassifier(
            loss="log_loss",
            penalty="l2",
            alpha=1e-5,
            max_iter=2000,
            tol=1e-5,
            random_state=seed,
        ),
    )


def fit_predict_probability(model, x_train, y_train, x_test) -> np.ndarray:
    unique = np.unique(y_train)
    if unique.size == 1:
        # A rare fold can be single-class for conversion. Preserve a valid nuisance
        # probability instead of crashing or fabricating a discriminative model.
        return np.full(x_test.shape[0], float(unique[0]), dtype=float)
    model.fit(x_train, y_train)
    return model.predict_proba(x_test)[:, 1]


def crossfit_nuisance(
    frame: pd.DataFrame,
    outcome: str,
    folds: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = frame[FEATURES].to_numpy(dtype=float)
    t = frame["treatment"].to_numpy(dtype=int)
    y = frame[outcome].to_numpy(dtype=int)
    n = len(frame)

    mu0 = np.empty(n, dtype=float)
    mu1 = np.empty(n, dtype=float)
    propensity = np.empty(n, dtype=float)

    # Stratify on treatment and outcome where possible so rare conversions are
    # distributed more evenly across folds.
    strata = (2 * t + y).astype(int)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)

    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, strata), start=1):
        x_train, x_test = x[train_idx], x[test_idx]
        t_train, y_train = t[train_idx], y[train_idx]

        p = float(t_train.mean())
        if not 0 < p < 1:
            raise RuntimeError(f"fold {fold} has no treatment overlap")
        propensity[test_idx] = p

        control_mask = t_train == 0
        treated_mask = t_train == 1
        if control_mask.sum() == 0 or treated_mask.sum() == 0:
            raise RuntimeError(f"fold {fold} lacks treated or control observations")

        mu0[test_idx] = fit_predict_probability(
            make_outcome_model(seed + fold * 2),
            x_train[control_mask],
            y_train[control_mask],
            x_test,
        )
        mu1[test_idx] = fit_predict_probability(
            make_outcome_model(seed + fold * 2 + 1),
            x_train[treated_mask],
            y_train[treated_mask],
            x_test,
        )

    return propensity, mu0, mu1


def aipw_summary(
    treatment: np.ndarray,
    outcome: np.ndarray,
    propensity: np.ndarray,
    mu0: np.ndarray,
    mu1: np.ndarray,
) -> dict[str, float | int | list[float]]:
    e = np.clip(propensity, 0.01, 0.99)
    score = (
        mu1
        - mu0
        + treatment * (outcome - mu1) / e
        - (1 - treatment) * (outcome - mu0) / (1 - e)
    )
    ate = float(score.mean())
    se = float(score.std(ddof=1) / np.sqrt(len(score)))
    margin = 1.96 * se

    treated_y = outcome[treatment == 1]
    control_y = outcome[treatment == 0]
    randomized_difference = float(treated_y.mean() - control_y.mean())

    return {
        "n": int(len(outcome)),
        "treated_n": int((treatment == 1).sum()),
        "control_n": int((treatment == 0).sum()),
        "treatment_rate": float(treatment.mean()),
        "treated_outcome_rate": float(treated_y.mean()),
        "control_outcome_rate": float(control_y.mean()),
        "randomized_difference_in_means": randomized_difference,
        "aipw_ate": ate,
        "aipw_standard_error": se,
        "aipw_ci95": [ate - margin, ate + margin],
        "mean_predicted_uplift": float((mu1 - mu0).mean()),
    }


def randomized_uplift_deciles(
    treatment: np.ndarray,
    outcome: np.ndarray,
    predicted_uplift: np.ndarray,
) -> pd.DataFrame:
    data = pd.DataFrame(
        {
            "treatment": treatment,
            "outcome": outcome,
            "predicted_uplift": predicted_uplift,
        }
    )
    # rank(method='first') makes quantile allocation deterministic under ties.
    ranks = data["predicted_uplift"].rank(method="first", ascending=False)
    data["decile"] = pd.qcut(ranks, 10, labels=False, duplicates="drop") + 1

    rows: list[dict[str, float | int]] = []
    for decile, group in data.groupby("decile", sort=True):
        treated = group[group["treatment"] == 1]["outcome"]
        control = group[group["treatment"] == 0]["outcome"]
        if len(treated) == 0 or len(control) == 0:
            observed_uplift = np.nan
        else:
            observed_uplift = float(treated.mean() - control.mean())
        rows.append(
            {
                "decile": int(decile),
                "n": int(len(group)),
                "mean_predicted_uplift": float(group["predicted_uplift"].mean()),
                "treated_n": int((group["treatment"] == 1).sum()),
                "control_n": int((group["treatment"] == 0).sum()),
                "randomized_observed_uplift": observed_uplift,
            }
        )
    return pd.DataFrame(rows)


def run(args: argparse.Namespace) -> None:
    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    frame = read_data(input_path, args.max_rows)
    if len(frame) < args.folds * 100:
        raise ValueError("sample is too small for the requested cross-fitting protocol")

    outcomes = [args.outcome] if args.outcome != "both" else ["visit", "conversion"]
    provenance = {
        "experiment": "P3-E3 Criteo randomized uplift validation",
        "source_file": input_path.name,
        "source_sha256": sha256_file(input_path),
        "rows_loaded_after_complete_case_filter": int(len(frame)),
        "max_rows_requested": args.max_rows,
        "folds": args.folds,
        "seed": args.seed,
        "features": FEATURES,
        "treatment": "treatment",
        "outcomes": outcomes,
        "estimand": "ATE in the released unbiased Criteo benchmark distribution",
        "design_note": "Source data originates from incrementality tests with randomized treatment. The released dataset is privacy-subsampled; no claim is made about the original commercial incrementality level.",
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    with (out_dir / "provenance.json").open("w", encoding="utf-8") as handle:
        json.dump(provenance, handle, indent=2)

    all_summaries: dict[str, dict] = {}
    t = frame["treatment"].to_numpy(dtype=int)

    for outcome_name in outcomes:
        y = frame[outcome_name].to_numpy(dtype=int)
        propensity, mu0, mu1 = crossfit_nuisance(
            frame=frame,
            outcome=outcome_name,
            folds=args.folds,
            seed=args.seed,
        )
        summary = aipw_summary(t, y, propensity, mu0, mu1)
        summary["outcome"] = outcome_name
        all_summaries[outcome_name] = summary

        deciles = randomized_uplift_deciles(t, y, mu1 - mu0)
        deciles.to_csv(out_dir / f"uplift_deciles_{outcome_name}.csv", index=False)

    with (out_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(all_summaries, handle, indent=2)

    print(json.dumps({"provenance": provenance, "results": all_summaries}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to criteo-uplift-v2.1.csv.gz")
    parser.add_argument("--out-dir", default="results/p3-e3-criteo-uplift")
    parser.add_argument("--outcome", choices=["visit", "conversion", "both"], default="both")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Development-only row cap. Omit for the final benchmark run.",
    )
    args = parser.parse_args()
    if args.folds < 2:
        parser.error("--folds must be at least 2")
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    return args


if __name__ == "__main__":
    run(parse_args())
