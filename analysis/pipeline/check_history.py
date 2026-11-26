# Independent re-check of the founder-history inputs (26.11.2026).
# The history is recomputed in a slow, obvious way for 695 random campaigns with an earlier campaign and 695 random
# campaigns overall, and compared with the values in features.parquet. Any mismatch would mean a bug or a leak
# (a campaign that had not ended yet at launch being counted).
#   python analysis/pipeline/check_history.py <folder with kickstarter_merged_v2.parquet and features.parquet>
import sys, os
import numpy as np, pandas as pd
DIR = sys.argv[1] if len(sys.argv) > 1 else 'v2'
raw = pd.read_parquet(os.path.join(DIR, 'kickstarter_merged_v2.parquet'), columns=['id', 'creator_id', 'state', 'launched_at', 'deadline'])
X = pd.read_parquet(os.path.join(DIR, 'features.parquet'),
                    columns=['id', 'creator_id', 'launched_at', 'creator_prior_n', 'creator_prior_funded', 'creator_prior_rate', 'first_timer'])
hist = raw[raw.state.isin(['successful', 'failed', 'canceled', 'suspended']) & (raw.launched_at > 1.2e9)]   # every campaign that ended
SAMPLES = (('campaigns with an earlier campaign', X[X.creator_prior_n > 0].sample(695, random_state=26)),
           ('random campaigns', X.sample(695, random_state=11)))
need = set(pd.concat([r.creator_id for _, r in SAMPLES]))
by_creator = {k: g for k, g in hist[hist.creator_id.isin(need)].groupby('creator_id')}

def check(rows):
    bad = []
    for r in rows.itertuples():
        g = by_creator.get(r.creator_id, hist.iloc[:0])
        earlier = g[g.deadline < r.launched_at]                                   # ended BEFORE this launch
        n, funded, failed = len(earlier), int((earlier.state == 'successful').sum()), int((earlier.state == 'failed').sum())
        rate = funded / (funded + failed) if funded + failed else np.nan
        ok = (n == r.creator_prior_n) and (funded == r.creator_prior_funded) and \
             (np.isnan(rate) and pd.isna(r.creator_prior_rate) or np.isclose(rate, r.creator_prior_rate)) and (int(n == 0) == r.first_timer)
        if not ok: bad.append((r.id, n, r.creator_prior_n, funded, r.creator_prior_funded))
    return bad

for label, rows in SAMPLES:
    bad = check(rows)
    print(f'{label}: {len(bad)} mismatches of {len(rows)}', bad[:5])
