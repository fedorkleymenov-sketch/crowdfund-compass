# Recompute the "what to change" figures with gains measured on the middle estimate (25.11.2026), same sample as stage4.py
import sys, warnings; sys.path.insert(0,'/home/claude/crowdfund-compass/app'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, modeling as M, advice as A
ART=joblib.load('v2/models_M.joblib')
D=M.prepare(pd.read_parquet('v2/features.parquet'))
TR=D[D.period.isin(['2023','2024'])&D.has_video.notna()].copy(); TE=D[D.period=='2025'].copy()
oof,(ts,),_=M.text_score(TR,[TE]); TR['text_score']=oof; TE['text_score']=ts
ART['verdict']={'reference_cut':0.115,'adjust_gain':5.0,'default_capacity':0.30}
adv=A.Advisor(ART)
lo,hi=adv.chances(TE); TE['low']=lo; TE['high']=hi
smp=TE.sample(4000,random_state=7); res=[(i,adv.fixes(r)) for i,r in smp.iterrows()]
best=pd.DataFrame([{'i':i,'lever':fx[0]['lever'] if fx else 'none','gain':fx[0]['gain'] if fx else 0} for i,fx in res]).set_index('i')
print('top fix by lever (share of campaigns):'); print(best.lever.value_counts(normalize=True).round(3).to_string())
print('best fix gain: median',round(best.gain.median(),1),'| share with no change >=2',round((best.lever=='none').mean(),3),'| >=5',round((best.gain>=5).mean(),3),'| >=10',round((best.gain>=10).mean(),3))
allfx=pd.DataFrame([dict(f,i=i) for i,fx in res for f in fx]); print('gain when the lever is offered (points of the middle estimate):'); print(allfx.groupby('lever').gain.agg(['size','median','max']).round(1).to_string())
smp=smp.join(best); smp['risky']=smp.low<0.115
smp['verdict']=np.select([smp.risky,smp.gain>=5],['Coach first','Adjust'],'Launch')
print(smp.groupby('verdict').agg(n=('success','size'),share=('success',lambda s:len(s)/len(smp)),funded_in_sample=('success','mean')).round(3).to_string())
for g in (3,5,8,10): print('adjust threshold',g,'-> Adjust share among non-coach',round(((~smp.risky)&(smp.gain>=g)).sum()/(~smp.risky).sum(),3))
# endpoint order: how often is the official-rate estimate the HIGHER one?
o,f=adv.estimates(TE); TE['off_higher']=f>o
print('official estimate higher than ours: share of 2025 campaigns',round(TE.off_higher.mean(),3)); print(TE.groupby('parent_category').off_higher.mean().round(2)[lambda s:s>0].to_string())
