
import json, asyncio, websockets, sys

async def grab():
    browser_ws = "ws://127.0.0.1:9222/devtools/browser/"
    async with websockets.connect(browser_ws) as ws:
        # Attach to Groq tab
        await ws.send(json.dumps({"id": 1, "method": "Target.attachToTarget",
            "params": {"targetId": "0E6E6A9A4403F2642ECF41F41B2C7D8D", "flatten": False}}))
        evt = json.loads(await ws.recv())
        sid = evt["params"]["sessionId"]
        print(f"SESSION: {sid}", flush=True)
        
        # Create a new page target to get a fresh session that accepts page-level WS
        await ws.send(json.dumps({"id": 2, "method": "Target.createTarget",
            "params": {"url": "https://console.groq.com/keys", "width": 1200, "height": 800}}))
        cr = json.loads(await ws.recv())
        new_tid = cr["result"]["targetId"]
        print(f"NEW TARGET: {new_tid}", flush=True)
        
        # Attach to new target  
        await ws.send(json.dumps({"id": 3, "method": "Target.attachToTarget",
            "params": {"targetId": new_tid, "flatten": False}}))
        evt2 = json.loads(await ws.recv())
        new_sid = evt2["params"]["sessionId"]
        print(f"NEW SESSION: {new_sid}", flush=True)
        
        # Try page-level WS for new session
        try:
            page_ws = f"ws://127.0.0.1:9222/devtools/page/{new_sid}"
            async with websockets.connect(page_ws, open_timeout=5) as pw:
                print("PAGE WS CONNECTED", flush=True)
                await pw.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
                await pw.recv()
                await pw.send(json.dumps({"id": 2, "method": "Page.navigate",
                    "params": {"url": "https://console.groq.com/keys"}}))
                await pw.recv()
                await asyncio.sleep(3)
                
                await pw.send(json.dumps({
                    "id": 3, "method": "Runtime.evaluate",
                    "params": {
                        "expression": """
                          (() => {
                            const els = Array.from(document.querySelectorAll("button, a, input")).map(el => ({
                              t: el.textContent.trim().substring(0,80),
                              v: el.value || "",
                              h: el.href || "",
                              ph: el.placeholder || "",
                              ty: el.tagName.toLowerCase(),
                              vis: el.offsetParent !== null,
                              x: el.getBoundingClientRect().x,
                              y: el.getBoundingClientRect().y
                            })).filter(e => e.vis);
                            return {
                              title: document.title,
                              url: window.location.href,
                              text: document.body ? document.body.innerText.substring(0,4000) : "",
                              els: els
                            };
                          })()
                        """,
                        "returnByValue": True
                    }
                }))
                result = json.loads(await pw.recv())
                page = result.get("result", {}).get("result", {}).get("value", {})
                
                print(f"\n=== {page.get('title', 'N/A')} ===", flush=True)
                print(f"URL: {page.get('url', 'N/A')}", flush=True)
                print(f"\nTEXT:", flush=True)
                print(page.get("text", "")[:3000], flush=True)
                print(f"\nELEMENTS ({len(page.get('els', []))}):", flush=True)
                for e in page.get("els", [])[:30]:
                    extra = ""
                    if e["ty"] == "input": extra = f" [ph={e['ph']}]"
                    elif e["h"]: extra = f" -> {e['h'][:60]}"
                    print(f"  ({e['x']:.0f},{e['y']:.0f}) [{e['ty']}] {e['t'][:70]}{extra}", flush=True)
                return
        except Exception as e:
            print(f"Page WS failed: {e}", flush=True)
        
        # Fallback: use browser WS with sessionId
        def cmd(mid, method, params={}):
            return json.dumps({"id": mid, "method": method, "params": {**params, "sessionId": new_sid}})
        
        await ws.send(cmd(10, "Runtime.enable"))
        await ws.recv()
        
        await ws.send(cmd(11, "Runtime.evaluate", {
            "expression": "document.title",
            "returnByValue": True
        }))
        r = json.loads(await ws.recv())
        print(f"FALLBACK TITLE: {json.dumps(r)[:200]}", flush=True)

asyncio.run(grab())
