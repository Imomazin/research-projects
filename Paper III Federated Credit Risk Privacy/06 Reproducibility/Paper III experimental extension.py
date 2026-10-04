import argparse, math, os, json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, roc_curve
from multiprocessing import Pool

warnings.filterwarnings('ignore')

DATA_PATH = Path('/mnt/data/default of credit card clients.xlsx')
ARCHIVE_PATH = Path('/mnt/data/Paper III All Results Combined (2).csv')
LOT = 128
ROUNDS = 50
LOCAL_STEPS = 8
LR = 1.0
L2 = 1e-4
DELTA = 1e-5

raw = pd.read_excel(DATA_PATH, sheet_name='Data', header=1)
FEATURE_COLS = [c for c in raw.columns if c not in ['ID','default payment next month']]
X_ALL = raw[FEATURE_COLS].to_numpy(dtype=np.float64)
Y_ALL = raw['default payment next month'].to_numpy(dtype=np.int8)
LIMIT_IDX = FEATURE_COLS.index('LIMIT_BAL')
D = len(FEATURE_COLS)
ARCH = pd.read_csv(ARCHIVE_PATH)
MM = ARCH[ARCH['dataset'].eq('main matrix')].copy()
SEEDS = MM[(MM['condition']=='C1') & (MM['treatment']=='D0')]['seed'].astype(int).tolist()

D4_MAP = {}
for _, r in MM[MM['treatment'].eq('D4')][['condition','seed','sigma']].drop_duplicates().iterrows():
    a,b = str(r['sigma']).split('/')
    D4_MAP[(str(r['condition']), int(r['seed']))] = (float(a), float(b))


def base_split(seed):
    idx = np.arange(len(Y_ALL))
    tr, te = train_test_split(idx, test_size=0.2, stratify=Y_ALL, random_state=int(seed))
    mu = X_ALL[tr].mean(axis=0)
    sd = X_ALL[tr].std(axis=0, ddof=0)
    sd[sd == 0] = 1.0
    Xtr = (X_ALL[tr] - mu) / sd
    Xte = (X_ALL[te] - mu) / sd
    ytr = Y_ALL[tr].copy()
    yte = Y_ALL[te].copy()
    bins = pd.qcut(pd.Series(X_ALL[tr, LIMIT_IDX]), q=5, labels=False, duplicates='drop').to_numpy()
    clients=[]
    for c in range(5):
        m = bins == c
        clients.append({'X': Xtr[m].copy(),'y_clean': ytr[m].copy(),'y_obs': ytr[m].copy(),'ids': tr[m].copy()})
    return clients, Xte, yte, te


def severe_partition(clients, rng):
    cls = clients
    c = cls[0]
    pos = np.flatnonzero(c['y_clean'] == 1)
    neg = np.flatnonzero(c['y_clean'] == 0)
    keep_pos = rng.choice(pos, size=int(round(0.30 * len(pos))), replace=False)
    keep = np.sort(np.concatenate([neg, keep_pos]))
    cls[0] = {k:v[keep] for k,v in c.items()}
    c = cls[1]
    pos = np.flatnonzero(c['y_clean'] == 1)
    neg = np.flatnonzero(c['y_clean'] == 0)
    keep_neg = rng.choice(neg, size=int(round(0.50 * len(neg))), replace=False)
    keep = np.sort(np.concatenate([pos, keep_neg]))
    cls[1] = {k:v[keep] for k,v in c.items()}
    return cls


def symmetric_noise(clients, rng, rate=0.20):
    for c in clients:
        n = len(c['y_obs'])
        k = int(round(rate * n))
        ix = rng.choice(n, size=k, replace=False)
        c['y_obs'][ix] = 1 - c['y_obs'][ix]
    return clients


def asymmetric_noise(clients, rng, rate=0.20):
    for c in clients:
        ix0 = np.flatnonzero(c['y_obs'] == 0)
        k = int(round(rate * len(ix0)))
        ix = rng.choice(ix0, size=k, replace=False)
        c['y_obs'][ix] = 1
    return clients


def prepare_condition(seed, condition, rng):
    clients, Xte, yte, te = base_split(seed)
    part_k = 5
    if condition in ('C2','S1','S2','S3'):
        clients = severe_partition(clients, rng)
    if condition in ('C3','C5','S1','S3'):
        clients = symmetric_noise(clients, rng, 0.20)
    if condition == 'C6': clients = asymmetric_noise(clients, rng, 0.20)
    if condition == 'C4': part_k = 2
    elif condition == 'C5': part_k = 3
    elif condition == 'C6': part_k = 2
    elif condition == 'S2': part_k = 2
    elif condition == 'S3': part_k = 2
    return clients, Xte, yte, te, part_k


def grad_matrix(X, y, theta):
    p = expit(X @ theta[:-1] + theta[-1])
    e = p - y
    return np.concatenate([e[:,None] * X, e[:,None]], axis=1)


def calibration(y, p, bins=10):
    p2 = np.clip(p, 1e-12, 1-1e-12)
    z = np.log(p2 / (1-p2))
    beta = np.array([0.0, 1.0])
    Z = np.column_stack([np.ones(len(z)), z])
    for _ in range(50):
        q = expit(Z @ beta)
        g = Z.T @ (q - y)
        w = q * (1-q)
        H = (Z.T * w) @ Z
        try:
            step = np.linalg.solve(H + 1e-10*np.eye(2), g)
        except np.linalg.LinAlgError:
            break
        beta -= step
        if np.max(np.abs(step)) < 1e-10: break
    edges = np.linspace(0,1,bins+1)
    ids = np.digitize(p, edges[1:-1], right=True)
    ece = 0.0
    for b in range(bins):
        m = ids == b
        if np.any(m): ece += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(beta[1]), float(beta[0]), float(ece)


def ks_stat(y, p):
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def attack_auc(member_score, non_score):
    labels = np.concatenate([np.ones(len(member_score)), np.zeros(len(non_score))])
    scores = np.concatenate([member_score, non_score])
    a = roc_auc_score(labels, scores)
    return float(a), float(2*a - 1)


def binary_loss_score(p, y):
    p = np.clip(p, 1e-12, 1-1e-12)
    py = np.where(y == 1, p, 1-p)
    return np.log(py)


def confidence_score(p): return np.maximum(p, 1-p)

def entropy_score(p):
    p = np.clip(p, 1e-12, 1-1e-12)
    ent = -(p*np.log(p) + (1-p)*np.log(1-p))
    return -ent


def parse_d4_pair(base_condition, seed): return D4_MAP[(base_condition, int(seed))]


def run_one(args):
    seed, condition, treatment, clip_norm, trace = args
    seed = int(seed)
    rng = np.random.RandomState(seed)
    clients, Xte, yte, teidx, part_k = prepare_condition(seed, condition, rng)
    theta = np.zeros(D+1, dtype=np.float64)
    ever = np.zeros(5, dtype=bool)
    round_norms=[]
    d4_base = 'C2' if condition in ('S1','S2','S3') else condition
    d4_pair = parse_d4_pair(d4_base, seed) if treatment == 'D4' else None

    for r in range(ROUNDS):
        selected = np.arange(5) if part_k == 5 else np.sort(rng.choice(5, size=part_k, replace=False))
        ever[selected] = True
        local_thetas=[]; local_weights=[]; norm_sum=0.0; norm_n=0
        for ci in selected:
            c = clients[ci]
            Xc, yc = c['X'], c['y_obs']
            n = len(yc); q = min(1.0, LOT/n); th = theta.copy()
            for _ in range(LOCAL_STEPS):
                sel = np.flatnonzero(rng.random_sample(n) < q)
                if len(sel) == 0: continue
                G = grad_matrix(Xc[sel], yc[sel], th)
                norms = np.linalg.norm(G, axis=1)
                norm_sum += float(norms.sum()); norm_n += len(norms)
                if treatment != 'D0': G *= np.minimum(1.0, clip_norm/(norms + 1e-12))[:,None]
                gsum = G.sum(axis=0)
                if treatment in ('D1','D2','D3','D4'):
                    if treatment == 'D1': sigma = 0.8
                    elif treatment == 'D2': sigma = 1.5
                    elif treatment == 'D3': sigma = 2.5
                    else:
                        low, high = d4_pair
                        sigma = high if r < 20 else low
                    gsum += rng.normal(0.0, sigma*clip_norm, size=D+1)
                grad = gsum / LOT; grad[:-1] += L2 * th[:-1]; th -= LR * grad
            local_thetas.append(th); local_weights.append(n)
        theta = np.average(np.stack(local_thetas), axis=0, weights=np.asarray(local_weights))
        round_norms.append(norm_sum/norm_n if norm_n else np.nan)

    pte = expit(Xte @ theta[:-1] + theta[-1])
    auc = float(roc_auc_score(yte, pte)); brier = float(brier_score_loss(yte, pte)); ks = ks_stat(yte, pte)
    slope, intercept, ece = calibration(yte, pte)
    memX=[]; memObs=[]; memClean=[]
    for ci,c in enumerate(clients):
        if ever[ci]:
            memX.append(c['X']); memObs.append(c['y_obs']); memClean.append(c['y_clean'])
    memX=np.vstack(memX); memObs=np.concatenate(memObs); memClean=np.concatenate(memClean)
    m_ix = rng.choice(len(memX), size=4000, replace=False); n_ix = rng.choice(len(Xte), size=4000, replace=False)
    pm = expit(memX[m_ix] @ theta[:-1] + theta[-1]); pn = pte[n_ix]
    ymo = memObs[m_ix]; ymc = memClean[m_ix]; yn = yte[n_ix]
    auc_lo, adv_lo = attack_auc(binary_loss_score(pm,ymo), binary_loss_score(pn,yn))
    auc_lc, adv_lc = attack_auc(binary_loss_score(pm,ymc), binary_loss_score(pn,yn))
    auc_cf, adv_cf = attack_auc(confidence_score(pm), confidence_score(pn))
    auc_en, adv_en = attack_auc(entropy_score(pm), entropy_score(pn))
    min_client = min(len(c['y_obs']) for c in clients)
    out={'seed':seed,'condition':condition,'treatment':treatment,'clip_norm':float(clip_norm),'auc':auc,'ks':ks,'gini':2*auc-1,'brier':brier,'cal_slope':slope,'cal_intercept':intercept,'ece':ece,'min_client':int(min_client),'n_train':int(sum(len(c['y_obs']) for c in clients)),'q':LOT/min_client,'steps':400,'n_mem':4000,'n_non':4000,'adv_loss_observed':adv_lo,'aucatk_loss_observed':auc_lo,'adv_loss_clean':adv_lc,'aucatk_loss_clean':auc_lc,'adv_confidence':adv_cf,'aucatk_confidence':auc_cf,'adv_entropy':adv_en,'aucatk_entropy':auc_en,'grad_norm_early':float(round_norms[0]),'grad_norm_late':float(round_norms[-1]),'grad_norm_mean':float(np.nanmean(round_norms))}
    if trace: out['trace'] = json.dumps([None if not np.isfinite(v) else float(v) for v in round_norms])
    return out


def run_tasks(tasks, workers):
    with Pool(processes=workers) as pool: return list(pool.imap_unordered(run_one, tasks, chunksize=1))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['smoke','severe','clip','gradient'],required=True); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--out',required=True); args=ap.parse_args()
    if args.mode=='smoke':
        seeds=SEEDS[:5]; tasks=[(s,c,t,1.0,False) for s in seeds for c in ['S1','S2'] for t in ['D0','D0C','D2','D4']]
    elif args.mode=='severe': tasks=[(s,c,t,1.0,False) for s in SEEDS for c in ['S1','S2'] for t in ['D0','D0C','D1','D2','D3','D4']]
    elif args.mode=='clip':
        clips=[1.0,0.75,0.5,0.25]; tasks=[(s,c,t,cl,False) for s in SEEDS for c in ['C1','C2','C3','C4','C5','C6'] for cl in clips for t in ['D0C','D2']]
    else:
        cp=ARCH[ARCH['dataset'].eq('checkpoint attack')]; seeds=[]
        for s in cp['seed'].dropna().astype(int).tolist():
            if s not in seeds: seeds.append(s)
        seeds=seeds[:30]; tasks=[(s,'C1',t,1.0,True) for s in seeds for t in ['D0','D3','D4']]
    rows=run_tasks(tasks,args.workers); df=pd.DataFrame(rows).sort_values(['condition','treatment','clip_norm','seed']); df.to_csv(args.out,index=False)
    print(f'wrote {len(df)} rows to {args.out}')
    print(df.groupby(['condition','treatment','clip_norm']).agg(auc_mean=('auc','mean'),adv_mean=('adv_loss_observed','mean'),slope=('cal_slope','mean')).to_string())

if __name__=='__main__': main()
