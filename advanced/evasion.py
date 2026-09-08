#!/usr/bin/env python3
"""
evasion.py — Evasion technique demonstration engine (EDUCATIONAL / LAB ONLY).

Demonstrates payload encoding, jitter, User-Agent rotation, domain fronting,
and process injection patterns for authorized security training labs, CTFs,
and red-team engagements with signed Rules of Engagement.

Safety: All demos are OUTPUT ONLY — no network traffic, no process injection.
"""

import argparse, base64, hashlib, os, random, sys, time


# ── 1. Payload Encoding ────────────────────────────────────────────────

def encode_base64(p: bytes) -> str:
    return base64.b64encode(p).decode()

def encode_hex(p: bytes) -> str:
    return p.hex()

def xor_encode(payload: bytes, key: bytes = None):
    key = key or os.urandom(random.randint(8, 32))
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(payload)), key

def aes_encrypt(plaintext: bytes, key=None, iv=None) -> dict:
    """AES-256-CBC. Falls back to AES-shaped XOR if no crypto lib installed."""
    def _xor_fallback(k, i, d):
        pad = 16 - (len(d) % 16)
        p = d + bytes([pad] * pad)
        ki = hashlib.sha256(k + i).digest()
        out, prev = bytearray(len(p)), i
        for j in range(0, len(p), 16):
            blk = bytes(a ^ b for a, b in zip(p[j : j + 16], prev))
            out[j : j + 16] = bytes(b ^ ki[idx % 32] for idx, b in enumerate(blk))
            prev = out[j : j + 16]
        return bytes(out)

    _enc = _xor_fallback
    try:
        AES = __import__("Crypto.Cipher.AES", fromlist=["AES"])
        _enc = lambda k, i, d: AES.new(k, AES.MODE_CBC, i).encrypt(
            d + bytes([16 - len(d) % 16] * (16 - len(d) % 16)))
    except ImportError:
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            def _enc(k, i, d):
                pad = 16 - len(d) % 16
                c = Cipher(algorithms.AES(k), modes.CBC(i), backend=default_backend())
                e = c.encryptor()
                return e.update(d + bytes([pad] * pad)) + e.finalize()
        except ImportError:
            pass

    key, iv = key or os.urandom(32), iv or os.urandom(16)
    return {
        "cipher": "AES-256-CBC",
        "ciphertext": base64.b64encode(_enc(key, iv, plaintext)).decode(),
        "key": base64.b64encode(key).decode(),
        "iv": base64.b64encode(iv).decode(),
    }


# ── 2. Jitter Randomization ─────────────────────────────────────────────

class Jitter:
    """Randomize beacon timing to evade detection."""
    def __init__(self, min_d=0.5, max_d=5.0, var=0.3):
        self.min_d, self.max_d, self.var = min_d, max_d, var

    def sleep(self) -> float:
        d = random.uniform(self.min_d, self.max_d) * (1 + random.uniform(-self.var, self.var))
        d = max(0.01, d)
        time.sleep(d)
        return d

    def next_beacon(self, base=60.0) -> float:
        return base * (1 + random.uniform(-self.var, self.var))


# ── 3. User-Agent Rotation ──────────────────────────────────────────────

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "curl/8.4.0",
]

class UARotator:
    def __init__(self, pool=None, strategy="random"):
        self.pool, self.strategy, self._idx = pool or UA_POOL, strategy, 0

    def next(self) -> str:
        if self.strategy == "random":
            return random.choice(self.pool)
        ua = self.pool[self._idx % len(self.pool)]
        self._idx += 1
        return ua

    def custom(self, browser="chrome", os="windows"):
        v = f"{random.randint(120, 130)}.0.{random.randint(4000, 6000)}.{random.randint(0, 200)}"
        return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v} Safari/537.36"


# ── 4. Domain Fronting ──────────────────────────────────────────────────

class DomainFront:
    """Traffic appears to go to front domain, Host header routes to target."""
    CDNs = ["azureedge.net", "cloudfront.net", "akamai.net", "fastly.net", "googleapis.com"]

    def __init__(self, front, target, cdn=None):
        self.front, self.target, self.cdn = front, target, cdn or random.choice(self.CDNs)

    def request(self, path="/", headers=None) -> dict:
        return {
            "dns_query": f"cdn-front.{self.front}",
            "tls_sni": f"cdn-front.{self.front}",
            "http_host_header": self.target,
            "path": path,
            "headers": {
                "Host": self.target,
                "User-Agent": UARotator().next(),
                "X-Forwarded-For": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                **(headers or {}),
            },
            "observable": self.front,
            "actual": self.target,
        }

    def explain(self) -> str:
        return f"Front: DNS/SNI = '{self.front}' (legitimate CDN) | Host header = '{self.target}' (hidden backend)"


# ── 5. Process Injection (SIMULATION ONLY) ──────────────────────────────

INJECTION_DATA = {
    "reflective_dll": {
        "steps": [
            "OpenProcess() → acquire target handle",
            "VirtualAllocEx() → allocate RWX memory",
            "WriteProcessMemory() → copy reflective loader + DLL",
            "CreateRemoteThread() → invoke loader entry",
            "Loader resolves imports, calls DllMain()",
        ],
        "indicators": ["RWX memory region", "thread start in unmapped memory"],
        "rules": ["Sysmon E8 cross-process CreateRemoteThread", "VirtualAllocEx RWX from unexpected source"],
    },
    "process_hollowing": {
        "steps": [
            "CreateProcess(target, CREATE_SUSPENDED)",
            "NtUnmapViewOfSection() → hollow original image",
            "VirtualAllocEx() → allocate for payload",
            "WriteProcessMemory() → write payload PE",
            "SetThreadContext() → redirect entry point",
            "ResumeThread() → execute payload",
        ],
        "indicators": ["process suspended then resumed", "image base mismatch"],
        "rules": ["Sysmon E1/10 mismatched image path", "suspended child then resumed"],
    },
    "apc_injection": {
        "steps": [
            "OpenProcess() → target handle",
            "VirtualAllocEx() + WriteProcessMemory() → payload",
            "QueueUserAPC() → add to alertable thread",
            "Target enters alertable state → executes",
        ],
        "indicators": ["alertable thread", "cross-process APC"],
        "rules": ["Thread in alertable state receiving cross-process APC"],
    },
    "thread_hijack": {
        "steps": [
            "CreateProcess(target, CREATE_SUSPENDED)",
            "VirtualAllocEx() + WriteProcessMemory() → payload",
            "SuspendThread() on target",
            "GetThreadContext() → save registers",
            "SetThreadContext() → redirect RIP/EIP",
            "ResumeThread()",
        ],
        "indicators": ["thread context modified", "RIP in injected region"],
        "rules": ["Cross-process SetThreadContext"],
    },
}

def gen_stub(size=64):
    stub = [0x90] * min(size, 64)
    stub[0], stub[1], stub[-2] = 0xEB, 0x05, 0xCC
    return " ".join(f"{b:02X}" for b in stub) + " ..."

def injection_demo(technique: str, target: str):
    d = INJECTION_DATA[technique]
    return {
        "technique": technique,
        "target": target,
        "shellcode_stub": gen_stub(),
        "steps": [f"{i+1}. {s}" for i, s in enumerate(d["steps"])],
        "indicators": d["indicators"],
        "detection_rules": d["rules"],
    }


# ── Demo functions ──────────────────────────────────────────────────────

def demo_encode(pay):
    print("\n=== Payload Encoding ===")
    d = pay.encode()
    print(f"[Original] {pay}")
    print(f"[Base64 ] {encode_base64(d)}")
    print(f"[Hex    ] {encode_hex(d)}")
    enc, k = xor_encode(d)
    print(f"[XOR    ] key={k.hex()}")
    a = aes_encrypt(d)
    print(f"[AES-256] ct={a['ciphertext'][:60]}...")

def demo_jitter(mn, mx):
    print(f"\n=== Jitter ({mn}s-{mx}s) ===")
    j = Jitter(mn, mx)
    for i in range(5):
        print(f"  Beacon {i+1}: {j.sleep():.3f}s")

def demo_ua(n):
    print("\n=== User-Agent Rotation ===")
    r = UARotator()
    for i in range(n):
        print(f"  [{i+1}] {r.next()}")

def demo_fronting(front, target):
    print(f"\n=== Domain Fronting ===")
    df = DomainFront(front, target)
    print(df.explain())
    req = df.request("/api/v1/beacon")
    for k, v in req.items():
        print(f"  {k}: {v}")

def demo_injection(tech, target):
    print(f"\n=== Process Injection ({tech}) ===")
    r = injection_demo(tech, target)
    print(f"Target: {r['target']} | Stub: {r['shellcode_stub']}")
    for s in r["steps"]:
        print(f"  {s}")
    print("Indicators: " + ", ".join(f"⚠ {x}" for x in r["indicators"]))
    print("Rules:      " + ", ".join(f"🛡 {x}" for x in r["detection_rules"]))


# ── CLI ──────────────────────────────────────────────────────────────────

def main(argv=None):
    p = argparse.ArgumentParser(description="Evasion engine (lab only)")
    p.add_argument("--demo-encode", action="store_true")
    p.add_argument("--payload", default="SELECT * FROM users")
    p.add_argument("--demo-jitter", action="store_true")
    p.add_argument("--min", type=float, default=0.5)
    p.add_argument("--max", type=float, default=3.0)
    p.add_argument("--demo-ua", action="store_true")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--demo-fronting", action="store_true")
    p.add_argument("--target", default="api.c2-backend.internal")
    p.add_argument("--front", default="cdn.microsoft.com")
    p.add_argument("--demo-injection", action="store_true")
    p.add_argument("--technique", default="process_hollowing", choices=list(INJECTION_DATA))
    a = p.parse_args(argv)
    if not any([a.demo_encode, a.demo_jitter, a.demo_ua, a.demo_fronting, a.demo_injection]):
        p.print_help()
        return 0
    if a.demo_encode: demo_encode(a.payload)
    if a.demo_jitter: demo_jitter(a.min, a.max)
    if a.demo_ua: demo_ua(a.count)
    if a.demo_fronting: demo_fronting(a.front, a.target)
    if a.demo_injection: demo_injection(a.technique, a.target)
    return 0

if __name__ == "__main__":
    sys.exit(main())
