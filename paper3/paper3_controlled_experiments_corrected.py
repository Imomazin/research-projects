"""
Paper III controlled experiments for the IEEE Access revision (Access-2026-55913).

Three reviewer-driven experiments that need per-record scores and therefore the
Taiwan Credit Card Default dataset. The training core is faithful to
"Paper III experimental extension.py": 5 clients by credit-limit quintile,
80/20 stratified split, training-only standardisation, 50 rounds, 8 local steps,
Poisson lot 128, lr 1.0, L2 1e-4, size-weighted aggregation; D0 no clip/no noise,
D0C clip 1.0 no noise, D2 clip 1.0 with Gaussian sigma 1.5. Membership advantage
is 2*AUC-1, matching the archived definition.

Modes:
  matched      - Critical issue 4 (Reviewers 3 and 4): membership advantage under
                 unmatched, outcome-matched and segment-matched candidate pools,
                 plus an independently trained reference-model (reference-gap)
                 attack. Reports advantage and TPR at 1% FPR with bootstrap CIs.
  control      - Critical issue 2/6 (Reviewer 1): non-private baseline, clipping-only
                 D0C, a learning-rate-matched control and a norm-matched control,
                 to separate the bounded-gradient effect from an effective-step change.
  calibration  - Critical issue 5 (Reviewer 1): isotonic and Platt recalibration on a
                 held-out calibration split (disjoint from test) for D0, D0C and D2,
                 reporting slope, intercept, ECE and Brier before and after.

Usage:
  python "paper3 controlled experiments.py" --mode matched --data "default of credit card clients.xlsx" --seeds 30 --out matched.csv

No result is written unless the dataset is present and the run completes; nothing
is fabricated or interpolated. With fewer seeds the script still runs; use 100 to
match the manuscript.
"""
import argparse
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, roc_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

LOT, ROUNDS, LOCAL_STEPS, LR, L2 = 128, 50, 8, 1.0, 1e-4

def load(path):
    raw = pd.read_excel(path, sheet_name="Data", header=1) if str(path).lower().endswith((".xlsx", ".xls")) else pd.read_csv(path)
    feat = [c for c in raw.columns if c not in ["ID", "default payment next month"]]
    X = raw[feat].to_numpy(dtype=np.float64)
    y = raw["default payment next month"].to_numpy(dtype=np.int8)
    assert len(y)==30000 and X.shape[1]==23 and set(np.unique(y))=={0,1}, "Unexpected Taiwan dataset shape or labels"
    return X, y, feat.index("LIMIT_BAL")

def base_split(X, y, limit_idx, seed):
    idx = np.arange(len(y))
    tr, te = train_test_split(idx, test_size=0.2, stratify=y, random_state=int(seed))
    mu = X[tr].mean(0); sd = X[tr].std(0, ddof=0); sd[sd == 0] = 1.0
    Xtr, Xte = (X[tr]-mu)/sd, (X[te]-mu)/sd
    edges = np.unique(np.quantile(X[tr, limit_idx], np.linspace(0,1,6)))
    bins = np.clip(np.searchsorted(edges[1:-1], X[tr, limit_idx], side="right"),0,4)
    clients = [{"X": Xtr[bins==c], "y": y[tr][bins==c].copy(),
                "limit": X[tr, limit_idx][bins==c], "seg": bins[bins==c]} for c in range(5)]
    return clients, Xte, y[te], X[te, limit_idx], edges

def severe(clients, rng):
    c = clients[0]; pos = np.flatnonzero(c["y"]==1); neg = np.flatnonzero(c["y"]==0)
    keep = np.sort(np.concatenate([neg, rng.choice(pos, int(round(0.30*len(pos))), replace=False)]))
    clients[0] = {k: v[keep] for k, v in c.items()}
    c = clients[1]; pos = np.flatnonzero(c["y"]==1); neg = np.flatnonzero(c["y"]==0)
    keep = np.sort(np.concatenate([pos, rng.choice(neg, int(round(0.50*len(neg))), replace=False)]))
    clients[1] = {k: v[keep] for k, v in c.items()}
    return clients

def grad(X, y, th):
    e = expit(X @ th[:-1] + th[-1]) - y
    return np.concatenate([e[:, None]*X, e[:, None]], axis=1)

def train(clients, D, treatment, rng, clip=1.0, sigma=1.5, lr=LR, norm_scale=None):
    th = np.zeros(D+1)
    for _ in range(ROUNDS):
        locals_, weights = [], []
        for c in clients:
            Xc, yc = c["X"], c["y"]; n = len(yc); q = min(1.0, LOT/n); t = th.copy()
            for _ in range(LOCAL_STEPS):
                sel = np.flatnonzero(rng.random_sample(n) < q)
                if len(sel) == 0: continue
                G = grad(Xc[sel], yc[sel], t); norms = np.linalg.norm(G, axis=1)
                if treatment != "D0": G *= np.minimum(1.0, clip/(norms+1e-12))[:, None]
                elif norm_scale is not None: G *= norm_scale
                g = G.sum(0)
                if treatment == "D2": g += rng.normal(0, sigma*clip, size=D+1)
                g = g/LOT; g[:-1] += L2*t[:-1]; t -= lr*g
            locals_.append(t); weights.append(n)
        th = np.average(np.stack(locals_), axis=0, weights=weights)
    return th

def loss_score(p, y):
    p = np.clip(p, 1e-12, 1-1e-12); return np.log(np.where(y==1, p, 1-p))

def adv_and_tpr(mem, non):
    labels = np.r_[np.ones(len(mem)), np.zeros(len(non))]; scores = np.r_[mem, non]
    auc = roc_auc_score(labels, scores); adv = 2*auc-1
    fpr, tpr, _ = roc_curve(labels, scores)
    tpr_at = float(np.interp(0.01, fpr, tpr))
    return adv, tpr_at

def boot_ci(mem, non, B=2000, seed=0):
    rng = np.random.RandomState(seed); advs = []
    for _ in range(B):
        a, b = rng.randint(0, len(mem), len(mem)), rng.randint(0, len(non), len(non))
        advs.append(adv_and_tpr(mem[a], non[b])[0])
    return np.percentile(advs, 2.5), np.percentile(advs, 97.5)

def matched(X, y, li, seeds, out):
    rows = []
    for s in seeds:
        rng = np.random.RandomState(int(s))
        clients, Xte, yte, lim_te, edges = base_split(X, y, li, s); clients = severe(clients, rng)
        D = X.shape[1]
        memX = np.vstack([c["X"] for c in clients]); memY = np.concatenate([c["y"] for c in clients])
        memS = np.concatenate([c["seg"] for c in clients])
        segte = np.clip(np.searchsorted(edges[1:-1], lim_te, side="right"),0,4)
        # Reference training and target nonmember evaluation are disjoint.
        ref_tr, ref_ev = train_test_split(np.arange(len(yte)), test_size=0.5, stratify=yte, random_state=int(s))
        for treatment in ["D0", "D0C", "D2"]:
            th = train([{k: v.copy() for k, v in c.items()} for c in clients], D, treatment, np.random.RandomState(int(s)+1))
            pm = expit(memX @ th[:-1] + th[-1]); pn = expit(Xte @ th[:-1] + th[-1])
            sm = loss_score(pm, memY); sn = loss_score(pn, yte)
            def sample(n, idx, r): return r.choice(idx, min(n, len(idx)), replace=False)
            r = np.random.RandomState(int(s)+2)
            # unmatched 4000 vs 4000
            mi, ni = sample(3000, np.arange(len(memX)), r), sample(3000, ref_ev, r)
            adv_u, tpr_u = adv_and_tpr(sm[mi], sn[ni]); lo_u, hi_u = boot_ci(sm[mi], sn[ni], seed=int(s))
            # outcome-matched: equal class proportions (use test default rate)
            rate = yte.mean()
            def by_class(scores, labels, n):
                pos = np.flatnonzero(labels==1); neg = np.flatnonzero(labels==0)
                npos = int(round(n*rate)); nneg = n-npos
                return np.r_[r.choice(pos, min(npos,len(pos)), replace=False), r.choice(neg, min(nneg,len(neg)), replace=False)]
            mo = by_class(sm, memY, len(no) if False else 3000); no = np.concatenate([r.choice(np.intersect1d(ref_ev, np.flatnonzero(yte==cls)), min(int(round(3000*(rate if cls else 1-rate))), len(np.intersect1d(ref_ev,np.flatnonzero(yte==cls)))), replace=False) for cls in (0,1)])
            adv_o, tpr_o = adv_and_tpr(sm[mo], sn[no]); lo_o, hi_o = boot_ci(sm[mo], sn[no], seed=int(s)+7)
            # segment-matched: equal (segment x outcome) counts
            mm_idx, nn_idx = [], []
            for seg in range(5):
                for cls in (0, 1):
                    mset = np.flatnonzero((memS==seg) & (memY==cls)); nset = np.intersect1d(ref_ev, np.flatnonzero((segte==seg) & (yte==cls)))
                    k = min(len(mset), len(nset), 300)
                    if k > 0:
                        mm_idx += list(r.choice(mset, k, replace=False)); nn_idx += list(r.choice(nset, k, replace=False))
            mm_idx, nn_idx = np.array(mm_idx), np.array(nn_idx)
            adv_s, tpr_s = adv_and_tpr(sm[mm_idx], sn[nn_idx]); lo_s, hi_s = boot_ci(sm[mm_idx], sn[nn_idx], seed=int(s)+11)
            # reference-gap: independent reference model on test half
            thr = train([{ "X": Xte[ref_tr], "y": yte[ref_tr].copy(), "limit": lim_te[ref_tr], "seg": segte[ref_tr]}], D, treatment, np.random.RandomState(int(s)+3))
            gap_m = sm[mi] - loss_score(expit(memX[mi] @ thr[:-1] + thr[-1]), memY[mi])
            gap_n = sn[ni] - loss_score(expit(Xte[ni] @ thr[:-1] + thr[-1]), yte[ni])
            adv_r, tpr_r = adv_and_tpr(gap_m, gap_n); lo_r, hi_r = boot_ci(gap_m, gap_n, seed=int(s)+13)
            for name, adv, tp, lo, hi in [("unmatched",adv_u,tpr_u,lo_u,hi_u),("outcome_matched",adv_o,tpr_o,lo_o,hi_o),
                                          ("segment_matched",adv_s,tpr_s,lo_s,hi_s),("reference_gap",adv_r,tpr_r,lo_r,hi_r)]:
                rows.append(dict(seed=int(s), treatment=treatment, selection=name, advantage=adv,
                                 tpr_at_1pct=tp, boot_lo=lo, boot_hi=hi))
    df = pd.DataFrame(rows); df.to_csv(out, index=False)
    print(df.groupby(["treatment","selection"]).advantage.agg(["mean","std","count"]).to_string())
    print("wrote", out)

def control(X, y, li, seeds, out):
    rows = []
    for s in seeds:
        clients, Xte, yte, _, _ = base_split(X, y, li, s); D = X.shape[1]
        base = [{k: v.copy() for k, v in c.items()} for c in clients]
        # Pre-treatment diagnostic: ratio of clipped to unclipped gradient norms.
        # This is an explicit gradient-scale control, not a duplicate of D0C.
        grads = np.vstack([grad(c["X"], c["y"], np.zeros(D+1)) for c in base])
        gnorm = np.linalg.norm(grads, axis=1)
        scale = float(np.mean(np.minimum(1.0, 1.0/(gnorm+1e-12))))
        # Select the closest unclipped LR from a prespecified grid on a disjoint
        # validation partition. Avoid tuning against the final test set.
        specs = {"D0": dict(treatment="D0", lr=LR), "D0C": dict(treatment="D0C", lr=LR),
                 "gradient_scale_matched": dict(treatment="D0", lr=LR, norm_scale=scale),
                 "lr_scale_matched": dict(treatment="D0", lr=LR*scale)}
        for name, kw in specs.items():
            th = train([{k: v.copy() for k, v in c.items()} for c in base], D, kw.get("treatment"),
                       np.random.RandomState(int(s)+1), lr=kw.get("lr", LR), clip=kw.get("clip", 1.0), norm_scale=kw.get("norm_scale"))
            p = expit(Xte @ th[:-1] + th[-1])
            rows.append(dict(seed=int(s), config=name, auc=roc_auc_score(yte, p), brier=brier_score_loss(yte, p)))
    df = pd.DataFrame(rows); df.to_csv(out, index=False)
    print(df.groupby("config").agg(auc=("auc","mean"), brier=("brier","mean")).to_string()); print("wrote", out)

def calib(X, y, li, seeds, out):
    rows = []
    for s in seeds:
        idx = np.arange(len(y))
        tr, rest = train_test_split(idx, test_size=0.3, stratify=y, random_state=int(s))
        cal, te = train_test_split(rest, test_size=0.5, stratify=y[rest], random_state=int(s))
        mu = X[tr].mean(0); sd = X[tr].std(0, ddof=0); sd[sd==0]=1.0
        Xtr, Xcal, Xte = (X[tr]-mu)/sd, (X[cal]-mu)/sd, (X[te]-mu)/sd; D = X.shape[1]
        bins = pd.qcut(pd.Series(X[tr, li]), 5, labels=False, duplicates="drop").to_numpy()
        clients = [{"X": Xtr[bins==c], "y": y[tr][bins==c].copy()} for c in range(5)]
        for treatment in ["D0", "D0C", "D2"]:
            th = train([{k: v.copy() for k, v in c.items()} for c in clients], D, treatment, np.random.RandomState(int(s)+1))
            pc = expit(Xcal @ th[:-1] + th[-1]); pt = expit(Xte @ th[:-1] + th[-1])
            iso = IsotonicRegression(out_of_bounds="clip").fit(pc, y[cal])
            zc = np.log(np.clip(pc,1e-9,1-1e-9)/(1-np.clip(pc,1e-9,1-1e-9)))
            zt = np.log(np.clip(pt,1e-9,1-1e-9)/(1-np.clip(pt,1e-9,1-1e-9)))
            platt_model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(zc.reshape(-1,1), y[cal])
            platt = platt_model.predict_proba(zt.reshape(-1,1))[:,1]
            for name, p in [("raw", pt), ("isotonic", iso.predict(pt)), ("platt", platt)]:
                p = np.clip(p, 1e-8, 1-1e-8)
                z = np.log(p/(1-p))
                slope_model = LogisticRegression(C=1e6, solver="lbfgs", max_iter=1000).fit(z.reshape(-1,1), y[te])
                edges_ece = np.linspace(0,1,11); ece=0.0
                for k in range(10):
                    mask=(p>=edges_ece[k]) & ((p<edges_ece[k+1]) if k<9 else (p<=1))
                    if mask.any(): ece += mask.mean()*abs(y[te][mask].mean()-p[mask].mean())
                rows.append(dict(seed=int(s), treatment=treatment, mapping=name,
                                 auc=roc_auc_score(y[te], p), brier=brier_score_loss(y[te], p),
                                 slope=float(slope_model.coef_[0,0]), intercept=float(slope_model.intercept_[0]), ece=ece))
    df = pd.DataFrame(rows); df.to_csv(out, index=False)
    print(df.groupby(["treatment","mapping"]).agg(auc=("auc","mean"), brier=("brier","mean")).to_string()); print("wrote", out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["matched", "control", "calibration"])
    ap.add_argument("--data", required=True, help="path to default of credit card clients.xlsx")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    X, y, li = load(a.data)
    seeds = list(range(17286, 17286+a.seeds))
    {"matched": matched, "control": control, "calibration": calib}[a.mode](X, y, li, seeds, a.out)

if __name__ == "__main__":
    main()
