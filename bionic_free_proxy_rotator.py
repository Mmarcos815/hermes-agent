#!/usr/bin/env python3
"""
BIONIC PROXY ROTATOR — Maximum Extraction
Forces free proxies to work through Tor chaining, multiple endpoints, and aggressive validation.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import requests
import json
import random
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────
TEST_URLS = [
    "https://api.ipify.org?format=json",
    "https://ipinfo.io/json",
    "https://httpbin.org/ip",
    "https://api.myip.com",
]

# Fresh proxy sources (prioritized)
FAST_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXY_LIST/master/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/ALBMINDBOI/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt",
    "https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/AnasAito/ProXee/main/proxies/http.txt",
    "https://raw.githubusercontent.com/AnasAito/ProXee/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/AnasAito/ProXee/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/ErcinDedeoglu/Proxies/main/Proxies/proxy.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/free.txt",
    "https://raw.githubusercontent.com/yuceltoluyag/Proxy/main/proxy.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/mallorson/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/BlackCage/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/HTTP.txt",
    "https://raw.githubusercontent.com/andykmc/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/hendrikbgr/Free-Proxy-List/master/proxy_list.txt",
]

# ── PROXY PARSER ─────────────────────────────────────────────────────────
def parse_proxies(text):
    """Extract IP:PORT from raw text."""
    proxies = set()
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        for part in line.split():
            if ':' in part:
                p = part.split(':')
                if len(p) == 2 and p[1].isdigit():
                    ip, port = p
                    if 0 < int(port) < 65536:
                        ip_parts = ip.split('.')
                        if len(ip_parts) == 4 and all(x.isdigit() and 0 <= int(x) <= 255 for x in ip_parts):
                            proxies.add(f"{ip}:{port}")
    return list(proxies)

def fetch_from_source(url):
    """Fetch proxies from a single source."""
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            return parse_proxies(resp.text)
    except:
        pass
    return []

def fetch_all_sources():
    """Fetch proxies from all sources."""
    all_proxies = set()
    for url in FAST_SOURCES:
        proxies = fetch_from_source(url)
        if proxies:
            all_proxies.update(proxies)
    return list(all_proxies)

# ── PROXY VALIDATOR ──────────────────────────────────────────────────────
def validate_proxy(proxy, timeout=4):
    """Test if proxy is working."""
    for test_url in TEST_URLS[:2]:
        try:
            resp = requests.get(
                test_url,
                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                timeout=timeout,
            )
            if resp.status_code == 200:
                return True
        except:
            continue
    return False

def validate_all_threaded(proxies, max_threads=100):
    """Validate all proxies with aggressive threading."""
    working = []
    dead = []
    lock = threading.Lock()
    count = [0]
    
    def test(proxy):
        result = validate_proxy(proxy)
        with lock:
            count[0] += 1
            if result:
                working.append(proxy)
            else:
                dead.append(proxy)
            if count[0] % 200 == 0:
                print(f"  Tested {count[0]}/{len(proxies)} ({len(working)} working)")
    
    threads = []
    for p in proxies:
        t = threading.Thread(target=test, args=(p,))
        threads.append(t)
        t.start()
        
        while len(threads) >= max_threads:
            for t in threads[:]:
                t.join(timeout=0.05)
                if not t.is_alive():
                    threads.remove(t)
    
    for t in threads:
        t.join()
    
    return working, dead

# ── TOR INTEGRATION ──────────────────────────────────────────────────────
def start_tor_proxy():
    """Start Tor as a SOCKS proxy."""
    try:
        # Check if Tor is installed
        result = subprocess.run(["which", "tor"], capture_output=True, text=True)
        if result.returncode != 0:
            print("Tor not found. Installing...")
            subprocess.run(["pip", "install", "requests[socks]"], capture_output=True)
            return None
        
        # Start Tor
        tor_process = subprocess.Popen(
            ["tor", "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(5)
        return tor_process
    except:
        return None

def get_tor_session():
    """Get a requests session through Tor."""
    session = requests.Session()
    session.proxies = {
        'http': 'socks5://127.0.0.1:9050',
        'https': 'socks5://127.0.0.1:9050',
    }
    return session

# ── PROXY ROTATOR ────────────────────────────────────────────────────────
class BionicProxyRotator:
    def __init__(self):
        self.proxies = []
        self.failed = set()
        self.tor_process = None
        self.stats = {"total_requests": 0, "successful": 0, "failed": 0}
    
    def build(self):
        """Build the proxy list."""
        print("=" * 60)
        print("BIONIC PROXY ROTATOR — BUILD")
        print("=" * 60)
        
        # Fetch
        print("\n[1] Fetching proxies...")
        proxies = fetch_all_sources()
        print(f"Fetched {len(proxies)} proxies")
        
        # Validate
        print(f"\n[2] Validating {len(proxies)} proxies...")
        working, dead = validate_all_threaded(proxies)
        print(f"\n{len(working)} working, {len(dead)} dead")
        
        self.proxies = working
        
        # Save
        Path.home().joinpath('.bionic_proxy').mkdir(parents=True, exist_ok=True)
        with open(Path.home() / '.bionic_proxy' / 'working_proxies.json', 'w') as f:
            json.dump({
                'working': working,
                'total_fetched': len(proxies),
                'timestamp': datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"\n[3] Saved to ~/.bionic_proxy/working_proxies.json")
        
        return working
    
    def load(self):
        """Load proxies from file."""
        proxy_file = Path.home() / '.bionic_proxy' / 'working_proxies.json'
        if proxy_file.exists():
            with open(proxy_file) as f:
                data = json.load(f)
            self.proxies = data.get('working', [])
            return self.proxies
        return []
    
    def get(self):
        """Get a random working proxy."""
        if not self.proxies:
            self.load()
        
        available = [p for p in self.proxies if p not in self.failed]
        if not available:
            self.failed.clear()  # Reset if all failed
            available = self.proxies
        
        if not available:
            return None
        
        proxy = random.choice(available)
        self.stats["total_requests"] += 1
        
        return {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
            "proxy": proxy,
        }
    
    def mark_failed(self, proxy):
        self.failed.add(proxy)
        self.stats["failed"] += 1
    
    def mark_success(self, proxy):
        self.stats["successful"] += 1
    
    def get_stats(self):
        return {
            "total_proxies": len(self.proxies),
            "working": len(self.proxies) - len(self.failed),
            "failed_count": len(self.failed),
            **self.stats,
        }

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bionic_free_proxy_rotator.py build|test|stats|get")
        sys.exit(1)
    
    cmd = sys.argv[1]
    rotator = BionicProxyRotator()
    
    if cmd == "build":
        rotator.build()
    
    elif cmd == "get":
        proxies = rotator.load()
        if proxies:
            proxy = rotator.get()
            print(json.dumps(proxy, indent=2))
        else:
            print("No proxies found. Run 'build' first.")
    
    elif cmd == "stats":
        stats = rotator.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif cmd == "test":
        proxy = rotator.get()
        if proxy:
            print(f"Testing {proxy['proxy']}...")
            resp = requests.get("https://httpbin.org/ip", proxies={"http": proxy['http'], "https": proxy['https']}, timeout=5)
            print(f"Response: {resp.status_code}")
        else:
            print("No proxies available.")
