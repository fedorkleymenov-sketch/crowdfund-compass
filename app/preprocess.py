"""preprocess.py — Crowdfund Compass app: turns the inputs for ONE planned campaign into the model's features.
It reuses the same functions as the training code (features.py, modeling.py), so training and app agree."""
import json, os
import numpy as np, pandas as pd, joblib, xgboost as xgb
import features as F, modeling as M

HERE = os.path.dirname(os.path.abspath(__file__))

def load_artifacts(folder=None):
    folder = folder or os.path.join(HERE, 'models')
    meta = json.load(open(os.path.join(folder, 'meta.json')))
    model = xgb.XGBClassifier(); model.load_model(os.path.join(folder, 'model.json'))
    text = joblib.load(os.path.join(folder, 'text_model.joblib'))          # TF-IDF + logistic regression
    art = {'model': model, 'features': meta['features'], 'platt': meta['platt'], 'sample_rate': meta['sample_rate'],
           'area_reference': {k: np.array(v) for k, v in meta['area_reference'].items()}, 'verdict': meta['verdict']}
    return art, meta, text

def campaign_features(c, meta, text):
    """c: dict with the app inputs. Returns a one-row DataFrame with every model feature plus helper columns."""
    launch = pd.Timestamp(c['launch_date']); goal = float(c['goal_usd']); dur = float(c['duration_days'])
    cat = meta['categories'][str(c['cat_id'])]; parent = cat['parent']
    med = cat.get('median_goal') or meta['parent_median_goal'][parent]        # median goal of recent campaigns in the category
    r = {'goal_usd': goal, 'launch': launch, 'parent_category': parent, 'name': c['name'], 'blurb': c['blurb'],
         'cat_id': int(c['cat_id']), 'parent_c': M.PARENTS.index(parent),
         'country_c': M.COUNTRIES.index(c['country']) if c['country'] in M.COUNTRIES else -1,
         # Ambition
         'duration_days': dur, 'log_goal_usd': np.log10(max(goal, 1)), 'log_goal_per_day': np.log10(max(goal / max(dur, 1), .1)),
         'goal_ratio': np.log10(max(goal, 1) / max(med, 1)),
         'goal_is_round': int(np.isclose((goal / 10 ** np.floor(np.log10(max(goal, 1)))) % 0.5, 0)),
         # Timing
         'launch_month': launch.month, 'launch_weekday': launch.weekday(),
         'holiday_window': int(launch <= pd.Timestamp(launch.year, 12, 25) <= launch + pd.Timedelta(days=dur)),
         'log_prep_days': np.log10(max(float(c['prep_days']), 0) + 1),
         # Founder
         'creator_prior_n': float(c['prior_n']), 'creator_prior_funded': float(c['prior_funded']),
         'creator_prior_rate': (c['prior_funded'] / c['prior_n']) if c['prior_n'] > 0 else np.nan,
         'first_timer': int(c['prior_n'] == 0),
         'log_days_since_last': np.log10(float(c['days_since_last']) + 1) if c['prior_n'] > 0 else np.nan,
         # Presentation
         'has_video': float(c['has_video']), 'prelaunch_activated': float(c['prelaunch'])}
    X = pd.DataFrame([r])
    X = pd.concat([X, F.text_features(X.name, X.blurb)], axis=1)                 # Pitch features (same function as in training)
    tfidf, lr = text
    X['text_score'] = lr.decision_function(tfidf.transform(X.name.fillna('') + ' . ' + X.blurb.fillna('')))   # product-type score
    return X
