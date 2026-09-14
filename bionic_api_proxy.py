#!/usr/bin/env python3
"""
Bionic Daughter — Local API Fallback Proxy
Listens on port 8000, proxies to Nous API with Ollama fallback.
No API key needed for local models.

Run: python bionic_api_proxy.py
"""

import json
import os
import sys
import time
import random
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urljoin

# Configuration
LISTEN_PORT = 8000
NOUS_BASE_URL = "https://inference-api.nousresearch.com/v1"
OLLAMA_BASE_URL = "http://localhost:11434"

# Model chain: try in this order
MODEL_CHAIN = [
    {
        "name": "nous/solar-pro4",
        "provider": "nous",
        "base_url": NOUS_BASE_URL,
        "model_id": "upstage/solar-pro4:free",
    },
    {
        "name": "nous/hermes-3",
        "provider": "nous",
        "base_url": NOUS_BASE_URL,
        "model_id": "nousresearch/hermes-3-llama-3.1-70b",
    },
    {
        "name": "local/qwen2.5-coder",
        "provider": "ollama",
        "base_url": OLLAMA_BASE_URL,
        "model_id": "qwen2.5-coder:14b",
    },
]


class APIProxyHandler(BaseHTTPRequestHandler):
    """Handle API requests with model fallback."""
    
    def do_POST(self):
        """Handle POST requests (chat completions)."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # Try each model in chain
        errors = []
        for model in MODEL_CHAIN:
            try:
                response = self._call_model(model, request_data)
                self._send_json(200, response)
                return
            except Exception as e:
                error_msg = str(e)[:100]
                errors.append(f"{model['name']}: {error_msg}")
                print(f"  ❌ {model['name']} failed: {error_msg}")
                continue
        
        # All models failed
        self._send_json(502, {
            "error": "All models failed",
            "details": errors
        })
    
    def _call_model(self, model, request_data):
        """Call a specific model."""
        if model["provider"] == "ollama":
            return self._call_ollama(model, request_data)
        else:
            return self._call_nous(model, request_data)
    
    def _call_nous(self, model, request_data):
        """Call Nous API."""
        url = f"{model['base_url']}/chat/completions"
        
        # Build payload
        payload = {
            "model": model["model_id"],
            "messages": request_data.get("messages", []),
            "temperature": request_data.get("temperature", 0.7),
            "max_tokens": request_data.get("max_tokens", 8192),
            "stream": False,
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Add API key if available
        api_key = os.environ.get("NOUS_API_KEY", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json()
    
    def _call_ollama(self, model, request_data):
        """Call Ollama API."""
        url = f"{model['base_url']}/api/chat"
        
        # Convert messages to Ollama format
        messages = request_data.get("messages", [])
        
        payload = {
            "model": model["model_id"],
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request_data.get("temperature", 0.7),
                "num_predict": request_data.get("max_tokens", 4096),
            }
        }
        
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        # Convert Ollama response to OpenAI format
        ollama_resp = response.json()
        return {
            "id": f"ollama-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model["model_id"],
            "choices": [{
                "index": 0,
                "message": ollama_resp.get("message", {"role": "assistant", "content": ""}),
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    
    def _send_json(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        """Handle GET requests (health check)."""
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "bionic-api-proxy"})
        elif self.path == "/v1/models":
            # Return available models
            models = [{"id": m["name"], "object": "model"} for m in MODEL_CHAIN]
            self._send_json(200, {"data": models, "object": "list"})
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    server = HTTPServer(("127.0.0.1", LISTEN_PORT), APIProxyHandler)
    print(f"🚀 Bionic API Proxy running on http://127.0.0.1:{LISTEN_PORT}")
    print(f"   Models in chain: {[m['name'] for m in MODEL_CHAIN]}")
    print(f"   Health check: http://127.0.0.1:{LISTEN_PORT}/health")
    print()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
