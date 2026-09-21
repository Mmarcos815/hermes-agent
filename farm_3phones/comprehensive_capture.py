#!/usr/bin/env python3
"""
comprehensive_capture.py — Mitmproxy addon for full Phone-02 traffic harvesting.

Covers:
  - HTTP + HTTPS + WebSocket flows (full request/response bodies)
  - Cookie extraction (session tokens, auth cookies, CSRF)
  - JSON reward payload capture (responses containing reward/gacha/pack/box/xp/card data)
  - HAR-style JSON dump to a per-session file
  - Console summary of high-value endpoints and cookies

Run:
  mitmdump -s comprehensive_capture.py -p 8082
  mitmweb -s comprehensive_capture.py --listen-port 8082 --web-port 8083

Output:
  - <SESSION_ID>.flows.json   — every flow as JSON (flow-level, not full body by default;
                               set DUMP_BODIES=1 to include full bodies)
  - <SESSION_ID>.cookies.json — all cookies seen, keyed by host
  - <SESSION_ID>.rewards.json — JSON responses that look like reward/gacha/pack payloads
  - console printout of cookies + reward endpoints as they arrive
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from mitmproxy import ctx, http, websocket

# ---------------------------------------------------------------------------
# Configuration (env overrides)
# ---------------------------------------------------------------------------
OUT_DIR = Path(os.environ.get("CAPTURE_OUT", "farm_3phones/capture"))
DUMP_BODIES = os.environ.get("DUMP_BODIES", "0") == "1"
REWARD_KEYWORDS = tuple(
    os.environ.get("REWARD_KEYWORDS",
                   "reward,gacha,pack,box,open,unpack,xp,card,elo,badge,coin,ticket,key,item,loot,drops,pull,mystery,rare,elite,shiny").lower().split(",")
)
SESSION_ID = os.environ.get("CAPTURE_SESSION", datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
OUT_DIR.mkdir(parents=True, exist_ok=True)

_session: Optional[http.HTTPFlow] = None

# In-memory aggregators (also flushed to disk incrementally)
cookies: Dict[str, List[Dict[str, Any]]] = {}
reward_payloads: List[Dict[str, Any]] = []
flow_index: List[Dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _flow_summary(f: http.HTTPFlow) -> Dict[str, Any]:
    """Lightweight per-flow metadata (cheap to store even when dumping thousands)."""
    req = f.request
    return {
        "id": getattr(f, "id", str(uuid.uuid4())),
        "session": SESSION_ID,
        "timestamp": _now_iso(),
        "method": req.method,
        "url": req.url,
        "host": req.host,
        "port": req.port,
        "path": req.path,
        "headers": _header_dict(req.headers),
        "status_code": f.response.status_code if f.response else None,
        "response_headers": _header_dict(f.response.headers) if f.response else None,
        "response_content_type": (f.response.headers.get("content-type") or "").lower() if f.response else None,
        "response_size": len(f.response.raw_content) if f.response else 0,
        "tcp_error": str(f.error) if f.error else None,
    }


def _header_dict(headers: http.Headers) -> Dict[str, str]:
    return {k: v for k, v in headers.items()}


def _try_parse_json(data: bytes) -> Any:
    try:
        return json.loads(data.decode("utf-8", errors="replace"))
    except (ValueError, UnicodeDecodeError):
        return None


def _is_reward_json(obj: Any) -> bool:
    """Heuristic: does this parsed JSON look like a reward/gacha/pack payload?"""
    if not isinstance(obj, dict):
        return False
    blob = json.dumps(obj).lower()
    hits = [k for k in REWARD_KEYWORDS if k in blob]
    if not hits:
        return False
    # require at least one "value-y" field to reduce noise (code-only JSON)
    value_fields = ("reward", "packs", "cards", "items", "coins", "xp", "tickets", "keys",
                    "boxes", "opens", "results", "data", "list", "draws", "pack_open")
    if not any(k in blob for k in value_fields):
        return False
    return True


def _extract_cookies(host: str, request: http.Request, response: http.Response) -> None:
    """Collect Set-Cookie from response + Cookie from request per host."""
    host_lower = host.lower()
    # Response cookies
    for raw in response.headers.get_all("set-cookie"):
        cookies.setdefault(host_lower, [])
        cookies[host_lower].append({
            "source": "response",
            "timestamp": _now_iso(),
            "flow_id": getattr(request, "id", ""),
            "url": request.url,
            "raw": raw,
        })
    # Request cookies (session tokens already held by client)
    req_cookie_hdr = request.headers.get("cookie")
    if req_cookie_hdr:
        cookies.setdefault(host_lower, [])
        cookies[host_lower].append({
            "source": "request",
            "timestamp": _now_iso(),
            "flow_id": getattr(request, "id", ""),
            "url": request.url,
            "raw": req_cookie_hdr,
        })


def _flush_cookies() -> None:
    path = OUT_DIR / f"{SESSION_ID}.cookies.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, default=str)
    ctx.log.info(f"[capture] cookies -> {path} ({sum(len(v) for v in cookies.values())} entries)")


def _flush_rewards() -> None:
    path = OUT_DIR / f"{SESSION_ID}.rewards.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(reward_payloads, f, indent=2, default=str)
    ctx.log.info(f"[capture] rewards -> {path} ({len(reward_payloads)} payloads)")


def _flush_flow_index() -> None:
    path = OUT_DIR / f"{SESSION_ID}.flows.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(flow_index, f, indent=2, default=str)
    ctx.log.info(f"[capture] flows -> {path} ({len(flow_index)} flows)")


def _maybe_dump_bodies(f: http.HTTPFlow) -> Dict[str, Any]:
    out = {}
    if DUMP_BODIES:
        if f.request.body:
            out["request_body_base64"] = base64.b64encode(f.request.body).decode()
            out["request_body_text"] = f.request.get_text()
        if f.response and f.response.raw_content:
            out["response_body_base64"] = base64.b64encode(f.response.raw_content).decode()
            out["response_body_text"] = f.response.get_text()
    return out


# ---------------------------------------------------------------------------
# Core hooks
# ---------------------------------------------------------------------------
def request(f: http.HTTPFlow) -> None:
    # Track cookies sent by client
    _extract_cookies(f.request.host, f.request, f.response if f.response else http.Response.make(0))
    flow_index.append(_flow_summary(f))


def response(f: http.HTTPFlow) -> None:
    fh = _flow_summary(f)
    flow_index[-1] = fh  # replace placeholder with completed summary

    # Cookies
    _extract_cookies(f.request.host, f.request, f.response)
    if f.response:
        _extract_cookies(f.request.host, f.request, f.response)

    # Bodies
    bodies = _maybe_dump_bodies(f)
    fh.update(bodies)

    # Cookie delta to disk incrementally (avoid losing data if we crash)
    if len(cookies) > 0 and len(cookies) % 50 == 0:
        _flush_cookies()
        _flush_flow_index()

    # Reward/gacha/json payload capture
    if f.response and f.response.content:
        parsed = _try_parse_json(f.response.raw_content)
        if parsed is not None:
            fh["parsed_json"] = True
            if _is_reward_json(parsed):
                entry = {
                    "flow_id": getattr(f, "id", ""),
                    "timestamp": _now_iso(),
                    "host": f.request.host,
                    "url": f.request.url,
                    "method": f.request.method,
                    "path": f.request.path,
                    "request_headers": _header_dict(f.request.headers),
                    "response_status": f.response.status_code,
                    "response_headers": _header_dict(f.response.headers),
                    "json": parsed,
                }
                if DUMP_BODIES:
                    entry["request_body"] = f.request.get_text()
                    entry["response_body"] = f.response.get_text()
                reward_payloads.append(entry)
                ctx.log.info(
                    "[reward] %s %s -> %d :: %s" %
                    (f.request.method, f.request.url, f.response.status_code, f.request.host)
                )
                _flush_rewards()
                _flush_flow_index()
        else:
            fh["parsed_json"] = False


def error(f: http.HTTPFlow) -> None:
    ctx.log.info("[capture.error] %s %s -> %s" % (f.request.method, f.request.url, f.error))
    if flow_index:
        flow_index[-1]["tcp_error"] = str(f.error)


# ---------------------------------------------------------------------------
# WebSocket support
# ---------------------------------------------------------------------------
def websocket_start(f: http.HTTPFlow) -> None:
    ctx.log.info("[capture.ws] upgrade %s %s" % (f.request.method, f.request.url))


def websocket_message(f: http.HTTPFlow) -> None:
    msg = f.ws.messages[-1]
    direction = "<" if msg.from_client else ">"
    try:
        text = msg.text
    except Exception:
        text = base64.b64encode(msg.bytes).decode()
    ctx.log.info("[capture.ws] %s %s: %s" % (direction, f.request.url, text[:500]))


def websocket_end(f: http.HTTPFlow) -> None:
    ctx.log.info("[capture.ws] close %s" % f.request.url)


# ---------------------------------------------------------------------------
# Summary on addon shutdown
# ---------------------------------------------------------------------------
def done() -> None:
    _flush_cookies()
    _flush_rewards()
    _flush_flow_index()
    # Console summary
    ctx.log.info("=" * 70)
    ctx.log.info("[capture] SESSION %s DONE" % SESSION_ID)
    ctx.log.info("[capture] total flows: %d" % len(flow_index))
    ctx.log.info("[capture] total cookies: %d  (hosts: %d)" %
                 (sum(len(v) for v in cookies.values()), len(cookies)))
    ctx.log.info("[capture] reward payloads: %d" % len(reward_payloads))
    # Show unique reward hosts
    reward_hosts = sorted({r["host"] for r in reward_payloads})
    if reward_hosts:
        ctx.log.info("[capture] reward hosts: %s" % ", ".join(reward_hosts))
    # Show cookie hosts
    cookie_hosts = sorted(cookies.keys())
    if cookie_hosts:
        ctx.log.info("[capture] cookie hosts: %s" % ", ".join(cookie_hosts))
    ctx.log.info("=" * 70)
