import sys,glob,warnings; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, modeling as M
D=M.prepare(pd.read_parquet('v2/features.parquet')); tr=D[D.period.isin(['2023','2024'])].copy()
oof,_,(v,m)=M.text_score(tr,[])
voc=np.array(v.get_feature_names_out()); o=np.argsort(m.coef_[0])
print('TOP +',list(voc[o[-45:]][::-1])); print('TOP -',list(voc[o[:30]]))
# title/blurb edits: campaigns seen LIVE in one scrape and finished in a later one
P=pd.concat([pd.read_parquet(p,columns=['id','scrape','state','name','blurb']) for p in sorted(glob.glob('v2/parts/*.parquet')) if p[-18:-8]>='2019-06-13'],ignore_index=True)
live=P[P.state=='live'].sort_values('scrape').drop_duplicates('id',keep='last')
fin=P[P.state.isin(['successful','failed'])].sort_values('scrape').drop_duplicates('id',keep='last')
j=live.merge(fin,on='id',suffixes=('_live','_fin')); j=j[j.scrape_fin>j.scrape_live]
j['name_changed']=j.name_live.fillna('')!=j.name_fin.fillna(''); j['blurb_changed']=j.blurb_live.fillna('')!=j.blurb_fin.fillna('')
j['len_diff']=j.name_fin.fillna('').str.len()-j.name_live.fillna('').str.len()
print(j.groupby('state_fin').agg(n=('id','size'),name_changed=('name_changed','mean'),blurb_changed=('blurb_changed','mean'),name_len_diff=('len_diff','mean')).round(3))
ex=j[j.name_changed&(j.state_fin=='successful')].sample(12,random_state=1)
for a,b in zip(ex.name_live,ex.name_fin): print('  LIVE:',a,'\n  FIN :',b)
# among finished: do names change between scrapes after the end?
f2=P[P.state.isin(['successful','failed'])].sort_values('scrape'); a=f2.drop_duplicates('id',keep='first'); b=f2.drop_duplicates('id',keep='last')
k=a.merge(b,on='id',suffixes=('_a','_b')); k=k[k.scrape_b>k.scrape_a]
print('finished, first vs last sighting: name changed',k.groupby('state_b').apply(lambda g:(g.name_a.fillna('')!=g.name_b.fillna('')).mean()).round(3).to_dict(),'blurb changed',k.groupby('state_b').apply(lambda g:(g.blurb_a.fillna('')!=g.blurb_b.fillna('')).mean()).round(3).to_dict(),len(k))
j[['id','name_live','blurb_live','state_fin','scrape_live']].to_parquet('v2/live_text.parquet',index=False)
