import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',300)
df=pd.read_parquet('all.parquet')
new=df[df.scrape>='2023-12-14']; old=df[df.scrape<'2023-12-14']
print('parent cats in new scrapes',new.parent_category.nunique(), sorted(new.parent_category.unique())[:40])
print('parent cats in old',old.parent_category.nunique())
print('by scrape n parent cats'); print(df.groupby('scrape').parent_category.nunique().to_string())
# mapping subcat->parent in new
mp=new[new.parent_category!=new.subcategory].groupby('subcategory').parent_category.nunique()
print('subcats in new',new.subcategory.nunique(),'ambiguous names (>1 parent):',(mp>1).sum()); print(mp[mp>1].to_string())
amb=mp[mp>1].index
print('old rows total',len(old),'old rows with ambiguous subcat name',old.subcategory.isin(amb).sum(), 'old subcats not in new',(~old.subcategory.isin(new.subcategory.unique())).sum())
fin=df[df.state.isin(['successful','failed'])].copy(); fin['y']=(fin.state=='successful').astype(int)
fin['L']=pd.to_datetime(fin.launched_at,unit='s'); fin['D']=pd.to_datetime(fin.deadline,unit='s'); fin['C']=pd.to_datetime(fin.created_at,unit='s')
fin['ly']=fin.L.dt.year
print('finished with old scrape (video/prelaunch unknown):',(fin.scrape<'2023-12-14').mean().round(4))
print('known-video share by launch year'); print(fin.assign(k=fin.scrape>='2023-12-14').groupby('ly').agg(n=('y','size'),known=('k','mean'),succ_known=('y',lambda s: s[fin.loc[s.index,'scrape']>='2023-12-14'].mean()),succ_unknown=('y',lambda s: s[fin.loc[s.index,'scrape']<'2023-12-14'].mean())).round(3).to_string())
k=fin[fin.scrape>='2023-12-14']
print('video vs success (known)'); print(k.groupby('has_video').y.agg(['size','mean']).round(3))
print('prelaunch vs success'); print(k.groupby(k.prelaunch_activated.astype(str)).y.agg(['size','mean']).round(3))
# sanity
fin['goal_usd']=fin.goal*fin.static_usd_rate; fin['dur']=(fin.deadline-fin.launched_at)/86400; fin['prep']=(fin.launched_at-fin.created_at)/86400
print(fin[['goal','goal_usd','dur','prep','static_usd_rate']].describe(percentiles=[.01,.05,.5,.95,.99]).round(2).to_string())
print('dur>92',(fin.dur>92).sum(),'dur<1',(fin.dur<1).sum(),'prep<0',(fin.prep<0).sum(),'goal<=1usd',(fin.goal_usd<=1).sum(),'goal>=1e7',(fin.goal_usd>=1e7).sum())
print('state consistent w pledged>=goal: succ & pledged<goal',((fin.y==1)&(fin.pledged<fin.goal)).sum(),' failed & pledged>=goal',((fin.y==0)&(fin.pledged>=fin.goal)).sum())
print('deadline after scrape date',(fin.D>pd.to_datetime(fin.scrape)+pd.Timedelta(days=1)).sum())
print('countries'); print(fin.country.value_counts().to_string())
print('2025-26 by month'); print(fin[fin.ly>=2025].groupby(fin.L.dt.to_period('M')).y.agg(['size','mean']).round(3).to_string())
print('split sizes: train<=2023',(fin.ly<=2023).sum(),fin[fin.ly<=2023].y.mean().round(3),'val 2024',(fin.ly==2024).sum(),'test',(fin.ly>=2025).sum(),fin[fin.ly>=2025].y.mean().round(3))
print('dup name+creator',fin.duplicated(['name','creator_id']).sum(),'blurb na',fin.blurb.isna().sum(),'creator na',fin.creator_id.isna().sum())
print('loc_type'); print(fin.loc_type.value_counts(dropna=False).to_string())
print('staff_pick by scrape'); print(fin.groupby('scrape').staff_pick.mean().round(3).to_string())
print('usd_pledged NA by scrape'); print(df.groupby('scrape').usd_pledged.apply(lambda s:s.isna().mean()).round(3).to_string())
print('parent cat (new only) success'); print(k.groupby('parent_category').y.agg(['size','mean']).round(3).to_string())
