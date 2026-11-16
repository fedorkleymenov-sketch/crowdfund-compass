"""features.py — Crowdfund Compass, shared feature module (Group 11).

One place that turns the merged Kickstarter table into model features.
Rule for every feature: it only uses what a founder knows BEFORE launch.
History features (category norms, creator track record) only use campaigns
that ENDED before the first day of the campaign's launch month (category
tables) or before the launch itself (creator).

Dropped on 16.11.2026: title capitalisation (`name_caps_share`), which made the Pitch score depend on Title Case.
Dropped on 16.11.2026 after the Phase 2 check: the three crowding features and
city size (no signal inside a category; crowding mostly reflected scraper coverage).

Use:
    import features as F
    raw = F.load_merged(path)            # the merged_v2 parquet parts
    X, tables = F.build_features(raw)    # X: one row per finished project; tables: small lookup tables for the app
"""
import glob, re
import numpy as np
import pandas as pd

DAY = 86400
LAST_SCRAPE = pd.Timestamp('2026-11-16')
# Categories whose listing sits at Kickstarter's cap (>= 2,150 projects listed in the 2025-12-18 scrape).
# In these, failed campaigns are under-covered most. Used for reporting and sample weights, never as a feature.
CAPPED_CAT_IDS = [28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 46, 47, 48, 50, 53, 250, 263, 280, 285, 311, 312, 313]
MIN_PRIOR = 20          # minimum prior campaigns for a category norm; else fall back to the parent category

GROUPS = {
    'Ambition':      ['log_goal_usd', 'goal_ratio', 'log_goal_per_day', 'duration_days', 'goal_is_round'],
    'Timing':        ['launch_month', 'launch_weekday', 'holiday_window', 'log_prep_days'],
    'Pitch':         ['name_len', 'name_words', 'blurb_len', 'blurb_words', 'name_has_digit', 'name_has_symbol',
                      'blurb_flesch', 'blurb_sentiment', 'kw_exclaim', 'kw_you', 'kw_we', 'kw_new_first'],
    'Founder':       ['creator_prior_n', 'creator_prior_funded', 'creator_prior_rate', 'first_timer', 'log_days_since_last'],
    'Presentation':  ['has_video', 'prelaunch_activated'],          # modern model (launches 2023+) only
    'Market':        ['cat_id', 'parent_category', 'country', 'cat_rate_12m', 'cat_trend', 'log_cat_n_12m'],
}

def load_merged(path):
    files = sorted(glob.glob(path + '/kickstarter_merged_v2_part*.parquet'))
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

# ---------------------------------------------------------------- text helpers
_VOWELS = re.compile(r'[aeiouy]+')
def _syllables(word):
    return max(1, len(_VOWELS.findall(word.lower())))

def flesch(text):
    """Flesch reading ease: higher = easier to read (about 60-70 is plain English)."""
    words = re.findall(r"[A-Za-z']+", text)
    if len(words) < 3: return np.nan
    sentences = max(1, len(re.findall(r'[.!?]+', text)))
    syl = sum(_syllables(w) for w in words)
    return 206.835 - 1.015 * len(words) / sentences - 84.6 * syl / len(words)

def text_features(name, blurb):
    """Pitch features from the title and the blurb (two pandas Series of text)."""
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()
    name = name.fillna('').astype(str); blurb = blurb.fillna('').astype(str)
    low = blurb.str.lower()
    out = pd.DataFrame(index=name.index)
    out['name_len'] = name.str.len()
    out['name_words'] = name.str.split().str.len()
    out['blurb_len'] = blurb.str.len()
    out['blurb_words'] = blurb.str.split().str.len()
    out['name_has_digit'] = name.str.contains(r'\d').astype(int)
    out['name_has_symbol'] = name.str.contains(r'[!?:&|\-–—]').astype(int)
    letters = name.str.count(r'[A-Za-z]').replace(0, np.nan)
    out['name_caps_share'] = (name.str.count(r'[A-Z]') / letters).fillna(0)
    out['blurb_flesch'] = blurb.map(flesch)
    out['blurb_sentiment'] = blurb.map(lambda t: sia.polarity_scores(t)['compound'])   # -1 negative .. +1 positive
    out['kw_exclaim'] = blurb.str.contains('!', regex=False).astype(int)
    out['kw_you'] = low.str.contains(r'\byou(?:r|rs)?\b').astype(int)
    out['kw_we'] = low.str.contains(r'\b(?:we|our|us)\b').astype(int)
    out['kw_new_first'] = low.str.contains(r'\b(?:new|first|debut)\b').astype(int)
    return out

# ---------------------------------------------------------------- history tables
def category_tables(hist, months):
    """For every category and every month start t: norms from campaigns that ENDED in the 12 months before t.
    hist: finished projects with columns cat_id, parent_category, deadline, launched_at, goal_usd, success."""
    rows = []
    dl = hist.deadline.values
    for t in months:
        t1 = t.timestamp(); t0 = (t - pd.Timedelta(days=365)).timestamp(); th = (t - pd.Timedelta(days=182)).timestamp()
        w = hist[(dl >= t0) & (dl < t1)]
        if len(w) == 0: continue
        w = w.assign(recent=(w.deadline >= th))
        for key in ['cat_id', 'parent_category']:
            g = w.groupby(key).agg(n=('success', 'size'), rate=('success', 'mean'), med_goal=('goal_usd', 'median'),
                                   n_recent=('recent', 'sum'), s_recent=('success', lambda s: s[w.loc[s.index, 'recent']].sum()))
            g['rate_recent'] = g.s_recent / g.n_recent.replace(0, np.nan)
            g['rate_older'] = (g.rate * g.n - g.s_recent) / (g.n - g.n_recent).replace(0, np.nan)
            g = g.reset_index().rename(columns={key: 'key'}); g['level'] = key; g['month'] = t
            rows.append(g[['level', 'key', 'month', 'n', 'rate', 'med_goal', 'rate_recent', 'rate_older']])
    tab = pd.concat(rows, ignore_index=True)
    tab['key'] = tab.key.astype(str)          # category id or parent name, stored as text
    return tab

def _count_before(sorted_vals, x):
    return np.searchsorted(sorted_vals, x, side='left')

def build_features(raw, with_text=True, verbose=True):
    say = print if verbose else (lambda *a, **k: None)
    d = raw.copy()
    d['goal_usd'] = d.goal * d.static_usd_rate
    d['launch'] = pd.to_datetime(d.launched_at, unit='s')
    launched = d[d.launched_at > 1.2e9].copy()                       # every project that really went live (any state)
    fin = launched[launched.state.isin(['successful', 'failed'])].copy()
    fin['success'] = (fin.state == 'successful').astype(int)
    fin = fin[fin.launch <= LAST_SCRAPE - pd.Timedelta(days=60)]     # semantic layer rule 6
    say('finished projects after exclusions:', len(fin))
    X = fin[['id', 'success', 'launch', 'launched_at', 'deadline', 'creator_id', 'cat_id', 'parent_category',
             'country', 'goal_usd', 'usd_pledged', 'name', 'blurb', 'slug', 'subcategory']].copy()
    X['launch_year'] = X.launch.dt.year

    # ---- 1) Ambition
    X['duration_days'] = (fin.deadline - fin.launched_at) / DAY
    X['log_goal_usd'] = np.log10(X.goal_usd.clip(lower=1))
    X['log_goal_per_day'] = np.log10((X.goal_usd / X.duration_days.clip(lower=1)).clip(lower=0.1))
    lead = (fin.goal / 10 ** np.floor(np.log10(fin.goal.clip(lower=1))))
    X['goal_is_round'] = np.isclose(lead % 0.5, 0).astype(int)        # 1,000 / 2,500 / 50,000 ... in the project's own currency

    # ---- 6) Market: category norms as of the first day of the launch month
    X['month_start'] = X.launch.dt.to_period('M').dt.to_timestamp()
    months = pd.date_range(X.month_start.min(), LAST_SCRAPE + pd.offsets.MonthBegin(1), freq='MS')
    tab = category_tables(fin, months)
    say('category table rows:', len(tab))
    c = tab[tab.level == 'cat_id'].drop(columns='level').rename(columns={'key': 'cat_id'})
    p = tab[tab.level == 'parent_category'].drop(columns='level').rename(columns={'key': 'parent_category'})
    c['cat_id'] = c.cat_id.astype('int64')
    X = X.merge(c.add_suffix('_c').rename(columns={'cat_id_c': 'cat_id', 'month_c': 'month_start'}), on=['cat_id', 'month_start'], how='left')
    X = X.merge(p.add_suffix('_p').rename(columns={'parent_category_p': 'parent_category', 'month_p': 'month_start'}), on=['parent_category', 'month_start'], how='left')
    use_c = X.n_c.fillna(0) >= MIN_PRIOR                              # enough history in the exact category?
    X['cat_rate_12m'] = np.where(use_c, X.rate_c, X.rate_p)
    med = np.where(use_c, X.med_goal_c, X.med_goal_p)
    X['goal_ratio'] = np.log10((X.goal_usd.clip(lower=1) / pd.Series(med, index=X.index).clip(lower=1)))   # 0 = at the category median; +1 = 10x
    X['cat_trend'] = np.where(use_c, X.rate_recent_c - X.rate_older_c, X.rate_recent_p - X.rate_older_p)   # last 6 months minus the 6 before
    X['log_cat_n_12m'] = np.log10(X.n_c.fillna(0) + 1)
    X['cat_norm_from_parent'] = (~use_c).astype(int)

    X['city'] = X.id.map(launched.set_index('id').city)        # kept for the app's 'similar campaigns', not a model feature
    X['capped_category'] = X.cat_id.isin(CAPPED_CAT_IDS).astype(int)   # reporting / weights only

    # ---- 2) Timing
    X['launch_month'] = X.launch.dt.month
    X['launch_weekday'] = X.launch.dt.weekday                                  # 0 = Monday (UTC)
    end = pd.to_datetime(X.deadline, unit='s')
    xmas = pd.to_datetime(X.launch.dt.year.astype(str) + '-12-25')
    X['holiday_window'] = ((X.launch <= xmas) & (end >= xmas)).astype(int)     # campaign runs over Christmas
    X['log_prep_days'] = np.log10((X.id.map(fin.set_index('id').created_at).rsub(X.launched_at) / DAY).clip(lower=0) + 1)

    # ---- 4) Founder: only campaigns of the same creator that ENDED before this launch
    hist = launched[launched.state.isin(['successful', 'failed', 'canceled', 'suspended']) & launched.creator_id.notna()]
    hist = hist.sort_values(['creator_id', 'deadline'])
    grp = {k: (v.deadline.values, np.cumsum((v.state == 'successful').values), np.cumsum(v.state.isin(['successful', 'failed']).values))
           for k, v in hist.groupby('creator_id') if len(v) > 1}
    pn = np.zeros(len(X)); pf = np.zeros(len(X)); pfin = np.zeros(len(X)); last = np.full(len(X), np.nan)
    cid = X.creator_id.values; lt = X.launched_at.values
    for i in range(len(X)):
        g = grp.get(cid[i])
        if g is None: continue
        k = np.searchsorted(g[0], lt[i], side='left')                          # campaigns with deadline < this launch
        if k:
            pn[i] = k; pf[i] = g[1][k - 1]; pfin[i] = g[2][k - 1]; last[i] = (lt[i] - g[0][k - 1]) / DAY
    X['creator_prior_n'] = pn
    X['creator_prior_funded'] = pf
    X['creator_prior_rate'] = np.where(pfin > 0, pf / np.where(pfin > 0, pfin, 1), np.nan)   # missing for first-timers
    X['first_timer'] = (pn == 0).astype(int)
    X['log_days_since_last'] = np.log10(last + 1)

    # ---- 5) Presentation (known only for projects last listed from 2023-12 on; used in the modern model only)
    X['has_video'] = X.id.map(fin.set_index('id').has_video)
    X['prelaunch_activated'] = X.id.map(fin.set_index('id').prelaunch_activated)

    # ---- 3) Pitch
    if with_text:
        X = pd.concat([X, text_features(X.name, X.blurb)], axis=1)
    drop = [c for c in X.columns if c.endswith('_c') or c.endswith('_p')]
    X = X.drop(columns=drop)
    return X, {'category': tab}
