import sys, warnings; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, xgboost as xgb, modeling as M, advice as A
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
ART=joblib.load('v2/models_M.joblib'); FM=ART['features']; BP=joblib.load('v2/best_params.joblib')['best_xgb']
D=M.prepare(pd.read_parquet('v2/features.parquet'))
P23=D[(D.period=='2023')&D.has_video.notna()].copy(); P24=D[D.period=='2024'].copy(); TR=pd.concat([P23,P24]); TE=D[D.period=='2025'].copy(); T26=D[D.period=='2026H1'].copy()
oof,(ts,t6),_=M.text_score(TR,[TE,T26]); TR['text_score']=oof; TE['text_score']=ts; T26['text_score']=t6
o2,(v2,),_=M.text_score(P23,[P24]); P23['text_score']=o2; P24['text_score']=v2
mono={'log_goal_usd':-1,'goal_ratio':-1,'log_goal_per_day':-1}
cons='('+','.join(str(mono.get(f,0)) for f in FM)+')'
def fit(tr,c=None): return xgb.XGBClassifier(subsample=.8,colsample_bytree=.8,n_jobs=2,random_state=42,**BP,**({'monotone_constraints':c} if c else {})).fit(tr[FM],tr.success)
for nm,c in [('final (no constraint)',None),('goal can only lower the chance',cons)]:
    v=fit(P23,c); m=fit(TR,c); p=m.predict_proba(TE[FM])[:,1]; p6=m.predict_proba(T26[FM])[:,1]
    q=TE.copy(); q['log_goal_usd']-=np.log10(1/.7); q['goal_ratio']+=np.log10(.7); q['log_goal_per_day']+=np.log10(.7)
    print(f'{nm:32s} val2024 {M.auc_within(P24.success,v.predict_proba(P24[FM])[:,1],P24.cat_id):.4f} | 2025 within cat {M.auc_within(TE.success,p,TE.cat_id):.4f} parent {M.auc_within(TE.success,p,TE.parent_category):.4f} overall {roc_auc_score(TE.success,p):.4f} Brier {brier_score_loss(TE.success,p):.4f} | 2026H1 {M.auc_within(T26.success,p6,T26.cat_id):.4f} | lower goal lowers chance in {(m.predict_proba(q[FM])[:,1]<p-1e-9).mean():.3f}')
# explanation tree on features a founder can read (no text score, no category codes)
EX=[f for f in FM if f not in ('text_score','cat_id','parent_c','country_c')]
t3=DecisionTreeClassifier(criterion='entropy',max_depth=3,min_samples_leaf=500,random_state=42).fit(TR[EX].fillna(-1),TR.success)
p=t3.predict_proba(TE[EX].fillna(-1))[:,1]; print('readable depth-3 tree: 2025 AUC within category',round(M.auc_within(TE.success,p,TE.cat_id),3),'overall',round(roc_auc_score(TE.success,p),3))
print(export_text(t3,feature_names=EX,decimals=2,show_weights=True))
# cohort-mode verdict mix: simulated cohorts of 40 campaigns drawn from 2025
adv=A.Advisor(ART); lo,hi=adv.chances(TE); TE['low']=lo; rng=np.random.default_rng(1); r=[]
for _ in range(500):
    c=TE.sample(40,random_state=int(rng.integers(1e9))); k=c.low.rank(method='first')<=12; r.append((c[k].success.mean(),(1-c[k].success).sum()/max((1-c.success).sum(),1),c[~k].success.mean()))
r=np.array(r); print('cohorts of 40, coach takes 12 (30%): funded share among the 12:',r[:,0].mean().round(3),'| share of the cohort\'s failures among the 12:',r[:,1].mean().round(3),'(5th-95th pct',np.percentile(r[:,1],5).round(2),np.percentile(r[:,1],95).round(2),') | funded share among the other 28:',r[:,2].mean().round(3))
