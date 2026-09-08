#!/usr/bin/env python3
"""Monitor for typosquatting attacks.

Generates candidate typosquats (deletions, transpositions, keyboard-adjacent
substitutions) and checks npm/PyPI registries for existence.
"""
import argparse, string
from urllib.error import HTTPError
from urllib.request import Request, urlopen

NPM = "https://registry.npmjs.org/{}"
PYPI = "https://pypi.org/pypi/{}/json"
ADJ = {"a":"qs","b":"vn","c":"xv","d":"se","e":"wr","f":"dg","g":"fh","h":"gj",
       "i":"uo","j":"hk","k":"jl","l":"k","m":"n","n":"mb","o":"ip","p":"o",
       "q":"wa","r":"et","s":"ad","t":"ry","u":"yi","v":"cb","w":"qe","x":"zc","y":"tu","z":"x"}

def gen(name):
    n = name.lower()
    cands = set()
    cands.update(n[:i]+n[i+1:] for i in range(len(n)))
    ch = list(n)
    for i in range(len(ch)-1):
        ch[i],ch[i+1]=ch[i+1],ch[i]; cands.add("".join(ch)); ch[i],ch[i+1]=ch[i+1],ch[i]
    for i,ch_ in enumerate(n):
        for nb in ADJ.get(ch_,""): cands.add(n[:i]+nb+n[i+1:])
    cands.discard(n)
    return cands

def exists(pkg, eco):
    url = NPM.format(pkg) if eco=="npm" else PYPI.format(pkg)
    try:
        r = Request(url, headers={"User-Agent":"typosquat/1.0"})
        return urlopen(r, timeout=10).status == 200
    except HTTPError as e: return e.code != 404
    except: return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--packages", nargs="+", required=True)
    p.add_argument("--ecosystem", choices=["npm","pypi"], default="pypi")
    a = p.parse_args()
    alerts = []
    for pkg in a.packages:
        hits = [c for c in gen(pkg) if exists(c, a.ecosystem)]
        if hits:
            print(f"  ⚠️  {pkg}: {', '.join(hits)}")
            alerts.extend(hits)
        else:
            print(f"  ✓ {pkg}: clean")
    print(f"\n{'='*40}\n{len(alerts)} live typosquat(s) found" if alerts else "No typosquats found")

if __name__=="__main__": main()
