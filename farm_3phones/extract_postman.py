#!/usr/bin/env python3
"""
extract_postman.py — Extract ALL endpoints from TCGplayer Postman collection.
"""
import json

with open('tcgplayer_postman/TCGPlayer.postman_collection.json') as f:
    data = json.load(f)

endpoints = []
for group in data['item']:
    name = group.get('name', '?')
    req = group.get('request', {})
    if isinstance(req, dict):
        url = req.get('url', '')
        if isinstance(url, dict):
            url = url.get('raw', '')
        method = req.get('method', 'GET')
        body = req.get('body', {})
        raw_body = body.get('raw', '') if isinstance(body, dict) else ''
        endpoints.append({
            'group': name,
            'method': method,
            'url': str(url)[:200],
            'body': str(raw_body)[:500]
        })

print(f"Total endpoints: {len(endpoints)}\n")
for ep in endpoints:
    print(f"[{ep['method']}] {ep['group']}")
    print(f"  URL: {ep['url']}")
    if ep['body']:
        print(f"  Body: {ep['body'][:200]}")
    print()
