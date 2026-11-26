import sys, time, warnings, json; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, xgboost as xgb, lightgbm as lgb, optuna, joblib
import features as F, modeling as M
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, confusion_matrix, brier_score_loss
optuna.logging.set_verbosity(optuna.logging.WARNING); pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
BP=joblib.load('v2/best_params.joblib'); OUT={}
D=M.prepare(pd.read_parquet('v2/features.parquet'))
FM=M.numeric_features(with_norms=False); FA=M.numeric_features(with_norms=False,with_presentation=False)   # 33 and 31 features
print('features M',len(FM),'A',len(FA))
def XG(tr,cols,w=None,mono=False,**kw):
    p=dict(BP['best_xgb']); p.update(kw)
    if mono: p['monotone_constraints']=M.monotone(cols)   # beyond class: a lower goal can never lower the chance
    return xgb.XGBClassifier(subsample=.8,colsample_bytree=.8,n_jobs=2,random_state=42,**p).fit(tr[cols],tr.success,sample_weight=w)
def logit_pipe(cols):
    num=[c for c in cols if c not in M.LABELS]
    pre=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()),num),('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),M.LABELS)])
    return make_pipeline(pre,LogisticRegression(C=0.5,max_iter=2000))
def sc(df,p): return {k:round(v,4) for k,v in M.scores(df,p).items()}
def with_text(tr,others):
    tr=tr.copy(); others=[o.copy() for o in others]; oof,sc_,vm=M.text_score(tr,others); tr['text_score']=oof
    for o,s in zip(others,sc_): o['text_score']=s
    return tr,others,vm
P23=D[(D.period=='2023')&D.has_video.notna()]; P24=D[D.period=='2024']; P25=D[D.period=='2025']; P26=D[D.period=='2026H1']
# ---------- (a) validation 2024, trained on 2023: beyond-class model + final candidates
tr,(va,),_=with_text(P23,[P24]); val={}
val['XGBoost (class), 33 features']=sc(va,XG(tr,FM).predict_proba(va[FM])[:,1])
val['Logistic regression, 33 features']=sc(va,logit_pipe(FM).fit(tr[FM],tr.success).predict_proba(va[FM])[:,1])
def objective(t):
    p=dict(n_estimators=t.suggest_int('n_estimators',150,700),learning_rate=t.suggest_float('learning_rate',.01,.15,log=True),num_leaves=t.suggest_int('num_leaves',6,48),
           min_child_samples=t.suggest_int('min_child_samples',20,200),subsample=t.suggest_float('subsample',.6,1),subsample_freq=1,colsample_bytree=t.suggest_float('colsample_bytree',.5,1),reg_lambda=t.suggest_float('reg_lambda',.01,10,log=True))
    s=[]
    for a,b in TimeSeriesSplit(3).split(tr):
        m=lgb.LGBMClassifier(**p,verbose=-1,n_jobs=2,random_state=42).fit(tr[FM].iloc[a],tr.success.iloc[a]); s.append(roc_auc_score(tr.success.iloc[b],m.predict_proba(tr[FM].iloc[b])[:,1]))
    return np.mean(s)
st=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42)); st.optimize(objective,n_trials=30); BL=st.best_params; print('lgbm best',BL,round(st.best_value,4))
LG=lambda t,cols: lgb.LGBMClassifier(**BL,subsample_freq=1,verbose=-1,n_jobs=2,random_state=42).fit(t[cols],t.success)
val['LightGBM + Optuna (beyond class), 33 features']=sc(va,LG(tr,FM).predict_proba(va[FM])[:,1])
print(pd.DataFrame(val).T.to_string()); OUT['val2024']=val
# ---------- (b) A (all years, no video/pre-launch) vs M (2023+), on 2024 and 2025
cmp={}
t0=time.time(); trA,(vaA,),_=with_text(D[D.period.isin(['<=2022','2023'])],[P24]); print('text A s',round(time.time()-t0))
for nm,kw in [('A: all years to 2023 (359k), XGBoost tuned on M',{}),('A: same, deeper (depth 6, 600 trees)',dict(max_depth=6,n_estimators=600,learning_rate=.05))]:
    cmp[('2024',nm)]=sc(vaA,XG(trA,FA,**kw).predict_proba(vaA[FA])[:,1])
cmp[('2024','M: 2023 only (18k), without video/pre-launch')]=sc(va,XG(tr,FA).predict_proba(va[FA])[:,1])
cmp[('2024','M: 2023 only (18k), with video/pre-launch')]=val['XGBoost (class), 33 features']
trA2,(teA,te26A),_=with_text(D[D.period.isin(['<=2022','2023','2024'])],[P25,P26])
mA=XG(trA2,FA,max_depth=6,n_estimators=600,learning_rate=.05); cmp[('2025','A: all years to 2024 (385k), deeper')]=sc(teA,mA.predict_proba(teA[FA])[:,1]); cmp[('2025','A: all years to 2024 (385k), XGBoost tuned on M')]=sc(teA,XG(trA2,FA).predict_proba(teA[FA])[:,1])
TR,(te,te26),VM=with_text(pd.concat([P23,P24]),[P25,P26])
cmp[('2025','M: 2023-24 (44k), without video/pre-launch')]=sc(te,XG(TR,FA).predict_proba(te[FA])[:,1])
plain=XG(TR,FM); final=XG(TR,FM,mono=True); p25=final.predict_proba(te[FM])[:,1]; p26=final.predict_proba(te26[FM])[:,1]
cmp[('2025','M: 2023-24 (44k), with video/pre-launch')]=sc(te,plain.predict_proba(te[FM])[:,1])
C=pd.DataFrame(cmp).T; print(C.to_string()); C.to_csv('v2/A_vs_M.csv'); OUT['A_vs_M']={f'{k[0]} | {k[1]}':v for k,v in cmp.items()}
# ---------- (c) TEST: every model trained on 2023-24, evaluated once on 2025 and 2026H1
Xt=TR[FM].fillna(-1); test={}
def both(nm,f): test[nm]={'2025':sc(te,f(te)),'2026H1':sc(te26,f(te26))}
both('Baseline: always "funded"',lambda d:np.full(len(d),TR.success.mean()))
cr=TR.groupby('cat_id').success.mean(); both('Baseline: category funding rate',lambda d:d.cat_id.map(cr).fillna(TR.success.mean()).values)
lg=logit_pipe(FM).fit(TR[FM],TR.success); both('Logistic regression',lambda d:lg.predict_proba(d[FM])[:,1])
dt=DecisionTreeClassifier(criterion='entropy',random_state=42,**BP['best_tree']).fit(Xt,TR.success); both('Decision tree',lambda d:dt.predict_proba(d[FM].fillna(-1))[:,1])
d3=DecisionTreeClassifier(criterion='entropy',max_depth=3,min_samples_leaf=200,random_state=42).fit(Xt,TR.success); both('Decision tree, depth 3 (app explanation)',lambda d:d3.predict_proba(d[FM].fillna(-1))[:,1])
rf=RandomForestClassifier(n_estimators=300,n_jobs=2,random_state=42,**BP['best_rf']).fit(Xt,TR.success); both('Random forest',lambda d:rf.predict_proba(d[FM].fillna(-1))[:,1])
both('XGBoost (grid search)',lambda d:plain.predict_proba(d[FM])[:,1])
both('XGBoost + goal rule (final model)',lambda d:final.predict_proba(d[FM])[:,1])
lgbm=LG(TR,FM); both('LightGBM + Optuna (beyond class)',lambda d:lgbm.predict_proba(d[FM])[:,1])
k6=XG(TR,M.KAGGLE6); both('XGBoost, 6 Kaggle-style features',lambda d:k6.predict_proba(d[M.KAGGLE6])[:,1])
T=pd.concat({y:pd.DataFrame({k:v[y] for k,v in test.items()}).T for y in ['2025','2026H1']}); print(T.to_string()); T.to_csv('v2/test_table.csv'); OUT['test']=test
# ---------- (d) calibration: Platt scaling learned on 2024 (model trained on 2023 with the same settings)
twin=XG(tr,FM,mono=True); z=lambda p:np.log(np.clip(p,1e-6,1-1e-6)/(1-np.clip(p,1e-6,1-1e-6)))
cal=LogisticRegression(C=1e6).fit(z(twin.predict_proba(va[FM])[:,1]).reshape(-1,1),va.success)
c25=cal.predict_proba(z(p25).reshape(-1,1))[:,1]; c26=cal.predict_proba(z(p26).reshape(-1,1))[:,1]
print('Platt a,b',cal.coef_[0][0].round(3),cal.intercept_[0].round(3),'| Brier 2025 raw',round(brier_score_loss(te.success,p25),4),'calibrated',round(brier_score_loss(te.success,c25),4),'| 2026H1 raw',round(brier_score_loss(te26.success,p26),4),'cal',round(brier_score_loss(te26.success,c26),4))
print('mean predicted vs actual 2025: raw',p25.mean().round(3),'cal',c25.mean().round(3),'actual',te.success.mean().round(3),'| 2026H1 raw',p26.mean().round(3),'actual',te26.success.mean().round(3))
bins=pd.cut(p25,np.linspace(0,1,11)); rel=pd.DataFrame({'p':p25,'y':te.success.values}).groupby(bins,observed=True).agg(n=('y','size'),predicted=('p','mean'),actual=('y','mean')).round(3); print(rel.to_string()); rel.to_csv('v2/reliability_2025.csv')
OUT['calibration']={'brier_raw_2025':float(brier_score_loss(te.success,p25)),'brier_cal_2025':float(brier_score_loss(te.success,c25))}
# ---------- (e) confusion matrix, by parent, capped vs rest (2025)
te=te.assign(p=p25); te26=te26.assign(p=p26)
print('confusion 2025 [rows actual failed/funded; cols predicted failed/funded]',confusion_matrix(te.success,(te.p>=.5).astype(int)).tolist())
bp=te.groupby('parent_category').apply(lambda g:pd.Series({'n':len(g),'funded in sample':g.success.mean(),'AUC within category':M.auc_within(g.success,g.p,g.cat_id),'AUC':roc_auc_score(g.success,g.p)})).round(3); print(bp.to_string()); bp.to_csv('v2/by_parent_2025.csv')
for nm,d in [('2025',te),('2026H1',te26)]:
    for c in [1,0]:
        g=d[d.capped_category==c]; print(nm,'capped' if c else 'other ','n',len(g),'funded',round(g.success.mean(),3),'AUC within category',round(M.auc_within(g.success,g.p,g.cat_id),4))
# ---------- (f) business metric: the coach helps the riskiest 30%
def reach(d,p,share=.3):
    k=int(len(d)*share); idx=np.argsort(p)[:k]; return d.success.values[idx].__rsub__(1).sum()/(1-d.success).sum()
for nm,d in [('2025',te),('2026H1',te26)]:
    base=d.cat_id.map(cr).fillna(TR.success.mean()).values
    print(nm,'failures reached in riskiest 30%: model',round(reach(d,d.p.values),3),'| category-rate baseline',round(reach(d,base+np.random.default_rng(0).uniform(0,1e-6,len(d))),3),'| 6 features',round(reach(d,k6.predict_proba(d[M.KAGGLE6])[:,1]),3),'| random 0.30 | failures',int((1-d.success).sum()))
    # within-category version: riskiest 30% inside each category
    r=d.groupby('cat_id').p.rank(pct=True); print('   inside each category:',round(((r<=.3)&(d.success==0)).sum()/(d.success==0).sum(),3))
# ---------- (g) level correction to the official rates per parent category
s=TR.groupby('parent_category').success.mean().to_dict()
te['p_sample']=c25; te['p_official']=M.prior_shift(c25,te.parent_category.values,s)
lv=te.groupby('parent_category').agg(n=('success','size'),sample_actual=('success','mean'),mean_p_sample=('p_sample','mean'),mean_p_official=('p_official','mean')).round(3); lv['official']=pd.Series(M.OFFICIAL_RATE); lv['train_sample_rate']=pd.Series(s).round(3); print(lv.to_string()); lv.to_csv('v2/levels_2025.csv')
print('all: sample mean p',te.p_sample.mean().round(3),'| corrected mean p',te.p_official.mean().round(3),'| median width of range',np.median(te.p_sample-te.p_official).round(3))
# down-weighting alternative: weight failures so the weighted training rate per parent equals the official rate
w=np.where(TR.success==0,TR.parent_category.map(lambda c:(s[c]/(1-s[c]))/(M.OFFICIAL_RATE[c]/(1-M.OFFICIAL_RATE[c]))),1.)
mw=XG(TR,FM,w=w,mono=True); pw=mw.predict_proba(te[FM])[:,1]
print('weighted model: AUC within category',round(M.auc_within(te.success,pw,te.cat_id),4),'| mean p',pw.mean().round(3),'| mean |weighted - shifted|',np.abs(pw-te.p_official).mean().round(3),'| corr',np.corrcoef(pw,te.p_official)[0,1].round(3))
# ---------- save
joblib.dump({'model':final,'features':FM,'tfidf':VM[0],'text_lr':VM[1],'platt':cal,'sample_rate':s,'tree3':d3,'logit':lg},'v2/models_M.joblib')
te[['id','success','p','p_sample','p_official','cat_id','parent_category','capped_category']].to_parquet('v2/test2025_pred.parquet'); json.dump(OUT,open('v2/stage2.json','w'),default=float)
imp=pd.Series(final.get_booster().get_score(importance_type='gain')).sort_values(ascending=False); print((imp/imp.sum()).round(3).head(15).to_string())
