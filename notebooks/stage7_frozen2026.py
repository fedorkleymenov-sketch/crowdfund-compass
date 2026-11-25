# Frozen test of the coaching rule on launches of January-June 2026 (25.11.2026).
# Everything is fixed as decided on 16.11 and uses only information available before 2026:
#   model trained on 2023-24, Platt calibration from 2024, official rates from Kickstarter's page of 1 January 2026,
#   ranking by the lower value, capacity 30%, single check-up cut 11.5%. Nothing below is tuned on 2026.
# Note: 2026 H1 was looked at before (AUC 0.866 reported on 16.11), but no rule or setting was chosen on it.
import sys, warnings; sys.path.insert(0,'/home/claude/crowdfund-compass/app'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, modeling as M, advice as A
ART=joblib.load('v2/models_M.joblib'); adv=A.Advisor(ART)
D=M.prepare(pd.read_parquet('v2/features.parquet'))
TR=D[D.period.isin(['2023','2024'])&D.has_video.notna()].copy()
TE=D[D.period=='2026H1'].copy()
oof,(ts,),_=M.text_score(TR,[TE]); TE['text_score']=ts
lo,hi=adv.chances(TE); TE['low']=lo; TE['high']=hi
fail=(1-TE.success.values)
s26=TE.groupby('parent_category').success.mean()
w=np.where(TE.success==0,TE.parent_category.map(lambda c:(s26[c]/(1-s26[c]))/(M.OFFICIAL_RATE[c]/(1-M.OFFICIAL_RATE[c]))),1.)   # same re-weighting as for 2025
def reach(score, wt, f, share=.3):
    s=np.asarray(score,float); tot=wt.sum(); cap=share*tot; sel_w=sel_f=0.
    for v in np.unique(s):
        m=s==v; gw=wt[m].sum(); gf=(wt*f)[m].sum(); take=min(1,(cap-sel_w)/gw) if gw>0 else 0
        if take<=0: break
        sel_w+=gw*take; sel_f+=gf*take
        if take<1: break
    return sel_f/(wt*f).sum(), sel_f/sel_w
P24=D[D.period.isin(['2023','2024'])]; P25=D[D.period.isin(['2023','2024','2025'])]
par24=P24.groupby('parent_category').success.mean()
sub24=TE.cat_id.map(P24.groupby('cat_id').success.mean()).fillna(TE.parent_category.map(par24))
sub25=TE.cat_id.map(P25.groupby('cat_id').success.mean()).fillna(TE.parent_category.map(P25.groupby('parent_category').success.mean()))
rules={'Lowest official main-category rate first':TE.parent_category.map(M.OFFICIAL_RATE).values,
 'Highest goal for the category first':(-TE.goal_ratio).values,
 'Lowest subcategory rate first (2023-24, as for 2025)':sub24.values,
 'Lowest subcategory rate first (2023-25, all data known before 2026)':sub25.values,
 'Model, ranked by the lower value (frozen)':TE.low.values}
prev=(w*fail).sum()/w.sum()
rows=[('Random (expected)',.3,prev)]+[(k,*reach(v,w,fail)) for k,v in rules.items()]+[('Maximum possible',min(1,.3/prev),1.)]
R=pd.DataFrame(rows,columns=['rule','failures reached','selected that failed']).round(3)
print('2026 H1 launches: n',len(TE),'| failures',int(fail.sum()),'| re-weighted share failing',round(prev,3)); print(R.to_string(index=False))
# paired bootstrap against each subcategory rule; point estimate = difference on the full sample (not the bootstrap mean)
P25c=P25[pd.to_datetime(P25.deadline, unit='s' if str(P25.deadline.dtype).startswith(('int','float')) else None) < pd.Timestamp('2026-01-01')]
rng=np.random.default_rng(7); mod=TE.low.values
cmp={'2023-24 rule (strongest)':sub24.values,'2023-25 rule':sub25.values}
if P25c is not None:
    cmp['2023-25 rule, outcomes resolved before 1 Jan 2026']=TE.cat_id.map(P25c.groupby('cat_id').success.mean()).fillna(TE.parent_category.map(P25c.groupby('parent_category').success.mean())).values
idx=[rng.integers(0,len(TE),len(TE)) for _ in range(500)]
for name,rule in cmp.items():
    point=reach(mod,w,fail)[0]-reach(rule,w,fail)[0]
    d=np.array([reach(mod[i],w[i],fail[i])[0]-reach(rule[i],w[i],fail[i])[0] for i in idx])
    print('model minus %s: %.3f points of recall (rule reaches %.3f); 95%% paired bootstrap interval %.3f to %.3f'%(name,point,reach(rule,w,fail)[0],*np.percentile(d,[2.5,97.5])))
# the fixed single check-up cut (11.5%, set on 2025) applied to 2026 H1
flag=TE.low.values<0.115
print('single check-up cut 11.5%%: share flagged %.3f (target 0.30) | failures reached %.3f | flagged that failed %.3f'%((w*flag).sum()/w.sum(),(w*fail*flag).sum()/(w*fail).sum(),(w*fail*flag).sum()/(w*flag).sum()))
print('unweighted sample: failures reached by model at 30%%: %.3f'%reach(TE.low.values,np.ones(len(TE)),fail)[0])
R.to_csv('v2/frozen_2026h1.csv',index=False)
