import sys, time, warnings, json; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, xgboost as xgb, joblib
import features as F, modeling as M
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, silhouette_score, roc_curve, brier_score_loss
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
BP=joblib.load('v2/best_params.joblib'); ART=joblib.load('v2/models_M.joblib'); FM=ART['features']
D=M.prepare(pd.read_parquet('v2/features.parquet')); D['yr']=np.where(D.period=='2026H1',2026,D.launch_year)
# ---- 1) walk-forward: train up to year t-1, test on year t (30 features: no video/pre-launch, no text score)
FW=[c for c in M.numeric_features(with_norms=False,with_presentation=False,with_text=False)]
rows=[]
for t in range(2019,2027):
    te=D[D.yr==t]
    for nm,tr in [('all earlier years',D[D.yr<t]),('last 2 years only',D[D.yr.between(t-2,t-1)])]:
        m=xgb.XGBClassifier(subsample=.8,colsample_bytree=.8,n_jobs=2,random_state=42,max_depth=6,n_estimators=400,learning_rate=.05).fit(tr[FW],tr.success)
        p=m.predict_proba(te[FW])[:,1]; rows.append((t if t<2026 else '2026 Jan-Jun',nm,len(tr),len(te),round(te.success.mean(),3),round(M.auc_within(te.success,p,te.cat_id),3),round(M.auc_within(te.success,p,te.parent_category),3),round(roc_auc_score(te.success,p),3)))
W=pd.DataFrame(rows,columns=['test year','training data','train rows','test rows','funded in sample','AUC within category','AUC within parent','AUC overall']); print(W.to_string(index=False)); W.to_csv('v2/walk_forward.csv',index=False)
# ---- 2) calibration detail and threshold
P=pd.read_parquet('v2/test2025_pred.parquet')
rel=P.groupby(pd.cut(P.p_sample,np.linspace(0,1,11)),observed=True).agg(n=('success','size'),predicted=('p_sample','mean'),actual=('success','mean')).round(3); print('reliability after Platt, 2025'); print(rel.to_string()); rel.to_csv('v2/reliability_2025_cal.csv')
fpr,tpr,thr=roc_curve(P.success,P.p_sample); j=np.argmax(tpr-fpr); print('Youden J threshold on 2025 (info only):',round(thr[j],3),'tpr',round(tpr[j],3),'fpr',round(fpr[j],3))
# level correction check: weight failures so that each parent matches the official rate, then compare
s=ART['sample_rate']; s25=P.groupby('parent_category').success.mean()
P['w']=np.where(P.success==0,P.parent_category.map(lambda c:(s25[c]/(1-s25[c]))/(M.OFFICIAL_RATE[c]/(1-M.OFFICIAL_RATE[c]))),1.)
chk=P.groupby('parent_category').apply(lambda g:pd.Series({'official':M.OFFICIAL_RATE[g.name],'weighted mean corrected p':np.average(g.p_official,weights=g.w),'mean corrected p':g.p_official.mean(),'mean sample p':g.p_sample.mean()})).round(3)
print(chk.to_string()); print('mean abs gap official vs weighted mean corrected:',(chk.official-chk['weighted mean corrected p']).abs().mean().round(3)); chk.to_csv('v2/level_check.csv')
print('share of 2025 campaigns: sample p>=0.5',(P.p_sample>=.5).mean().round(3),'| corrected p>=0.5',(P.p_official>=.5).mean().round(3),'| both',((P.p_sample>=.5)&(P.p_official>=.5)).mean().round(3))
# ---- 3) support model: linear regression on money raised (class)
raw=pd.read_parquet('v2/kickstarter_merged_v2.parquet',columns=['id','pledged','static_usd_rate','usd_pledged'])
D=D.merge(raw.assign(raised=raw.usd_pledged.fillna(raw.pledged*raw.static_usd_rate))[['id','raised']],on='id')
D['log_raised']=np.log10(D.raised+1)
tr=D[D.period.isin(['2023','2024'])&D.has_video.notna()].copy(); te=D[D.period=='2025'].copy()
oof,(ts,),_=M.text_score(tr,[te]); tr['text_score']=oof; te['text_score']=ts
num=[c for c in FM if c not in M.LABELS]
def design(d,ref=None):
    Z=d[num].copy(); Z['prior_rate_missing']=Z.creator_prior_rate.isna().astype(int)
    Z=Z.fillna(tr[num].median()); Z=pd.concat([Z,pd.get_dummies(d.parent_category,drop_first=True,dtype=float)],axis=1)
    return Z if ref is None else Z.reindex(columns=ref,fill_value=0)
Zt=design(tr); Zv=design(te,Zt.columns)
for nm,a,b in [('all campaigns',tr,te),('funded campaigns only',tr[tr.success==1],te[te.success==1])]:
    lr=LinearRegression().fit(Zt.loc[a.index],a.log_raised); pr=lr.predict(Zv.loc[b.index]); base=b.cat_id.map(a.groupby('cat_id').log_raised.median()).fillna(a.log_raised.median())
    err=np.abs(pr-b.log_raised); print(f'money raised, {nm}: n_test={len(b)} R2={lr.score(Zv.loc[b.index],b.log_raised):.3f} RMSE(log10)={np.sqrt(((pr-b.log_raised)**2).mean()):.3f} | typical error factor x{10**np.median(err):.2f} | category-median baseline RMSE={np.sqrt(((base-b.log_raised)**2).mean()):.3f} factor x{10**np.median(np.abs(base-b.log_raised)):.2f}')
    if nm.startswith('funded'): joblib.dump({'lr':lr,'cols':list(Zt.columns),'medians':tr[num].median()},'v2/model_raised.joblib')
# ---- 4) k-means archetypes (beyond class) on launches 2023-24
A=tr.copy(); A['log_prior']=np.log10(A.creator_prior_n+1)
KF=['log_goal_usd','duration_days','log_prep_days','log_prior','prelaunch_activated','has_video','name_words','blurb_words']
scl=StandardScaler().fit(A[KF]); Z=scl.transform(A[KF]); sm=np.random.default_rng(0).choice(len(Z),6000,replace=False)
for k in range(3,8):
    km=KMeans(k,n_init=5,random_state=42).fit(Z); print('k',k,'silhouette',round(silhouette_score(Z[sm],km.labels_[sm]),3),'inertia',int(km.inertia_))
km=KMeans(4,n_init=10,random_state=42).fit(Z); A['arch']=km.labels_
prof=A.groupby('arch').agg(n=('success','size'),funded_in_sample=('success','mean'),median_goal_usd=('goal_usd','median'),duration=('duration_days','median'),prep_days=('log_prep_days',lambda s:10**s.median()-1),first_timer=('first_timer','mean'),prelaunch=('prelaunch_activated','mean'),video=('has_video','mean'),title_words=('name_words','median')).round(2); print(prof.to_string()); prof.to_csv('v2/archetypes.csv')
joblib.dump({'scaler':scl,'kmeans':km,'features':KF},'v2/model_archetypes.joblib')
# ---- 5) nearest neighbours: similar past campaigns (beyond class)
NF=['log_goal_usd','duration_days','log_prep_days','log_prior','prelaunch_activated','has_video','text_score','first_timer']
te['log_prior']=np.log10(te.creator_prior_n+1); s2=StandardScaler().fit(A[NF]); nb=np.full(len(te),np.nan); pos={i:k for k,i in enumerate(te.index)}
for par,g in A.groupby('parent_category'):
    q=te[te.parent_category==par]
    if len(q)==0: continue
    nn=NearestNeighbors(n_neighbors=10).fit(s2.transform(g[NF])); _,ix=nn.kneighbors(s2.transform(q[NF]))
    nb[[pos[i] for i in q.index]]=g.success.values[ix].mean(axis=1)
te['nb']=nb; print('similar campaigns (10 nearest in the same parent category, 2023-24): funded share of neighbours as a predictor of 2025 outcomes: AUC within category',round(M.auc_within(te.success,te.nb,te.cat_id),3),'| overall',round(roc_auc_score(te.success,te.nb),3))
print(te.groupby(pd.cut(te.nb,[-.01,.2,.4,.6,.8,1])).success.agg(n='size',funded='mean').round(3).to_string())
