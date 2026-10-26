"""Industrial classification and power-regression federated learning benchmarks.

This is an experimental implementation, not a report of completed findings.
Private training uses Opacus differential privacy accounting. Secure aggregation,
reconstruction attacks, poisoning and membership-inference tests are NOT included.
"""
import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, brier_score_loss, f1_score,
    matthews_corrcoef, mean_absolute_error, mean_squared_error,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "Datasets"


def load_data(name):
    if name == "maintenance":
        path = DATA / "Manufacturing Maintenance.csv"
        frame = pd.read_csv(path)
        y = frame["Machine failure"].astype(int).to_numpy()
        forbidden = ["Machine failure", "UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
        X = pd.get_dummies(frame.drop(columns=forbidden), columns=["Type"], dtype=int)
        source_files = [path]
        task = "classification"
    elif name == "steel":
        path = DATA / "Steel Quality Faults.csv"
        frame = pd.read_csv(path)
        y = LabelEncoder().fit_transform(frame["Fault_Type"])
        X = frame.drop(columns=["Fault_Type"])
        source_files = [path]
        task = "classification"
    elif name == "semiconductor":
        folder = DATA / "Semiconductor Segments"
        parts = sorted(folder.glob("Part *.txt"))
        if len(parts) != 13:
            raise ValueError("Expected all thirteen semiconductor data segments")
        lines = []
        for part in parts:
            lines.extend(line for line in part.read_text().splitlines() if line.strip())
        X = pd.DataFrame([list(map(float, line.split())) for line in lines])
        if X.shape != (1567, 590):
            raise ValueError(f"Unexpected semiconductor matrix: {X.shape}")
        label_path = folder / "Labels.txt"
        y = np.array([int(line.split()[0]) == 1 for line in label_path.read_text().splitlines()
                      if line.strip()], dtype=int)
        if len(y) != len(X):
            raise ValueError("Semiconductor label alignment failure")
        source_files = [*parts, label_path]
        task = "classification"
    elif name == "power":
        path = DATA / "Power Plant Output.csv"
        frame = pd.read_csv(path)
        if list(frame.columns) != ["AT", "V", "AP", "RH", "PE"]:
            raise ValueError("Unexpected power generation dataset schema")
        X, y = frame.drop(columns=["PE"]), frame["PE"].astype(float).to_numpy()
        source_files = [path]
        task = "regression"
    else:
        raise ValueError(f"Unknown dataset: {name}")
    X = X.apply(pd.to_numeric, errors="coerce")
    if X.isna().all(axis=0).any():
        X = X.loc[:, ~X.isna().all(axis=0)]
    if len(X) != len(y) or len(X) < 100 or X.shape[1] < 2:
        raise ValueError("Invalid dataset dimensions")
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    return X, np.asarray(y), task, hashes


def split_and_prepare(X, y, task, seed, max_rows):
    rng = np.random.default_rng(seed)
    all_index = np.arange(len(y))
    if max_rows and max_rows < len(y):
        strat = y if task == "classification" else None
        chosen, _ = train_test_split(all_index, train_size=max_rows, random_state=seed, stratify=strat)
        all_index = np.sort(chosen)
    strat = y[all_index] if task == "classification" else None
    fit, test = train_test_split(all_index, test_size=0.15, random_state=seed, stratify=strat)
    strat_fit = y[fit] if task == "classification" else None
    train, valid = train_test_split(fit, test_size=0.15 / 0.85, random_state=seed + 1,
                                   stratify=strat_fit)
    assert not (set(train) & set(test) or set(train) & set(valid) or set(test) & set(valid))
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x_train = scaler.fit_transform(imputer.fit_transform(X.iloc[train])).astype("float32")
    x_valid = scaler.transform(imputer.transform(X.iloc[valid])).astype("float32")
    x_test = scaler.transform(imputer.transform(X.iloc[test])).astype("float32")
    targets = [y[train], y[valid], y[test]]
    normalisation = None
    if task == "regression":
        mean = float(np.mean(targets[0]))
        std = float(np.std(targets[0]))
        if std <= 0:
            raise ValueError("Degenerate target")
        targets = [(v.astype("float32") - mean) / std for v in targets]
        normalisation = {"mean": mean, "std": std}
    return (x_train, x_valid, x_test), tuple(targets), normalisation, {
        "training_rows": len(train), "validation_rows": len(valid), "test_rows": len(test),
        "seed": seed, "partition_scope": "single dataset with simulated clients",
        "train_index_sha256": hashlib.sha256(np.sort(train).astype("int64").tobytes()).hexdigest(),
        "test_index_sha256": hashlib.sha256(np.sort(test).astype("int64").tobytes()).hexdigest(),
    }


def client_partitions(y, task, clients, concentration, seed):
    rng = np.random.default_rng(seed)
    n = len(y)
    groups = y if task == "classification" else np.digitize(y, np.quantile(y, [0.2, 0.4, 0.6, 0.8]))
    for attempt in range(250):
        allocation = [[] for _ in range(clients)]
        for category in np.unique(groups):
            idx = np.flatnonzero(groups == category)
            rng.shuffle(idx)
            proportions = rng.dirichlet(np.repeat(concentration, clients))
            lengths = rng.multinomial(len(idx), proportions)
            splits = np.split(idx, np.cumsum(lengths)[:-1])
            for client, block in enumerate(splits):
                allocation[client].extend(block.tolist())
        if min(map(len, allocation)) >= 20:
            a = [np.array(sorted(items), dtype=int) for items in allocation]
            flat = np.concatenate(a)
            assert len(flat) == n and len(np.unique(flat)) == n
            return a, attempt
    raise RuntimeError("Dirichlet partition produced undersized clients; increase alpha or rows")


def network(n_features, output_size):
    return nn.Sequential(nn.Linear(n_features, 32), nn.ReLU(),
                         nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, output_size))


def loader(x, y, task, batch, shuffle, generator=None):
    dtype = torch.long if task == "classification" else torch.float32
    return DataLoader(TensorDataset(torch.from_numpy(np.asarray(x, dtype="float32")),
                                    torch.as_tensor(y, dtype=dtype)),
                      batch_size=min(batch, len(y)), shuffle=shuffle, generator=generator)


def train_epochs(model, optimizer, data, task, epochs):
    criterion = nn.CrossEntropyLoss() if task == "classification" else nn.MSELoss()
    model.train()
    for _ in range(epochs):
        for xb, yb in data:
            optimizer.zero_grad()
            logits = model(xb)
            target = yb if task == "classification" else yb.reshape(-1, 1)
            loss = criterion(logits, target)
            loss.backward()
            optimizer.step()


def pooled_network(x, y, task, classes, opts):
    model = network(x.shape[1], classes if task == "classification" else 1)
    optim = torch.optim.SGD(model.parameters(), lr=opts.lr)
    g = torch.Generator().manual_seed(opts.seed + 400)
    data = loader(x, y, task, opts.batch, shuffle=True, generator=g)
    train_epochs(model, optim, data, task, opts.epochs * opts.rounds)
    return model


def federate(x, y, task, classes, parts, opts, private=False):
    if private:
        try:
            from opacus import PrivacyEngine
        except ImportError as exc:
            raise RuntimeError("Install Opacus to execute private DP-SGD") from exc
    global_model = network(x.shape[1], classes if task == "classification" else 1)
    client_contexts = []
    for client, indices in enumerate(parts):
        model = network(x.shape[1], classes if task == "classification" else 1)
        optimizer = torch.optim.SGD(model.parameters(), lr=opts.lr)
        g = torch.Generator().manual_seed(opts.seed + 1000 + client)
        train_data = loader(x[indices], y[indices], task, opts.batch, shuffle=True, generator=g)
        engine = None
        if private:
            engine = PrivacyEngine(accountant="rdp", secure_mode=False)
            model, optimizer, train_data = engine.make_private(
                module=model, optimizer=optimizer, data_loader=train_data,
                noise_multiplier=opts.noise, max_grad_norm=opts.clip, poisson_sampling=True
            )
        client_contexts.append((model, optimizer, train_data, engine, len(indices)))
    selected_count = max(1, int(np.ceil(opts.clients * opts.participation)))
    rng = np.random.default_rng(opts.seed + 2000)
    estimated_bytes = 0
    for _ in range(opts.rounds):
        selected = rng.choice(opts.clients, size=selected_count, replace=False)
        total = 0
        accumulator = None
        for cid in selected:
            model, optimizer, data, engine, count = client_contexts[int(cid)]
            raw = model._module if private else model
            raw.load_state_dict(global_model.state_dict())
            train_epochs(model, optimizer, data, task, opts.epochs)
            state = raw.state_dict()
            if accumulator is None:
                accumulator = {key: value.detach().clone().float() * count for key, value in state.items()}
            else:
                for key in state:
                    accumulator[key] += state[key].detach().float() * count
            total += count
            estimated_bytes += 2 * sum(v.numel() * v.element_size() for v in state.values())
        new_state = {k: v / total for k, v in accumulator.items()}
        global_model.load_state_dict(new_state)
    info = {
        "mode": "federated_dp_sgd" if private else "fedavg",
        "estimated_bidirectional_parameter_bytes": estimated_bytes,
        "client_sizes": [c[4] for c in client_contexts],
        "rounds": opts.rounds, "round_participation": selected_count,
        "aggregation": "size-weighted average without cryptographic secure aggregation",
        "actual_distributed_silos": False,
        "secure_aggregation_executed": False,
    }
    if private:
        delta = min(1e-5, 0.1 / len(x))
        epsilons = []
        for _, _, _, engine, _ in client_contexts:
            events = len(engine.accountant.history)
            epsilons.append(float(engine.get_epsilon(delta=delta)) if events else 0.0)
        info.update({
            "privacy_unit": "training record",
            "delta": delta, "epsilon_by_simulated_client": epsilons,
            "epsilon_max": max(epsilons), "epsilon_min": min(epsilons),
            "noise_multiplier": opts.noise, "max_gradient_norm": opts.clip,
            "accountant": "Opacus RDP", "secure_rng": False,
            "privacy_attacks_executed": False,
        })
    return global_model, info


def evaluate(model, x, y, task, normalisation):
    model.eval()
    with torch.no_grad():
        scores = model(torch.tensor(x, dtype=torch.float32)).numpy()
    if task == "regression":
        original = y * normalisation["std"] + normalisation["mean"]
        predicted = scores.reshape(-1) * normalisation["std"] + normalisation["mean"]
        return {
            "mae_mw": float(mean_absolute_error(original, predicted)),
            "rmse_mw": float(np.sqrt(mean_squared_error(original, predicted))),
        }
    scores = scores - scores.max(axis=1, keepdims=True)
    probabilities = np.exp(scores) / np.exp(scores).sum(axis=1, keepdims=True)
    predicted = np.argmax(probabilities, axis=1)
    result = {
        "accuracy": float(accuracy_score(y, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(y, predicted)),
    }
    if probabilities.shape[1] == 2 and len(np.unique(y)) == 2:
        result["brier_score"] = float(brier_score_loss(y, probabilities[:, 1]))
        result["roc_auc"] = float(roc_auc_score(y, probabilities[:, 1]))
    return result


def execute(opts):
    if opts.clients < 2 or not (0 < opts.participation <= 1) or opts.noise <= 0 or opts.clip <= 0:
        raise ValueError("Invalid federation or privacy parameters")
    random.seed(opts.seed)
    np.random.seed(opts.seed)
    torch.manual_seed(opts.seed)
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
    X, y, task, hashes = load_data(opts.dataset)
    prepared, targets, normalisation, split = split_and_prepare(
        X, y, task, opts.seed, opts.max_rows
    )
    xtr, xva, xte = prepared
    ytr, yva, yte = targets
    parts, partition_attempts = client_partitions(ytr, task, opts.clients, opts.alpha, opts.seed)
    n_classes = int(len(np.unique(y))) if task == "classification" else 1
    if task == "classification" and len(np.unique(ytr)) != n_classes:
        raise ValueError("Some classes missing from training")
    if task == "classification":
        simple = LogisticRegression(max_iter=1000)
    else:
        simple = Ridge(alpha=1.0)
    simple.fit(xtr, ytr)
    if task == "classification":
        def classical_metric(x, y_eval):
            pred = simple.predict(x)
            return {"balanced_accuracy": float(balanced_accuracy_score(y_eval, pred)),
                    "macro_f1": float(f1_score(y_eval, pred, average="macro", zero_division=0)),
                    "mcc": float(matthews_corrcoef(y_eval, pred))}
    else:
        def classical_metric(x, y_eval):
            actual = y_eval * normalisation["std"] + normalisation["mean"]
            pred = simple.predict(x) * normalisation["std"] + normalisation["mean"]
            return {"mae_mw": float(mean_absolute_error(actual, pred)),
                    "rmse_mw": float(np.sqrt(mean_squared_error(actual, pred)))}
    pooled = pooled_network(xtr, ytr, task, n_classes, opts)
    nonprivate, fedinfo = federate(xtr, ytr, task, n_classes, parts, opts, private=False)
    private, dpinfo = federate(xtr, ytr, task, n_classes, parts, opts, private=True)
    results = {
        "study": "Privacy, Trust and Intelligent Systems in Industry Six",
        "execution_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": opts.dataset, "task": task, "n_total": len(y),
        "features": list(X.columns.map(str)), "source_sha256": hashes,
        "split": split,
        "synthetic_federation": True, "partition_alpha": opts.alpha,
        "partition_attempt": partition_attempts,
        "software": {"torch": torch.__version__, "numpy": np.__version__,
                     "pandas": pd.__version__},
        "parameters": vars(opts),
        "models": {
            "linear_baseline": {"validation": classical_metric(xva, yva),
                                "test": classical_metric(xte, yte)},
            "pooled_mlp": {"validation": evaluate(pooled, xva, yva, task, normalisation),
                           "test": evaluate(pooled, xte, yte, task, normalisation)},
            "fedavg": {"validation": evaluate(nonprivate, xva, yva, task, normalisation),
                       "test": evaluate(nonprivate, xte, yte, task, normalisation),
                       "protocol": fedinfo},
            "federated_dp_sgd": {
                "validation": evaluate(private, xva, yva, task, normalisation),
                "test": evaluate(private, xte, yte, task, normalisation),
                "protocol": dpinfo},
        },
        "limits": [
            "Single public dataset and artificially allocated clients, not cross-factory field evidence.",
            "All test evaluations are held out from preprocessing and training.",
            "Formal differential privacy does not imply protection against all threat models.",
            "Membership inference, reconstruction, poisoning and secure aggregation remain untested.",
            "One seed is a pilot, not a statistically robust comparison.",
        ],
    }
    output = Path(opts.output) if opts.output else ROOT / "Experiments" / "Results" / (
        opts.dataset.title() + " Pilot Results.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"saved": str(output), "dataset": opts.dataset,
                      "models": {k: v["test"] for k, v in results["models"].items()},
                      "max_epsilon": dpinfo["epsilon_max"]}, indent=2))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["maintenance", "steel", "semiconductor", "power"],
                        default="maintenance")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clients", type=int, default=4)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--participation", type=float, default=0.75)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--noise", type=float, default=1.2)
    parser.add_argument("--clip", type=float, default=1.0)
    parser.add_argument("--max-rows", type=int, default=0,
                        help="Stratified pilot subsample only; 0 uses all observations.")
    parser.add_argument("--output", default="")
    execute(parser.parse_args())


if __name__ == "__main__":
    main()
