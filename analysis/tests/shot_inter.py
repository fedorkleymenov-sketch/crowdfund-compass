import json,sys,time,base64,subprocess,urllib.request,websocket
W,H=int(sys.argv[1]),int(sys.argv[2]); pages=sys.argv[3:]
p=subprocess.Popen(['google-chrome','--headless=new','--no-sandbox','--disable-gpu','--hide-scrollbars','--remote-debugging-port=9333','--remote-allow-origins=*',f'--window-size={W},{H}','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(3); tabs=json.load(urllib.request.urlopen('http://127.0.0.1:9333/json')); ws=websocket.create_connection([t for t in tabs if t['type']=='page'][0]['webSocketDebuggerUrl']); i=[0]
def cmd(m,**k):
    i[0]+=1; ws.send(json.dumps({'id':i[0],'method':m,'params':k}))
    while True:
        r=json.loads(ws.recv())
        if r.get('id')==i[0]: return r.get('result',{})
cmd('Emulation.setDeviceMetricsOverride',width=W,height=H,deviceScaleFactor=1,mobile=W<600)
for pg in pages:
    cmd('Page.navigate',url='http://localhost:8501/?page='+pg.replace(' ','%20')); time.sleep(9)
    import glob as _g
    css="".join("@font-face{font-family:'Inter';font-weight:%s;src:url(data:font/woff2;base64,%s) format('woff2');}"%(w,base64.b64encode(open(f'/home/claude/work/fonts/package/files/inter-latin-{w}-normal.woff2','rb').read()).decode()) for w in (400,600,700,800))
    cmd('Runtime.evaluate',expression="(function(){var s=document.createElement('style');s.textContent="+json.dumps(css)+";document.head.appendChild(s);})()"); time.sleep(3)
    h=cmd('Runtime.evaluate',expression="Math.max(document.querySelector('[data-testid=\"stMain\"]')?.scrollHeight||0, document.body.scrollHeight)").get('result',{}).get('value',H)
    cmd('Emulation.setDeviceMetricsOverride',width=W,height=min(int(h)+40,4200),deviceScaleFactor=1,mobile=W<600); time.sleep(2)
    d=cmd('Page.captureScreenshot',format='png'); open(f"{pg.replace(' ','_')}_{W}.png",'wb').write(base64.b64decode(d['data']))
    cmd('Emulation.setDeviceMetricsOverride',width=W,height=H,deviceScaleFactor=1,mobile=W<600); print(pg,h)
p.kill()
