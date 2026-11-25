"""advice.py — Crowdfund Compass: explanations, area scores, "what to change" and the verdict (Group 11).
Works on the feature table produced by features.py + modeling.py and on the saved final model.
Everything here describes associations in past campaigns. It never promises an outcome."""
import numpy as np, pandas as pd, xgboost as xgb
import modeling as M

DAY = 86400
AREAS = {
    'Ambition':     ['log_goal_usd', 'goal_ratio', 'log_goal_per_day', 'duration_days', 'goal_is_round'],
    'Timing':       ['launch_month', 'launch_weekday', 'holiday_window', 'log_prep_days'],
    'Pitch':        ['name_len', 'name_words', 'blurb_len', 'blurb_words', 'name_has_digit', 'name_has_symbol',
                     'blurb_flesch', 'blurb_sentiment', 'kw_exclaim', 'kw_you', 'kw_we', 'kw_new_first'],
    'Founder':      ['creator_prior_n', 'creator_prior_funded', 'creator_prior_rate', 'first_timer', 'log_days_since_last'],
    'Presentation': ['has_video', 'prelaunch_activated'],
    'Market':       ['cat_id', 'parent_c', 'country_c', 'text_score'],      # "how your type of product has done"
}

def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6); return np.log(p / (1 - p))

def middle(a, b):
    """Middle estimate: halfway between the two estimates on the log-odds scale."""
    return 1 / (1 + np.exp(-(_logit(np.asarray(a, float)) + _logit(np.asarray(b, float))) / 2))

class Advisor:
    def __init__(self, art):
        self.model, self.feats, self.platt, self.sample_rate = art['model'], art['features'], art['platt'], art['sample_rate']
        self.ref = art.get('area_reference')          # sorted SHAP sums per area for the reference campaigns
        self.cut = art.get('verdict')                 # dict with the reference cut for single check-ups

    # ---- probabilities: high end = calibrated in our sample, low end = shifted to Kickstarter's official rates
    def estimates(self, df):
        """The two estimates by source: (calibrated chance in our data, the same shifted to Kickstarter's official rates).
        Usually the official one is lower, but in categories where the official rate is higher than in our data it is higher."""
        raw = self.model.predict_proba(df[self.feats].astype(float))[:, 1]
        ours = self._calibrate(raw)
        official = M.prior_shift(ours, df.parent_category.values, self.sample_rate)
        return ours, official

    def chances(self, df):
        ours, official = self.estimates(df)
        return np.minimum(ours, official), np.maximum(ours, official)          # (low end, high end), whatever the source

    def _calibrate(self, raw):
        """Platt scaling: chance = 1 / (1 + exp(-(a * logit(raw) + b))). Stored either as a fitted model or as the two numbers."""
        if isinstance(self.platt, dict):
            return 1 / (1 + np.exp(-(self.platt['a'] * _logit(raw) + self.platt['b'])))
        return self.platt.predict_proba(_logit(raw).reshape(-1, 1))[:, 1]

    # ---- SHAP (beyond class): how much each feature pushed this campaign's score up or down
    def shap(self, df):
        c = self.model.get_booster().predict(xgb.DMatrix(df[self.feats].astype(float)), pred_contribs=True)
        return pd.DataFrame(c[:, :-1], columns=self.feats, index=df.index)

    def area_sums(self, df):
        s = self.shap(df)
        return pd.DataFrame({a: s[cols].sum(axis=1) for a, cols in AREAS.items()})

    def area_scores(self, df):
        """0-100 per area: the share of reference campaigns whose features in this area helped less. 50 = typical."""
        a = self.area_sums(df)
        return pd.DataFrame({k: np.searchsorted(self.ref[k], a[k].values, side='right') / len(self.ref[k]) * 100 for k in AREAS}, index=df.index).round(0)

    # ---- "what to change": try one change at a time on the levers a founder controls
    def _variants(self, r, min_budget_usd=None):
        out = []
        def v(lever, label, **changes):
            x = r.copy()
            for k, val in changes.items(): x[k] = val
            out.append((lever, label, x))
        goal = r.goal_usd; floor = goal * 0.5 if min_budget_usd is None else min_budget_usd
        for f in (0.9, 0.8, 0.7, 0.6, 0.5):
            g = goal * f
            if g < floor - 1e-9: break
            d = np.log10(f)
            v('Goal', f'Lower the goal by {round((1 - f) * 100)}% (to about ${g:,.0f})', goal_usd=g, log_goal_usd=np.log10(max(g, 1)),
              goal_ratio=r.goal_ratio + d, log_goal_per_day=r.log_goal_per_day + d)
        for dur in (15, 21, 30, 45):
            if abs(dur - r.duration_days) >= 4:
                v('Duration', f'Run the campaign for {dur} days instead of {r.duration_days:.0f}', duration_days=dur,
                  log_goal_per_day=np.log10(max(r.goal_usd / dur, .1)), holiday_window=self._holiday(r.launch, dur))
        for shift in range(1, 7):
            day = r.launch + pd.Timedelta(days=shift)
            v('Launch day', f'Launch on a {day.day_name()} instead of a {r.launch.day_name()}', launch_weekday=day.weekday(),
              launch_month=day.month, holiday_window=self._holiday(day, r.duration_days))
        if r.holiday_window == 1:
            day = pd.Timestamp(r.launch.year + 1, 1, 8) if r.launch.month in (11, 12) else r.launch + pd.Timedelta(days=35)   # 8 January of the NEXT year
            v('Launch date', 'Move the launch so the campaign does not run over Christmas', launch_month=day.month, launch_weekday=day.weekday(), holiday_window=0)
        if r.has_video == 0: v('Video', 'Add a campaign video', has_video=1)
        if r.prelaunch_activated == 0: v('Pre-launch page', 'Open a pre-launch page before launch', prelaunch_activated=1)
        prep = 10 ** r.log_prep_days - 1
        if prep < 30:
            for extra in (14, 30):
                v('Preparation', f'Take {extra} more days to prepare before launch', log_prep_days=np.log10(prep + extra + 1))
        if r.name_words <= 4:
            add = 7 - r.name_words
            v('Title', 'Say what it is in the title (about 7 words)', name_words=7, name_len=r.name_len + 6 * add, name_has_symbol=1)
        if r.blurb_len < 80:
            v('Blurb', 'Use the full blurb (about 120 characters)', blurb_len=120, blurb_words=20)
        return out

    @staticmethod
    def _holiday(launch, duration):
        x = pd.Timestamp(launch.year, 12, 25)
        return int(launch <= x <= launch + pd.Timedelta(days=float(duration)))

    def fixes(self, r, min_budget_usd=None, top=3, min_gain=2.0):
        """Best single change per lever, sorted by gain in the MIDDLE ESTIMATE (points), the number the app shows.
        'gain' is kept unrounded, so thresholds (2 points to show, 5 points for Adjust) are applied before any rounding."""
        base = pd.DataFrame([r]); var = self._variants(r, min_budget_usd)
        if not var: return []
        V = pd.DataFrame([x for _, _, x in var])
        lo0, hi0 = self.chances(base); lo, hi = self.chances(V)
        mid0, mid = middle(lo0, hi0)[0], middle(lo, hi)
        t = pd.DataFrame({'lever': [a for a, _, _ in var], 'change': [b for _, b, _ in var], 'gain': (mid - mid0) * 100,
                          'low': lo * 100, 'high': hi * 100, 'mid': mid * 100, 'mid_before': mid0 * 100})
        t = t.sort_values('gain', ascending=False).drop_duplicates('lever')
        return t[t.gain >= min_gain].head(top).to_dict('records')

    # ---- verdict
    def verdict(self, low_end, fixes, in_riskiest_share=None):
        """The assessment of one campaign. Coach first: lower value below the reference cut (11.5%).
        Adjust: not that, but one change adds at least `adjust_gain` points to the middle estimate. Launch: otherwise.
        Coaching slots in a cohort are a separate decision (riskiest teams by rank, up to the coach's capacity)."""
        risky = in_riskiest_share if in_riskiest_share is not None else (low_end < self.cut['reference_cut'])
        if risky: return 'Coach first'
        if fixes and fixes[0]['gain'] >= self.cut['adjust_gain']: return 'Adjust'
        return 'Launch'
