import sys; sys.path.insert(0,'/home/claude/work')
import pandas as pd, numpy as np, features as F, xgboost as xgb
from sklearn.metrics import roc_auc_score
pd.set_option('display.width',250); pd.set_option('display.max_rows',300)
X=pd.read_parquet('v2/features.parquet'); raw=pd.read_parquet('v2/kickstarter_merged_v2.parquet'); pr=pd.read_parquet('v2/presence.parquet')
h1=X[(X.launch_year==2026)&(X.launch<'2026-07-01')]; print('2026 Jan-Jun:',len(h1),round(h1.success.mean(),4))
E=X[X.launch_year.isin([2023,2024])&X.has_video.notna()].copy()
def wauc(df,f,by='cat_id'):
    tot=w=0
    for _,g in df.groupby(by):
        v=g[[f,'success']].dropna()
        if v.success.nunique()==2 and v[f].nunique()>1: tot+=roc_auc_score(v.success,v[f])*len(v); w+=len(v)
    return round(tot/w,3) if w else np.nan
print('\n(1) Founder signal inside a category, launches 2023-24, capped vs other categories')
for nm,d in [('all',E),('29 capped',E[E.capped_category==1]),('other 145',E[E.capped_category==0])]:
    print(f'{nm:10s} n={len(d):6d} funded={d.success.mean():.3f} | prior_n {wauc(d,"creator_prior_n")} | prior_rate (repeat creators only) {wauc(d,"creator_prior_rate")} n_repeat={int((d.creator_prior_n>0).sum())}')
    t=np.select([d.creator_prior_n==0,d.creator_prior_rate==0,d.creator_prior_rate<1],['first','none funded','some funded'],'all funded'); t=pd.Series(t,index=d.index); t[(d.creator_prior_n>0)&d.creator_prior_rate.isna()]='x'
    print(d.groupby(t).success.agg(n='size',funded='mean').round(3).drop('x',errors='ignore').T.to_string())
print('\n(2) Clean test: the creator\'s previous campaign was FIRST SEEN WHILE LIVE (so it entered our data before its outcome existed)')
first=pr.sort_values('scrape').drop_duplicates('id',keep='first').set_index('id').state
h=raw[raw.state.isin(['successful','failed'])&(raw.launched_at>1.2e9)&raw.creator_id.notna()][['id','creator_id','deadline','state']].sort_values('deadline')
cur=E[['id','creator_id','launched_at','success','capped_category','cat_id']].dropna(subset=['creator_id']).sort_values('launched_at')
m=pd.merge_asof(cur,h.rename(columns={'id':'prev_id','state':'prev_state'}),left_on='launched_at',right_on='deadline',by='creator_id',allow_exact_matches=False)
m=m.dropna(subset=['prev_id']); m['prev_first']=m.prev_id.map(first); m['prev_funded']=(m.prev_state=='successful').astype(int)
for nm,d in [('all previous campaigns',m),('previous first seen live',m[m.prev_first=='live']),('  of which other categories',m[(m.prev_first=='live')&(m.capped_category==0)])]:
    g=d.groupby('prev_funded').success.agg(n='size',funded='mean').round(3)
    print(f'{nm:30s} prev failed: n={g.n.get(0,0)}, now funded {g.funded.get(0,np.nan)} | prev funded: n={g.n.get(1,0)}, now funded {g.funded.get(1,np.nan)} | AUC {round(roc_auc_score(d.success,d.prev_funded),3)}')
# how were previous failed campaigns' share: clean vs all
print('share of previous campaigns that failed: all',round(1-m.prev_funded.mean(),3),'| first seen live',round(1-m[m.prev_first=='live'].prev_funded.mean(),3))
print('\n(3) Uniform odds correction (failures covered 0.412, successes 0.836 -> multiply odds by',round(.412/.836,3),')')
k=.412/.836
for nm,p in [('first campaign',E[E.creator_prior_n==0].success.mean()),('earlier, all funded',E[(E.creator_prior_rate==1)].success.mean()),('earlier, none funded',E[(E.creator_prior_rate==0)].success.mean())]:
    o=p/(1-p)*k; print(f'  {nm:22s} sample {p:.3f} -> corrected {o/(1+o):.3f}')
print('\n(4) Does founder history add to a model? XGBoost, train 2023 -> evaluate 2024, AUC within category')
feats=[f for g,v in F.GROUPS.items() for f in v if f not in('parent_category','country')]
E['country_c']=E.country.astype('category').cat.codes; E['parent_c']=E.parent_category.astype('category').cat.codes
allf=feats+['country_c','parent_c']; fo=F.GROUPS['Founder']
tr=E[E.launch_year==2023]; te=E[E.launch_year==2024].copy()
def fit(cols,w=None): return xgb.XGBClassifier(n_estimators=400,max_depth=5,learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,n_jobs=2,random_state=42).fit(tr[cols],tr.success,sample_weight=w)
def rep(nm,cols,w=None):
    mod=fit(cols,w); te['p']=mod.predict_proba(te[cols])[:,1]
    r=[nm,wauc(te,'p'),wauc(te,'p','parent_category'),round(roc_auc_score(te.success,te.p),3),wauc(te[te.capped_category==1],'p'),wauc(te[te.capped_category==0],'p')]
    return r
rows=[rep('all 35 features',allf),rep('without founder group',[c for c in allf if c not in fo]),rep('without market rate/size/trend',[c for c in allf if c not in('cat_rate_12m','cat_trend','log_cat_n_12m')]),
      rep('capped rows weight 0.5',allf,np.where(tr.capped_category==1,.5,1.)),rep('capped rows weight 0.25',allf,np.where(tr.capped_category==1,.25,1.)),
      rep('capped: failures weight x3',allf,np.where((tr.capped_category==1)&(tr.success==0),3.,1.))]
print(pd.DataFrame(rows,columns=['model','AUC within category','within parent','overall','within cat: capped','within cat: other']).to_string(index=False))
print('eval 2024: capped n',int((te.capped_category==1).sum()),'funded',round(te[te.capped_category==1].success.mean(),3),'| other n',int((te.capped_category==0).sum()),'funded',round(te[te.capped_category==0].success.mean(),3))
