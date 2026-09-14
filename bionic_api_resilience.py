#!/usr/bin/env python3
"""
Bionic Daughter — API Resilience & Model Fallback Configuration
Uses red-tactics skill patterns for authorized API security testing.

This script configures:
1. Model fallback chain (cloud → local)
2. Retry with exponential backoff
3. Rate limit probing (for authorized testing)
4. Timeout handling

Run: python bionic_api_resilience.py
"""

import json
import time
import random
import requests
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# MODEL FALLBACK CHAIN
# Primary → Fallback 1 → Fallback 2 → Local
# ═══════════════════════════════════════════════════════════════════

MODEL_CHAIN = [
    {
        "name": "nous/solar-pro4",
        "provider": "nous",
        "base_url": "https://inference-api.nousresearch.com/v1",
        "api_key_env": "NOUS_API_KEY",
        "max_tokens": 8192,
        "timeout": 120,
    },
    {
        "name": "nous/hermes-3-llama-3.1-70b",
        "provider": "nous",
        "base_url": "https://inference-api.nousresearch.com/v1",
        "api_key_env": "NOUS_API_KEY",
        "max_tokens": 8192,
        "timeout": 120,
    },
    {
        "name": "local/qwen2.5-coder",
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "max_tokens": 4096,
        "timeout": 300,
    },
]

# ═══════════════════════════════════════════════════════════════════
# RETRY WITH EXPONENTIAL BACKOFF
# ═══════════════════════════════════════════════════════════════════

class ResilientAPICall:
    """Handle transient failures without hammering the API."""
    
    def __init__(self, max_retries=5, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def call(self, fn, *args, **kwargs):
        """Call function with retry logic."""
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                
                # Rate limit — wait and retry
                if "429" in error_str or "rate limit" in error_str:
                    delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"  [RATE LIMIT] Waiting {delay:.1f}s before retry {attempt+1}/{self.max_retries}")
                    time.sleep(delay)
                
                # Timeout — retry with backoff
                elif "timeout" in error_str:
                    if attempt == self.max_retries - 1:
                        raise
                    print(f"  [TIMEOUT] Retry {attempt+1}/{self.max_retries}")
                    time.sleep(self.base_delay)
                
                # Server error — retry
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    delay = self.base_delay * (2 ** attempt)
                    print(f"  [SERVER ERROR] Waiting {delay:.1f}s before retry {attempt+1}/{self.max_retries}")
                    time.sleep(delay)
                
                else:
                    raise
        
        raise Exception("All retries exhausted")


# ═══════════════════════════════════════════════════════════════════
# MODEL FALLBACK CHAIN
# ═══════════════════════════════════════════════════════════════════

class ModelFallbackChain:
    """Cascade through models when one fails."""
    
    def __init__(self, models=None):
        self.models = models or MODEL_CHAIN
        self.resilient = ResilientAPICall()
    
    def chat(self, messages, temperature=0.7, max_tokens=None):
        """Try each model in chain until one succeeds."""
        errors = []
        
        for model in self.models:
            try:
                print(f"  Trying {model['name']}...")
                result = self._call_model(model, messages, temperature, max_tokens)
                print(f"  ✅ Success with {model['name']}")
                return result
            except Exception as e:
                error_msg = str(e)[:100]
                errors.append(f"{model['name']}: {error_msg}")
                print(f"  ❌ Failed: {error_msg}")
                continue
        
        raise Exception(f"All models failed:\n" + "\n".join(errors))
    
    def _call_model(self, model, messages, temperature, max_tokens):
        """Call a specific model."""
        if model["provider"] == "ollama":
            return self._call_ollama(model, messages, temperature, max_tokens)
        else:
            return self._call_openai_compatible(model, messages, temperature, max_tokens)
    
    def _call_ollama(self, model, messages, temperature, max_tokens):
        """Call local Ollama model."""
        url = f"{model['base_url']}/api/chat"
        
        # Convert messages to Ollama format
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        payload = {
            "model": model["name"].split("/")[-1],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens or model.get("max_tokens", 4096),
            }
        }
        
        response = requests.post(url, json=payload, timeout=model.get("timeout", 300))
        response.raise_for_status()
        return response.json()["response"]
    
    def _call_openai_compatible(self, model, messages, temperature, max_tokens):
        """Call OpenAI-compatible API."""
        import os
        
        url = f"{model['base_url']}/chat/completions"
        api_key = os.environ.get(model.get("api_key_env", ""), "")
        
        headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model["name"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or model.get("max_tokens", 8192),
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=model.get("timeout", 120))
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


# ═══════════════════════════════════════════════════════════════════
# RATE LIMIT PROBE (Authorized Testing Only)
# ═══════════════════════════════════════════════════════════════════

def probe_rate_limit(endpoint, headers=None, max_rps=100):
    """
    Map the rate limit boundary. Stop at first 429.
    ONLY for authorized testing against systems you own.
    """
    headers = headers or {}
    
    for rps in [1, 5, 10, 20, 50, 100]:
        responses = []
        for _ in range(rps):
            try:
                r = requests.get(endpoint, headers=headers, timeout=10)
                responses.append(r.status_code)
            except:
                responses.append(0)
        
        if 429 in responses:
            print(f"Rate limit hit at {rps} req/s")
            return rps
        
        time.sleep(1)
    
    print(f"No rate limit found up to {max_rps} req/s")
    return max_rps


# ═══════════════════════════════════════════════════════════════════
# MAIN — Test the chain
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("BIONIC DAUGHTER — API Resilience Configuration")
    print("=" * 60)
    
    # Test the fallback chain
    chain = ModelFallbackChain()
    
    messages = [
        {"role": "system", "content": "You are Bionic Daughter. Respond briefly."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    
    try:
        response = chain.chat(messages)
        print(f"\nResponse: {response}")
    except Exception as e:
        print(f"\nAll models failed: {e}")
    
    print("\n" + "=" * 60)
    print("Configuration complete.")
    print("Models in chain:")
    for m in MODEL_CHAIN:
        print(f"  • {m['name']} ({m['provider']})")
