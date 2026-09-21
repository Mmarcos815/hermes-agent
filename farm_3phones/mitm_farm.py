"""Dad 3-phone MITM farm addon - run: mitmdump -p 8080 -s farm_3phones/mitm_farm.py -w farm_3phones/phone01.mitm"""
from mitmproxy import http

KEEP = ("courtyard.io", "riprush", "emeraldmyth", "dena", "pokemon", "privy.io", "tcgdex")

def request(flow: http.HTTPFlow):
    host = flow.request.pretty_host
    if any(k in host for k in KEEP):
        flow.metadata["keep"] = True
    # tag Courtyard buy for snipe replay
    if "api.courtyard.io" in host and "pack" in flow.request.path.lower():
        print(f"[SNIPER] {flow.request.method} {host}{flow.request.path}")

def response(flow: http.HTTPFlow):
    if flow.metadata.get("keep"):
        ct = flow.response.headers.get("content-type", "")
        print(f"[KEEP] {flow.request.pretty_host}{flow.request.path} -> {flow.response.status_code} {ct[:40]}")
    else:
        # drop noise to keep pcaps small - still forwarded, just not logged
        pass
