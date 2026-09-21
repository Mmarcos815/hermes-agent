#!/usr/bin/env python3
"""hCaptcha Solver Pipeline — production implementation.
Capture (Playwright) → Solve (2Captcha / CapSolver) → Use (httpx POST).

Requirements:
  pip install playwright beautifulsoup4 httpx
  playwright install chromium
"""

import asyncio
import hashlib
import logging
import random
import re
import time
from base64 import b64encode
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
log = logging.getLogger("hcaptcha-pipeline")


@dataclass
class Config:
    site_key: str = ""
    site_url: str = "https://example.com"
    proxy: Optional[str] = None
    proxy_list: Optional[List[str]] = None
    timeout: float = 30.0
    max_retries: int = 3
    solver_provider: str = "2captcha"
    api_key: str = ""
    httpx_timeout: float = 30.0
    poll_interval: float = 5.0
    poll_timeout: float = 120.0


@dataclass
class Challenge:
    sitekey: str
    site_url: str
    page_url: str
    rqtoken: Optional[str] = None
    image_b64: Optional[str] = None
    image_url: Optional[str] = None
    task_html: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Solution:
    token: str
    challenge_type: str = "unknown"
    latency_ms: float = 0.0
    provider: str = "unknown"
    solved_at: float = field(default_factory=time.time)
    task_id: Optional[str] = None


@dataclass
class UseResult:
    page_url: str
    status_code: int
    provider: str
    latency_ms: float
    solved_at: float
    response_body: Optional[str] = None
    error: Optional[str] = None


class HcaptchaError(Exception):
    pass


class SiteKeyMissingError(HcaptchaError):
    pass


class BalanceError(HcaptchaError):
    pass


class RateLimitError(HcaptchaError):
    pass


class SolveTimeoutError(HcaptchaError):
    pass


class NetworkError(HcaptchaError):
    pass


class BaseSolver:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    async def solve(self, challenge: Challenge) -> Solution:
        raise NotImplementedError

    def _make_client(self) -> httpx.AsyncClient:
        proxy_url = self.cfg.proxy or (self.cfg.proxy_list[0] if self.cfg.proxy_list else None)
        proxies = {}
        if proxy_url:
            proxies["http://"] = proxy_url
            proxies["https://"] = proxy_url
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self.cfg.httpx_timeout),
            proxies=proxies if proxies else None,
            follow_redirects=True,
        )


class CaptchaSolver2Captcha(BaseSolver):
    API_URL = "https://api.2captcha.com"

    async def solve(self, challenge: Challenge) -> Solution:
        api_key = self.cfg.api_key
        if not api_key:
            raise HcaptchaError("2Captcha API key not configured")

        client = self._make_client()
        try:
            submit_url = f"{self.API_URL}/in.php"
            data = {
                "key": api_key,
                "method": "userrecaptcha",
                "googlekey": challenge.sitekey,
                "pageurl": challenge.page_url,
                "json": 1,
            }
            log.debug(f"[2Captcha] submitting task")
            resp = await client.post(submit_url, data=data)
            await self._check_errors(resp, "submit")

            body = resp.json()
            if body.get("status") != 1:
                raise HcaptchaError(f"2Captcha submit rejected: {body.get('request', '')}")

            task_id = body["request"]
            log.info(f"[2Captcha] task_id={task_id}")

            return await self._poll(client, task_id, api_key, "2captcha")

        finally:
            await client.aclose()

    async def _poll(self, client: httpx.AsyncClient, task_id: str, api_key: str, provider: str) -> Solution:
        poll_url = f"{self.API_URL}/res.php"
        deadline = time.monotonic() + self.cfg.poll_timeout
        t0 = time.monotonic()

        while time.monotonic() < deadline:
            await asyncio.sleep(self.cfg.poll_interval)
            params = {"key": api_key, "action": "get", "id": task_id, "json": 1}
            resp = await client.get(poll_url, params=params)
            await self._check_errors(resp, "poll")
            body = resp.json()
            request = body.get("request", "")

            if body.get("status") == 1:
                latency_ms = (time.monotonic() - t0) * 1000
                return Solution(token=request, challenge_type="hcaptcha", latency_ms=latency_ms, provider=provider, task_id=task_id)

            if "ERROR_NO_BALANCE" in request:
                raise BalanceError("2Captcha: insufficient balance")
            if "ERROR_NO_SLOT" in request or "Too many requests" in request:
                raise RateLimitError(f"2Captcha: {request}")
            if "ERROR_CAPTCHA_UNSOLVABLE" in request:
                raise HcaptchaError(f"2Captcha: unsolvable: {request}")

            log.debug(f"[2Captcha] poll: {request}")

        raise SolveTimeoutError(f"2Captcha: timeout after {self.cfg.poll_timeout}s, task={task_id}")

    async def _check_errors(self, resp: httpx.Response, stage: str) -> None:
        if resp.status_code == 429:
            raise RateLimitError(f"2Captcha {stage}: 429")
        if resp.status_code >= 500:
            raise NetworkError(f"2Captcha {stage}: server error {resp.status_code}")
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise NetworkError(f"2Captcha {stage}: HTTP {e.response.status_code}")


class CaptchaSolverCapSolver(BaseSolver):
    API_URL = "https://api.capsolver.com"

    async def solve(self, challenge: Challenge) -> Solution:
        api_key = self.cfg.api_key
        if not api_key:
            raise HcaptchaError("CapSolver API key not configured")

        client = self._make_client()
        try:
            create_url = f"{self.API_URL}/task"
            payload = {
                "clientKey": api_key,
                "task": {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": challenge.page_url,
                    "websiteKey": challenge.sitekey,
                },
            }
            log.debug(f"[CapSolver] creating task")
            resp = await client.post(create_url, json=payload)
            await self._check_errors(resp, "create")
            body = resp.json()
            task_id = body.get("taskId")
            if not task_id:
                error = body.get("errorDescription", body.get("error", "unknown"))
                raise HcaptchaError(f"CapSolver create failed: {error}")
            log.info(f"[CapSolver] task_id={task_id}")
            return await self._poll(client, task_id, api_key, "capsolver")
        finally:
            await client.aclose()

    async def _poll(self, client: httpx.AsyncClient, task_id: str, api_key: str, provider: str) -> Solution:
        poll_url = f"{self.API_URL}/getTaskResult"
        deadline = time.monotonic() + self.cfg.poll_timeout
        t0 = time.monotonic()

        while time.monotonic() < deadline:
            await asyncio.sleep(self.cfg.poll_interval)
            resp = await client.post(poll_url, json={"clientKey": api_key, "taskId": task_id})
            await self._check_errors(resp, "poll")
            body = resp.json()

            if body.get("status") == "ready":
                solution_data = body.get("solution", {})
                token = solution_data.get("gRecaptchaResponse") or solution_data.get("token", "")
                if not token:
                    raise HcaptchaError("CapSolver: empty solution")
                latency_ms = (time.monotonic() - t0) * 1000
                return Solution(token=token, challenge_type="hcaptcha", latency_ms=latency_ms, provider=provider, task_id=task_id)

            if body.get("status") == "failed":
                err = body.get("errorDescription", "unknown")
                raise HcaptchaError(f"CapSolver task failed: {err}")

            if "ERROR_NO_BALANCE" in str(body):
                raise BalanceError("CapSolver: insufficient balance")
            if "RATE_LIMIT" in str(body):
                raise RateLimitError("CapSolver: rate limited")

            log.debug(f"[CapSolver] poll: status={body.get('status')}")

        raise SolveTimeoutError(f"CapSolver: timeout after {self.cfg.poll_timeout}s, task={task_id}")

    async def _check_errors(self, resp: httpx.Response, stage: str) -> None:
        if resp.status_code == 429:
            raise RateLimitError(f"CapSolver {stage}: 429")
        if resp.status_code >= 500:
            raise NetworkError(f"CapSolver {stage}: server error {resp.status_code}")
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise NetworkError(f"CapSolver {stage}: HTTP {e.response.status_code}")


class CaptchaSolverSimulated(BaseSolver):
    async def solve(self, challenge: Challenge) -> Solution:
        log.info(f"[SIMULATED] solving sitekey={challenge.sitekey[:10]}...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        token = hashlib.sha256(f"{challenge.sitekey}{challenge.page_url}{time.time()}{random.random()}".encode()).hexdigest()
        return Solution(token=token, challenge_type="simulated", latency_ms=0.0, provider="simulated")


def make_solver(cfg: Config) -> BaseSolver:
    registry = {"2captcha": CaptchaSolver2Captcha, "capsolver": CaptchaSolverCapSolver, "simulated": CaptchaSolverSimulated}
    cls = registry.get(cfg.solver_provider)
    if cls is None:
        log.warning(f"unknown solver '{cfg.solver_provider}' -> simulated")
        return CaptchaSolverSimulated(cfg)
    return cls(cfg)


class BrowserDriver:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._proxy_index = 0

    async def start(self) -> None:
        self._pw = await async_playwright().start()
        proxy_url = self.cfg.proxy or (self.cfg.proxy_list[self._proxy_index % len(self.cfg.proxy_list)] if self.cfg.proxy_list else None)
        if self._proxy_index == 0 and self.cfg.proxy_list:
            self._proxy_index += 1

        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]

        self._browser = await self._pw.chromium.launch(
            headless=True,
            args=args,
            proxy={"server": proxy_url} if proxy_url else None,
        )

        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Connection": "keep-alive",
            },
        )

        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        self._page = await self._context.new_page()

    async def rotate_proxy(self) -> None:
        if self._context:
            await self._context.close()
        proxy_url = self.cfg.proxy or (self.cfg.proxy_list[self._proxy_index % len(self.cfg.proxy_list)] if self.cfg.proxy_list else None)
        if self.cfg.proxy_list:
            self._proxy_index += 1

        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            proxy={"server": proxy_url} if proxy_url else None,
        )
        await self._context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        self._page = await self._context.new_page()
        log.info(f"[BROWSER] rotated proxy to {proxy_url}")

    async def extract_hcaptcha(self, page_url: str) -> Challenge:
        log.info(f"[BROWSER] loading {page_url}")
        try:
            await self._page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            raise NetworkError(f"failed to load page: {e}")

        try:
            await self._page.wait_for_selector('iframe[src*="hcaptcha.com"]', timeout=15000)
        except Exception:
            log.warning("[BROWSER] hCaptcha iframe not found within 15s")

        html = await self._page.content()
        return self._parse(html, page_url)

    def _parse(self, html: str, page_url: str) -> Challenge:
        soup = BeautifulSoup(html, "lxml")
        sitekey = self.cfg.site_key or ""

        if not sitekey:
            for el in soup.find_all(attrs={"data-sitekey": True}):
                sitekey = el["data-sitekey"]
                break

        if not sitekey:
            for iframe in soup.find_all("iframe"):
                src = iframe.get("src", "")
                if "hcaptcha.com" in src:
                    m = re.search(r"[?&](?:sitekey|sc)=([a-zA-Z0-9_-]{10,60})", src)
                    if m:
                        sitekey = m.group(1)
                        break
                    m2 = re.search(r"[?&]id=([a-zA-Z0-9_-]{10,60})", src)
                    if m2:
                        sitekey = m2.group(1)
                        break

        if not sitekey:
            raise SiteKeyMissingError(f"Could not find hCaptcha sitekey on {page_url}. Pass --sitekey explicitly.")

        metadata = {"title": soup.title.string.strip() if soup.title and soup.title.string else "", "viewport": "1920x1080"}
        for el in soup.find_all(attrs={"data-rqtoken": True}):
            metadata["rqtoken"] = el["data-rqtoken"]
            break

        log.info(f"[BROWSER] extracted sitekey={sitekey[:12]}... from {page_url}")
        return Challenge(sitekey=sitekey, site_url=self.cfg.site_url, page_url=page_url, metadata=metadata)

    async def close(self) -> None:
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()


class UseStage:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    async def submit(self, page_url: str, solution: Solution, proxy_rotation: bool = False) -> UseResult:
        t0 = time.monotonic()
        client = self._make_client()
        try:
            target_url = self.cfg.site_url.rstrip("/") if self.cfg.site_url and not self.cfg.site_url.startswith("https://example.com") else page_url.rstrip("/")
            payload = {"h-captcha-response": solution.token}
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Origin": self._origin(target_url),
                "Referer": page_url,
            }
            log.info(f"[USE] POST {target_url} (token_len={len(solution.token)})")
            resp = await client.post(target_url, data=payload, headers=headers, timeout=httpx.Timeout(self.cfg.httpx_timeout))

            if resp.status_code == 429:
                log.warning("[USE] 429 rate limited")
                if proxy_rotation and self.cfg.proxy_list:
                    raise RateLimitError("target returned 429 — rotate proxy")

            latency_ms = (time.monotonic() - t0) * 1000
            return UseResult(
                page_url=page_url,
                status_code=resp.status_code,
                provider=solution.provider,
                latency_ms=latency_ms,
                solved_at=solution.solved_at,
                response_body=resp.text[:2000],
            )
        except httpx.TimeoutException:
            raise NetworkError(f"POST timed out after {self.cfg.httpx_timeout}s")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"HTTP 429: {e.response.text[:200]}")
            raise NetworkError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.ProxyError as e:
            raise NetworkError(f"proxy error: {e}")
        finally:
            await client.aclose()

    def _make_client(self) -> httpx.AsyncClient:
        proxy_url = self.cfg.proxy or (self.cfg.proxy_list[0] if self.cfg.proxy_list else None)
        proxies = {}
        if proxy_url:
            proxies["http://"] = proxy_url
            proxies["https://"] = proxy_url
        return httpx.AsyncClient(timeout=httpx.Timeout(self.cfg.httpx_timeout), proxies=proxies if proxies else None, follow_redirects=True)

    def _origin(self, url: str) -> str:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"


class Pipeline:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.browser = BrowserDriver(self.cfg)
        self.solver = make_solver(self.cfg)
        self.use_stage = UseStage(self.cfg)

    async def run(self, page_url: str, use_proxy_rotation: bool = True) -> Dict[str, Any]:
        log.info("=" * 60)
        log.info(f"Pipeline: {page_url}")
        log.info(f"  solver={self.cfg.solver_provider} proxy={'yes' if self.cfg.proxy or self.cfg.proxy_list else 'no'}")
        log.info("=" * 60)

        await self.browser.start()
        try:
            challenge = await self.browser.extract_hcaptcha(page_url)
        except Exception:
            await self.browser.close()
            raise

        try:
            solution = await self.solver.solve(challenge)
            log.info(f"[SOLVED] token_len={len(solution.token)} provider={solution.provider}")
        except Exception:
            await self.browser.close()
            raise

        await self.browser.close()

        try:
            result = await self.use_stage.submit(page_url, solution, proxy_rotation=use_proxy_rotation)
        except RateLimitError:
            if use_proxy_rotation and self.cfg.proxy_list:
                log.info("[PIPELINE] retrying after 429 with new proxy")
                await self.browser.start()
                try:
                    ch2 = await self.browser.extract_hcaptcha(page_url)
                except Exception:
                    ch2 = challenge
                try:
                    sol2 = await self.solver.solve(ch2)
                except Exception:
                    sol2 = solution
                await self.browser.close()
                result = await self.use_stage.submit(page_url, sol2, proxy_rotation=False)
            else:
                raise
        except Exception as e:
            raise HcaptchaError(f"use failed: {e}") from e

        log.info(f"[DONE] status={result.status_code} provider={result.provider} latency={result.latency_ms:.0f}ms")
        return {
            "page_url": result.page_url,
            "status_code": result.status_code,
            "provider": result.provider,
            "latency_ms": round(result.latency_ms, 1),
            "solved_at": result.solved_at,
            "response_body": result.response_body,
            "error": result.error,
            "token_used": solution.token[:16] + "..." if solution.token else None,
        }


def main():
    import argparse

    ap = argparse.ArgumentParser(description="hCaptcha solver pipeline — production")
    ap.add_argument("url", nargs="?", default="https://example.com/protected")
    ap.add_argument("-k", "--sitekey", default="")
    ap.add_argument("-p", "--provider", default="2captcha", choices=["2captcha", "capsolver", "simulated"])
    ap.add_argument("--api-key", default="")
    ap.add_argument("--proxy", default=None)
    ap.add_argument("--proxy-list", default=None)
    ap.add_argument("--site-url", default="")
    ap.add_argument("-t", "--timeout", type=float, default=30.0)
    ap.add_argument("--poll-interval", type=float, default=5.0)
    ap.add_argument("--poll-timeout", type=float, default=120.0)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    proxy_list = None
    if args.proxy_list:
        proxy_list = [p.strip() for p in args.proxy_list.split(",") if p.strip()]

    cfg = Config(
        site_key=args.sitekey,
        site_url=args.site_url or args.url,
        proxy=args.proxy,
        proxy_list=proxy_list,
        timeout=args.timeout,
        solver_provider=args.provider,
        api_key=args.api_key,
        httpx_timeout=args.timeout,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
    )

    async def _run():
        pipe = Pipeline(cfg)
        try:
            result = await pipe.run(args.url)
        except (HcaptchaError, NetworkError) as e:
            print(json.dumps({"error": str(e), "type": type(e).__name__}, indent=2))
            return
        print(json.dumps(result, indent=2))

    asyncio.run(_run())


if __name__ == "__main__":
    main()
