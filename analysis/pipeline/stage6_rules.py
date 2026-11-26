# Equal-capacity comparison of the model with simple rules, 2025 re-weighted to Kickstarter's official mix (25.11.2026)
import sys, warnings; sys.path.insert(0,'/home/claude/crowdfund-compass/app'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, modeling as M, advice as A
ART=joblib.load('v2/models_M.joblib'); adv=A.Advisor(ART)
D=M.prepare(pd.read_parquet('v2/features.parquet'))
TR=D[D.period.isin(['2023','2024'])&D.has_video.notna()].copy(); TE=D[D.period=='2025'].copy()
oof,(ts,),_=M.text_score(TR,[TE]); TE['text_score']=ts
lo,hi=adv.chances(TE); TE['low']=lo; TE['high']=hi
s25=TE.groupby('parent_category').success.mean()
w=np.where(TE.success==0,TE.parent_category.map(lambda c:(s25[c]/(1-s25[c]))/(M.OFFICIAL_RATE[c]/(1-M.OFFICIAL_RATE[c]))),1.)
fail=(1-TE.success.values)
def reach(score, share=.3):
    """Take the lowest scores until `share` of the (weighted) cohort is selected; ties at the cutoff are taken proportionally."""
    s=np.asarray(score,float); tot=w.sum(); cap=share*tot; sel_w=0; sel_f=0
    for v in np.unique(s):
        m=s==v; gw=w[m].sum(); gf=(w*fail)[m].sum()
        take=min(1,(cap-sel_w)/gw) if gw>0 else 0
        if take<=0: break
        sel_w+=gw*take; sel_f+=gf*take
        if take<1: break
    return sel_f/(w*fail).sum(), sel_f/sel_w
P=D[D.period.isin(['2023','2024'])]
cat_rate=P.groupby('cat_id').success.mean(); par_rate=P.groupby('parent_category').success.mean()
rules={'Random (expected)':None,
 "Lowest official main-category rate first":TE.parent_category.map(M.OFFICIAL_RATE),
 'Lowest 2023-24 main-category rate in our data first':TE.parent_category.map(par_rate),
 'Lowest 2023-24 subcategory rate in our data first':TE.cat_id.map(cat_rate).fillna(TE.parent_category.map(par_rate)),
 'Lowest 2023-24 subcategory rate, outcomes resolved before 1 Jan 2025':TE.cat_id.map(P[pd.to_datetime(P.deadline,unit='s')<pd.Timestamp('2025-01-01')].groupby('cat_id').success.mean()).fillna(TE.parent_category.map(par_rate)),
 'Goal relative to the category (highest goal ratio first)':-TE.goal_ratio,
 'Model, ranked by the lower value':TE.low}
rows=[]
for k,v in rules.items():
    if v is None: rows.append((k,0.300,(w*fail).sum()/w.sum()))
    else: a,b=reach(v); rows.append((k,a,b))
mx=min(1,.3/((w*fail).sum()/w.sum())); rows.append(('Perfect ranking (maximum possible)',mx,1.0))
R=pd.DataFrame(rows,columns=['rule','share of all failures reached','share of selected teams that failed']).round(3)
print('2025 test year, n =',len(TE),'| failures',int(fail.sum()),'| re-weighted share failing',round((w*fail).sum()/w.sum(),3)); print(R.to_string(index=False))
R.to_csv('v2/rules_vs_model_2025.csv',index=False)
# per 100 campaigns
print('failures found per 100 campaigns at 30% capacity:',{r:round(a*(w*fail).sum()/w.sum()*100,1) for r,a,b in rows})
