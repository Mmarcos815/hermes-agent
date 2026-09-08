
import json, asyncio, websockets

async def grab_key():
    ws_url = "ws://127.0.0.1:9222/devtools/browser/"
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"id":1,"method":"Target.getTargets"}))
        r = json.loads(await ws.recv())
        targets = r.get('result',{}).get('targetInfos',[])
        
        groq = None
        for t in targets:
            if 'console.groq.com/keys' in (t.get('url') or ''):
                groq = t
                break
        
        if not groq:
            print("Groq tab not found!")
            return
        
        tid = groq.get('targetId') or groq.get('id')
        print(f"Target: {groq.get('title','')} (id={tid})")
        
        await ws.send(json.dumps({"id":2,"method":"Target.attachToTarget","params":{"targetId":tid,"flatten":True}}))
        ar = json.loads(await ws.recv())
        sid = ar.get('result',{}).get('sessionId')
        print(f"Session: {sid}")
        
        if not sid:
            print("No session ID")
            return
        
        await ws.send(json.dumps({"id":3,"method":"Runtime.enable"}))
        await ws.recv()
        
        await ws.send(json.dumps({"id":4,"method":"Page.navigate","params":{"url":"https://console.groq.com/keys"}}))
        await ws.recv()
        await asyncio.sleep(2)
        
        await ws.send(json.dumps({
            "id":5,"method":"Runtime.evaluate",
            "params":{
                "expression":"""
                  (() => {
                    const els = Array.from(document.querySelectorAll('button, a, input')).map(el => ({
                      t: el.textContent.trim().substring(0,80),
                      v: el.value || '',
                      h: el.href || '',
                      ph: el.placeholder || '',
                      ty: el.tagName.toLowerCase(),
                      vis: el.offsetParent !== null,
                      x: el.getBoundingClientRect().x,
                      y: el.getBoundingClientRect().y
                    })).filter(e => e.vis);
                    return {
                      title: document.title,
                      text: document.body ? document.body.innerText.substring(0,3000) : '',
                      els: els
                    };
                  })()
                """,
                "returnByValue": True
            }
        }))
        result = json.loads(await ws.recv())
        page = result.get('result',{}).get('result',{}).get('value',{})
        
        print(f"\n=== {page.get('title','')} ===")
        print(f"URL: {page.get('url','')}")
        print(f"\nTEXT:")
        print(page.get('text','')[:2500])
        print(f"\nELEMENTS ({len(page.get('els',[]))}):")
        for e in page.get('els',[])[:25]:
            extra = ""
            if e['ty'] == 'input': extra = f" [ph={e['ph']}]"
            elif e['h']: extra = f" -> {e['h'][:60]}"
            print(f"  ({e['x']:.0f},{e['y']:.0f}) [{e['ty']}] {e['t'][:70]}{extra}")

asyncio.run(grab_key())
