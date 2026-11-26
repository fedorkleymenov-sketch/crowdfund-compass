# Coverage of our data against Kickstarter's official totals of 1 January 2026 (26.11.2026).
# Kickstarter's "unsuccessful" is everything launched that is neither funded nor live: launched 685,397 =
# successful 292,062 + unsuccessful 391,396 + live 1,939, and the success rate 42.73% = successful / (launched - live).
# So it includes cancelled and suspended campaigns. This script compares like with like.
#   python analysis/pipeline/coverage.py <folder with kickstarter_merged_v2.parquet>
import sys, os
import pandas as pd
DIR = sys.argv[1] if len(sys.argv) > 1 else 'v2'
raw = pd.read_parquet(os.path.join(DIR, 'kickstarter_merged_v2.parquet'), columns=['id', 'state', 'launched_at', 'deadline'])
LAUNCHED, SUCCESSFUL, UNSUCCESSFUL, LIVE = 685_397, 292_062, 391_396, 1_939
assert LAUNCHED == SUCCESSFUL + UNSUCCESSFUL + LIVE and round(SUCCESSFUL / (LAUNCHED - LIVE), 4) == 0.4273
ended = raw[(pd.to_datetime(raw.deadline, unit='s') < '2026-01-01') & (raw.launched_at > 1e9)]
n = ended.state.value_counts()
s, f, c, su = (int(n.get(k, 0)) for k in ('successful', 'failed', 'canceled', 'suspended'))
print('our campaigns ended before 1 January 2026:', n.to_dict())
print(f'funded:                                  {s:,} of {SUCCESSFUL:,} = {s / SUCCESSFUL:.1%}')
print(f'failed only (old comparison):            {f:,} of {UNSUCCESSFUL:,} = {f / UNSUCCESSFUL:.1%}')
print(f'failed, cancelled or suspended (like with like): {f + c + su:,} of {UNSUCCESSFUL:,} = {(f + c + su) / UNSUCCESSFUL:.1%}')
