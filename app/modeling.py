"""modeling.py — Crowdfund Compass, shared modelling helpers (Group 11)."""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, f1_score, brier_score_loss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
import features as F

PARENTS = ['Art', 'Comics', 'Crafts', 'Dance', 'Design', 'Fashion', 'Film & Video', 'Food', 'Games', 'Journalism',
           'Music', 'Photography', 'Publishing', 'Technology', 'Theater']
COUNTRIES = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'IT', 'HK', 'ES', 'MX', 'NL', 'SE', 'JP', 'SG', 'NZ', 'DK', 'CH',
             'PL', 'IE', 'BE', 'AT', 'NO', 'GR', 'SI', 'LU']
# Kickstarter's official all-time success rate per parent category (stats page, last updated 01.01.2026)
OFFICIAL_RATE = {'Games': .5229, 'Technology': .2490, 'Design': .4461, 'Film & Video': .3826, 'Publishing': .4001,
                 'Comics': .6884, 'Music': .5051, 'Fashion': .3139, 'Art': .4943, 'Food': .2578, 'Photography': .3643,
                 'Theater': .5958, 'Crafts': .2772, 'Journalism': .2373, 'Dance': .6089}
LABELS = ['cat_id', 'parent_c', 'country_c']
NORMS = ['cat_rate_12m', 'cat_trend', 'log_cat_n_12m']
PRESENTATION = ['has_video', 'prelaunch_activated']
# Beyond class: the model may only learn that a higher goal lowers the chance of funding, never the opposite.
GOAL_MONOTONE = {'log_goal_usd': -1, 'goal_ratio': -1, 'log_goal_per_day': -1}

def monotone(features):
    return '(' + ','.join(str(GOAL_MONOTONE.get(f, 0)) for f in features) + ')'

KAGGLE6 = ['cat_id', 'parent_c', 'country_c', 'log_goal_usd', 'duration_days', 'launch_month', 'name_len']

def prepare(X):
    """Add label codes and the test-window flags. Same function for training data and app inputs."""
    X = X.copy()
    X['parent_c'] = X.parent_category.map({p: i for i, p in enumerate(PARENTS)})
    X['country_c'] = X.country.map({c: i for i, c in enumerate(COUNTRIES)}).fillna(-1)
    X['text'] = X.name.fillna('') + ' . ' + X.blurb.fillna('')
    X['period'] = np.select([X.launch_year <= 2022, X.launch_year == 2023, X.launch_year == 2024, X.launch_year == 2025,
                             X.launch < '2026-07-01'], ['<=2022', '2023', '2024', '2025', '2026H1'], 'drop')
    return X[X.period != 'drop'].sort_values('launched_at').reset_index(drop=True)

def numeric_features(with_presentation=True, with_norms=True, with_text=True):
    cols = [f for g, v in F.GROUPS.items() for f in v if f not in ('cat_id', 'parent_category', 'country')]
    if not with_presentation: cols = [c for c in cols if c not in PRESENTATION]
    if not with_norms: cols = [c for c in cols if c not in NORMS]
    return LABELS + cols + (['text_score'] if with_text else [])

def auc_within(y, p, groups):
    """AUC computed inside each group, averaged with the group size as weight."""
    d = pd.DataFrame({'y': np.asarray(y), 'p': np.asarray(p), 'g': np.asarray(groups)})
    tot = w = 0
    for _, g in d.groupby('g'):
        if g.y.nunique() == 2:
            tot += roc_auc_score(g.y, g.p) * len(g); w += len(g)
    return tot / w

def scores(df, p, thr=0.5):
    y = df.success.values; yhat = (p >= thr).astype(int)
    return {'AUC within category': auc_within(y, p, df.cat_id), 'AUC within parent': auc_within(y, p, df.parent_category),
            'AUC overall': roc_auc_score(y, p), 'accuracy': accuracy_score(y, yhat),
            'precision': precision_score(y, yhat, zero_division=0), 'recall': recall_score(y, yhat),
            'F1': f1_score(y, yhat), 'Brier': brier_score_loss(y, p)}

def text_score(train, others, seed=42):
    """Text mining (class): TF-IDF on title + blurb, then a logistic regression. Returns one number per campaign:
    how much its wording looks like funded campaigns. Training rows get out-of-fold scores (each row is scored by
    a model that never saw it), so the score does not leak the row's own outcome."""
    def make():
        return (TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_features=30000, sublinear_tf=True, strip_accents='unicode'),
                LogisticRegression(C=1.0, max_iter=300))
    oof = np.zeros(len(train))
    for a, b in KFold(5, shuffle=True, random_state=seed).split(train):
        v, m = make(); m.fit(v.fit_transform(train.text.iloc[a]), train.success.iloc[a])
        oof[b] = m.decision_function(v.transform(train.text.iloc[b]))
    v, m = make(); m.fit(v.fit_transform(train.text), train.success)
    return oof, [m.decision_function(v.transform(o.text)) for o in others], (v, m)

def prior_shift(p, parent, sample_rate):
    """Level correction (beyond class): move the odds by the gap between the funded rate in our sample and
    Kickstarter's official rate for the parent category."""
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4); out = np.empty_like(p)
    for c in np.unique(parent):
        k = np.asarray(parent) == c; pi = OFFICIAL_RATE[c]; s = sample_rate[c]
        odds = p[k] / (1 - p[k]) * (pi / (1 - pi)) / (s / (1 - s))
        out[k] = odds / (1 + odds)
    return out
