#!/usr/bin/env python3
"""
Groq Inference Client
Ultra-fast LLM inference without local RAM usage.
Free tier available at https://console.groq.com
"""

import os, json, sys
from pathlib import Path

try:
    from groq import Groq
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "groq"])
    from groq import Groq

class GroqInference:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key or self.api_key == "your-api-key-here":
            print("ERROR: Set GROQ_API_KEY environment variable")
            print("Get key at: https://console.groq.com/keys")
            sys.exit(1)
        self.client = Groq(api_key=self.api_key)
        self.models = {
            "llama-70b": "llama-3.1-70b-versatile",
            "llama-8b": "llama-3.1-8b-instant",
            "mixtral": "mixtral-8x7b-32768",
            "gemma": "gemma2-9b-it",
        }
    
    def chat(self, message, model="llama-70b", system_prompt=None):
        """Send a message and get a response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.models.get(model, model),
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    
    def security_analysis(self, target, findings):
        """Analyze security findings."""
        system = "You are an elite security analyst. Analyze findings and provide actionable remediation."
        prompt = f"Target: {target}\nFindings: {json.dumps(findings, indent=2)}"
        return self.chat(prompt, system_prompt=system)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", "-m", help="Message to send")
    parser.add_argument("--model", default="llama-70b")
    parser.add_argument("--system", help="System prompt")
    args = parser.parse_args()
    
    client = GroqInference()
    if args.message:
        response = client.chat(args.message, model=args.model, system_prompt=args.system)
        print(response)
    else:
        print("Groq Inference Client Ready")
        print("Usage: python groq_client.py -m 'Your message'")
        print("Models: llama-70b, llama-8b, mixtral, gemma")
