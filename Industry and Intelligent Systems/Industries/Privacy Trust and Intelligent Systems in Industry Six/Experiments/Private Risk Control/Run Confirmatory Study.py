"""Execute the tuning, confirmatory, sensitivity and attack stages of the study.

Usage examples (from this folder):
    python "Run Confirmatory Study.py" tune --datasets maintenance steel
    python "Run Confirmatory Study.py" main --datasets maintenance --seeds 1 2 3 4 5
    python "Run Confirmatory Study.py" sensitivity --datasets maintenance --seeds 1 2 3 --variants poison
    python "Run Confirmatory Study.py" reconstruction --datasets maintenance --seeds 1
Every run writes one JSON file; failures are written to a failure log rather than dropped.
"""
import argparse
import importlib.util
import json
import math
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load_library():
    spec = importlib.util.spec_from_file_location("private_risk_control", HERE / "Private Risk Control Library.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["private_risk_control"] = module
    spec.loader.exec_module(module)
    return module


L = load_library()
CONFIG = json.loads((HERE / "Study Configuration.json").read_text())
TUNED_PATH = HERE / "Tuned Hyperparameters.json"
RESULTS = HERE / "Results"


def tuned():
    return json.loads(TUNED_PATH.read_text()) if TUNED_PATH.exists() else {}


def class_weights(task):
    if task.kind != "multiclass":
        return None
    counts = np.array([L.STEEL_PUBLIC_COUNTS[n] for n in task.class_names], dtype=float)
    return np.minimum(counts.sum() / (len(counts) * counts), 20.0).astype(np.float32)


def make_cfg(task, method, hp, **overrides):
    c = CONFIG["training"]
    algo = {"central": "fedavg", "local": "fedavg", "fedavg": "fedavg", "fedprox": "fedprox",
            "scaffold": "scaffold", "trimmed": "fedavg", "median": "fedavg", "dp": "dp"}[method]
    lr_key = {"trimmed": "fedavg", "median": "fedavg"}.get(method, method)
    cfg = L.TrainConfig(kind=task.kind, rounds=c["rounds"], local_epochs=c["local_epochs"],
                        batch=CONFIG.get("batch_by_dataset", {}).get(task.name, c["batch"]), hidden=tuple(c["hidden"]), clip=c["clip"],
                        delta=c["delta"], algorithm=algo,
                        momentum=0.0 if method == "scaffold" else c["momentum"],
                        lr=hp.get(lr_key, {}).get("lr", c["default_lr"]),
                        prox_mu=hp.get("fedprox", {}).get("mu", 0.01),
                        pos_weight=L.PUBLIC_POSITIVE_WEIGHT.get(task.name, 1.0),
                        class_weights=class_weights(task),
                        aggregator={"trimmed": "trimmed", "median": "median"}.get(method, "mean"))
    if method == "dp":
        dp = hp.get("dp", {})
        cfg.batch = dp.get("batch", cfg.batch)
        cfg.momentum = dp.get("momentum", cfg.momentum)
        if task.kind == "binary":
            cfg.pos_weight = dp.get("pos_weight", cfg.pos_weight)
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def pooled(prep, key):
    X = np.concatenate([c["X" + key] for c in prep.clients])
    y = np.concatenate([c["y" + key] for c in prep.clients])
    return X, y


def predict(model, X, kind):
    if isinstance(model, tuple):  # (sklearn model, kind)
        m = model[0]
        if kind == "binary":
            return m.predict_proba(X)[:, 1]
        if kind == "multiclass":
            return m.predict_proba(X)
        return m.predict(X)
    if isinstance(model, dict):  # constant reference
        n = len(X)
        if kind == "binary":
            return np.full(n, model["p"])
        if kind == "multiclass":
            return np.tile(model["p"], (n, 1))
        return np.full(n, model["p"])
    return L.scores(model, X, kind)


def selection_metric(kind, out, y):
    if kind == "binary":
        from sklearn.metrics import average_precision_score
        return float(average_precision_score(y, out)) if 0 < y.sum() < len(y) else float("nan")
    if kind == "multiclass":
        from sklearn.metrics import f1_score
        return float(f1_score(y, out.argmax(axis=1), average="macro", zero_division=0))
    return -float(np.sqrt(np.mean((out - y) ** 2)))


def train_models(task, prep, seed, hp, eps_list, include=None, overrides=None):
    overrides = overrides or {}
    d = prep.clients[0]["Xtr"].shape[1]
    classes = len(task.class_names) if task.kind == "multiclass" else 1
    Xtr, ytr = pooled(prep, "tr")
    models, logs = {}, {}
    include = include or ["reference", "linear", "central", "local", "fedavg", "fedprox",
                          "scaffold", "trimmed", "median", "dp"]
    t = time.perf_counter()
    if "reference" in include:
        if task.kind == "binary":
            models["reference"] = {"p": float(ytr.mean())}
        elif task.kind == "multiclass":
            models["reference"] = {"p": np.bincount(ytr, minlength=classes) / len(ytr)}
        else:
            models["reference"] = {"p": float(ytr.mean())}
    if "linear" in include:
        from sklearn.linear_model import LogisticRegression, Ridge
        if task.kind == "regression":
            m = Ridge(alpha=1.0).fit(Xtr, ytr)
        else:
            cfg = make_cfg(task, "central", hp)
            w = L.example_weights(ytr, cfg)
            m = LogisticRegression(max_iter=3000, C=1.0).fit(Xtr, ytr, sample_weight=w)
        models["linear"] = (m, task.kind)
    logs["linear_seconds"] = time.perf_counter() - t
    if "central" in include:
        t = time.perf_counter()
        models["central"] = L.train_central(Xtr, ytr, make_cfg(task, "central", hp, **overrides), d, classes, seed)
        logs["central_seconds"] = time.perf_counter() - t
    if "local" in include:
        t = time.perf_counter()
        models["local"] = [L.train_central(c["Xtr"], c["ytr"], make_cfg(task, "local", hp, **overrides), d,
                                           classes, seed + 100 + k) for k, c in enumerate(prep.clients)]
        logs["local_seconds"] = time.perf_counter() - t
    for method in ["fedavg", "fedprox", "scaffold", "trimmed", "median"]:
        if method in include:
            cfg = make_cfg(task, method, hp, **overrides)
            models[method], logs[method] = L.federated_train(prep.clients, cfg, d, classes, seed)
    if "dp" in include:
        for eps in eps_list:
            cfg = make_cfg(task, "dp", hp, target_epsilon=float(eps), secure=True, **overrides)
            name = f"dp eps {eps:g}"
            models[name], logs[name] = L.federated_train(prep.clients, cfg, d, classes, seed)
    return models, logs, classes


def evaluate(task, prep, models):
    out = {}
    for name, model in models.items():
        res = {}
        if name == "local":
            per = []
            for k, m in enumerate(model):
                g = L.metrics_for(task.kind, predict(m, prep.Xte, task.kind), prep.yte, prep)
                c = prep.clients[k]
                own = (L.metrics_for(task.kind, predict(m, c["Xte"], task.kind), c["yte"], prep)
                       if len(c["yte"]) > 0 else {})
                per.append({"global_test": g, "own_test": own})
            res["clients"] = per
            out[name] = res
            continue
        res["test"] = L.metrics_for(task.kind, predict(model, prep.Xte, task.kind), prep.yte, prep)
        for label, (X, y, _) in prep.extra_tests.items():
            res[label] = L.metrics_for(task.kind, predict(model, X, task.kind), y, prep)
        per = []
        for c in prep.clients:
            if len(c["yte"]) >= 5 and (task.kind != "binary" or 0 < c["yte"].sum() < len(c["yte"])):
                per.append(L.metrics_for(task.kind, predict(model, c["Xte"], task.kind), c["yte"], prep))
            else:
                per.append(None)
        res["client_tests"] = per
        out[name] = res
    return out


def policy_block(task, prep, model, mu, methods, seed, secure_label, edges=None, poison=None,
                 test_sets=None):
    pol = L.RiskPolicy(**CONFIG["policy"])
    rng = np.random.default_rng(seed + 7)
    K = len(prep.clients)
    secure = L.SecureAggregator(K, f"calibration-{seed}-{secure_label}".encode())
    cal_out = [predict(model, c["Xcal"], task.kind) for c in prep.clients]
    cal_y = [c["ycal"] for c in prep.clients]
    test_sets = test_sets or {"test": (prep.Xte, prep.yte)}
    test_sets = {**test_sets, **{k: (v[0], v[1]) for k, v in prep.extra_tests.items()}}
    preds = {k: predict(model, X, task.kind) for k, (X, y) in test_sets.items()}
    res = {}
    for method in methods:
        t = time.perf_counter()
        if task.kind == "binary":
            if method == "default":
                policy = {"t_low": 0.5, "t_high": 0.5}
            else:
                policy = L.binary_policy(cal_out, cal_y, mu, pol, method, rng,
                                         secure if method not in ("nonprivate_ltt", "nonprivate_plugin") else None,
                                         counter=0, poison=poison if method == "proposed" else None,
                                         edges=edges)
            entry = {"policy": {k: v for k, v in policy.items()
                                if k in ("t_low", "t_high", "bins_low", "bins_high", "n1_lower", "n0_lower")}}
            for k, (X, y) in test_sets.items():
                entry[k] = L.apply_binary_policy(preds[k], y, policy)
                if method == "proposed":
                    entry[k]["binning_ece"] = L.expected_calibration_error(L.binning_calibrate(preds[k], policy), y)
        elif task.kind == "multiclass":
            policy = ({"threshold": 0.0} if method == "default" else
                      L.selective_policy(cal_out, cal_y, mu, pol, method, rng,
                                         secure if not method.startswith("nonprivate") else None))
            entry = {"policy": policy}
            for k, (X, y) in test_sets.items():
                entry[k] = L.apply_selective_policy(preds[k], y, policy)
        else:
            if method == "default":
                continue
            res_cal = [o - y for o, y in zip(cal_out, cal_y)]
            policy = L.interval_policy(res_cal, mu, pol, method, rng,
                                       secure if not method.startswith("nonprivate") else None)
            entry = {"policy": policy}
            for k, (X, y) in test_sets.items():
                entry[k] = L.apply_interval_policy(preds[k], y, policy, prep.target_scale)
        entry["seconds"] = time.perf_counter() - t
        res[method] = entry
    res["secure_aggregation"] = {"bytes": secure.bytes_sent, "seconds": secure.seconds}
    return res


def hai_events(task, prep, model, policy_res):
    """Event-level detection on later HAI sessions for a fitted binary policy."""
    label = "later sessions"
    if task.name != "hai" or label not in prep.extra_tests:
        return None
    X, y, rows = prep.extra_tests[label]
    p = predict(model, X, task.kind)
    ev = task.events.iloc[rows].reset_index(drop=True)
    out = {}
    for method, entry in policy_res.items():
        if method == "secure_aggregation":
            continue
        pol = entry["policy"]
        alarm = (p >= pol["t_high"]) & ~(p < pol["t_low"])
        flag = ~(p < pol["t_low"])
        events = []
        for (sess, eid), grp in ev[ev["Event ID"] >= 0].groupby(["Session", "Event ID"]):
            idx = grp.index.to_numpy()
            first_w = grp["Window Index"].min()
            first_sec = int(grp.loc[grp["Window Index"] == first_w, "Event First Second"].iloc[0])
            res = {"session": sess, "event": int(eid)}
            for name, mask in (("alarm", alarm), ("flag", flag)):
                hit = idx[mask[idx]]
                if len(hit):
                    w = int(ev.loc[hit, "Window Index"].min())
                    res[name + "_delay_seconds"] = (w - first_w) * 30 + 30 - first_sec
                else:
                    res[name + "_delay_seconds"] = None
            events.append(res)
        normal = ev["Event ID"].to_numpy() < 0
        out[method] = {"events": events,
                       "detected_by_alarm": float(np.mean([e["alarm_delay_seconds"] is not None for e in events])),
                       "detected_by_flag": float(np.mean([e["flag_delay_seconds"] is not None for e in events])),
                       "normal_windows_alarmed": float(alarm[normal].mean()),
                       "normal_windows_flagged": float(flag[normal].mean())}
    return out


def privacy_report(task, prep, log, mu):
    delta = CONFIG["training"]["delta"]
    K = len(prep.clients)
    eps_cal = L.skellam_epsilon_exact(mu, delta)
    seq = []
    for q, s, T in zip(log["sample_rate_by_client"], log["noise_multiplier_by_client"], log["steps_by_client"]):
        rdp = L.dpsgd_rdp_curve(q, s, T) + L.skellam_rdp(mu)
        seq.append(L.rdp_to_epsilon(rdp, 2 * delta))
    return {"epsilon_training_max": log["epsilon_max"], "skellam_mu_total": mu,
            "epsilon_calibration_secure_sum": eps_cal,
            "epsilon_calibration_without_secure_aggregation": L.skellam_epsilon_exact(mu / K, delta),
            "epsilon_total_parallel": max(log["epsilon_max"], eps_cal), "delta": delta,
            "epsilon_total_sequential_worst_client": max(seq), "delta_sequential": 2 * delta}


def mia(task, prep, models, seed):
    rng = np.random.default_rng(seed + 11)
    Xm, ym = pooled(prep, "tr")
    out = {}
    if task.kind == "regression":
        return out
    for name, m in models.items():
        if name in ("central", "fedavg") or name.startswith("dp eps"):
            out[name] = L.membership_inference(m, Xm, ym, prep.Xte, prep.yte, task.kind, rng)
    return out


def write(result, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(L.jsonable(result), indent=1) + "\n")


def header(task, prep, seed, stage, design):
    return {"study": "Privacy, Trust & Intelligent Systems in Industry 6.0", "stage": stage,
            "dataset": task.name, "design": design, "seed": seed, "kind": task.kind,
            "executed_utc": datetime.now(timezone.utc).isoformat(), "source_sha256": task.hashes,
            "features_used": len(prep.feature_names),
            "clients": [{"train": len(c["ytr"]), "calibration": len(c["ycal"]), "test": len(c["yte"]),
                         "train_positive": int(c["ytr"].sum()) if task.kind == "binary" else None,
                         "calibration_positive": int(c["ycal"].sum()) if task.kind == "binary" else None}
                        for c in prep.clients],
            "test_rows": int(len(prep.yte)),
            "extra_tests": {k: int(len(v[1])) for k, v in prep.extra_tests.items()},
            "configuration": CONFIG, "notes": task.notes}


def gas_recalibration(task, prep, models, eps_list, seed):
    """Recalibrate interval policies on 2014 rows (split across clients) and test on 2015."""
    X14, y14, _ = prep.extra_tests["year 2014"]
    X15, y15, _ = prep.extra_tests["year 2015"]
    K = len(prep.clients)
    parts = np.array_split(np.random.default_rng(seed + 3).permutation(len(y14)), K)
    pol = L.RiskPolicy(**CONFIG["policy"])
    out = {}
    for name in ["fedavg"] + [f"dp eps {e:g}" for e in eps_list]:
        eps = CONFIG["calibration_epsilon_for_nonprivate_models"] if name == "fedavg" else float(name.split()[-1])
        mu = L.calibrate_skellam_mu(float(eps), CONFIG["training"]["delta"])
        res = [predict(models[name], X14[ix], task.kind) - y14[ix] for ix in parts]
        rng = np.random.default_rng(seed + 9)
        entry = {}
        for method in ("nonprivate_ltt", "proposed"):
            policy = L.interval_policy(res, mu, pol, method, rng,
                                       L.SecureAggregator(K, f"recal-{seed}".encode()) if method == "proposed" else None)
            entry[method] = {"policy": policy,
                             "year 2015": L.apply_interval_policy(predict(models[name], X15, task.kind), y15,
                                                                  policy, prep.target_scale)}
        out[name] = entry
    return out


def run_main(dataset, design, seed, eps_list):
    task = L.load_task(dataset)
    prep = L.prepare(task, seed, design, clients=CONFIG["clients"], alpha=CONFIG["dirichlet_alpha"])
    hp = tuned().get(dataset, {})
    result = header(task, prep, seed, "main", design)
    models, logs, _ = train_models(task, prep, seed, hp, eps_list)
    result["training_logs"] = logs
    result["metrics"] = evaluate(task, prep, models)
    methods = CONFIG["policy_methods"]
    result["risk_control"] = {}
    result["privacy"] = {}
    for eps in eps_list:
        name = f"dp eps {eps:g}"
        mu = L.calibrate_skellam_mu(float(eps), CONFIG["training"]["delta"])
        result["risk_control"][name] = policy_block(task, prep, models[name], mu, methods, seed, name)
        result["privacy"][name] = privacy_report(task, prep, logs[name], mu)
    mu4 = L.calibrate_skellam_mu(CONFIG["calibration_epsilon_for_nonprivate_models"], CONFIG["training"]["delta"])
    result["risk_control"]["fedavg"] = policy_block(task, prep, models["fedavg"], mu4, methods, seed, "fedavg")
    if task.name == "gas":
        result["recalibration"] = gas_recalibration(task, prep, models, eps_list, seed)
    if task.name == "hai":
        result["hai_events"] = {k: hai_events(task, prep, models[k], result["risk_control"][k])
                                for k in ("fedavg", f"dp eps {CONFIG['headline_epsilon']:g}")}
    result["membership_inference"] = mia(task, prep, models, seed)
    write(result, RESULTS / "Main" / f"{dataset.title()} {design.title()}", f"Seed {seed}.json")
    return result


def run_sensitivity(dataset, design, seed, variant):
    task = L.load_task(dataset)
    hp = tuned().get(dataset, {})
    eps = CONFIG["headline_epsilon"]
    clients, alpha, overrides, include = CONFIG["clients"], CONFIG["dirichlet_alpha"], {}, ["fedavg", "dp"]
    edges, poison_levels, corruption = None, None, None
    if variant.startswith("alpha"):
        alpha = float(variant.split()[1])
    elif variant.startswith("clients"):
        clients = int(variant.split()[1])
    elif variant.startswith("participation"):
        overrides["participation"] = float(variant.split()[1])
    elif variant == "label noise":
        overrides.update({"label_noise_client": 0, "label_noise_rate": 0.3})
    elif variant == "poison":
        overrides.update({"malicious_client": 0})
        include = ["fedavg", "trimmed", "median", "dp"]
    elif variant.startswith("bins"):
        edges = L.binary_edges(int(variant.split()[1]))
    elif variant == "histogram poison":
        poison_levels = [0.25, 0.5, 1.0, 2.0]
    elif variant == "corruption":
        corruption = [("gaussian", 0.5), ("gaussian", 1.0), ("missing", 0.2), ("missing", 0.4)]
    prep = L.prepare(task, seed, design, clients=clients, alpha=alpha)
    result = header(task, prep, seed, "sensitivity", design)
    result["variant"] = variant
    models, logs, _ = train_models(task, prep, seed, hp, [eps], include=include + ["reference"],
                                   overrides=overrides)
    result["training_logs"] = logs
    result["metrics"] = evaluate(task, prep, models)
    mu = L.calibrate_skellam_mu(float(eps), CONFIG["training"]["delta"])
    methods = ["nonprivate_ltt", "proposed"]
    result["risk_control"] = {}
    for name in [n for n in models if n != "reference"]:
        tests = None
        if corruption:
            rng = np.random.default_rng(seed + 31)
            tests = {f"{h} {lvl:g}": (L.corrupt(prep.Xte, h, lvl, rng), prep.yte) for h, lvl in corruption}
        result["risk_control"][name] = policy_block(task, prep, models[name], mu, methods, seed, name,
                                                    edges=edges, test_sets=tests)
        if corruption:
            result["metrics"][name]["corrupted"] = {
                k: L.metrics_for(task.kind, predict(models[name], X, task.kind), y, prep)
                for k, (X, y) in tests.items()}
    if poison_levels and task.kind == "binary":
        name = f"dp eps {eps:g}"
        n1 = sum(int(c["ycal"].sum()) for c in prep.clients)
        B = len(L.BINARY_EDGES) - 1
        result["histogram_poison"] = {}
        for lvl in poison_levels:
            fake = np.zeros(B, dtype=np.int64)
            fake[-1] = int(round(lvl * n1))  # fabricated high-score faults inflate the denominator
            result["histogram_poison"][f"{lvl:g}"] = policy_block(task, prep, models[name], mu, ["proposed"],
                                                                  seed, f"poison-{lvl}", poison={"pos": fake})
    write(result, RESULTS / "Sensitivity" / f"{dataset.title()} {variant.title()}", f"Seed {seed}.json")
    return result


def run_reconstruction(dataset, seed):
    task = L.load_task(dataset)
    prep = L.prepare(task, seed, "simulated", clients=CONFIG["clients"], alpha=CONFIG["dirichlet_alpha"])
    hp = tuned().get(dataset, {})
    d = prep.clients[0]["Xtr"].shape[1]
    classes = len(task.class_names) if task.kind == "multiclass" else 1
    cfg = make_cfg(task, "fedavg", hp, rounds=3)
    params, _ = L.federated_train(prep.clients, cfg, d, classes, seed)
    rng = np.random.default_rng(seed + 5)
    X, y = pooled(prep, "tr")
    pick = rng.choice(len(y), 200, replace=False)
    out = {"no protection": [], "clipping only": []}
    for sigma in (0.5, 1.0, 2.0):
        out[f"clip and noise multiplier {sigma:g}"] = []
    for i in pick:
        out["no protection"].append(L.reconstruct_from_update(params, X[i], y[i], task.kind))
        out["clipping only"].append(L.reconstruct_from_update(params, X[i], y[i], task.kind, clip=1.0))
        for sigma in (0.5, 1.0, 2.0):
            out[f"clip and noise multiplier {sigma:g}"].append(
                L.reconstruct_from_update(params, X[i], y[i], task.kind, clip=1.0, noise_sigma=sigma, rng=rng))
    summary = {}
    for k, v in out.items():
        cos = [r["cosine"] for r in v if r.get("recovered")]
        rel = [r["relative_error"] for r in v if r.get("recovered")]
        summary[k] = {"records": len(v), "recovered": len(cos), "median_cosine": float(np.median(cos)),
                      "median_relative_error": float(np.median(rel)),
                      "share_cosine_above_0_99": float(np.mean(np.array(cos) > 0.99))}
    result = header(task, prep, seed, "reconstruction", "simulated")
    result["reconstruction"] = summary
    write(result, RESULTS / "Reconstruction", f"{dataset.title()} Seed {seed}.json")
    return result


def run_tuning(dataset, design):
    """Learning-rate selection on an internal split of the tuning seed's training rows only."""
    task = L.load_task(dataset)
    seed = CONFIG["tuning_seed"]
    prep = L.prepare(task, seed, design, clients=CONFIG["clients"], alpha=CONFIG["dirichlet_alpha"])
    rng = np.random.default_rng(seed)
    inner = []
    val_X, val_y = [], []
    for c in prep.clients:
        n = len(c["ytr"])
        v = rng.random(n) < 0.25
        inner.append({**c, "Xtr": c["Xtr"][~v], "ytr": c["ytr"][~v]})
        val_X.append(c["Xtr"][v])
        val_y.append(c["ytr"][v])
    vX, vy = np.concatenate(val_X), np.concatenate(val_y)
    inner_prep = L.Prepared(inner, vX, vy, None, {}, prep.target_scale, prep.target_mean,
                            prep.feature_names, prep.design, prep.scaler)
    d = vX.shape[1]
    classes = len(task.class_names) if task.kind == "multiclass" else 1
    grid = CONFIG["tuning"]["lr_grid"]
    out, record = {}, []
    public_w = L.PUBLIC_POSITIVE_WEIGHT.get(task.name, 1.0)
    for method in ["central", "fedavg", "fedprox", "scaffold", "dp"]:
        best = None
        if method == "fedprox":
            options = [{"mu": mu} for mu in CONFIG["tuning"]["prox_mu_grid"]]
        elif method == "dp":
            options = [{"batch": b, "momentum": m, "pos_weight": w}
                       for b in CONFIG["tuning"].get("dp_batch_grid_by_dataset", {}).get(
                           task.name, CONFIG["tuning"]["dp_batch_grid"])
                       for m in CONFIG["tuning"]["dp_momentum_grid"]
                       for w in sorted({1.0, public_w})]
        else:
            options = [{}]
        lrs = CONFIG["tuning"]["dp_lr_grid"] if method == "dp" else grid
        for lr in lrs:
            for opt in options:
                mu = opt.get("mu")
                hp = {method: {"lr": lr, **opt}, "fedprox": {"mu": mu if mu is not None else 0.01}}
                if method == "dp":
                    hp["dp"] = {"lr": lr, **opt}
                over = {"target_epsilon": float(CONFIG["headline_epsilon"])} if method == "dp" else {}
                cfg = make_cfg(task, method, hp, **over)
                try:
                    if method == "central":
                        Xp, yp = pooled(inner_prep, "tr")
                        params = L.train_central(Xp, yp, cfg, d, classes, seed)
                    else:
                        params, _ = L.federated_train(inner, cfg, d, classes, seed)
                    score = selection_metric(task.kind, L.scores(params, vX, task.kind), vy)
                except Exception as exc:  # recorded, not hidden
                    score = float("nan")
                    record.append({"method": method, "lr": lr, **opt, "error": repr(exc)})
                record.append({"method": method, "lr": lr, **opt, "validation": score})
                if np.isfinite(score) and (best is None or score > best[0]):
                    best = (score, lr, opt)
        out[method] = {"lr": best[1], "validation": best[0], **best[2]}
    out["local"] = dict(out["central"])
    allp = tuned()
    allp[dataset] = out
    TUNED_PATH.write_text(json.dumps(L.jsonable(allp), indent=1) + "\n")
    write({"dataset": dataset, "design": design, "seed": seed, "grid": record, "selected": out},
          RESULTS / "Tuning", f"{dataset.title()}.json")
    return out


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("stage", choices=["tune", "main", "sensitivity", "reconstruction"])
    cli.add_argument("--datasets", nargs="+", required=True)
    cli.add_argument("--seeds", nargs="+", type=int, default=[1])
    cli.add_argument("--design", default=None)
    cli.add_argument("--variants", nargs="+", default=[])
    cli.add_argument("--epsilons", nargs="+", type=float, default=None)
    args = cli.parse_args()
    eps_list = args.epsilons or CONFIG["epsilons"]
    failures = []
    for ds in args.datasets:
        designs = [args.design] if args.design else CONFIG["designs"][ds]
        for design in designs:
            if args.stage == "tune":
                if design != CONFIG["designs"][ds][0]:
                    continue
                try:
                    print(ds, json.dumps(L.jsonable(run_tuning(ds, design))), flush=True)
                except Exception:
                    failures.append({"dataset": ds, "stage": "tune", "error": traceback.format_exc()})
                continue
            for seed in args.seeds:
                jobs = args.variants if args.stage == "sensitivity" else [None]
                for variant in jobs:
                    t = time.perf_counter()
                    try:
                        if args.stage == "main":
                            run_main(ds, design, seed, eps_list)
                        elif args.stage == "sensitivity":
                            run_sensitivity(ds, design, seed, variant)
                        else:
                            run_reconstruction(ds, seed)
                        print(f"{args.stage} {ds} {design} seed {seed} {variant or ''} done in "
                              f"{time.perf_counter() - t:.1f}s", flush=True)
                    except Exception:
                        failures.append({"dataset": ds, "design": design, "seed": seed, "variant": variant,
                                         "stage": args.stage, "error": traceback.format_exc()})
                        print("FAILED", ds, design, seed, variant, flush=True)
                        print(failures[-1]["error"], flush=True)
            if args.stage == "reconstruction":
                break
    if failures:
        RESULTS.mkdir(parents=True, exist_ok=True)
        with (RESULTS / "Failure Log.jsonl").open("a") as f:
            for item in failures:
                f.write(json.dumps({**item, "logged_utc": datetime.now(timezone.utc).isoformat()}) + "\n")


if __name__ == "__main__":
    main()
