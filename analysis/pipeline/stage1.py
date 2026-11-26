import sys, time, warnings; sys.path.insert(0,'/home/claude/work'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, xgboost as xgb, joblib
import features as F, modeling as M
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
pd.set_option('display.width',250)
D=M.prepare(pd.read_parquet('v2/features.parquet')); print(D.period.value_counts().to_dict())
tr=D[D.period=='2023'].copy(); va=D[D.period=='2024'].copy()
tr=tr[tr.has_video.notna()]
t=time.time(); tr['text_score'],(va['text_score'],),_=M.text_score(tr,[va]); print('text score s',round(time.time()-t))
FULL=M.numeric_features(); rows={}
def add(name,p): rows[name]=M.scores(va,p); print(name,{k:round(v,3) for k,v in rows[name].items()},flush=True)
# 1 baselines
add('Baseline: always "funded"',np.full(len(va),tr.success.mean()))
cr=tr.groupby('cat_id').success.mean(); add('Baseline: category funding rate',va.cat_id.map(cr).fillna(tr.success.mean()).values)
add('Text only (TF-IDF + logistic)',1/(1+np.exp(-va.text_score.values)))
# 2 class models
tscv=TimeSeriesSplit(n_splits=3)
num=[c for c in FULL if c not in M.LABELS]
pre=ColumnTransformer([('num',make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()),num),('cat',OneHotEncoder(handle_unknown='ignore',min_frequency=20),M.LABELS)])
logit=make_pipeline(pre,LogisticRegression(C=0.5,max_iter=2000)).fit(tr[FULL],tr.success); add('Logistic regression',logit.predict_proba(va[FULL])[:,1])
Xt=tr[FULL].fillna(-1); Xv=va[FULL].fillna(-1)
g=GridSearchCV(DecisionTreeClassifier(criterion='entropy',random_state=42),{'max_depth':[3,5,7,9,12],'min_samples_leaf':[20,50,100,200]},cv=tscv,scoring='roc_auc').fit(Xt,tr.success)
print('tree best',g.best_params_); add('Decision tree (grid search)',g.predict_proba(Xv)[:,1]); best_tree=g.best_params_
t3=DecisionTreeClassifier(criterion='entropy',max_depth=3,min_samples_leaf=200,random_state=42).fit(Xt,tr.success); add('Decision tree, depth 3 (for the app)',t3.predict_proba(Xv)[:,1])
g=GridSearchCV(RandomForestClassifier(n_estimators=300,n_jobs=2,random_state=42),{'max_depth':[10,None],'min_samples_leaf':[5,20]},cv=tscv,scoring='roc_auc').fit(Xt,tr.success)
print('rf best',g.best_params_); add('Random forest (grid search)',g.predict_proba(Xv)[:,1]); best_rf=g.best_params_
g=GridSearchCV(xgb.XGBClassifier(subsample=.8,colsample_bytree=.8,n_jobs=2,random_state=42),{'max_depth':[3,5,7],'learning_rate':[.03,.1],'n_estimators':[200,400]},cv=tscv,scoring='roc_auc').fit(tr[FULL],tr.success)
print('xgb best',g.best_params_); add('XGBoost (grid search)',g.predict_proba(va[FULL])[:,1]); best_xgb=g.best_params_
def xg(cols,train=tr,w=None): return xgb.XGBClassifier(subsample=.8,colsample_bytree=.8,n_jobs=2,random_state=42,**best_xgb).fit(train[cols],train.success,sample_weight=w)
# feature-set variants (same XGBoost)
for nm,cols in [('XGBoost without category norms',M.numeric_features(with_norms=False)),('XGBoost without text score',M.numeric_features(with_text=False)),
                ('XGBoost without video / pre-launch',M.numeric_features(with_presentation=False)),('XGBoost, 6 Kaggle-style features',M.KAGGLE6)]:
    add(nm,xg(cols).predict_proba(va[cols])[:,1])
R=pd.DataFrame(rows).T.round(3); print(R.to_string()); R.to_csv('v2/stage1_val2024.csv')
joblib.dump({'best_tree':best_tree,'best_rf':best_rf,'best_xgb':best_xgb},'v2/best_params.joblib')
# category norms on a second, non-test split: train 2021-22 -> 2023 (no presentation features)
D2=D[D.launch_year.isin([2021,2022,2023])].copy(); a=D2[D2.launch_year<=2022].copy(); b=D2[D2.launch_year==2023].copy()
a['text_score'],(b['text_score'],),_=M.text_score(a,[b])
for nm,cols in [('2021-22 -> 2023 with norms',M.numeric_features(with_presentation=False)),('2021-22 -> 2023 without norms',M.numeric_features(with_presentation=False,with_norms=False))]:
    p=xg(cols,a).predict_proba(b[cols])[:,1]; print(nm,round(M.auc_within(b.success,p,b.cat_id),4),round(M.auc_within(b.success,p,b.parent_category),4))
