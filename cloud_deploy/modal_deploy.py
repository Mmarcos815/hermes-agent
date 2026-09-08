# ============================================================================
# BIONIC DAUGHTER — MODAL OLLAMA INFERENCE ENDPOINT
# "THERES ALWAYS A WAY" — Serverless GPU inference for bionic models.
#
# Deploys an Ollama server with the bionic model on Modal GPU,
# exposing an OpenAI-compatible /v1/chat/completions endpoint.
#
# Usage:
#   modal deploy cloud_deploy/modal_deploy.py    # deploy, returns URL
#   modal run cloud_deploy/modal_deploy.py::serve  # local test
#
# After deploy, use with any OpenAI SDK:
#   client = OpenAI(base_url=URL + "/v1", api_key="any")
#   client.chat.completions.create(model="bionic-daughter", messages=[...])
# ============================================================================

import asyncio
import json
import os
import subprocess
import time
from typing import Any, Dict

import modal

# --- Config ---------------------------------------------------------------

BIONIC_MODEL = os.environ.get("BIONIC_MODEL", "bionic-daughter:latest")
GPU_TYPE = os.environ.get("GPU_TYPE", "A10G")
OLLAMA_PORT = 11434

# --- Modal Image -----------------------------------------------------------

ollama_image = modal.Image.from_registry("ollama/ollama:latest").pip_install("httpx>=0.27")

app = modal.App("bionic-daughter-ollama")
model_vol = modal.Volume.from_name("ollama-model-cache", create_if_missing=True)


# --- Ollama Server Manager -------------------------------------------------

class OllamaServer:
    """Start `ollama serve` in a Modal container, pull model, proxy requests."""

    def __init__(self, model: str, model_dir: str = "/root/.ollama"):
        self.model = model
        self.model_dir = model_dir
        self._proc: subprocess.Popen | None = None

    async def start(self):
        import httpx
        env = {**os.environ, "OLLAMA_HOST": f"0.0.0.0:{OLLAMA_PORT}", "OLLAMA_MODELS": self.model_dir}
        self._proc = subprocess.Popen(["ollama", "serve"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 120
        async with httpx.AsyncClient() as c:
            while time.monotonic() < deadline:
                try:
                    r = await c.get(f"http://127.0.0.1:{OLLAMA_PORT}/api/tags", timeout=2)
                    if r.status_code == 200:
                        print("[Ollama] ready")
                        return
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(1)
        raise TimeoutError("Ollama failed to start")

    async def ensure_model(self, model: str):
        import httpx
        url = f"http://127.0.0.1:{OLLAMA_PORT}"
        r = await httpx.AsyncClient().get(f"{url}/api/tags")
        names = [m.get("name", "") for m in r.json().get("models", [])]
        if any(m.startswith(model.split(":")[0]) for m in names):
            print(f"[Ollama] model '{model}' cached")
            return
        print(f"[Ollama] pulling '{model}'...")
        async with httpx.AsyncClient(timeout=httpx.Timeout(600)) as c:
            async with c.stream("POST", f"{url}/api/pull", json={"name": model}) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            print(f"  {json.loads(line).get('status', '')}")
                        except json.JSONDecodeError:
                            pass
        print(f"[Ollama] model '{model}' ready")

    async def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import httpx
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as c:
            r = await c.post(f"http://127.0.0.1:{OLLAMA_PORT}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()


# --- Modal GPU Class -------------------------------------------------------

@app.cls(
    image=ollama_image,
    gpu=GPU_TYPE,
    container_idle_timeout=300,
    max_containers=1,
    volumes={"/root/.ollama": model_vol},
)
class BionicOllama:
    """Hosts Ollama + bionic model, exposes OpenAI-compatible endpoint."""

    @modal.enter()
    async def _startup(self):
        self.server = OllamaServer(BIONIC_MODEL)
        await self.server.start()
        await self.server.ensure_model(BIONIC_MODEL)

    @modal.exit()
    async def _shutdown(self):
        if self.server._proc:
            self.server._proc.terminate()
            self.server._proc.wait(timeout=10)

    @modal.asgi_app()
    def web(self):
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        import httpx

        async def chat_completions(request):
            try:
                body = await request.json()
            except Exception:
                return JSONResponse({"error": "invalid JSON"}, status_code=400)
            if body.get("stream"):
                return JSONResponse({"error": "streaming not yet supported"}, status_code=501)
            result = await self.server.chat({
                "model": BIONIC_MODEL,
                "messages": body.get("messages", []),
                "stream": False,
                "options": {
                    "temperature": body.get("temperature", 0.7),
                    "top_p": body.get("top_p", 0.95),
                    "num_predict": body.get("max_tokens", 512),
                },
            })
            return JSONResponse({
                "id": f"bionic-{int(time.time() * 1000)}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": BIONIC_MODEL,
                "choices": [{"index": 0, "message": result.get("message", {}), "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                },
            })

        async def health(request):
            return JSONResponse({"status": "ok", "model": BIONIC_MODEL})

        return Starlette(routes=[
            Route("/v1/chat/completions", chat_completions, methods=["POST"]),
            Route("/health", health),
        ])


# --- Local Test Entrypoint -------------------------------------------------

@app.local_entrypoint()
def serve():
    """Deploy and print endpoint URL + health check."""
    import httpx
    print("=" * 60)
    print("BIONIC DAUGHTER — Modal Ollama")
    print("=" * 60)
    try:
        url = BionicOllama().web_url()
        print(f"Endpoint : {url}/v1/chat/completions")
        print(f"Health   : {url}/health")
        print(f"Model    : {BIONIC_MODEL}")
        print(f"GPU      : {GPU_TYPE}")
        r = httpx.get(f"{url}/health", timeout=5)
        print(f"Health   : {r.json()}")
    except Exception as e:
        print(f"Note: run 'modal deploy cloud_deploy/modal_deploy.py' for URL ({e})")
    print("=" * 60)
