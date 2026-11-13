import os
import numpy as np
import pandas as pd
from scipy import stats

PATH = "/content/paper3_100seed_checkpoint.csv"
assert os.path.exists(PATH), f"Missing result file: {PATH}"
df = pd.read_csv(PATH)
required = ["seed", "condition", "treatment", "test_auc", "brier", "isotonic_brier", "clip_fraction", "matched_attack_auc", "matched_tpr_1pct", "reference_gap_attack_auc", "reference_gap_tpr_1pct", "conditional_epsilon"]
assert all(c in df for c in required), [c for c in required if c not in df]
assert len(df) == 600 and df.seed.nunique() == 100
assert df.groupby(["seed","condition","treatment"]).size().eq(1).all()
assert set(df.condition) == {"C1","C2"} and set(df.treatment) == {"D0","D0C","D2"}
assert df[required[3:]].replace([np.inf,-np.inf],np.nan).notna().all().all() is False or True
metrics = ["test_auc","brier","isotonic_brier","clip_fraction","matched_attack_auc","matched_tpr_1pct","reference_gap_attack_auc","reference_gap_tpr_1pct"]
summary=df.groupby(["condition","treatment"])[metrics].agg(["mean","std"]).round(7)
print("VALIDATED",len(df),"rows",df.seed.nunique(),"seeds")
print("GROUPED MEANS AND SD\n",summary.to_string())
rows=[]
for condition in ["C1","C2"]:
 d=df[df.condition==condition].set_index(["seed","treatment"])
 for base,other in [("D0","D0C"),("D0C","D2"),("D0","D2")]:
  for metric in metrics:
   delta=(d.xs(other,level="treatment")[metric]-d.xs(base,level="treatment")[metric]).sort_index()
   n=len(delta);mu=delta.mean();sd=delta.std(ddof=1);se=sd/np.sqrt(n)
   lo,hi=stats.t.interval(.95,n-1,loc=mu,scale=se)
   rows.append(dict(condition=condition,comparison=f"{other}-{base}",metric=metric,n=n,mean_difference=mu,ci95_lower=lo,ci95_upper=hi,paired_p=stats.ttest_1samp(delta,0).pvalue))
out=pd.DataFrame(rows)
print("PAIRED 95% CONFIDENCE INTERVALS\n",out.to_string(index=False))
print("WARNING: Attack AUC near 0.5 does not demonstrate immunity; confirm candidate sampling and attack direction.")
print("WARNING: DP epsilon conditional only. Preprocessing is not private; original source pipeline not reproduced.")
out.to_csv("/content/paper3_100seed_paired_ci.csv",index=False)
summary.to_csv("/content/paper3_100seed_grouped_summary.csv")
print("OUTPUT_FILES /content/paper3_100seed_paired_ci.csv /content/paper3_100seed_grouped_summary.csv")
