import sys, warnings, json; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, features as F, modeling as M, advice as A
from sklearn.tree import export_text
pd.set_option('display.width',250); pd.set_option('display.max_rows',200); pd.set_option('display.max_colwidth',90)
ART=joblib.load('v2/models_M.joblib'); FM=ART['features']
D=M.prepare(pd.read_parquet('v2/features.parquet'))
TR=D[D.period.isin(['2023','2024'])&D.has_video.notna()].copy(); TE=D[D.period=='2025'].copy()
oof,(ts,),_=M.text_score(TR,[TE]); TR['text_score']=oof; TE['text_score']=ts
adv=A.Advisor(ART)
# ---- 1) SHAP: global importance
S=adv.shap(TE); imp=S.abs().mean().sort_values(ascending=False)
print('mean |SHAP| top 12 (log-odds):'); print(imp.head(12).round(3).to_string())
G=pd.Series({a:S[c].abs().sum(axis=1).mean() for a,c in A.AREAS.items()}); print('by area, share of total:'); print((G/G.sum()).round(3).sort_values(ascending=False).to_string())
(G/G.sum()).to_csv('v2/shap_by_area.csv'); imp.to_csv('v2/shap_by_feature.csv')
# additivity check: SHAP sums + base = model margin
c=ART['model'].get_booster().predict(__import__('xgboost').DMatrix(TE[FM]),pred_contribs=True); raw=ART['model'].predict_proba(TE[FM])[:,1]
print('SHAP additivity: max |sum - logit(p)| =',float(np.abs(c.sum(axis=1)-np.log(raw/(1-raw))).max().round(5)))
# ---- 2) area scores: reference = training campaigns 2023-24
ref=adv.area_sums(TR); ART['area_reference']={k:np.sort(ref[k].values) for k in A.AREAS}; adv.ref=ART['area_reference']
AS=adv.area_scores(TE); TE=TE.join(AS.add_prefix('score_'))
for a in A.AREAS:
    b=pd.cut(TE['score_'+a],[-1,25,60,100],labels=['weak (0-25)','to improve (26-60)','strong (61-100)'])
    t=TE.groupby(b,observed=True).success.agg(n='size',funded='mean'); print(a, ' | '.join(f'{i}: n={int(r.n)}, funded {r.funded:.2f}' for i,r in t.iterrows()))
# ---- 3) chances and the verdict numbers
lo,hi=adv.chances(TE); TE['low']=lo; TE['high']=hi
s25=TE.groupby('parent_category').success.mean()
TE['w']=np.where(TE.success==0,TE.parent_category.map(lambda c:(s25[c]/(1-s25[c]))/(M.OFFICIAL_RATE[c]/(1-M.OFFICIAL_RATE[c]))),1.)   # re-weight to Kickstarter's official mix
print('re-weighted cohort: share failing',round((TE.w*(1-TE.success)).sum()/TE.w.sum(),3),'| sample: share failing',round(1-TE.success.mean(),3))
def reach(score,share,weights=None):
    w=np.ones(len(TE)) if weights is None else weights.values; o=np.argsort(score.values); cw=np.cumsum(w[o])/w.sum(); k=o[cw<=share]
    f=(1-TE.success.values)*w; return f[k].sum()/f.sum(), f[k].sum()/w[k].sum(), score.values[k].max()
rows=[]
for share in (.2,.3,.4,.5):
    a=reach(TE.high,share); b=reach(TE.low,share); c=reach(TE.low,share,TE.w)
    rows.append((share,round(a[0],3),round(b[0],3),round(b[1],3),round(c[0],3),round(c[1],3),round(c[2],3)))
V=pd.DataFrame(rows,columns=['coach capacity','sample: failures reached, rank by high end','sample: failures reached, rank by low end','sample: share of the group that fails','official mix: failures reached','official mix: share of the group that fails','low-end chance at the cut']); print(V.T.to_string()); V.to_csv('v2/verdict_capacity.csv',index=False)
# within-category check: ranking by low end keeps the within-category AUC
print('AUC within category: high',round(M.auc_within(TE.success,TE.high,TE.cat_id),4),'low',round(M.auc_within(TE.success,TE.low,TE.cat_id),4),'| within parent: high',round(M.auc_within(TE.success,TE.high,TE.parent_category),4),'low',round(M.auc_within(TE.success,TE.low,TE.parent_category),4),'| overall: high',round(__import__('sklearn.metrics').metrics.roc_auc_score(TE.success,TE.high),4),'low',round(__import__('sklearn.metrics').metrics.roc_auc_score(TE.success,TE.low),4))
# who is in the riskiest 30% under each ranking, by parent
TE['risk_hi']=TE.high.rank(pct=True)<=.3; TE['risk_lo']=TE.low.rank(pct=True)<=.3
print(TE.groupby('parent_category').agg(n=('success','size'),in_riskiest_by_high=('risk_hi','mean'),in_riskiest_by_low=('risk_lo','mean')).round(2).T.to_string())
cut30=reach(TE.low,.3,TE.w)[2]; ART['verdict']={'reference_cut':float(cut30),'adjust_gain':5.0,'default_capacity':0.30}; adv.cut=ART['verdict']
# ---- 4) what to change: best single change for every 2025 campaign (minimum budget assumed = half the goal)
import time; t0=time.time(); smp=TE.sample(4000,random_state=7); res=[]
for i,r in smp.iterrows():
    fx=adv.fixes(r); res.append((i,fx))
print('fixes s',round(time.time()-t0))
best=pd.DataFrame([{'i':i,'lever':fx[0]['lever'] if fx else 'none','gain':fx[0]['gain'] if fx else 0,'n':len(fx)} for i,fx in res]).set_index('i')
print('top fix by lever (share of campaigns):'); print(best.lever.value_counts(normalize=True).round(3).to_string())
print('gain of the best fix, points: median',best.gain.median(),'| p75',best.gain.quantile(.75),'| share >=5',round((best.gain>=5).mean(),3),'| >=10',round((best.gain>=10).mean(),3))
allfx=pd.DataFrame([dict(f,i=i) for i,fx in res for f in fx]); print('mean gain when the lever is offered:'); print(allfx.groupby('lever').gain.agg(['size','median','max']).round(1).to_string())
smp=smp.join(best); smp['risky']=smp.low<cut30
smp['verdict']=np.select([smp.risky,smp.gain>=5],['Rethink','Adjust'],'Launch')
print(smp.groupby('verdict').agg(n=('success','size'),share=('success',lambda s:len(s)/len(smp)),funded_in_sample=('success','mean'),low=('low','mean'),high=('high','mean')).round(3).to_string())
for g in (3,5,8,10): print('adjust threshold',g,'-> Adjust share among non-coach',round(((~smp.risky)&(smp.gain>=g)).sum()/(~smp.risky).sum(),3))
# direction check of the levers against the raw data (within category, 2023-24): does the model's advice agree with what we see?
print('monotonic check: share of campaigns where a 30% lower goal LOWERS the predicted chance:')
q=smp.copy(); q['log_goal_usd']-=np.log10(1/.7)*1; q['goal_ratio']+=np.log10(.7); q['log_goal_per_day']+=np.log10(.7); print(round((adv.chances(q)[1]<smp.high-1e-9).mean(),3))
# ---- 5) product types that do badly: Market area
low=TE[TE.score_Market<=15]; print('Market score <=15: n',len(low),'funded in sample',round(low.success.mean(),3),'| others',round(TE[TE.score_Market>15].success.mean(),3))
print(low.groupby('parent_category').size().sort_values(ascending=False).head(6).to_dict()); print(low.subcategory.value_counts().head(10).to_dict())
# ---- 6) depth-3 tree for the plain explanation
print(export_text(ART['tree3'],feature_names=FM,decimals=2))
# ---- 7) three example campaigns
for i in [smp[smp.verdict=='Rethink'].index[3],smp[smp.verdict=='Adjust'].index[3],smp[smp.verdict=='Launch'].index[3]]:
    r=TE.loc[i]; print('\n',r['name'][:70],'|',r.parent_category,'/',r.subcategory,'| goal $',round(r.goal_usd),'| outcome:',['failed','funded'][r.success])
    print('  chance range',round(r.low*100),'-',round(r.high*100),'% | areas',{a:int(r['score_'+a]) for a in A.AREAS},'| verdict',smp.verdict.get(i))
    for f in adv.fixes(r): print('   +',f['gain'],'pts:',f['change'])
EX=[f for f in FM if f not in ('text_score','cat_id','parent_c','country_c')]
from sklearn.tree import DecisionTreeClassifier
ART['tree_readable']=DecisionTreeClassifier(criterion='entropy',max_depth=3,min_samples_leaf=500,random_state=42).fit(TR[EX].fillna(-1),TR.success); ART['tree_features']=EX
joblib.dump(ART,'v2/models_M.joblib'); TE[['id','low','high','success','parent_category','cat_id']+['score_'+a for a in A.AREAS]].to_parquet('v2/reference_2025.parquet')
