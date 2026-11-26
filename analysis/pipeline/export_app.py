# export_app.py — writes the small files the Streamlit app needs (no raw data): model, text model, lookup numbers.
import sys, json; sys.path.insert(0,'/home/claude/work')
import numpy as np, pandas as pd, joblib, advice as A, modeling as M
out='repo/app/models'
ART=joblib.load('v2/models_M.joblib'); ART['model'].save_model(out+'/model.json')
joblib.dump((ART['tfidf'],ART['text_lr']),out+'/text_model.joblib',compress=3)
X=pd.read_parquet('v2/features.parquet',columns=['cat_id','subcategory','parent_category','launch_year','goal_usd','success'])
raw=pd.read_parquet('v2/kickstarter_merged_v2.parquet',columns=['cat_id','cat_slug']).drop_duplicates('cat_id').set_index('cat_id').cat_slug
tab=pd.read_parquet('v2/cat_table.parquet'); last=tab[tab.month==tab.month.max()]
cm=last[(last.level=='cat_id')&(last.n>=20)].set_index('key').med_goal; pm=last[last.level=='parent_category'].set_index('key').med_goal
recent=X[X.launch_year>=2023].groupby('cat_id').size()
cats={}
for cid,g in X.groupby('cat_id'):
    if recent.get(cid,0)<20: continue                       # only categories with enough recent campaigns to say anything
    slug=raw[cid]; name=g.subcategory.iloc[0]
    cats[str(int(cid))]={'name':name if '/' in slug else name+' (general)','parent':g.parent_category.iloc[0],'median_goal':float(cm[str(int(cid))]) if str(int(cid)) in cm.index else None}
t=ART['tree_readable'].tree_
T=pd.read_csv('v2/test_table.csv',index_col=[0,1]); fm=T.xs('XGBoost + goal rule (final model)',level=1)
meta={'features':ART['features'],'platt':{'a':float(ART['platt'].coef_[0][0]),'b':float(ART['platt'].intercept_[0])},'sample_rate':{k:float(v) for k,v in ART['sample_rate'].items()},
      'official_rate':M.OFFICIAL_RATE,'verdict':dict(ART['verdict'],reference_cut=0.115),'area_reference':{k:np.quantile(v,np.linspace(0,1,201)).round(5).tolist() for k,v in ART['area_reference'].items()},
      'categories':cats,'parent_median_goal':{k:float(v) for k,v in pm.items()},'countries':M.COUNTRIES,
      'tree':{'features':ART['tree_features'],'feature':t.feature.tolist(),'threshold':t.threshold.round(4).tolist(),'left':t.children_left.tolist(),'right':t.children_right.tolist(),'funded_share':(t.value[:,0,1]/t.value[:,0].sum(axis=1)).round(4).tolist()},
      'test':{'auc_within_category_2025':float(fm.loc['2025','AUC within category']),'auc_within_category_2026h1':float(fm.loc['2026H1','AUC within category']),'auc_overall_2025':float(fm.loc['2025','AUC overall']),'accuracy_2025':float(fm.loc['2025','accuracy']),'n_train':43904,'n_test_2025':26533},
      'built':'2026-11-16'}
json.dump(meta,open(out+'/meta.json','w'))
import os; print({f:os.path.getsize(out+'/'+f) for f in os.listdir(out)}, len(cats),'categories')

# ---- Similar campaigns: slim table of public campaigns (no creator names or ids). Source: Web Robots Kickstarter scrapes.
import features as F
D=M.prepare(pd.read_parquet('v2/features.parquet')); S=D[D.period.isin(['2023','2024','2025','2026H1'])&D.has_video.notna()].copy()
S['text_score']=ART['text_lr'].decision_function(ART['tfidf'].transform(S.text)); S['log_prior']=np.log10(S.creator_prior_n+1)
NF=['log_goal_usd','duration_days','log_prep_days','log_prior','prelaunch_activated','has_video','text_score','first_timer']
sim=S[['name','cat_id','parent_category','country','city','goal_usd','success','launch_year']+NF].copy()
sim['goal_usd']=sim.goal_usd.round(0); sim[NF]=sim[NF].astype('float32'); sim['cat_id']=sim.cat_id.astype('int16'); sim['success']=sim.success.astype('int8'); sim['launch_year']=sim.launch_year.astype('int16')
for c in ['parent_category','country']: sim[c]=sim[c].astype('category')
sim.to_parquet(out+'/similar.parquet',index=False,compression='zstd')
meta['similar']={'features':NF,'mean':S[NF].mean().round(5).to_dict(),'std':S[NF].std().round(5).to_dict(),'n':int(len(sim))}
# ---- Category benchmarks: official all-time rates + profile of FUNDED campaigns in our data (launches 2023 to June 2026)
raw=pd.read_parquet('v2/kickstarter_merged_v2.parquet',columns=['id','pledged','static_usd_rate','usd_pledged'])
Fd=S[S.success==1].merge(raw.assign(raised=raw.usd_pledged.fillna(raw.pledged*raw.static_usd_rate))[['id','raised']],on='id')
def prof(g): return {'n':int(len(g)),'median_goal':float(g.goal_usd.median()),'median_raised':float(g.raised.median()),'median_days':float(g.duration_days.median()),'prelaunch':float(g.prelaunch_activated.mean()),'video':float(g.has_video.mean()),'first_timer':float(g.first_timer.mean())}
meta['benchmarks']={'parent':{k:prof(g) for k,g in Fd.groupby('parent_category')},'category':{str(int(k)):prof(g) for k,g in Fd.groupby('cat_id') if len(g)>=30}}
meta['official_launched']={'Games':102875,'Technology':59446,'Design':60395,'Film & Video':91638,'Publishing':73301,'Comics':33565,'Music':72348,'Fashion':42556,'Art':56825,'Food':37178,'Photography':14835,'Theater':13753,'Crafts':15291,'Journalism':6691,'Dance':4700}
json.dump(meta,open(out+'/meta.json','w'))
print({f:os.path.getsize(out+'/'+f) for f in os.listdir(out)}, 'similar rows',len(sim),'funded profile rows',len(Fd))
