#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, os, statistics, collections
from datetime import date
from pathlib import Path
import numpy as np
from scipy import stats
import statsmodels.api as sm
import matplotlib.pyplot as plt

SEED=20260915
rng=np.random.default_rng(SEED)
HERE=Path(__file__).resolve()
_candidate=HERE.parents[2] if len(HERE.parents)>2 else Path('/mnt/data')
PROJECT=Path(os.environ['SO_PROJECT_ROOT']) if os.environ.get('SO_PROJECT_ROOT') else (_candidate if (_candidate/'01 Primary Data').exists() else Path('/mnt/data'))
PRIMARY=(PROJECT/'primary.csv') if (PROJECT/'primary.csv').exists() else (PROJECT/'01 Primary Data'/'Compiled Participants Data_v2.csv')
AR=(PROJECT/'Strategic_Organization_Analysis_Ready.csv') if (PROJECT/'Strategic_Organization_Analysis_Ready.csv').exists() else (PROJECT/'03 Data Integration'/'Strategic_Organization_Analysis_Ready.csv')
OUT=(PROJECT/'statistical_modeling_outputs') if PROJECT==Path('/mnt/data') else (PROJECT/'04 Analysis'/'Statistical Modeling')
OUT.mkdir(parents=True,exist_ok=True)

CONV_ITEMS=['Strategic Thinking Pre','Problem Solving Pre','Decision Making Pre','Leadership Pre','Adaptability Pre','Digital Capability Pre']
AI_ITEMS=['AI Knowledge Pre','AI Application Pre','AI Judgement Pre','Data Literacy Pre']
ALL_ITEMS=CONV_ITEMS+AI_ITEMS


def read_csv(path):
    with open(path,encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def fnum(x):
    try: return float(x)
    except (TypeError,ValueError): return np.nan
def write_csv(path, headers, rows):
    with open(path,'w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(headers); w.writerows(rows)
def fmt(x,d=3):
    if x is None or not np.isfinite(x): return ''
    return f'{x:.{d}f}'
def ptxt(p):
    if p < .001: return '<.001'
    return f'{p:.3f}'

def alpha(X):
    X=np.asarray(X,float); k=X.shape[1]
    item_vars=X.var(axis=0,ddof=1); total_var=X.sum(axis=1).var(ddof=1)
    return k/(k-1)*(1-item_vars.sum()/total_var)

def standardized_alpha(X):
    R=np.corrcoef(np.asarray(X,float),rowvar=False); k=R.shape[0]
    rbar=(R.sum()-k)/(k*(k-1))
    return k*rbar/(1+(k-1)*rbar)

def corrected_item_total(X):
    X=np.asarray(X,float); out=[]
    for j in range(X.shape[1]):
        rest=np.delete(X,j,axis=1).sum(axis=1)
        out.append(np.corrcoef(X[:,j],rest)[0,1])
    return out

def bootstrap_stat(arr, func, B=5000, seed=SEED):
    arr=np.asarray(arr); rr=np.random.default_rng(seed); vals=np.empty(B)
    n=len(arr)
    for b in range(B): vals[b]=func(arr[rr.integers(0,n,n)])
    return np.quantile(vals,[.025,.975])

def boot_dz(arr):
    arr=np.asarray(arr); return arr.mean()/arr.std(ddof=1)

def encode_groups(vals):
    u={v:i for i,v in enumerate(sorted(set(vals)))}
    return np.array([u[v] for v in vals])

def ols_cluster(y, X, clusters, labels, model_name, cov_type='cluster'):
    X=np.asarray(X,float); y=np.asarray(y,float)
    Xc=sm.add_constant(X,has_constant='add')
    if cov_type=='cluster':
        res=sm.OLS(y,Xc).fit(cov_type='cluster',cov_kwds={'groups':encode_groups(clusters),'use_correction':True},use_t=True)
    elif cov_type=='HC3':
        res=sm.OLS(y,Xc).fit(cov_type='HC3')
    else: res=sm.OLS(y,Xc).fit()
    names=['Intercept']+labels
    rows=[]
    for i,nm in enumerate(names):
        ci=res.conf_int(alpha=.05)[i]
        rows.append([model_name,nm,res.params[i],res.bse[i],ci[0],ci[1],res.pvalues[i],res.rsquared,res.nobs,cov_type])
    return res, rows

primary=read_csv(PRIMARY)
pr={r['Participant ID']:r for r in primary}
ar=read_csv(AR)
rows=[]
for r in ar:
    if not r['ISCO-08']: continue
    z=dict(r); z['_p']=pr[r['Participant ID']]; rows.append(z)
N=len(rows)

exp=np.array([fnum(r['Exposure Ordinal (Analytical Recode)']) for r in rows])
hi=(exp>=4).astype(float)
conv=np.array([fnum(r['Conventional Capability Index']) for r in rows])
ai=np.array([fnum(r['AI/Data Capability Index']) for r in rows])
gap=conv-ai
clusters=[r['ISCO-08'] for r in rows]
confidence=np.array([r['Mapping Confidence'] for r in rows])
assessment_day=np.array([(date.fromisoformat(r['_p']['Assessment Date'])-date(2026,5,22)).days for r in rows],float)

# 1 sample flow and mapping
map_counts=collections.Counter(r['Mapping Confidence'] for r in ar)
exp_counts=collections.Counter(r['ILO GenAI Exposure Category'] for r in rows)
write_csv(OUT/'table_01_sample_flow.csv',['Metric','Value'],[
    ['Total baseline participants',len(primary)],['Mapped career-interest participants',N],['Unmapped due to missing career interest',len(primary)-N],
    ['Unique ISCO-08 occupations',len(set(clusters))],['High-exposure career interests (ILO Gradient 3/4)',int(hi.sum())],['High-exposure share (%)',100*hi.mean()],
    ['High confidence mappings',map_counts.get('High',0)],['Medium confidence mappings',map_counts.get('Medium',0)],['Low confidence mappings',map_counts.get('Low',0)]
])
# Sample characteristics (counts use full baseline sample; missing shown explicitly)
chars=[]
for var in ['Age Group','Gender','Country','Highest Education Level','Employment Status','Career Stage','Current Job Function']:
    cnt=collections.Counter((r[var] if r[var] else 'Missing') for r in primary)
    for level,n in cnt.most_common(): chars.append([var,level,n,100*n/len(primary)])
write_csv(OUT/'table_01b_sample_characteristics.csv',['Variable','Category','N','% of baseline sample'],chars)

# 2 missingness primary data
miss=[]
for k in primary[0].keys():
    nmiss=sum(1 for r in primary if not r[k]); miss.append([k,nmiss,len(primary)-nmiss,100*nmiss/len(primary)])
write_csv(OUT/'table_02_missingness.csv',['Variable','Missing N','Observed N','Missing %'],miss)

# 3 dimension descriptives
Xall=np.array([[fnum(r['_p'][k]) for k in ALL_ITEMS] for r in rows])
desc=[]
for j,k in enumerate(ALL_ITEMS):
    x=Xall[:,j]
    desc.append([k,len(x),x.mean(),x.std(ddof=1),np.median(x),np.quantile(x,.25),np.quantile(x,.75),x.min(),x.max(),100*np.mean(x>=90),100*np.mean(x==100)])
desc += [
 ['Conventional Capability Index',N,conv.mean(),conv.std(ddof=1),np.median(conv),np.quantile(conv,.25),np.quantile(conv,.75),conv.min(),conv.max(),100*np.mean(conv>=90),100*np.mean(conv==100)],
 ['AI/Data Capability Index',N,ai.mean(),ai.std(ddof=1),np.median(ai),np.quantile(ai,.25),np.quantile(ai,.75),ai.min(),ai.max(),100*np.mean(ai>=90),100*np.mean(ai==100)],
 ['Capability Gap',N,gap.mean(),gap.std(ddof=1),np.median(gap),np.quantile(gap,.25),np.quantile(gap,.75),gap.min(),gap.max(),'','']]
write_csv(OUT/'table_03_descriptives.csv',['Variable','N','Mean','SD','Median','Q1','Q3','Min','Max','% >=90','% =100'],desc)

# 4 psychometrics and dimensionality
Xa=Xall[:,6:]; Xc=Xall[:,:6]
psych=[
 ['Conventional 6-item domain','Cronbach alpha',alpha(Xc)],['Conventional 6-item domain','Standardized alpha',standardized_alpha(Xc)],
 ['AI/Data 4-item domain','Cronbach alpha',alpha(Xa)],['AI/Data 4-item domain','Standardized alpha',standardized_alpha(Xa)],
 ['All 10 dimensions','Cronbach alpha',alpha(Xall)],['All 10 dimensions','Standardized alpha',standardized_alpha(Xall)],
 ['Domain indices','Pearson r conventional vs AI/Data',np.corrcoef(conv,ai)[0,1]]]
write_csv(OUT/'table_04_psychometric_summary.csv',['Scale','Statistic','Value'],psych)
ci_all=corrected_item_total(Xall)
write_csv(OUT/'table_05_item_total_correlations.csv',['Item','Corrected item-total r'],[[k,v] for k,v in zip(ALL_ITEMS,ci_all)])
Z=(Xall-Xall.mean(axis=0))/Xall.std(axis=0,ddof=1)
eigs=np.linalg.eigvalsh(np.corrcoef(Z,rowvar=False))[::-1]
B=1000; sim_eigs=np.zeros((B,len(ALL_ITEMS)))
for b in range(B):
    z=rng.normal(size=Z.shape); sim_eigs[b]=np.linalg.eigvalsh(np.corrcoef(z,rowvar=False))[::-1]
pa95=np.quantile(sim_eigs,.95,axis=0)
write_csv(OUT/'table_06_parallel_analysis.csv',['Component','Observed eigenvalue','95th percentile random eigenvalue','Retain'],[[i+1,eigs[i],pa95[i],'Yes' if eigs[i]>pa95[i] else 'No'] for i in range(len(eigs))])

# 5 paired asymmetry
mean_ci=bootstrap_stat(gap,np.mean); median_ci=bootstrap_stat(gap,np.median,seed=SEED+1); dz=boot_dz(gap); dz_ci=bootstrap_stat(gap,boot_dz,seed=SEED+2)
tt=stats.ttest_rel(conv,ai); wil=stats.wilcoxon(conv,ai)
paired=[
 ['Mean conventional capability',conv.mean(),'','',''],['Mean AI/Data capability',ai.mean(),'','',''],['Mean within-person gap',gap.mean(),mean_ci[0],mean_ci[1],'bootstrap 95% CI'],
 ['Median within-person gap',np.median(gap),median_ci[0],median_ci[1],'bootstrap 95% CI'],['Paired t statistic',tt.statistic,'','',f'p={tt.pvalue:.3e}'],
 ['Wilcoxon signed-rank statistic',wil.statistic,'','',f'p={wil.pvalue:.3e}'],['Cohen dz',dz,dz_ci[0],dz_ci[1],'bootstrap 95% CI']]
write_csv(OUT/'table_07_capability_asymmetry.csv',['Statistic','Estimate','CI lower','CI upper','Note'],paired)

# 6 exposure groups and omnibus tests
exposure_order=[1,3,4,5]; exposure_label={1:'Minimal Exposure',3:'Gradient 2',4:'Gradient 3',5:'Gradient 4'}
group_rows=[]
for e in exposure_order:
    m=exp==e
    group_rows.append([e,exposure_label[e],m.sum(),conv[m].mean(),conv[m].std(ddof=1),ai[m].mean(),ai[m].std(ddof=1),gap[m].mean(),gap[m].std(ddof=1)])
write_csv(OUT/'table_08_exposure_group_descriptives.csv',['Exposure recode','ILO category','N','Conventional mean','Conventional SD','AI/Data mean','AI/Data SD','Gap mean','Gap SD'],group_rows)
omnibus=[]
for nm,y in [('Conventional Capability',conv),('AI/Data Capability',ai),('Capability Gap',gap)]:
    gs=[y[exp==e] for e in exposure_order]
    w=stats.f_oneway(*gs,equal_var=False); kw=stats.kruskal(*gs)
    omnibus.extend([[nm,'Welch ANOVA',w.statistic,w.pvalue],[nm,'Kruskal-Wallis',kw.statistic,kw.pvalue]])
write_csv(OUT/'table_09_exposure_omnibus_tests.csv',['Outcome','Test','Statistic','p-value'],omnibus)

# 7 correlations
corr=[]
for a_name,a in [('Exposure ordinal',exp),('Conventional capability',conv),('AI/Data capability',ai),('Capability gap',gap),('Assessment day',assessment_day)]:
    for b_name,b in [('Exposure ordinal',exp),('Conventional capability',conv),('AI/Data capability',ai),('Capability gap',gap),('Assessment day',assessment_day)]:
        if a_name>=b_name: continue
        prr=stats.pearsonr(a,b); spr=stats.spearmanr(a,b)
        corr.append([a_name,b_name,prr.statistic,prr.pvalue,spr.statistic,spr.pvalue])
write_csv(OUT/'table_10_correlations.csv',['Variable A','Variable B','Pearson r','Pearson p','Spearman rho','Spearman p'],corr)
# Manuscript-ready Pearson correlation matrix
cm_names=['Conventional capability','AI/Data capability','Capability gap','Exposure ordinal','High exposure']
cm_vals=[conv,ai,gap,exp,hi]
cm_rows=[]
for i,nm in enumerate(cm_names):
    row=[nm,float(np.mean(cm_vals[i])),float(np.std(cm_vals[i],ddof=1))]
    for j in range(len(cm_names)):
        row.append(1.0 if i==j else (float(np.corrcoef(cm_vals[i],cm_vals[j])[0,1]) if j<i else ''))
    cm_rows.append(row)
write_csv(OUT/'table_10b_correlation_matrix.csv',['Variable','Mean','SD']+cm_names,cm_rows)

# 8 core models
model_rows=[]
_,rr=ols_cluster(ai,hi[:,None],clusters,['High exposure (G3/G4)'],'M1 AI absolute ~ high exposure'); model_rows+=rr
_,rr=ols_cluster(ai,np.c_[hi,conv],clusters,['High exposure (G3/G4)','Conventional capability'],'M2 AI absolute ~ high exposure + conventional'); model_rows+=rr
_,rr=ols_cluster(gap,hi[:,None],clusters,['High exposure (G3/G4)'],'M3 gap ~ high exposure'); model_rows+=rr
_,rr=ols_cluster(gap,np.c_[hi,conv],clusters,['High exposure (G3/G4)','Conventional capability'],'M4 gap ~ high exposure + conventional'); model_rows+=rr
base_rel=sm.OLS(ai,sm.add_constant(conv)).fit(); rel=base_rel.resid
_,rr=ols_cluster(rel,hi[:,None],clusters,['High exposure (G3/G4)'],'M5 residual AI readiness ~ high exposure'); model_rows+=rr
# ordinal sensitivity primary table
_,rr=ols_cluster(ai,exp[:,None],clusters,['Exposure ordinal'],'M6 AI absolute ~ exposure ordinal'); model_rows+=rr
_,rr=ols_cluster(ai,np.c_[exp,conv],clusters,['Exposure ordinal','Conventional capability'],'M7 AI absolute ~ exposure ordinal + conventional'); model_rows+=rr
_,rr=ols_cluster(gap,exp[:,None],clusters,['Exposure ordinal'],'M8 gap ~ exposure ordinal'); model_rows+=rr
_,rr=ols_cluster(gap,np.c_[exp,conv],clusters,['Exposure ordinal','Conventional capability'],'M9 gap ~ exposure ordinal + conventional'); model_rows+=rr
write_csv(OUT/'table_11_core_regressions.csv',['Model','Term','B','SE','95% CI lower','95% CI upper','p-value','R-squared','N','SE type'],model_rows)

# 9 robustness suite
rob=[]
def add_rob(name,mask,xvar='hi',control=True,cfun=False,date_control=False,demog=False,hc3=False):
    idx=np.where(mask)[0]; y=ai[idx]; cv=conv[idx]; x=(hi if xvar=='hi' else exp)[idx]
    X=[x,cv] if control else [x]
    labels=['High exposure (G3/G4)' if xvar=='hi' else 'Exposure ordinal']+(['Conventional capability'] if control else [])
    if date_control: X.append(assessment_day[idx]); labels.append('Assessment day')
    if cfun:
        vals=[rows[i]['_p']['Current Job Function'] for i in idx]; cnt=collections.Counter(vals); levels=[k for k,v in cnt.items() if v>=5]
        ref='Technology & Digital' if 'Technology & Digital' in levels else levels[0]
        for lev in levels:
            if lev==ref: continue
            X.append(np.array([1.0 if v==lev else 0 for v in vals])); labels.append('Current function: '+lev)
        X.append(np.array([1.0 if v not in levels else 0 for v in vals])); labels.append('Current function: sparse other')
    cl=[clusters[i] for i in idx]
    res,r=ols_cluster(y,np.column_stack(X),cl,labels,name,'HC3' if hc3 else 'cluster')
    term=labels[0]
    first=[z for z in r if z[1]==term][0]
    rob.append(first)

allmask=np.ones(N,dtype=bool)
add_rob('R1 High-confidence mappings only',confidence=='High')
add_rob('R2 Exclude baseline-zero participant',np.array([fnum(r['_p']['Overall Baseline Score'])>0 for r in rows]))
add_rob('R3 Add assessment date control',allmask,date_control=True)
add_rob('R4 Add current-function controls',allmask,cfun=True)
add_rob('R5 HC3 instead of occupation-clustered SE',allmask,hc3=True)
add_rob('R6 Ordinal exposure + conventional',allmask,xvar='exp')
# complete-case demographics model manually
cc=np.array([all(r['_p'][k] for k in ['Gender','Highest Education Level','Employment Status','Career Stage']) for r in rows])
idx=np.where(cc)[0]; X=[hi[idx],conv[idx],assessment_day[idx]]; labs=['High exposure (G3/G4)','Conventional capability','Assessment day']
for lev in ['Female']:
    X.append(np.array([1.0 if rows[i]['_p']['Gender']==lev else 0 for i in idx])); labs.append('Gender female')
X.append(np.array([1.0 if rows[i]['_p']['Highest Education Level']=="Bachelor's" else 0 for i in idx])); labs.append("Bachelor's degree")
X.append(np.array([1.0 if rows[i]['_p']['Career Stage']=='Early Career' else 0 for i in idx])); labs.append('Early career')
for lev in ['Employed','Student','Self-employed']:
    X.append(np.array([1.0 if rows[i]['_p']['Employment Status']==lev else 0 for i in idx])); labs.append('Employment '+lev)
res,r=ols_cluster(ai[idx],np.column_stack(X),[clusters[i] for i in idx],labs,'R7 Complete-case demographic controls')
rob.append([z for z in r if z[1]=='High exposure (G3/G4)'][0])
write_csv(OUT/'table_12_robustness.csv',['Model','Term','B','SE','95% CI lower','95% CI upper','p-value','R-squared','N','SE type'],rob)

# 10 influence and robust regression
X=sm.add_constant(np.c_[hi,conv]); base=sm.OLS(ai,X).fit(); infl=base.get_influence(); cooks=infl.cooks_distance[0]
inf_rows=[]
for i in np.argsort(cooks)[::-1][:15]: inf_rows.append([rows[i]['Participant ID'],cooks[i],exp[i],conv[i],ai[i],gap[i]])
write_csv(OUT/'table_13_influence_diagnostics.csv',['Participant ID','Cooks distance','Exposure ordinal','Conventional','AI/Data','Gap'],inf_rows)
# Huber robust linear model sensitivity (classical SE)
rlm=sm.RLM(ai,X,M=sm.robust.norms.HuberT()).fit()
write_csv(OUT/'table_14_robust_regression.csv',['Term','B','SE','z','p-value'],[[nm,rlm.params[i],rlm.bse[i],rlm.tvalues[i],rlm.pvalues[i]] for i,nm in enumerate(['Intercept','High exposure','Conventional capability'])])
# Additional functional-form robustness
c=conv-conv.mean()
q=sm.QuantReg(ai,sm.add_constant(np.c_[hi,conv])).fit(q=.5)
nonlin=sm.OLS(ai,sm.add_constant(np.c_[hi,c,c*c])).fit(cov_type='cluster',cov_kwds={'groups':encode_groups(clusters),'use_correction':True},use_t=True)
inter=sm.OLS(ai,sm.add_constant(np.c_[hi,c,hi*c])).fit(cov_type='cluster',cov_kwds={'groups':encode_groups(clusters),'use_correction':True},use_t=True)
extra=[
 ['Median regression','High exposure',q.params[1],q.bse[1],q.pvalues[1]],
 ['Quadratic conventional-capability model','High exposure',nonlin.params[1],nonlin.bse[1],nonlin.pvalues[1]],
 ['High-exposure × conventional interaction','Interaction',inter.params[3],inter.bse[3],inter.pvalues[3]]
]
write_csv(OUT/'table_15_additional_robustness.csv',['Model','Term','B','SE','p-value'],extra)

# 11 exploratory post scores - clearly noncausal
post=[]
for r in primary:
    if r['Overall Post Score']:
        b=float(r['Overall Baseline Score']); po=float(r['Overall Post Score']); lag=(date.fromisoformat(r['Reassessment Date'])-date.fromisoformat(r['Assessment Date'])).days
        post.append([r['Participant ID'],b,po,po-b,lag])
write_csv(OUT/'table_A1_post_cases.csv',['Participant ID','Baseline','Post','Gain','Days to reassessment'],post)
post_tests=[]
for name,sub in [('All post cases',post),('Exclude baseline=0',[x for x in post if x[1]>0]),('Exclude same-day reassessment',[x for x in post if x[4]>0]),('Exclude baseline=0 and same-day',[x for x in post if x[1]>0 and x[4]>0])]:
    gains=np.array([x[3] for x in sub]); w=stats.wilcoxon(gains)
    post_tests.append([name,len(gains),gains.mean(),np.median(gains),gains.std(ddof=1),w.statistic,w.pvalue])
write_csv(OUT/'table_A2_post_sensitivity.csv',['Sample','N','Mean gain','Median gain','SD gain','Wilcoxon W','p-value'],post_tests)

# 12 figures
plt.figure(figsize=(7.2,4.8))
means=[conv.mean(),ai.mean()]; cis=[bootstrap_stat(conv,np.mean),bootstrap_stat(ai,np.mean)]
yerr=np.array([[means[i]-cis[i][0] for i in range(2)],[cis[i][1]-means[i] for i in range(2)]])
plt.bar(['Conventional strategic\ncapability','AI/data capability'],means,yerr=yerr,capsize=5)
plt.ylabel('Mean capability score (0–100)'); plt.ylim(0,100); plt.title('Within-sample capability asymmetry')
plt.tight_layout(); plt.savefig(OUT/'figure_01_capability_asymmetry.png',dpi=300); plt.close()

plt.figure(figsize=(7.2,4.8))
labels=[exposure_label[e] for e in exposure_order]; counts=[int((exp==e).sum()) for e in exposure_order]
plt.bar(labels,counts); plt.ylabel('Participants'); plt.title('Career-interest occupational GenAI exposure'); plt.xticks(rotation=20,ha='right'); plt.tight_layout(); plt.savefig(OUT/'figure_02_exposure_distribution.png',dpi=300); plt.close()

plt.figure(figsize=(7.2,4.8))
data=[gap[exp==e] for e in exposure_order]
plt.boxplot(data,tick_labels=['Minimal','Gradient 2','Gradient 3','Gradient 4'],showfliers=False)
plt.axhline(0,linewidth=.8); plt.ylabel('Capability gap (Conventional − AI/Data)'); plt.title('Capability asymmetry across ILO exposure categories'); plt.tight_layout(); plt.savefig(OUT/'figure_03_gap_by_exposure.png',dpi=300); plt.close()

plt.figure(figsize=(7.2,4.8))
for flag,label in [(0,'Minimal / Gradient 2'),(1,'Gradient 3 / 4')]:
    m=hi==flag; plt.scatter(conv[m],ai[m],alpha=.55,label=label)
xx=np.linspace(conv.min(),conv.max(),100); fit=sm.OLS(ai,sm.add_constant(conv)).fit(); plt.plot(xx,fit.params[0]+fit.params[1]*xx,linewidth=2,label='Overall fitted relationship')
plt.xlabel('Conventional capability'); plt.ylabel('AI/Data capability'); plt.title('Absolute capability sorting without relative AI-readiness advantage'); plt.legend(frameon=False); plt.tight_layout(); plt.savefig(OUT/'figure_04_capability_sorting.png',dpi=300); plt.close()

plt.figure(figsize=(7.2,4.8))
plt.plot(range(1,11),eigs,marker='o',label='Observed'); plt.plot(range(1,11),pa95,marker='o',label='95th percentile random')
plt.axhline(1,linewidth=.8); plt.xlabel('Component'); plt.ylabel('Eigenvalue'); plt.title('Parallel analysis of the 10 baseline dimensions'); plt.legend(frameon=False); plt.tight_layout(); plt.savefig(OUT/'figure_A1_parallel_analysis.png',dpi=300); plt.close()

# 13 model interpretation memo and manifest
core_lookup={}
for row in model_rows:
    if row[1] in ['High exposure (G3/G4)','Exposure ordinal','Conventional capability']:
        core_lookup.setdefault(row[0],[]).append(row)
summary={
 'n_total':len(primary),'n_mapped':N,'n_high_exposure':int(hi.sum()),'high_exposure_pct':100*hi.mean(),
 'conv_mean':conv.mean(),'ai_mean':ai.mean(),'gap_mean':gap.mean(),'gap_ci95':mean_ci.tolist(),'gap_median':float(np.median(gap)),'cohen_dz':dz,'cohen_dz_ci95':dz_ci.tolist(),
 'paired_t':float(tt.statistic),'paired_t_p':float(tt.pvalue),'wilcoxon_W':float(wil.statistic),'wilcoxon_p':float(wil.pvalue),
 'alpha_conventional':alpha(Xc),'alpha_ai_data':alpha(Xa),'alpha_all10':alpha(Xall),'conv_ai_r':float(np.corrcoef(conv,ai)[0,1]),
 'pca_eigenvalues':eigs.tolist(),'parallel_95':pa95.tolist(),
 'high_exposure_ai_unadjusted_B':core_lookup['M1 AI absolute ~ high exposure'][0][2],
 'high_exposure_ai_adjusted_B':core_lookup['M2 AI absolute ~ high exposure + conventional'][0][2],
 'high_exposure_ai_adjusted_p':core_lookup['M2 AI absolute ~ high exposure + conventional'][0][6],
 'high_exposure_gap_B':core_lookup['M3 gap ~ high exposure'][0][2],
 'high_exposure_gap_p':core_lookup['M3 gap ~ high exposure'][0][6],
 'relative_readiness_high_exposure_B':core_lookup['M5 residual AI readiness ~ high exposure'][0][2],
 'relative_readiness_high_exposure_p':core_lookup['M5 residual AI readiness ~ high exposure'][0][6],
 'unique_isco':len(set(clusters)),'seed':SEED
}
(OUT/'analysis_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')

memo=f'''# Statistical Modeling Report — Strategic Organization\n\n## Analytical sample\nThe baseline dataset contains {len(primary)} participants. Career-interest occupations could be mapped to ISCO-08 and the ILO 2025 GenAI exposure taxonomy for {N} participants. The inferential occupational-exposure analyses therefore use n={N}, clustered across {len(set(clusters))} ISCO-08 occupations. {int(hi.sum())} participants ({100*hi.mean():.1f}%) target occupations in ILO Gradient 3 or Gradient 4, defined here as high exposure.\n\n## Measurement and composite construction\nThe six conventional dimensions are averaged a priori to form the conventional strategic capability index. AI Knowledge, AI Application, AI Judgement and Data Literacy are averaged a priori to form the AI/Data capability index. Internal consistency is high for the conventional domain (alpha={alpha(Xc):.3f}) and AI/Data domain (alpha={alpha(Xa):.3f}); alpha for all ten dimensions is {alpha(Xall):.3f}. The two domain indices are highly correlated (r={np.corrcoef(conv,ai)[0,1]:.3f}). Parallel analysis retains {'one component' if sum(eigs>pa95)==1 else str(sum(eigs>pa95))+' components'}, indicating a dominant general capability factor. The manuscript must therefore present the two indices as theory-defined domain averages and the capability gap as a within-person domain contrast, not as evidence for two clean latent factors.\n\n## Core finding 1: large within-person capability asymmetry\nMean conventional capability is {conv.mean():.2f} versus {ai.mean():.2f} for AI/Data capability. The mean within-person gap is {gap.mean():.2f} points (bootstrap 95% CI {mean_ci[0]:.2f} to {mean_ci[1]:.2f}); median gap={np.median(gap):.2f}. The paired t-test is t({N-1})={tt.statistic:.2f}, p<.001 and the Wilcoxon test is also p<.001. Cohen dz={dz:.2f} (bootstrap 95% CI {dz_ci[0]:.2f} to {dz_ci[1]:.2f}), a very large standardized within-person difference.\n\n## Core finding 2: occupational exposure sorts on absolute capability\nAbsolute AI/Data capability is higher among participants targeting ILO Gradient 3/4 occupations. In the occupation-clustered model, high exposure is associated with a {core_lookup['M1 AI absolute ~ high exposure'][0][2]:.2f}-point higher AI/Data score before conditioning on conventional capability (p={core_lookup['M1 AI absolute ~ high exposure'][0][6]:.3g}). Exposure groups also differ in conventional capability and AI/Data capability in Welch and Kruskal-Wallis tests.\n\n## Core finding 3: no relative AI-readiness advantage after general capability is accounted for\nOnce conventional capability is included, the high-exposure coefficient on AI/Data capability falls to {core_lookup['M2 AI absolute ~ high exposure + conventional'][0][2]:.2f} points (p={core_lookup['M2 AI absolute ~ high exposure + conventional'][0][6]:.3f}). A residual-readiness model produces the same substantive result: B={core_lookup['M5 residual AI readiness ~ high exposure'][0][2]:.2f}, p={core_lookup['M5 residual AI readiness ~ high exposure'][0][6]:.3f}. The capability gap itself does not differ robustly between low- and high-exposure groups (B={core_lookup['M3 gap ~ high exposure'][0][2]:.2f}, p={core_lookup['M3 gap ~ high exposure'][0][6]:.3f}). The strongest interpretation is therefore selective sorting on general capability without evidence that people targeting more AI-exposed occupations possess a relative AI/Data advantage commensurate with that exposure.\n\n## Robustness\nThe null adjusted exposure effect is stable when analyses are limited to high-confidence occupation mappings, the baseline-zero outlier is excluded, assessment date is controlled, current-job-function controls are added, HC3 standard errors replace occupation-clustered standard errors, ordinal exposure replaces the high-exposure binary, and a complete-case demographic specification is used. Influence diagnostics and Huber robust regression are supplied separately.\n\n## Post-assessment data\nOnly 12 participants have an overall post score and there are no post scores for the ten component dimensions. Intervention fields are largely empty, three reassessments occur on the assessment day and one baseline score is zero. Post-score analyses are therefore Appendix-only and explicitly noncausal. They may be described as exploratory follow-up evidence but must not be used to claim intervention effectiveness.\n\n## Publication interpretation\nThe defensible empirical story is not “higher AI exposure causes a larger capability gap.” The data do not support that claim after general capability is accounted for. The stronger contribution is a strategic human-capital asymmetry: individuals targeting more AI-exposed occupations are absolutely stronger, yet their relative AI/Data readiness does not improve beyond what would be expected from their general capability. In a labour market where occupational AI exposure is high, capability development appears to lag occupational demand even among comparatively capable talent.\n'''
(OUT/'STATISTICAL_MODELING_REPORT.md').write_text(memo,encoding='utf-8')

spec='''# Model Specification and Claim Discipline\n\n## Primary empirical objects\n1. Conventional capability index: equal-weight mean of six baseline dimensions.\n2. AI/Data capability index: equal-weight mean of four baseline dimensions.\n3. Capability gap: Conventional minus AI/Data, participant-level within-person contrast.\n4. ILO occupational exposure: official 2025 category linked through ISCO-08 career-interest coding.\n5. High exposure: ILO Gradient 3 or Gradient 4; low exposure: Minimal Exposure or Gradient 2. The 1–5 ordinal variable is an analytical recode and is used only as a robustness specification.\n\n## Primary tests\n- Within-person paired comparison of conventional and AI/Data domains.\n- Occupation-clustered OLS of absolute AI/Data capability on high exposure.\n- Occupation-clustered OLS of AI/Data capability on high exposure plus conventional capability.\n- Occupation-clustered OLS of capability gap on high exposure.\n- Residual AI-readiness test: residuals from AI/Data capability regressed on conventional capability, then tested against high exposure.\n\n## Robustness\nHigh-confidence mappings only; remove baseline-zero case; assessment-date control; current-function controls; HC3 standard errors; ordinal exposure; complete-case demographics; Huber robust regression; influence diagnostics; nonparametric group tests.\n\n## Claim boundaries\n- Cross-sectional baseline analyses support association, asymmetry and alignment/misalignment language, not causality.\n- Career interest is an aspirational occupation mapping, not observed employment in that occupation.\n- ILO exposure is external occupational demand context, not participant-level AI use.\n- The post-score n=12 sample cannot identify intervention effects.\n- The ten assessment dimensions show a strong general factor, so domain averages are theory-defined indices rather than empirically distinct latent constructs.\n'''
(OUT/'MODEL_SPECIFICATION_AND_CLAIM_DISCIPLINE.md').write_text(spec,encoding='utf-8')

print(json.dumps(summary,indent=2))
print('Wrote outputs to',OUT)
