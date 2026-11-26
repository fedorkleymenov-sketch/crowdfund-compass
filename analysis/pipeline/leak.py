import pandas as pd, numpy as np, xgboost as xgb
from sklearn.metrics import roc_auc_score
m=pd.read_parquet('v2/kickstarter_merged_v2.parquet')
d=m[m.state.isin(['successful','failed'])].copy()
d['y']=(d.state=='successful').astype(int)
d['L']=pd.to_datetime(d.launched_at,unit='s'); d['yr']=d.L.dt.year
d=d[d.L<=pd.Timestamp('2026-11-16')-pd.Timedelta(days=60)]
d['log_goal']=np.log10((d.goal*d.static_usd_rate).clip(lower=1)); d['dur']=(d.deadline-d.launched_at)/86400
d['prep']=np.log1p((d.launched_at-d.created_at)/86400); d['month']=d.L.dt.month; d['wday']=d.L.dt.weekday
d['name_len']=d.name.str.len(); d['blurb_len']=d.blurb.fillna('').str.len()
for c in ['country','parent_category']: d[c+'_c']=d[c].astype('category').cat.codes
d['known']=d.has_video.notna().astype(int)
BASE=['log_goal','dur','prep','month','wday','name_len','blurb_len','country_c','parent_category_c','cat_id']
VP=['has_video','prelaunch_activated']
FORBIDDEN={'has_video','prelaunch_activated','known','scrape','first_scrape','n_scrapes','staff_pick','spotlight','pledged','usd_pledged','backers_count','state_changed_at'}
def fit(tr,feats):
    return xgb.XGBClassifier(n_estimators=300,max_depth=6,learning_rate=0.08,subsample=0.8,colsample_bytree=0.8,n_jobs=2,random_state=42).fit(tr[feats],tr.y)
def auc(mod,te,feats): return round(roc_auc_score(te.y,mod.predict_proba(te[feats])[:,1]),4)

print('TEST 1 structural: all-years feature list has no forbidden column:', set(BASE).isdisjoint(FORBIDDEN))

print('\nTEST 2 the leak is real (so excluding it matters). Train <=2021, evaluate on 2022 launches (80% known):')
tr=d[d.yr<=2021]; te=d[d.yr==2022]
print('  share known in 2022:',round(te.known.mean(),3),'| funded rate if known',round(te[te.known==1].y.mean(),3),'| if unknown',round(te[te.known==0].y.mean(),3))
print('  AUC of the known-flag alone :',round(roc_auc_score(te.y,-te.known),4))
a=fit(tr,BASE); b=fit(tr,BASE+['known']); c=fit(tr,BASE+VP)
print('  AUC all-years features       :',auc(a,te,BASE))
print('  AUC + known flag             :',auc(b,te,BASE+['known']))
print('  AUC + video/prelaunch w. NaN :',auc(c,te,BASE+VP),' <- variant (a), learns the flag through NaN')
te24=d[d.yr==2024]
print('  same three models on 2024 (flag constant, all known):',auc(a,te24,BASE),auc(b,te24,BASE+['known']),auc(c,te24,BASE+VP))

print('\nTEST 3 invariance: scramble video/prelaunch/scrape columns, all-years predictions must not move')
t2=te.copy(); rng=np.random.default_rng(0)
for col in ['has_video','prelaunch_activated','known']: t2[col]=rng.permutation(t2[col].values)
print('  max |change in predicted probability| =',float(np.abs(a.predict_proba(te[BASE])[:,1]-a.predict_proba(t2[BASE])[:,1]).max()))

print('\nTEST 4 modern model: no missing values at all in its rows')
mod=d[(d.yr>=2023)]; n0=len(mod); mod=mod[mod.has_video.notna()&mod.prelaunch_activated.notna()]
print('  rows launch>=2023:',n0,'| dropped for unknown video/prelaunch:',n0-len(mod),'| remaining missing values:',int(mod[VP].isna().sum().sum()))
print('  known flag takes',mod.known.nunique(),'value(s) in these rows -> it cannot carry information')

print('\nCOMPARISON (preliminary, 10 simple features)')
rows=[]
for ev,trmax in [(2024,2023),(2025,2024)]:
    te=d[d.yr==ev]
    A=d[d.yr<=trmax]; M=mod[mod.yr<=trmax]
    rows.append((ev,'all-years, no video/prelaunch',len(A),auc(fit(A,BASE),te,BASE)))
    rows.append((ev,'2023+ only, no video/prelaunch',len(M),auc(fit(M,BASE),te,BASE)))
    rows.append((ev,'2023+ only, with video/prelaunch',len(M),auc(fit(M,BASE+VP),te,BASE+VP)))
print(pd.DataFrame(rows,columns=['eval year','model','train rows','AUC']).to_string(index=False))
print('eval sizes',(d.yr==2024).sum(),(d.yr==2025).sum(),'funded',round(d[d.yr==2024].y.mean(),3),round(d[d.yr==2025].y.mean(),3))
