# merge_v2.py — rebuild the merged Kickstarter table from the raw Web Robots scrapes.
# Changes vs merge.py (v1): keeps the category slug/ids (-> correct parent category for every scrape),
# marks has_video / prelaunch_activated as MISSING when the scrape file has no such field,
# and keeps one compact file per scrape so we can see in which scrapes each project was listed.
# Usage: python3 -I merge_v2.py <out_dir> <raw_file> [<raw_file> ...]     (one or more Kickstarter_* files)
import sys, gzip, json, zipfile, os, io
import pandas as pd

BASE = ['id', 'name', 'blurb', 'goal', 'pledged', 'state', 'country', 'currency', 'static_usd_rate',
        'usd_pledged', 'backers_count', 'created_at', 'launched_at', 'deadline', 'state_changed_at',
        'staff_pick', 'spotlight', 'prelaunch_activated', 'video', 'category', 'location', 'creator', 'slug']
NUM = ['created_at', 'launched_at', 'deadline', 'state_changed_at', 'goal', 'pledged', 'static_usd_rate',
       'usd_pledged', 'backers_count', 'id', 'creator_id', 'cat_id', 'cat_parent_id']

def j(v):
    if isinstance(v, dict): return v
    if isinstance(v, str) and v.startswith('{'):
        try: return json.loads(v)
        except Exception: return {}
    return {}

def compact(df, has_video_field, has_prelaunch_field):
    cat = df['category'].map(j); loc = df['location'].map(j); cre = df['creator'].map(j)
    out = df[[c for c in BASE if c not in ('category', 'location', 'creator', 'video', 'prelaunch_activated')]].copy()
    out['subcategory'] = cat.map(lambda d: d.get('name'))
    out['cat_slug'] = cat.map(lambda d: d.get('slug'))
    out['cat_id'] = cat.map(lambda d: d.get('id'))
    out['cat_parent_id'] = cat.map(lambda d: d.get('parent_id'))
    out['city'] = loc.map(lambda d: d.get('displayable_name'))
    out['loc_type'] = loc.map(lambda d: d.get('type'))
    out['loc_state'] = loc.map(lambda d: d.get('state'))
    out['creator_id'] = cre.map(lambda d: d.get('id'))
    # 1.0 / 0.0 when the file has the field, missing (NaN) when it does not
    out['has_video'] = df['video'].notna().astype(float) if has_video_field else float('nan')
    if has_prelaunch_field:
        out['prelaunch_activated'] = df['prelaunch_activated'].map(
            lambda v: 1.0 if v in (True, 'true', 'True') else (0.0 if v in (False, 'false', 'False') else float('nan')))
    else:
        out['prelaunch_activated'] = float('nan')
    for c in NUM: out[c] = pd.to_numeric(out[c], errors='coerce')
    for c in ['staff_pick', 'spotlight']:
        out[c] = out[c].map(lambda v: v in (True, 'true', 'True'))
    return out

def read_json_gz(path):
    rows, has_v, has_p = [], False, False
    with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: obj = json.loads(line)
            except json.JSONDecodeError: continue
            data = obj.get('data', obj)
            projs = data.get('projects', [data]) if isinstance(data, dict) else []
            for p in projs:
                if isinstance(p, dict) and 'id' in p:
                    has_v = has_v or ('video' in p); has_p = has_p or ('prelaunch_activated' in p)
                    rows.append({k: p.get(k) for k in BASE})
    return pd.DataFrame(rows, columns=BASE), has_v, has_p

def read_zip(path):
    frames, has_v, has_p = [], False, False
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.lower().endswith('.csv') and not os.path.basename(n).startswith('._'):
                d = pd.read_csv(io.BytesIO(z.read(n)), low_memory=False, usecols=lambda c: c in BASE)
                has_v = has_v or ('video' in d.columns); has_p = has_p or ('prelaunch_activated' in d.columns)
                frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    for c in BASE:
        if c not in df: df[c] = None
    return df, has_v, has_p

outdir = sys.argv[1]
for src in sys.argv[2:]:
    scrape = os.path.basename(src).split('Kickstarter_')[1][:10]
    part = f'{outdir}/parts/{scrape}.parquet'
    if os.path.exists(part): continue
    df, has_v, has_p = read_json_gz(src) if src.endswith('.json.gz') else read_zip(src)
    c = compact(df, has_v, has_p); c['scrape'] = scrape
    c = c.dropna(subset=['id']).drop_duplicates('id', keep='last')
    c.to_parquet(part + '.tmp', index=False); os.replace(part + '.tmp', part)
    print(scrape, 'raw rows', len(df), 'unique', len(c), 'video field', has_v, 'prelaunch field', has_p, flush=True)

# ---- Final step: build the merged table (latest state per project) and the presence table ----
import glob
PARENT = {'art': 'Art', 'comics': 'Comics', 'crafts': 'Crafts', 'dance': 'Dance', 'design': 'Design',
          'fashion': 'Fashion', 'film & video': 'Film & Video', 'food': 'Food', 'games': 'Games',
          'journalism': 'Journalism', 'music': 'Music', 'photography': 'Photography',
          'publishing': 'Publishing', 'technology': 'Technology', 'theater': 'Theater'}
allp = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(outdir + '/parts/*.parquet'))], ignore_index=True)
allp['id'] = allp.id.astype('int64')
# presence: one row per project x scrape it was listed in (used to study which projects drop out)
pres = allp[['id', 'scrape', 'state', 'pledged', 'goal', 'launched_at', 'deadline']]
for i in range(5):
    pres.iloc[i::5].to_parquet(f'{outdir}/presence_part{i+1}.parquet', index=False)
seen = allp.groupby('id').scrape.agg(first_scrape='min', n_scrapes='size')
m = allp.sort_values('scrape').drop_duplicates('id', keep='last').merge(seen, left_on='id', right_index=True)
m['parent_category'] = m.cat_slug.str.split('/').str[0].str.lower().map(PARENT)   # "art/painting" -> Art
m['is_top_level_category'] = ~m.cat_slug.fillna('').str.contains('/')
m = m.sort_values('id').reset_index(drop=True)
n_parts = 8
for i in range(n_parts):
    m.iloc[i::n_parts].to_parquet(f'{outdir}/kickstarter_merged_v2_part{i+1}.parquet', index=False)
fin = m[m.state.isin(['successful', 'failed'])]
print('scrapes', allp.scrape.nunique(), '| unique projects', len(m), '| finished', len(fin),
      '| success rate', round((fin.state == 'successful').mean(), 4), '| parent categories', m.parent_category.nunique())
