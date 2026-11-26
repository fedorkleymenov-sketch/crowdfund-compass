import pandas as pd, numpy as np
df=pd.read_parquet('all.parquet')
df['L']=pd.to_datetime(df.launched_at,unit='s'); df['D']=pd.to_datetime(df.deadline,unit='s')
pre=df[(df.D<'2025-01-15')&(df.launched_at>1e9)]
print('ended before 2025-01-15, by state'); print(pre.state.value_counts().to_string())
s=(pre.state=='successful').sum(); f=(pre.state=='failed').sum(); c=(pre.state=='canceled').sum()
S=651000*0.4198; F=376698
print('ours succ',s,'failed',f,'canceled',c); print('official succ ~',round(S),'unsuccessful',F)
print('coverage succ',round(s/S,3),'coverage failed (failed only)',round(f/F,3),'(failed+canceled)',round((f+c)/F,3))
print('our rate',round(s/(s+f),3),'official',0.4198)
# 60-day cut for test window
fin=df[df.state.isin(['successful','failed'])]
last=pd.Timestamp('2026-11-16')
print('finished launched within 60d of last scrape',(fin.L>last-pd.Timedelta(days=60)).sum())
print('live rows by launch month'); l=df[df.state=='live']; print(l.groupby(l.L.dt.to_period('M')).size().tail(8).to_string())
# 2026 scrape composition by state
print(df[df.scrape=='2026-11-16'].state.value_counts().to_string())
# tabletop 2024 check vs Kickstarter 80% (5314/6646)
t=fin[(fin.subcategory=='Tabletop Games')&(fin.L.dt.year==2024)]
print('tabletop 2024 ours n',len(t),'succ',(t.state=='successful').sum(),'rate',round((t.state=='successful').mean(),3))
# creators
c=fin.groupby('creator_id').size(); print('share of finished projects by repeat creators',round(c[c>1].sum()/len(fin),3))
print('test first-timers etc later')
