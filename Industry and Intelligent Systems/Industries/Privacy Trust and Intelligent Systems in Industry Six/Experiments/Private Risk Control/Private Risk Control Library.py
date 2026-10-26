"""Private aggregate risk control for federated industrial learning.

Library for the study "Privacy, Trust & Intelligent Systems in Industry 6.0".

Components
- Task loaders for eight industrial and security datasets with provenance hashes.
- A three-layer perceptron written in NumPy with exact per-example clipping
  (per-example norms of linear layers are computed from activation and error norms).
- Federated optimisers: FedAvg, FedProx, SCAFFOLD, coordinate-wise trimmed mean and
  median aggregation, and DP-FedAvg (local DP-SGD with Poisson sampling).
- Privacy accounting with Google's dp_accounting RDP accountant for DP-SGD and an exact
  numerical Renyi divergence for the Skellam mechanism.
- Pairwise-mask secure aggregation (X25519 key agreement, HKDF, ChaCha20 masks, modular
  arithmetic) for integer histograms and fixed-point model parameters.
- Private aggregate risk control: client histograms of calibration scores with
  distributed Skellam noise, secure summation, and a fixed-sequence binomial-Skellam test
  that certifies decision thresholds for monotone risks (miss rate, false-alarm rate,
  joint selective error, regression interval exceedance).
- Attack and robustness utilities: loss-threshold membership inference, model poisoning,
  calibration-histogram poisoning, analytic gradient reconstruction, test-time corruption.

Nothing in this module reports results. Results come only from executed runs.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import logging

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp, expit
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    average_precision_score, balanced_accuracy_score, f1_score, matthews_corrcoef,
    mean_absolute_error, mean_squared_error, r2_score, roc_auc_score, roc_curve,
)

logging.getLogger("absl").setLevel(logging.ERROR)

STUDY_ROOT = Path(__file__).resolve().parents[2]
DATA = STUDY_ROOT / "Datasets"

# Public prevalence metadata taken from source documentation, used for fixed class weights.
# Fixed weights keep the DP-SGD loss independent of private label counts.
PUBLIC_POSITIVE_WEIGHT = {
    "maintenance": 25.0,    # AI4I documentation: 339 failures in 10,000 records
    "semiconductor": 14.0,  # SECOM documentation: 104 fails in 1,567 records
    "bosch": 20.0,          # Bosch CNC: 70 anomalous of 1,702 recordings (dataset README counts)
    "hai": 30.0,            # HAI 21.03 documentation: attack intervals are a few percent of test time
    "iot": 0.11,            # RT-IoT2022 documentation: attacks outnumber benign flows about nine to one
}
STEEL_PUBLIC_COUNTS = {  # UCI 198 documented class counts
    "Pastry": 158, "Z_Scratch": 190, "K_Scatch": 391, "Stains": 72,
    "Dirtiness": 55, "Bumps": 402, "Other_Faults": 673,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# Task loading


@dataclass
class Task:
    name: str
    kind: str  # binary, multiclass, regression
    X: pd.DataFrame
    y: np.ndarray
    natural_clients: np.ndarray | None = None
    periods: np.ndarray | None = None
    sessions: np.ndarray | None = None
    time_index: np.ndarray | None = None
    class_names: list | None = None
    unit: str = ""
    hashes: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    signed_log: bool = False
    events: object = None


def load_task(name: str) -> Task:
    if name == "maintenance":
        path = DATA / "Manufacturing Maintenance.csv"
        frame = pd.read_csv(path)
        y = frame["Machine failure"].astype(int).to_numpy()
        forbidden = ["Machine failure", "UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"]
        X = pd.get_dummies(frame.drop(columns=forbidden), columns=["Type"], dtype=float)
        task = Task(name, "binary", X, y, hashes={path.name: sha256_file(path)},
                    notes=["Synthetic AI4I records; failure-mode flags excluded"])
    elif name == "steel":
        path = DATA / "Steel Quality Faults.csv"
        frame = pd.read_csv(path)
        # The mirror spells the UCI column K_Scatch as K_Scratch; counts are otherwise identical.
        frame["Fault_Type"] = frame["Fault_Type"].replace({"K_Scratch": "K_Scatch"})
        counts = frame["Fault_Type"].value_counts().to_dict()
        if counts != STEEL_PUBLIC_COUNTS:
            raise ValueError(f"Steel class counts differ from UCI documentation: {counts}")
        names = sorted(STEEL_PUBLIC_COUNTS)
        y = frame["Fault_Type"].map({n: i for i, n in enumerate(names)}).to_numpy()
        X = frame.drop(columns=["Fault_Type"]).astype(float)
        task = Task(name, "multiclass", X, y, class_names=names,
                    hashes={path.name: sha256_file(path)})
    elif name == "semiconductor":
        folder = DATA / "Semiconductor Segments"
        parts = sorted(folder.glob("Part *.txt"))
        if len(parts) != 13:
            raise ValueError("Expected thirteen SECOM segments")
        rows = []
        for part in parts:
            for line in part.read_text().splitlines():
                if line.strip():
                    rows.append([float(v) for v in line.split()])
        X = pd.DataFrame(rows)
        X.columns = [f"Sensor {i}" for i in range(X.shape[1])]
        labels = [r for r in (folder / "Labels.txt").read_text().splitlines() if r.strip()]
        y = np.array([int(r.split()[0]) == 1 for r in labels], dtype=int)
        if X.shape != (1567, 590) or len(y) != 1567 or y.sum() != 104:
            raise ValueError("SECOM reconstruction failed")
        hashes = {p.name: sha256_file(p) for p in parts}
        hashes["Labels.txt"] = sha256_file(folder / "Labels.txt")
        task = Task(name, "binary", X, y, hashes=hashes)
    elif name == "power":
        path = DATA / "Power Plant Output.csv"
        frame = pd.read_csv(path)
        X, y = frame.drop(columns=["PE"]).astype(float), frame["PE"].to_numpy(float)
        task = Task(name, "regression", X, y, unit="MW", hashes={path.name: sha256_file(path)})
    elif name == "gas":
        folder = DATA / "Gas Turbine Annual Records"
        files = [(2011, "Gas Turbine First Year.csv"), (2012, "Gas Turbine Second Year.csv"),
                 (2013, "Gas Turbine Third Year.csv"), (2014, "Gas Turbine Fourth Year.csv"),
                 (2015, "Gas Turbine Fifth Year.csv")]
        frames, years, hashes = [], [], {}
        for year, file in files:
            data = pd.read_csv(folder / file)
            frames.append(data)
            years.extend([year] * len(data))
            hashes[file] = sha256_file(folder / file)
        frame = pd.concat(frames, ignore_index=True)
        if len(frame) != 36733:
            raise ValueError("Gas turbine row count mismatch")
        y = frame["NOX"].to_numpy(float)
        X = frame.drop(columns=["NOX", "CO"]).astype(float)
        task = Task(name, "regression", X, y, periods=np.array(years), unit="mg/m3",
                    hashes=hashes)
    elif name == "iot":
        path = DATA / "IoT Intrusion Source" / "Real Time IoT Traffic.zip"
        with zipfile.ZipFile(path) as archive:
            member = [m for m in archive.namelist() if Path(m).name == "RT_IOT2022"]
            frame = pd.read_csv(io.BytesIO(archive.read(member[0])), low_memory=False)
        if len(frame) != 123117:
            raise ValueError("RT-IoT row count mismatch")
        benign = {"Thing_Speak", "MQTT_Publish", "Wipro_bulb"}
        y = (~frame["Attack_type"].isin(benign)).astype(int).to_numpy()
        X = frame.drop(columns=["Attack_type", "Unnamed: 0"], errors="ignore")
        X = pd.get_dummies(X, columns=["proto", "service"], dummy_na=True, dtype=float)
        X = X.apply(pd.to_numeric, errors="coerce").astype(float)
        task = Task(name, "binary", X, y, hashes={path.name: sha256_file(path)},
                    signed_log=True, sessions=frame["Attack_type"].to_numpy())
    elif name == "bosch":
        path = DATA / "Bosch CNC" / "Bosch CNC Derived Features.csv"
        frame = pd.read_csv(path)
        features = [c for c in frame.columns if c[:2] in ("X ", "Y ", "Z ")]
        X = pd.concat([frame[features].astype(float),
                       pd.get_dummies(frame["Operation"], prefix="Operation", dtype=float)], axis=1)
        y = frame["Anomaly"].astype(int).to_numpy()
        month, year = frame["Timeframe"].str.split("_").str[0], frame["Timeframe"].str.split("_").str[1]
        period = year.astype(int) * 100 + month.map({"Feb": 2, "Aug": 8}).astype(int)
        task = Task(name, "binary", X, y, natural_clients=frame["Machine"].to_numpy(),
                    periods=period.to_numpy(), hashes={path.name: sha256_file(path)},
                    notes=["Three physical machines; recording length excluded from predictors"])
    elif name == "hai":
        path = DATA / "HAI Industrial Control" / "HAI Window Features.csv.gz"
        frame = pd.read_csv(path)
        meta = ["Session", "Window Start", "Window Index", "Attack", "Attack Seconds",
                "Event ID", "Event First Second"]
        X = frame.drop(columns=meta).astype(float)
        y = frame["Attack"].astype(int).to_numpy()
        task = Task(name, "binary", X, y, sessions=frame["Session"].to_numpy(),
                    time_index=frame["Window Index"].to_numpy(),
                    hashes={path.name: sha256_file(path)},
                    notes=["HAI 21.03 attack sessions; 30-second windows"])
        task.events = frame[["Session", "Window Index", "Event ID", "Event First Second"]].copy()
    else:
        raise ValueError(name)
    task.X = task.X.replace([np.inf, -np.inf], np.nan)
    return task


# Partitioning


def dirichlet_clients(labels: np.ndarray, clients: int, alpha: float, rng, min_size=30):
    """Label-skewed simulated clients; labels may be bins of a continuous target."""
    for _ in range(500):
        owner = np.empty(len(labels), dtype=int)
        for value in np.unique(labels):
            idx = np.flatnonzero(labels == value)
            share = rng.dirichlet(np.full(clients, alpha))
            owner[idx] = rng.choice(clients, size=len(idx), p=share)
        sizes = np.bincount(owner, minlength=clients)
        if sizes.min() >= min_size:
            return owner
    raise RuntimeError("Could not create clients of the minimum size")


def bernoulli_roles(n: int, rng, p_test=0.2, p_cal=0.2):
    """Independent per-record role assignment (train 0, calibration 1, test 2).

    Independence across records is required by the parallel-composition argument.
    """
    u = rng.random(n)
    return np.where(u < p_test, 2, np.where(u < p_test + p_cal, 1, 0))


def blocked_roles(index: np.ndarray, rng, block=20, p_cal=0.25):
    """Contiguous-block calibration assignment within a chronological session."""
    blocks = index // block
    unique = np.unique(blocks)
    chosen = set(unique[rng.random(len(unique)) < p_cal].tolist())
    return np.array([1 if b in chosen else 0 for b in blocks])


@dataclass
class Prepared:
    clients: list  # list of dicts with Xtr, ytr, Xcal, ycal, Xte, yte
    Xte: np.ndarray
    yte: np.ndarray
    test_client: np.ndarray
    extra_tests: dict
    target_scale: float
    target_mean: float
    feature_names: list
    design: str
    scaler: dict


def fit_scaler(X: np.ndarray, signed_log: bool):
    if signed_log:
        X = np.sign(X) * np.log1p(np.abs(X))
    med = np.nanmedian(X, axis=0)
    filled = np.where(np.isnan(X), med, X)
    q75, q25 = np.nanpercentile(filled, 75, axis=0), np.nanpercentile(filled, 25, axis=0)
    scale = q75 - q25
    std = filled.std(axis=0)
    scale = np.where(scale > 1e-9, scale, np.where(std > 1e-9, std, 1.0))
    keep = std > 1e-12
    return {"median": med, "scale": scale, "keep": keep, "signed_log": signed_log}


def apply_scaler(X: np.ndarray, s: dict):
    if s["signed_log"]:
        X = np.sign(X) * np.log1p(np.abs(X))
    X = np.where(np.isnan(X), s["median"], X)
    Z = (X - s["median"]) / s["scale"]
    Z = np.clip(Z, -10, 10)
    return Z[:, s["keep"]].astype(np.float32)


def prepare(task: Task, seed: int, design: str, clients=4, alpha=0.5, max_missing=0.5):
    """Create federated clients with train, calibration and test roles.

    Normalisation constants are estimated from pooled training rows and treated as public
    metadata (an assumption disclosed in the manuscript).
    """
    rng = np.random.default_rng(seed)
    X = task.X.to_numpy(dtype=float)
    keep_cols = np.isnan(X).mean(axis=0) <= max_missing
    X = X[:, keep_cols]
    names = list(np.asarray(task.X.columns)[keep_cols])
    y = task.y.astype(float if task.kind == "regression" else int)
    n = len(y)
    extra = {}
    owner = np.zeros(n, dtype=int)
    roles = np.zeros(n, dtype=int)
    if design == "simulated":
        strat = y if task.kind != "regression" else np.digitize(y, np.quantile(y, [.2, .4, .6, .8]))
        if task.name == "gas":
            # Federated pool restricted to 2011-2013; later years are out-of-period tests.
            in_pool = np.isin(task.periods, [2011, 2012, 2013])
        else:
            in_pool = np.ones(n, dtype=bool)
        pool = np.flatnonzero(in_pool)
        owner_pool = dirichlet_clients(strat[pool], clients, alpha, rng)
        owner[:] = -1
        owner[pool] = owner_pool
        roles[:] = -1
        roles[pool] = bernoulli_roles(len(pool), rng)
        if task.name == "gas":
            for year in (2014, 2015):
                extra[f"year {year}"] = np.flatnonzero(task.periods == year)
    elif design == "machines":
        machines = sorted(np.unique(task.natural_clients))
        owner = np.array([machines.index(m) for m in task.natural_clients])
        roles = bernoulli_roles(n, rng)
    elif design == "machine holdout":
        # Leave one machine out; seed selects which machine is unseen (cycled).
        machines = sorted(np.unique(task.natural_clients))
        unseen = machines[seed % len(machines)]
        seen = [m for m in machines if m != unseen]
        owner = np.array([seen.index(m) if m in seen else -1 for m in task.natural_clients])
        roles = np.where(owner >= 0, 0, -1)
        idx_seen = np.flatnonzero(owner >= 0)
        r = bernoulli_roles(len(idx_seen), rng, p_test=0.2, p_cal=0.2)
        roles[idx_seen] = r
        extra[f"unseen machine {unseen}"] = np.flatnonzero(owner < 0)
    elif design == "time holdout":
        # Bosch: recordings up to February 2020 for learning; later recordings are tested.
        early = task.periods <= 202002
        machines = sorted(np.unique(task.natural_clients))
        owner = np.array([machines.index(m) for m in task.natural_clients])
        owner[~early] = -1
        roles = np.full(n, -1)
        roles[early] = bernoulli_roles(int(early.sum()), rng)
        extra["later periods"] = np.flatnonzero(~early)
    elif design == "sessions":
        # HAI: sessions test1-test3 are clients; test4-test5 are later sessions for testing.
        sess = task.sessions
        learn = ["test1", "test2", "test3"]
        owner = np.array([learn.index(s) if s in learn else -1 for s in sess])
        roles = np.full(n, -1)
        for k in range(len(learn)):
            idx = np.flatnonzero(owner == k)
            local = rng.random(len(idx))
            blocks = task.time_index[idx] // 20
            ub = {b: rng.random() for b in np.unique(blocks)}
            u = np.array([ub[b] for b in blocks])
            roles[idx] = np.where(u < 0.2, 2, np.where(u < 0.4, 1, 0))
        extra["later sessions"] = np.flatnonzero(np.isin(sess, ["test4", "test5"]))
    else:
        raise ValueError(design)
    train_rows = np.flatnonzero((owner >= 0) & (roles == 0))
    scaler = fit_scaler(X[train_rows], task.signed_log)
    Z = apply_scaler(X, scaler)
    names = list(np.asarray(names)[scaler["keep"]])
    t_mean, t_scale = 0.0, 1.0
    yy = y.astype(np.float32) if task.kind == "regression" else y
    if task.kind == "regression":
        t_mean, t_scale = float(y[train_rows].mean()), float(y[train_rows].std())
        yy = ((y - t_mean) / t_scale).astype(np.float32)
    out = []
    for k in range(int(owner.max()) + 1):
        tr = np.flatnonzero((owner == k) & (roles == 0))
        ca = np.flatnonzero((owner == k) & (roles == 1))
        te = np.flatnonzero((owner == k) & (roles == 2))
        out.append({"Xtr": Z[tr], "ytr": yy[tr], "Xcal": Z[ca], "ycal": yy[ca],
                    "Xte": Z[te], "yte": yy[te], "rows": {"train": tr, "cal": ca, "test": te}})
    te_all = np.flatnonzero((owner >= 0) & (roles == 2))
    test_client = owner[te_all]
    extra_sets = {k: (Z[v], yy[v], v) for k, v in extra.items()}
    return Prepared(out, Z[te_all], yy[te_all], test_client, extra_sets, t_scale, t_mean,
                    names, design, scaler)


# Model


class MLP:
    """Three-layer perceptron with ReLU activations stored as a list of arrays."""

    def __init__(self, d, out, hidden=(64, 32), rng=None):
        rng = rng or np.random.default_rng(0)
        sizes = [d, *hidden, out]
        self.params = []
        for a, b in zip(sizes[:-1], sizes[1:]):
            bound = math.sqrt(6.0 / a)
            self.params.append(rng.uniform(-bound, bound, size=(a, b)).astype(np.float32))
            self.params.append(np.zeros(b, dtype=np.float32))

    @staticmethod
    def forward(params, X):
        W1, b1, W2, b2, W3, b3 = params
        z1 = X @ W1 + b1
        a1 = np.maximum(z1, 0)
        z2 = a1 @ W2 + b2
        a2 = np.maximum(z2, 0)
        return z1, a1, z2, a2, a2 @ W3 + b3

    @staticmethod
    def logits(params, X, batch=8192):
        outs = [MLP.forward(params, X[i:i + batch])[-1] for i in range(0, len(X), batch)]
        return np.concatenate(outs) if outs else np.zeros((0, params[-1].shape[0]), np.float32)


def output_error(out, y, kind, weights):
    """Per-example derivative of the (weighted) loss with respect to the output layer."""
    if kind == "binary":
        p = expit(out[:, 0])
        return ((p - y) * weights)[:, None].astype(np.float32)
    if kind == "multiclass":
        z = out - out.max(axis=1, keepdims=True)
        p = np.exp(z)
        p /= p.sum(axis=1, keepdims=True)
        p[np.arange(len(y)), y] -= 1.0
        return (p * weights[:, None]).astype(np.float32)
    return (out[:, 0] - y)[:, None].astype(np.float32)


def per_example_loss(params, X, y, kind):
    out = MLP.logits(params, X)
    if kind == "binary":
        return np.logaddexp(0, out[:, 0]) - y * out[:, 0]
    if kind == "multiclass":
        z = out - out.max(axis=1, keepdims=True)
        logp = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
        return -logp[np.arange(len(y)), y]
    return 0.5 * (out[:, 0] - y) ** 2


def backward_terms(params, X, y, kind, weights):
    W1, b1, W2, b2, W3, b3 = params
    z1, a1, z2, a2, out = MLP.forward(params, X)
    d3 = output_error(out, y, kind, weights)
    d2 = (d3 @ W3.T) * (z2 > 0)
    d1 = (d2 @ W2.T) * (z1 > 0)
    return (X, d1), (a1, d2), (a2, d3)


def batch_gradient(params, X, y, kind, weights):
    terms = backward_terms(params, X, y, kind, weights)
    m = max(len(X), 1)
    grads = []
    for a, d in terms:
        grads += [a.T @ d / m, d.sum(axis=0) / m]
    return grads


def clipped_noisy_gradient(params, X, y, kind, weights, clip, sigma, expected_batch, rng):
    """DP-SGD gradient: exact per-example clipping of the full parameter vector.

    For a linear layer the per-example weight gradient is the outer product a_i d_i^T,
    whose Frobenius norm is ||a_i|| ||d_i||; the bias gradient is d_i. The clipped sum
    over examples is therefore A^T diag(c) D without materialising per-example tensors.
    """
    terms = backward_terms(params, X, y, kind, weights)
    sq = np.zeros(len(X), dtype=np.float64)
    for a, d in terms:
        sq += (np.square(a).sum(axis=1) + 1.0) * np.square(d).sum(axis=1)
    norms = np.sqrt(sq)
    factor = np.minimum(1.0, clip / np.maximum(norms, 1e-12)).astype(np.float32)
    grads = []
    for a, d in terms:
        dc = d * factor[:, None]
        grads += [a.T @ dc, dc.sum(axis=0)]
    noisy = [(g + rng.normal(0.0, sigma * clip, size=g.shape)).astype(np.float32) / expected_batch
             for g in grads]
    return noisy, norms


# Privacy accounting


def dpsgd_epsilon(q, sigma, steps, delta):
    from dp_accounting import dp_event
    from dp_accounting.rdp import rdp_privacy_accountant as rdp
    if steps == 0:
        return 0.0
    acc = rdp.RdpAccountant()
    acc.compose(dp_event.PoissonSampledDpEvent(min(q, 1.0), dp_event.GaussianDpEvent(sigma)), steps)
    return float(acc.get_epsilon(delta))


_SIGMA_CACHE = {}


def calibrate_dpsgd_sigma(target_eps, q, steps, delta, lo=0.3, hi=200.0):
    """Smallest noise multiplier (to a relative tolerance of 1e-4) meeting the target epsilon."""
    key = (round(float(target_eps), 6), round(float(q), 8), int(steps), float(delta))
    if key in _SIGMA_CACHE:
        return _SIGMA_CACHE[key]
    if dpsgd_epsilon(q, hi, steps, delta) > target_eps:
        raise ValueError("Target epsilon unreachable")
    while hi / lo > 1.0001:
        mid = math.sqrt(lo * hi)
        if dpsgd_epsilon(q, mid, steps, delta) > target_eps:
            lo = mid
        else:
            hi = mid
    _SIGMA_CACHE[key] = hi
    return hi


RDP_ORDERS = np.array([1.25, 1.5, 1.75, 2, 2.5, 3, 3.5, 4, 5, 6, 8, 10, 12, 14, 16, 20, 24,
                       28, 32, 40, 48, 56, 64, 96, 128, 192, 256], dtype=float)


def skellam_rdp(mu, orders=RDP_ORDERS, sensitivity=1):
    """Exact Renyi divergence between Skellam(mu, mu) and its shift by the sensitivity."""
    if mu <= 0:
        return np.full(len(orders), np.inf)
    sd = math.sqrt(2 * mu)
    L = int(math.ceil(40 * sd + 200))
    k = np.arange(-L, L + 1)
    logp = stats.skellam.logpmf(k, mu, mu)
    logq = stats.skellam.logpmf(k - sensitivity, mu, mu)
    finite = np.isfinite(logp) & np.isfinite(logq)
    logp, logq = logp[finite], logq[finite]
    out = []
    for a in orders:
        out.append(float(logsumexp(a * logp + (1 - a) * logq) / (a - 1)))
    return np.array(out)


def rdp_to_epsilon(rdp, delta, orders=RDP_ORDERS):
    from dp_accounting.rdp import rdp_privacy_accountant as r
    eps, _ = r.compute_epsilon(list(orders), list(rdp), delta)
    return float(eps)


def skellam_epsilon(mu, delta):
    return rdp_to_epsilon(skellam_rdp(mu), delta)


def skellam_delta_exact(mu, eps, sensitivity=1):
    """Exact hockey-stick divergence of the shifted Skellam pair (both directions)."""
    sd = math.sqrt(2 * mu)
    L = int(math.ceil(60 * sd + 400))
    k = np.arange(-L, L + 1)
    p = stats.skellam.pmf(k, mu, mu)
    q = stats.skellam.pmf(k - sensitivity, mu, mu)
    return float(max(np.sum(np.maximum(0.0, p - math.exp(eps) * q)),
                     np.sum(np.maximum(0.0, q - math.exp(eps) * p))))


def skellam_epsilon_exact(mu, delta, hi=50.0):
    """Smallest epsilon with exact delta(epsilon) <= delta, by bisection."""
    lo = 0.0
    if skellam_delta_exact(mu, hi) > delta:
        return float("inf")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if skellam_delta_exact(mu, mid) > delta:
            lo = mid
        else:
            hi = mid
    return hi


def calibrate_skellam_mu(target_eps, delta, lo=1e-3, hi=1e5):
    """Smallest total Skellam parameter whose exact privacy profile meets (eps, delta)."""
    if skellam_delta_exact(lo, target_eps) <= delta:
        return lo
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if skellam_delta_exact(mid, target_eps) > delta:
            lo = mid
        else:
            hi = mid
    return hi


def gaussian_epsilon(sigma, delta):
    return rdp_to_epsilon(RDP_ORDERS / (2 * sigma ** 2), delta)


def dpsgd_rdp_curve(q, sigma, steps, orders=RDP_ORDERS):
    from dp_accounting.rdp import rdp_privacy_accountant as r
    return np.array([r._compute_rdp_poisson_subsampled_gaussian(min(q, 1.0), sigma, [a])[0]
                     for a in orders]) * steps


# Secure aggregation


class SecureAggregator:
    """Semi-honest pairwise-mask secure summation (Bonawitz et al., 2017, without dropout recovery).

    Each client pair derives a shared key by X25519 agreement and HKDF-SHA256; the key seeds
    a ChaCha20 keystream that is read as 32-bit words. Client i adds masks shared with
    higher-indexed clients and subtracts masks shared with lower-indexed clients, so the
    masks cancel in the modular sum. The server sees only masked vectors. If any client
    drops out after masking, the sum cannot be recovered (no secret sharing is implemented).
    """

    MOD = 1 << 32

    def __init__(self, clients: int, session: bytes):
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        self.k = clients
        self.session = session
        self.private = [X25519PrivateKey.generate() for _ in range(clients)]
        self.public = [p.public_key() for p in self.private]
        self.public_bytes = [pk.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
                             for pk in self.public]
        self.bytes_sent = 32 * clients * clients  # public keys broadcast to every client
        self.seconds = 0.0

    def _mask(self, i, j, length, counter):
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
        shared = self.private[i].exchange(self.public[j])
        lo, hi = min(i, j), max(i, j)
        info = self.session + f"|{lo}|{hi}|{counter}".encode()
        key = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(shared)
        nonce = counter.to_bytes(16, "little")
        stream = Cipher(algorithms.ChaCha20(key, nonce), mode=None).encryptor().update(bytes(4 * length))
        return np.frombuffer(stream, dtype="<u4").astype(np.uint64)

    def masked_input(self, i, vector_u32, counter):
        masked = vector_u32.astype(np.uint64)
        for j in range(self.k):
            if j == i:
                continue
            m = self._mask(i, j, len(vector_u32), counter)
            masked = (masked + m) % self.MOD if i < j else (masked - m) % self.MOD
        return masked.astype(np.uint32)

    def sum_integers(self, vectors, counter=0):
        """Securely sum signed integer vectors; returns the signed sum."""
        start = time.perf_counter()
        enc = [(np.asarray(v, dtype=np.int64) % self.MOD).astype(np.uint32) for v in vectors]
        masked = [self.masked_input(i, v, counter) for i, v in enumerate(enc)]
        self.bytes_sent += sum(4 * len(m) for m in masked)
        total = np.zeros(len(masked[0]), dtype=np.uint64)
        for m in masked:
            total = (total + m.astype(np.uint64)) % self.MOD
        signed = total.astype(np.int64)
        signed[signed >= self.MOD // 2] -= self.MOD
        self.seconds += time.perf_counter() - start
        return signed

    def mean_parameters(self, param_lists, counter, weights=None, scale=2 ** 20, bound=1000.0):
        """Size-weighted mean: each client pre-multiplies by its public weight share."""
        w = np.ones(len(param_lists)) if weights is None else np.asarray(weights, dtype=float)
        w = w / w.sum()
        flat = [np.concatenate([p.ravel() for p in params]) * wk for params, wk in zip(param_lists, w)]
        ints = [np.round(np.clip(f, -bound, bound) * scale).astype(np.int64) for f in flat]
        total = self.sum_integers(ints, counter)
        mean = total.astype(np.float64) / scale
        out, pos = [], 0
        for p in param_lists[0]:
            out.append(mean[pos:pos + p.size].reshape(p.shape).astype(np.float32))
            pos += p.size
        return out


# Federated training


@dataclass
class TrainConfig:
    kind: str
    rounds: int = 25
    local_epochs: int = 2
    batch: int = 64
    lr: float = 0.05
    momentum: float = 0.9
    prox_mu: float = 0.0
    hidden: tuple = (64, 32)
    pos_weight: float = 1.0
    class_weights: np.ndarray | None = None
    participation: float = 1.0
    clip: float = 1.0
    target_epsilon: float | None = None
    delta: float = 1e-5
    aggregator: str = "mean"  # mean, trimmed, median
    algorithm: str = "fedavg"  # fedavg, fedprox, scaffold, dp
    secure: bool = False
    malicious_client: int | None = None
    malicious_scale: float = 4.0
    label_noise_client: int | None = None
    label_noise_rate: float = 0.0
    max_grad_norm: float = 5.0


def example_weights(y, cfg: TrainConfig):
    if cfg.kind == "binary":
        return np.where(y == 1, cfg.pos_weight, 1.0).astype(np.float32)
    if cfg.kind == "multiclass":
        return cfg.class_weights[y].astype(np.float32)
    return np.ones(len(y), dtype=np.float32)


def n_outputs(kind, classes):
    return classes if kind == "multiclass" else 1


def local_update(params, X, y, cfg: TrainConfig, rng, sigma=None, global_params=None,
                 c_global=None, c_local=None):
    params = [p.copy() for p in params]
    velocity = [np.zeros_like(p) for p in params]
    n = len(y)
    w = example_weights(y, cfg)
    steps_per_epoch = max(1, int(math.ceil(n / cfg.batch)))
    q = min(1.0, cfg.batch / max(n, 1))
    steps = 0
    for _ in range(cfg.local_epochs):
        order = rng.permutation(n)
        for s in range(steps_per_epoch):
            if cfg.algorithm == "dp":
                idx = np.flatnonzero(rng.random(n) < q)
                grads, _ = clipped_noisy_gradient(params, X[idx], y[idx], cfg.kind, w[idx],
                                                  cfg.clip, sigma, q * n, rng)
            else:
                idx = order[s * cfg.batch:(s + 1) * cfg.batch]
                if len(idx) == 0:
                    continue
                grads = batch_gradient(params, X[idx], y[idx], cfg.kind, w[idx])
                total = math.sqrt(sum(float(np.square(g).sum()) for g in grads))
                if total > cfg.max_grad_norm:  # batch-level norm clipping for numerical stability
                    grads = [g * (cfg.max_grad_norm / total) for g in grads]
            if cfg.algorithm == "fedprox" and global_params is not None:
                grads = [g + cfg.prox_mu * (p - gp) for g, p, gp in zip(grads, params, global_params)]
            if cfg.algorithm == "scaffold":
                grads = [g - cl + cg for g, cl, cg in zip(grads, c_local, c_global)]
            for i in range(len(params)):
                velocity[i] = cfg.momentum * velocity[i] + grads[i]
                params[i] = params[i] - cfg.lr * velocity[i]
            steps += 1
    new_c = None
    if cfg.algorithm == "scaffold":
        new_c = [cl - cg + (gp - p) / (steps * cfg.lr)
                 for cl, cg, gp, p in zip(c_local, c_global, global_params, params)]
    return params, steps, new_c


def aggregate(updates, how, weights=None):
    if how == "mean":
        w = np.ones(len(updates)) if weights is None else np.asarray(weights, dtype=float)
        w = w / w.sum()
        return [np.tensordot(w, np.stack([u[i] for u in updates]), axes=1).astype(np.float32)
                for i in range(len(updates[0]))]
    stacked = [np.stack([u[i] for u in updates]) for i in range(len(updates[0]))]
    if how == "median":
        return [np.median(s, axis=0).astype(np.float32) for s in stacked]
    if how == "trimmed":
        k = len(updates)
        b = int(math.floor(0.25 * k))
        if b == 0:  # fewer than four clients: nothing can be trimmed
            return aggregate(updates, "mean")
        out = []
        for s in stacked:
            srt = np.sort(s, axis=0)
            out.append(srt[b:k - b].mean(axis=0).astype(np.float32))
        return out
    raise ValueError(how)


def federated_train(clients, cfg: TrainConfig, d, classes, seed):
    rng = np.random.default_rng(seed)
    model = MLP(d, n_outputs(cfg.kind, classes), cfg.hidden, rng)
    g = model.params
    K = len(clients)
    log = {"rounds": cfg.rounds, "clients": K, "algorithm": cfg.algorithm,
           "aggregator": cfg.aggregator, "secure_aggregation": cfg.secure,
           "parameter_count": int(sum(p.size for p in g))}
    data = []
    for k, c in enumerate(clients):
        y = c["ytr"].copy()
        if cfg.label_noise_client == k and cfg.label_noise_rate > 0:
            flip = rng.random(len(y)) < cfg.label_noise_rate
            if cfg.kind == "binary":
                y[flip] = 1 - y[flip]
            elif cfg.kind == "multiclass":
                y[flip] = rng.integers(0, classes, flip.sum())
        data.append((c["Xtr"], y))
    sigmas, qs, steps_total = [None] * K, [], [0] * K
    if cfg.algorithm == "dp":
        for k, (X, _) in enumerate(data):
            n = len(X)
            q = min(1.0, cfg.batch / n)
            T = cfg.rounds * cfg.local_epochs * max(1, int(math.ceil(n / cfg.batch)))
            sigmas[k] = calibrate_dpsgd_sigma(cfg.target_epsilon, q, T, cfg.delta)
            qs.append(q)
    c_global = [np.zeros_like(p) for p in g] if cfg.algorithm == "scaffold" else None
    c_locals = [[np.zeros_like(p) for p in g] for _ in range(K)] if cfg.algorithm == "scaffold" else None
    secure = SecureAggregator(K, f"model-{seed}".encode()) if cfg.secure else None
    selected_count = max(1, int(math.ceil(cfg.participation * K)))
    bytes_down = bytes_up = 0
    t0 = time.perf_counter()
    for r in range(cfg.rounds):
        chosen = sorted(rng.choice(K, size=selected_count, replace=False).tolist())
        updates, dcs = [], []
        for k in chosen:
            X, y = data[k]
            p_new, steps, new_c = local_update(g, X, y, cfg, rng, sigmas[k], g,
                                               c_global, c_locals[k] if c_locals else None)
            steps_total[k] += steps
            if cfg.malicious_client == k:
                p_new = [gp - cfg.malicious_scale * (pn - gp) for gp, pn in zip(g, p_new)]
            if cfg.algorithm == "scaffold":
                dcs.append([nc - oc for nc, oc in zip(new_c, c_locals[k])])
                c_locals[k] = new_c
            updates.append(p_new)
        bytes_down += 4 * log["parameter_count"] * len(chosen)
        bytes_up += 4 * log["parameter_count"] * len(chosen)
        sizes = [len(data[k][1]) for k in chosen]
        if secure is not None and cfg.aggregator == "mean":
            g = secure.mean_parameters(updates, counter=r, weights=sizes)
        else:
            g = aggregate(updates, cfg.aggregator, sizes)
        if cfg.algorithm == "scaffold":
            c_global = [cg + np.mean([dc[i] for dc in dcs], axis=0) * len(chosen) / K
                        for i, cg in enumerate(c_global)]
            bytes_up += 4 * log["parameter_count"] * len(chosen)
            bytes_down += 4 * log["parameter_count"] * len(chosen)
    log["train_seconds"] = time.perf_counter() - t0
    log["parameter_bytes_up"] = bytes_up
    log["parameter_bytes_down"] = bytes_down
    if secure is not None:
        log["secure_aggregation_bytes"] = secure.bytes_sent
        log["secure_aggregation_seconds"] = secure.seconds
    if cfg.algorithm == "dp":
        eps = [dpsgd_epsilon(qs[k], sigmas[k], steps_total[k], cfg.delta) for k in range(K)]
        log.update({"privacy_unit": "one training record (add or remove)",
                    "accountant": "dp_accounting RDP, Poisson-subsampled Gaussian",
                    "delta": cfg.delta, "clip": cfg.clip, "target_epsilon": cfg.target_epsilon,
                    "noise_multiplier_by_client": sigmas, "sample_rate_by_client": qs,
                    "steps_by_client": steps_total, "epsilon_by_client": eps,
                    "epsilon_max": max(eps)})
    return g, log


def train_central(X, y, cfg: TrainConfig, d, classes, seed):
    rng = np.random.default_rng(seed)
    model = MLP(d, n_outputs(cfg.kind, classes), cfg.hidden, rng)
    local_cfg = TrainConfig(**{**cfg.__dict__, "local_epochs": cfg.rounds * cfg.local_epochs,
                               "algorithm": "fedavg"})
    params, _, _ = local_update(model.params, X, y, local_cfg, rng)
    return params


# Scores and metrics


def scores(params, X, kind):
    out = MLP.logits(params, X)
    if kind == "binary":
        return expit(out[:, 0])
    if kind == "multiclass":
        z = out - out.max(axis=1, keepdims=True)
        p = np.exp(z)
        return p / p.sum(axis=1, keepdims=True)
    return out[:, 0]


def expected_calibration_error(p, y, bins=15):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    ece = 0.0
    for b in range(bins):
        m = idx == b
        if m.any():
            ece += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(ece)


def binary_metrics(p, y):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    pred = (p >= 0.5).astype(int)
    res = {"pr_auc": float(average_precision_score(y, p)) if 0 < y.sum() < len(y) else float("nan"),
           "roc_auc": float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) else float("nan"),
           "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
           "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
           "mcc": float(matthews_corrcoef(y, pred)),
           "recall_rare": float(pred[y == 1].mean()) if (y == 1).any() else float("nan"),
           "false_positive_rate": float(pred[y == 0].mean()) if (y == 0).any() else float("nan"),
           "brier": float(np.mean((p - y) ** 2)),
           "nll": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
           "ece": expected_calibration_error(p, y),
           "prevalence": float(y.mean()), "n": int(len(y))}
    return res


def multiclass_metrics(P, y):
    pred = P.argmax(axis=1)
    conf = P.max(axis=1)
    return {"accuracy": float((pred == y).mean()),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
            "mcc": float(matthews_corrcoef(y, pred)),
            "ece": expected_calibration_error(conf, (pred == y).astype(float)),
            "nll": float(-np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-7, 1)))),
            "n": int(len(y))}


def regression_metrics(pred, y, scale, mean):
    a = y * scale + mean
    b = pred * scale + mean
    return {"rmse": float(np.sqrt(mean_squared_error(a, b))), "mae": float(mean_absolute_error(a, b)),
            "r2": float(r2_score(a, b)), "n": int(len(y))}


def metrics_for(kind, out, y, prep: Prepared):
    if not np.all(np.isfinite(out)):
        return {"diverged": True, "n": int(len(y))}
    if kind == "binary":
        return binary_metrics(out, y)
    if kind == "multiclass":
        return multiclass_metrics(out, y)
    return regression_metrics(out, y, prep.target_scale, prep.target_mean)


# Private aggregate risk control


BINARY_EDGES = np.concatenate([[-np.inf], expit(np.linspace(-8, 8, 25)), [np.inf]])  # 26 bins
CONFIDENCE_EDGES = np.concatenate([[-np.inf], np.linspace(0.15, 1.0, 18)[:-1], [np.inf]])
RESIDUAL_EDGES = np.concatenate([[0.0], np.linspace(0.05, 4.0, 80), [np.inf]])


def histogram(values, edges):
    return np.histogram(values, bins=edges)[0].astype(np.int64)


def skellam_noise(mu, size, rng):
    if mu <= 0:
        return np.zeros(size, dtype=np.int64)
    return rng.poisson(mu, size).astype(np.int64) - rng.poisson(mu, size).astype(np.int64)


def binomial_skellam_pvalue(m_noisy, n, alpha, mu_sum):
    """P(Bin(n, alpha) + Z <= m) with Z ~ Skellam(mu_sum, mu_sum); exact convolution.

    Under H: risk >= alpha, the noisy count is stochastically at least this large, so the
    probability is a valid (super-uniform) p-value for rejecting H.
    """
    n = int(max(n, 0))
    if n == 0:
        return 1.0
    b = np.arange(n + 1)
    pb = stats.binom.pmf(b, n, alpha)
    if mu_sum <= 0:
        return float(stats.binom.cdf(math.floor(m_noisy), n, alpha))
    return float(np.sum(pb * stats.skellam.cdf(math.floor(m_noisy) - b, mu_sum, mu_sum)))


def count_lower_bound(total_noisy, bins, mu, delta_n):
    if mu <= 0:
        return int(total_noisy)
    q = stats.skellam.ppf(1 - delta_n, bins * mu, bins * mu)
    return int(max(0, math.floor(total_noisy - q)))


def resolve_method(method, mu):
    """Map a policy variant to (noise scale, scan rule)."""
    table = {"proposed": (mu, "proposed"), "ucb_without_noise": (mu, "ucb_without_noise"),
             "plugin": (mu, "plugin"), "nonprivate_ltt": (0.0, "ucb_without_noise"),
             "nonprivate_plugin": (0.0, "plugin")}
    return table[method]


def sample_size_bound(total_noisy, bins, mu, delta_n, base):
    if base == "plugin" or mu <= 0:
        return int(max(total_noisy, 0))
    return count_lower_bound(total_noisy, bins, mu, delta_n)


def risk_scan(cum_noisy, mu, n_lower, alpha, delta_b, method):
    """Fixed-sequence scan over nested decision sets ordered by increasing risk.

    cum_noisy[j] is the (noisy) number of risk events when the first j+1 bins are admitted.
    Returns the number of admitted bins (0 means nothing can be certified).
    method: proposed, ucb_without_noise, plugin.
    """
    admitted = 0
    for j, m in enumerate(cum_noisy):
        if method == "plugin":
            ok = n_lower > 0 and m / n_lower <= alpha
        elif method == "ucb_without_noise":
            ok = binomial_skellam_pvalue(m, n_lower, alpha, 0.0) <= delta_b
        elif method == "proposed":
            ok = binomial_skellam_pvalue(m, n_lower, alpha, (j + 1) * mu) <= delta_b
        else:
            raise ValueError(method)
        if not ok:
            break
        admitted = j + 1
    return admitted


@dataclass
class RiskPolicy:
    alpha_miss: float = 0.10
    alpha_false_alarm: float = 0.05
    alpha_selective: float = 0.10
    alpha_interval: float = 0.10
    delta_test: float = 0.04
    delta_count: float = 0.01


def private_histograms(client_values, edges, mu_total, rng, secure, counter):
    """Clients add Skellam(mu/K, mu/K) noise; the server learns only the secure sum."""
    K = len(client_values)
    vectors = []
    for v in client_values:
        h = histogram(v, edges)
        vectors.append(h + skellam_noise(mu_total / K, len(h), rng))
    if secure is not None:
        return secure.sum_integers(vectors, counter)
    return np.sum(vectors, axis=0)


def binary_edges(bins):
    """Fixed score grid equally spaced on the logit scale between -8 and 8, plus two open bins."""
    return np.concatenate([[-np.inf], expit(np.linspace(-8, 8, bins - 1)), [np.inf]])


def binary_policy(client_scores, client_labels, mu, policy: RiskPolicy, method, rng, secure=None,
                  counter=0, poison=None, edges=None):
    """Certify t_low (miss control) and t_high (false-alarm control) for binary detection."""
    edges = BINARY_EDGES if edges is None else edges
    B = len(edges) - 1
    mu_eff, base = resolve_method(method, mu)
    pos = private_histograms([s[y == 1] for s, y in zip(client_scores, client_labels)], edges,
                             mu_eff, rng, secure, counter)
    neg = private_histograms([s[y == 0] for s, y in zip(client_scores, client_labels)], edges,
                             mu_eff, rng, secure, counter + 1)
    if poison is not None:
        pos = pos + poison.get("pos", 0)
        neg = neg + poison.get("neg", 0)
    n1 = sample_size_bound(pos.sum(), B, mu_eff, policy.delta_count, base)
    n0 = sample_size_bound(neg.sum(), B, mu_eff, policy.delta_count, base)
    lo_bins = risk_scan(np.cumsum(pos), mu_eff, n1, policy.alpha_miss, policy.delta_test, base)
    hi_bins = risk_scan(np.cumsum(neg[::-1]), mu_eff, n0, policy.alpha_false_alarm,
                        policy.delta_test, base)
    t_low = edges[lo_bins] if lo_bins > 0 else -np.inf  # pass automatically when score < t_low
    t_high = edges[B - hi_bins] if hi_bins > 0 else np.inf  # alarm automatically when score >= t_high
    calibrated = (np.maximum(pos, 0) + 0.5) / (np.maximum(pos, 0) + np.maximum(neg, 0) + 1.0)
    return {"t_low": float(t_low), "t_high": float(t_high), "bins_low": int(lo_bins),
            "bins_high": int(hi_bins), "n1_lower": n1, "n0_lower": n0,
            "noisy_pos": pos.tolist(), "noisy_neg": neg.tolist(),
            "binning_probabilities": calibrated.tolist(), "edges": edges.tolist()}


def apply_binary_policy(p, y, pol):
    t_low, t_high = pol["t_low"], pol["t_high"]
    auto_pass = p < t_low
    auto_alarm = (p >= t_high) & ~auto_pass
    escalate = ~auto_pass & ~auto_alarm
    pos, neg = y == 1, y == 0
    return {"miss_rate": float(auto_pass[pos].mean()) if pos.any() else float("nan"),
            "false_alarm_rate": float(auto_alarm[neg].mean()) if neg.any() else float("nan"),
            "escalation_rate": float(escalate.mean()),
            "automation_rate": float(1 - escalate.mean()),
            "auto_pass_rate": float(auto_pass.mean()), "auto_alarm_rate": float(auto_alarm.mean()),
            "faults_escalated": float(escalate[pos].mean()) if pos.any() else float("nan"),
            "faults_alarmed": float(auto_alarm[pos].mean()) if pos.any() else float("nan")}


def binning_calibrate(p, pol):
    edges = np.asarray(pol["edges"], dtype=float)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, len(edges) - 2)
    return np.asarray(pol["binning_probabilities"])[idx]


def selective_policy(client_probs, client_labels, mu, policy, method, rng, secure=None, counter=0):
    edges = CONFIDENCE_EDGES
    B = len(edges) - 1
    wrong_vals, all_vals = [], []
    for P, y in zip(client_probs, client_labels):
        conf, pred = P.max(axis=1), P.argmax(axis=1)
        wrong_vals.append(conf[pred != y])
        all_vals.append(conf)
    mu_eff, base = resolve_method(method, mu)
    wrong = private_histograms(wrong_vals, edges, mu_eff, rng, secure, counter)
    total = private_histograms(all_vals, edges, mu_eff, rng, secure, counter + 1)
    n = sample_size_bound(total.sum(), B, mu_eff, policy.delta_count, base)
    # Admit bins from the highest confidence downwards; risk = P(wrong and admitted).
    admitted = risk_scan(np.cumsum(wrong[::-1]), mu_eff, n, policy.alpha_selective,
                         policy.delta_test, base)
    threshold = edges[B - admitted] if admitted > 0 else np.inf
    return {"threshold": float(threshold), "bins": int(admitted), "n_lower": n}


def apply_selective_policy(P, y, pol):
    conf, pred = P.max(axis=1), P.argmax(axis=1)
    accept = conf >= pol["threshold"]
    wrong = pred != y
    return {"joint_error": float((accept & wrong).mean()), "coverage": float(accept.mean()),
            "selective_error": float(wrong[accept].mean()) if accept.any() else float("nan"),
            "escalation_rate": float(1 - accept.mean())}


def interval_policy(client_res, mu, policy, method, rng, secure=None, counter=0):
    edges = RESIDUAL_EDGES
    B = len(edges) - 1
    mu_eff, base = resolve_method(method, mu)
    hist = private_histograms([np.abs(r) for r in client_res], edges, mu_eff, rng, secure, counter)
    n = sample_size_bound(hist.sum(), B, mu_eff, policy.delta_count, base)
    # Exclude residual bins from the top: the risk is P(|residual| > q).
    admitted = risk_scan(np.cumsum(hist[::-1]), mu_eff, n, policy.alpha_interval,
                         policy.delta_test, base)
    q = edges[B - admitted] if admitted > 0 else np.inf
    return {"half_width_scaled": float(q), "bins": int(admitted), "n_lower": n}


def apply_interval_policy(pred, y, pol, scale):
    q = pol["half_width_scaled"]
    covered = np.abs(y - pred) < q
    return {"coverage": float(covered.mean()), "exceedance": float(1 - covered.mean()),
            "half_width": float(q * scale) if np.isfinite(q) else float("inf")}


# Attacks


def membership_inference(params, Xm, ym, Xn, yn, kind, rng, max_n=5000):
    """Loss-threshold attack (Yeom et al., 2018): lower loss signals membership."""
    nm = min(len(ym), len(yn), max_n)
    im = rng.choice(len(ym), nm, replace=False)
    inn = rng.choice(len(yn), nm, replace=False)
    lm = per_example_loss(params, Xm[im], ym[im], kind)
    ln = per_example_loss(params, Xn[inn], yn[inn], kind)
    s = np.concatenate([-lm, -ln])
    lab = np.concatenate([np.ones(nm), np.zeros(nm)])
    fpr, tpr, _ = roc_curve(lab, s)
    res = {"auc": float(roc_auc_score(lab, s)), "advantage": float(np.max(tpr - fpr)),
           "tpr_at_1pct_fpr": float(np.interp(0.01, fpr, tpr)), "pairs": int(nm)}
    if kind == "binary":
        pm, pn = ym[im] == 1, yn[inn] == 1
        if pm.sum() >= 5 and pn.sum() >= 5:
            s2 = np.concatenate([-lm[pm], -ln[pn]])
            l2 = np.concatenate([np.ones(pm.sum()), np.zeros(pn.sum())])
            res["auc_rare_class"] = float(roc_auc_score(l2, s2))
    return res


def reconstruct_from_update(params, x, y, kind, weights=1.0, noise_sigma=0.0, clip=None, rng=None):
    """Analytic input recovery from first-layer gradients of a single-record update.

    For one record, dL/dW1 = x d1^T and dL/db1 = d1, so x = dL/dW1[:, j] / dL/db1[j] for any
    hidden unit j with non-zero bias gradient. Returns cosine similarity and relative error.
    """
    X, Y = x[None, :], np.array([y])
    terms = backward_terms(params, X, Y, kind, np.array([weights], dtype=np.float32))
    (a, d1) = terms[0]
    gW1, gb1 = a.T @ d1, d1.sum(axis=0)
    if clip is not None:
        norm = math.sqrt(sum(float((np.square(aa).sum() + 1) * np.square(dd).sum()) for aa, dd in terms))
        f = min(1.0, clip / max(norm, 1e-12))
        gW1, gb1 = gW1 * f, gb1 * f
    if noise_sigma > 0:
        gW1 = gW1 + rng.normal(0, noise_sigma, gW1.shape)
        gb1 = gb1 + rng.normal(0, noise_sigma, gb1.shape)
    j = int(np.argmax(np.abs(gb1)))
    if abs(gb1[j]) < 1e-12:
        return {"recovered": False}
    xh = gW1[:, j] / gb1[j]
    cos = float(xh @ x / (np.linalg.norm(xh) * np.linalg.norm(x) + 1e-12))
    rel = float(np.linalg.norm(xh - x) / (np.linalg.norm(x) + 1e-12))
    return {"recovered": True, "cosine": cos, "relative_error": rel}


def corrupt(X, how, level, rng):
    X = X.copy()
    if how == "gaussian":
        return (X + rng.normal(0, level, X.shape)).astype(np.float32)
    if how == "missing":
        mask = rng.random(X.shape) < level
        X[mask] = 0.0  # imputed with the training median, which is zero after scaling
        return X
    raise ValueError(how)


def jsonable(obj):
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj)):
        return str(obj)
    return obj
