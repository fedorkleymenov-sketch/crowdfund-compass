# Stronger simple rules at equal coach capacity (26.11.2026, after the independent examiner review).
#
# Why: the simple rules in stage6_rules.py and stage7_frozen2026.py only look at the category or the goal.
# A coach's own rule of thumb looks at the team: first campaign? pre-launch page? large goal?
# This script adds that rule and a one-page scorecard, with the SAME weighting, capacity and tie rule as stage6/stage7.
#
# It needs no raw data: it runs on app/models/similar.parquet (all 83,427 training and test campaigns) and meta.json.
#   python notebooks/stage8_simple_rules.py
# The model's own figures cannot be recomputed here (its per-campaign predictions need the raw data);
# they are copied from stage6_rules.py (2025) and stage7_frozen2026.py (January-June 2026).
import os, json, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, '..', 'app', 'models')
D = pd.read_parquet(os.path.join(MODELS, 'similar.parquet'))
OFFICIAL = json.load(open(os.path.join(MODELS, 'meta.json')))['official_rate']
MODEL_REPORTED = {2025: 0.511, 2026: 0.511}          # from stage6_rules.py and stage7_frozen2026.py
CAPACITY = 0.30

D['parent_category'] = D.parent_category.astype(str)
D['no_prelaunch'] = (D.prelaunch_activated == 0).astype(int)
D['big_goal'] = (D.goal_usd > 10000).astype(int)       # about where the explanation tree of notebook 04 splits ($10,000-13,000)
TRAIN = D[D.launch_year.isin([2023, 2024])].copy()      # the same training years as the model

def logit(p):
    p = np.clip(p, 1e-3, 1 - 1e-3); return np.log(p / (1 - p))

def official_mix_weights(te):
    """Same re-weighting as stage6/stage7: each failed campaign counts more, so every main category has Kickstarter's official share of failures."""
    s = te.groupby('parent_category').success.mean()
    return np.where(te.success == 0, te.parent_category.map(lambda c: (s[c] / (1 - s[c])) / (OFFICIAL[c] / (1 - OFFICIAL[c]))), 1.).astype(float)

def reach(score, w, fail, share=CAPACITY):
    """Take the lowest scores until `share` of the weighted cohort is selected; ties at the cut-off are taken proportionally.
    Returns (share of all failures reached, share of the selected teams that failed)."""
    u, inv = np.unique(np.asarray(score, float), return_inverse=True)
    gw = np.bincount(inv, weights=w, minlength=len(u)); gf = np.bincount(inv, weights=w * fail, minlength=len(u))
    cap = share * w.sum(); cw = np.cumsum(gw); k = int(np.searchsorted(cw, cap, side='left'))
    before = cw[k - 1] if k > 0 else 0.
    take = min(1., (cap - before) / gw[k]) if k < len(u) else 0.
    sel_f = gf[:k].sum() + (gf[k] * take if k < len(u) else 0.)
    return sel_f / (w * fail).sum(), sel_f / cap

# ---- the rules, all fitted on 2023-24 launches only
cat_rate = TRAIN.groupby('cat_id').success.mean(); par_rate = TRAIN.groupby('parent_category').success.mean()
def subcategory_rate(x):
    return x.cat_id.map(cat_rate).fillna(x.parent_category.map(par_rate)).values
QUESTIONS = ['first_timer', 'no_prelaunch', 'big_goal']
TRAIN['sub_logit'] = logit(subcategory_rate(TRAIN))
card = LogisticRegression(C=1e6, max_iter=1000).fit(TRAIN[['sub_logit'] + QUESTIONS], TRAIN.success)
print('Scorecard (logistic regression on 2023-24): points on the log-odds scale')
print('  subcategory rate (log-odds) x %.2f | first campaign %.2f | no pre-launch page %.2f | goal above $10,000 %.2f | start %.2f'
      % (*card.coef_[0], card.intercept_[0]))

rng = np.random.default_rng(7)
for year, label in ((2025, '2025 launches'), (2026, 'January-June 2026 launches')):
    te = D[D.launch_year == year].copy(); w = official_mix_weights(te); fail = 1 - te.success.values.astype(float)
    prev = (w * fail).sum() / w.sum()
    sub = subcategory_rate(te); te['sub_logit'] = logit(sub)
    rules = {
        'Lowest official main-category rate first': te.parent_category.map(OFFICIAL).values,
        'Highest goal in USD first': -te.log_goal_usd.values,
        'Lowest 2023-24 subcategory rate first (best category rule)': sub,
        'Three yes/no questions (first campaign, no pre-launch page, goal above $10,000)': -(te[QUESTIONS].sum(axis=1)).values,
        'Scorecard: subcategory rate + the three questions': card.predict_proba(te[['sub_logit'] + QUESTIONS])[:, 1],
    }
    rows = [('Random (expected)', CAPACITY, prev)] + [(k, *reach(v, w, fail)) for k, v in rules.items()]
    rows += [('Our model, ranked by the lower value (from stage6/stage7, needs raw data)', MODEL_REPORTED[year], MODEL_REPORTED[year] * prev / CAPACITY),
             ('Maximum possible', min(1, CAPACITY / prev), 1.)]
    R = pd.DataFrame(rows, columns=['rule', 'failures reached', 'selected that failed'])
    R['failing teams found per 100'] = (R['failures reached'] * prev * 100).round(1)
    print('\n%s: n = %d | failures %d | re-weighted share failing %.3f' % (label, len(te), int(fail.sum()), prev))
    print(R.round(3).to_string(index=False))
    # paired bootstrap, scorecard minus the best category rule (campaigns resampled; rules and weights held fixed)
    a = rules['Scorecard: subcategory rate + the three questions']; b = sub
    point = reach(a, w, fail)[0] - reach(b, w, fail)[0]
    d = np.array([reach(a[i], w[i], fail[i])[0] - reach(b[i], w[i], fail[i])[0] for i in (rng.integers(0, len(te), len(te)) for _ in range(1000))])
    print('scorecard minus best category rule: %+.3f (95%% paired bootstrap %+.3f to %+.3f) | reported model minus scorecard: %+.3f'
          % (point, *np.percentile(d, [2.5, 97.5]), MODEL_REPORTED[year] - reach(a, w, fail)[0]))
