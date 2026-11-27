import sys, re
from streamlit.testing.v1 import AppTest
mode=sys.argv[1]
for p in ["Check-up","Coach view","Goal optimizer","Similar campaigns"]:
    at = AppTest.from_file("/home/claude/crowdfund-compass/app/app.py", default_timeout=120)
    if mode=="new": at.query_params["page"]=p
    else: at.session_state["nav"]=p
    at.run()
    txt=" ".join(m.value for m in at.markdown if "<style" not in m.value)
    txt=re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
    keys=re.findall(r"(?:Rethink|Adjust|Launch)\b|\d+(?:\.\d+)?%|\$[\d,]+|\d+ of 10|\+\d+ points|#\d", txt)
    print(p, keys[:45])
