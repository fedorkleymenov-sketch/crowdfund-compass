
import json,sys,nbformat,os
from nbclient import NotebookClient
REP=[("!pip -q install vaderSentiment lightgbm optuna",""),("!pip -q install vaderSentiment        # sentiment word list (beyond class)",""),("!pip -q install vaderSentiment",""),
     ("project = 'drive/My Drive/crowdfund_compass'","project = '/home/claude/work/repo/app'"),("path = 'drive/My Drive/ks_scrapes/merged_v2'","path = '/mnt/user-data/outputs/merged_v2'"),
     ("out = project + '/models'","out = '/home/claude/work/nbrun'")]
os.makedirs('/home/claude/work/nbrun',exist_ok=True)
for name in sys.argv[1:]:
    nb=nbformat.read(f'out/{name}',as_version=4); orig=[c.source for c in nb.cells]
    for c in nb.cells:
        if c.cell_type=='code':
            for a,b in REP: c.source=c.source.replace(a,b)
    NotebookClient(nb,timeout=3600,kernel_name='python3').execute()
    for c,o in zip(nb.cells,orig): c.source=o
    nbformat.write(nb,f'repo/notebooks/{name}'); print(name,'executed, cells with output:',sum(1 for c in nb.cells if c.cell_type=='code' and c.outputs),flush=True)
