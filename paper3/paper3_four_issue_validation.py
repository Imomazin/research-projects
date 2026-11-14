"""Supplementary design addressing four methodological concerns.
Public, fixed preprocessing and client partition, fixed Poisson sampling rate,
equal client weights, Gaussian clipped updates and a public calibration partition.
Privacy applies to records in the protected TRAINING partition only. The UCI
benchmark is public; the simulation designates a disjoint calibration subset as
public auxiliary data, so no privacy is claimed for calibration records.
"""
import argparse, hashlib, math
import numpy as np
import pandas as pd
from scipy.special import expit, logsumexp, gammaln
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, roc_curve
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

Q=0.02; SIGMA=1.5; CLIP=1.; LOT=128; ROUNDS=50; STEPS=8; LR=.3; L2=1e-4; DELTA=1e-5
EDGES=np.array([50000.,100000.,150000.,200000.])

def rdp_eps(q=Q,sigma=SIGMA,steps=ROUNDS*STEPS,delta=DELTA):
    # Exact integer-order RDP of Poisson subsampled Gaussian under add/remove adjacency.
    # Conservative standard RDP-to-(eps,delta) conversion; no claim of optimality.
    results=[]
    for a in range(2,33):
        k=np.arange(a+1)
        logs=gammaln(a+1)-gammaln(k+1)-gammaln(a-k+1)
        logs+=k*np.log(q)+(a-k)*np.log1p(-q)+k*(k-1)/(2*sigma*sigma)
        rdp=steps*logsumexp(logs)/(a-1)
        results.append((a,rdp+np.log(1/delta)/(a-1)))
    return min(results,key=lambda x:x[1])

def load(path):
    if path.endswith(('.xls','.xlsx')):
        df=pd.read_excel(path,sheet_name='Data',header=1)
    else:df=pd.read_csv(path)
    cols=[c for c in df if c not in ('ID','default payment next month')]
    assert len(df)==30000 and len(cols)==23 and int(df['default payment next month'].sum())==6636
    X=df[cols].to_numpy(float);y=df['default payment next month'].to_numpy(int)
    # All transforms below are fixed publicly, not fitted from protected records.
    scales=[]
    for c in cols:
        if c=='LIMIT_BAL': scales.append(100000.)
        elif c=='AGE':scales.append(100.)
        elif c in ('SEX','MARRIAGE','EDUCATION'):scales.append(5.)
        elif c.startswith('PAY_') and not c.startswith('PAY_AMT'):scales.append(10.)
        else:scales.append(100000.)
    X=X/np.asarray(scales)
    limit=df['LIMIT_BAL'].to_numpy(float)
    return X,y,limit

def partitions(X,y,limit,seed):
    ix=np.arange(len(y))
    target,aux=train_test_split(ix,test_size=.30,random_state=seed,stratify=y)
    public,test=train_test_split(aux,test_size=.5,random_state=seed+1,stratify=y[aux])
    # Public calibration/reference and test records are excluded from the private training population.
    return target,public,test

def clients(X,y,limit,ix):
    seg=np.searchsorted(EDGES,limit[ix],side='right')
    return [(X[ix[seg==j]],y[ix[seg==j]]) for j in range(5)]

def gradients(X,y,theta):
    e=expit(X@theta[:-1]+theta[-1])-y
    return np.c_[e[:,None]*X,e]

def train(cl,seed,mode):
    d=cl[0][0].shape[1];th=np.zeros(d+1)
    rng=np.random.RandomState(seed)
    for _ in range(ROUNDS):
        locals=[]
        for x,y in cl:
            t=th.copy();n=len(y)
            for __ in range(STEPS):
                sel=np.flatnonzero(rng.random_sample(n)<Q)
                if not len(sel):continue
                G=gradients(x[sel],y[sel],t)
                norms=np.linalg.norm(G,axis=1)
                Gc=G*np.minimum(1.,CLIP/(norms+1e-12))[:,None]
                if mode=='unclipped':g=G.sum(0)
                elif mode=='normmatched':
                    # Exactly match the clipped aggregate norm for the same minibatch;
                    # the remaining difference is gradient direction, not step magnitude.
                    gu=G.sum(0);gc=Gc.sum(0)
                    g=gu*(np.linalg.norm(gc)/(np.linalg.norm(gu)+1e-12))
                else:g=Gc.sum(0)
                if mode=='private':g+=rng.normal(0,SIGMA*CLIP,size=d+1)
                g=g/LOT;g[:-1]+=L2*t[:-1];t-=LR*g
            locals.append(t)
        th=np.mean(locals,axis=0) # public fixed equal aggregation weights
    return th

def score(X,y,theta):
    p=np.clip(expit(X@theta[:-1]+theta[-1]),1e-10,1-1e-10)
    return np.log(np.where(y==1,p,1-p))

def attack(a,b):
    yy=np.r_[np.ones(len(a)),np.zeros(len(b))]
    ss=np.r_[a,b];auc=roc_auc_score(yy,ss)
    fpr,tpr,_=roc_curve(yy,ss)
    # conservative attainable operating point, no linear interpolation
    t=float(np.max(tpr[fpr<=.01]))
    return 2*auc-1,t

def metrics(y,p):
    p=np.clip(p,1e-9,1-1e-9)
    ece=0.
    for lo,hi in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:]):
        m=(p>=lo)&(p<hi if hi<1 else p<=hi)
        if m.any():ece+=m.mean()*abs(y[m].mean()-p[m].mean())
    return roc_auc_score(y,p),brier_score_loss(y,p),ece

def experiment(X,y,limit,seed):
    target,public,test=partitions(X,y,limit,seed)
    cl=clients(X,y,limit,target)
    # paired random streams for controls; private stream has added Gaussian draws.
    models={k:train(cl,seed+101,k) for k in ('unclipped','clipped','normmatched','private')}
    rows=[]
    for name,th in models.items():
        p=expit(X[test]@th[:-1]+th[-1]);auc,brier,ece=metrics(y[test],p)
        rows.append(dict(seed=seed,analysis='controls',method=name,auc=auc,brier=brier,ece=ece,advantage=np.nan,tpr_at_1pct=np.nan))
    # Shadow reference has same 5-client FL architecture but a smaller disjoint training set.
    shadow=train(clients(X,y,limit,public),seed+301,'clipped')
    rng=np.random.RandomState(seed+401)
    segm=np.searchsorted(EDGES,limit[target],side='right')
    segn=np.searchsorted(EDGES,limit[test],side='right')
    mm=[];nn=[]
    for j in range(5):
        for cls in (0,1):
            m=target[(segm==j)&(y[target]==cls)]
            n=test[(segn==j)&(y[test]==cls)]
            k=min(len(m),len(n))
            if k:
                mm.extend(rng.choice(m,k,replace=False));nn.extend(rng.choice(n,k,replace=False))
    mm=np.array(mm,dtype=int);nn=np.array(nn,dtype=int)
    for name in ('clipped','private'):
        t=models[name]
        direct=attack(score(X[mm],y[mm],t),score(X[nn],y[nn],t))
        gap=attack(score(X[mm],y[mm],t)-score(X[mm],y[mm],shadow),score(X[nn],y[nn],t)-score(X[nn],y[nn],shadow))
        for method,(adv,tpr) in [('matched_loss',direct),('matched_shadow_gap',gap)]:
            rows.append(dict(seed=seed,analysis='membership',method=name+'_'+method,auc=np.nan,brier=np.nan,ece=np.nan,advantage=adv,tpr_at_1pct=tpr))
    # Public auxiliary calibration: postprocessing of DP model + publicly designated labels.
    theta=models['private'];pc=expit(X[public]@theta[:-1]+theta[-1]);pt=expit(X[test]@theta[:-1]+theta[-1])
    iso=IsotonicRegression(out_of_bounds='clip').fit(pc,y[public])
    logits=lambda p:np.log(np.clip(p,1e-9,1-1e-9)/(1-np.clip(p,1e-9,1-1e-9)))
    pl=LogisticRegression(C=1e6,max_iter=1000).fit(logits(pc).reshape(-1,1),y[public])
    for method,p in [('raw',pt),('isotonic_public',iso.predict(pt)),('platt_public',pl.predict_proba(logits(pt).reshape(-1,1))[:,1])]:
        auc,brier,ece=metrics(y[test],p)
        rows.append(dict(seed=seed,analysis='calibration',method=method,auc=auc,brier=brier,ece=ece,advantage=np.nan,tpr_at_1pct=np.nan))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--seed-start',type=int,default=17286);ap.add_argument('--seeds',type=int,default=10)
    a=ap.parse_args();X,y,limit=load(a.data)
    order,eps=rdp_eps()
    print(f'Conditional protected-training mechanism: q={Q}, sigma={SIGMA}, steps={ROUNDS*STEPS}, delta={DELTA}, integer-RDP epsilon<={eps:.6f} (alpha={order})',flush=True)
    rows=[]
    for s in range(a.seed_start,a.seed_start+a.seeds):
        rows.extend(experiment(X,y,limit,s));pd.DataFrame(rows).to_csv(a.out,index=False)
        print('finished',s,flush=True)
    print('rows',len(rows),flush=True)
if __name__=='__main__':main()
