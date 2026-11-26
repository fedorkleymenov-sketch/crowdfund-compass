import sys, re
from streamlit.testing.v1 import AppTest
PAGES = ["Home","Check-up","Goal optimizer","Coach view","Similar campaigns","Benchmarks","How it works"]
mode=sys.argv[1]
out={}
for p in PAGES:
    at = AppTest.from_file("/home/claude/crowdfund-compass/app/app.py", default_timeout=120)
    if mode=="new": at.query_params["page"]=p
    else: at.session_state["nav"]=p
    at.run()
    txt=" ".join(m.value for m in at.markdown)+" ".join(c.value for c in at.caption)
    nums=re.findall(r"\d+(?:\.\d+)?%|\$[\d,]+|\d+ of 10", txt)
    out[p]=(len(at.exception), nums[:40])
    print(p, "exceptions:", len(at.exception), [e.message[:150] for e in at.exception])
import json; json.dump(out, open(f"/tmp/{mode}.json","w"))
