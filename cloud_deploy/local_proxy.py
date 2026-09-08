#!/usr/bin/env python3
"""
Local Proxy for Cloud Ollama API
Forwards OpenAI-compatible requests to cloud Ollama with auth, failover,
health checking, circuit breaker, and SSE streaming pass-through.

Usage:
    python local_proxy.py            # start on :8080
    python local_proxy.py --port 9090
"""

import argparse
import os
import sys
import time
from pathlib import Path
from http import HTTPStatus

import requests
import yaml
from flask import Flask, request, Response, jsonify

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).parent / "hermes_config.yaml"

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)


def resolve_env(value):
    """Replace ${ENV_VAR} with the actual environment variable value."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

class Provider:
    """A single upstream cloud provider."""

    def __init__(self, name: str, cfg: dict):
        self.name = name
        self.base_url = cfg["base_url"].rstrip("/")
        self.api_key = resolve_env(cfg.get("api_key", ""))
        self.models = cfg.get("models", [cfg.get("model_name", "llama3.1")])
        self.priority = cfg.get("priority", 99)
        self.timeout = cfg.get("timeout", 120)
        self.healthy = True
        self.consecutive_failures = 0

    def mark_healthy(self):
        self.healthy = True
        self.consecutive_failures = 0

    def mark_unhealthy(self):
        self.consecutive_failures += 1
        threshold = config.get("cloud_deploy", {}).get("health_check", {}).get("unhealthy_threshold", 3)
        if self.consecutive_failures >= threshold:
            self.healthy = False

    def headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h


# Build provider list sorted by priority
providers: list[Provider] = []
for name, cfg in config.get("cloud_deploy", {}).get("providers", {}).items():
    if cfg.get("enabled", True):
        providers.append(Provider(name, cfg))
providers.sort(key=lambda p: p.priority)

if not providers:
    print("ERROR: No providers configured in hermes_config.yaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)


def select_provider(model: str | None = None) -> Provider | None:
    """Pick the best healthy provider. If model given, prefer one that has it."""
    if model:
        for p in providers:
            if p.healthy and model in p.models:
                return p
    for p in providers:
        if p.healthy:
            return p
    return None


@app.route("/v1/models", methods=["GET"])
def list_models():
    """Aggregate models from all providers."""
    all_models = []
    for p in providers:
        for m in p.models:
            all_models.append({"id": m, "object": "model", "owned_by": p.name})
    return jsonify({"data": all_models, "object": "list"})


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """Main chat endpoint with failover across providers."""
    body = request.get_json(force=True)
    model = body.get("model")
    stream = body.get("stream", False)

    max_attempts = config.get("cloud_deploy", {}).get("fallback", {}).get("retry_attempts", 3)
    last_error = None

    for _ in range(max_attempts):
        provider = select_provider(model)
        if not provider:
            return jsonify({"error": "No healthy providers available"}), HTTPStatus.SERVICE_UNAVAILABLE

        try:
            url = f"{provider.base_url}/chat/completions"
            resp = requests.post(url, json=body, headers=provider.headers(),
                                 timeout=provider.timeout, stream=stream)

            if resp.status_code == 200:
                provider.mark_healthy()
                if stream:
                    def generate():
                        for chunk in resp.iter_lines():
                            if chunk:
                                yield f"data: {chunk.decode()}\n\n"
                        yield "data: [DONE]\n\n"
                    return Response(generate(), content_type="text/event-stream")
                return jsonify(resp.json()), 200

            provider.mark_unhealthy()
            last_error = resp.text

        except requests.RequestException as e:
            provider.mark_unhealthy()
            last_error = str(e)

    return jsonify({"error": "All providers failed", "detail": last_error}), HTTPStatus.BAD_GATEWAY


@app.route("/v1/embeddings", methods=["POST"])
def embeddings():
    """Forward embedding requests."""
    body = request.get_json(force=True)
    provider = select_provider(body.get("model"))
    if not provider:
        return jsonify({"error": "No healthy providers"}), HTTPStatus.SERVICE_UNAVAILABLE
    try:
        url = f"{provider.base_url}/embeddings"
        resp = requests.post(url, json=body, headers=provider.headers(), timeout=provider.timeout)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), HTTPStatus.BAD_GATEWAY


@app.route("/v1/health", methods=["GET"])
def health():
    """Health status of all providers."""
    status = []
    for p in providers:
        status.append({
            "name": p.name,
            "healthy": p.healthy,
            "priority": p.priority,
            "models": p.models,
            "failures": p.consecutive_failures,
        })
    overall = "ok" if any(p.healthy for p in providers) else "down"
    return jsonify({"status": overall, "providers": status})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Local proxy for cloud Ollama API")
    parser.add_argument("--port", type=int, default=8080, help="Local port (default: 8080)")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    print("=" * 55)
    print("  CLOUD OLLAMA LOCAL PROXY")
    print(f"  Endpoint:  http://{args.host}:{args.port}/v1")
    print("=" * 55)
    print()
    print("Configured providers:")
    for p in providers:
        print(f"  [{p.priority}] {p.name:10s} → {p.base_url}  models={p.models}")
    print()
    print("Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
