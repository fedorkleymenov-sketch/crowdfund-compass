import sys, time; sys.path.insert(0,'/home/claude/work')
import features as F, pandas as pd
t=time.time(); raw=pd.read_parquet('/home/claude/work/v2/kickstarter_merged_v2.parquet')
X,tabs=F.build_features(raw); print('seconds',round(time.time()-t))
X.to_parquet('/home/claude/work/v2/features.parquet',index=False); tabs['category'].to_parquet('/home/claude/work/v2/cat_table.parquet',index=False)
feats=[f for g in F.GROUPS.values() for f in g]; print(len(feats),'features'); print(X[[f for f in feats if f not in('parent_category','country')]].describe().T[['count','mean','min','50%','max']].round(3).to_string())
