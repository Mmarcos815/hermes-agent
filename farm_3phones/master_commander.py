#!/usr/bin/env python3
"""
master_commander.py — Ultimate TCGplayer + Farm commander.
Ties together: search, deals, farm control, MITM, Frida, web analysis.

Commands:
  tcg search <query>     - Search TCGplayer
  tcg deals <query>      - Find deals under market price
  tcg track <pid>        - Track price history
  tcg product <pid>      - Full product details
  farm status            - Farm device status
  farm monitor           - Launch scrcpy monitors
  web analyze <url>      - Analyze checkout page
  apk scan <path>        - Scan APK for endpoints
  mitm start             - Start MITM capture
"""
import sys, subprocess, requests, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tcgplayer_bot.tcgplayer_ultimate import search, autocomplete, product_details, listings, price_history, find_deals

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json', 'Accept': 'application/json',
    'Origin': 'https://www.tcgplayer.com', 'Referer': 'https://www.tcgplayer.com/',
}

def cmd_search(args):
    if not args:
        print("Usage: master search <query>")
        return
    query = ' '.join(args)
    print(f"\n=== Searching TCGplayer: {query} ===")
    results = search(query, limit=20)
    for r in results:
        name = r.get('productName', '?')
        lowest = r.get('lowestPrice', '?')
        market = r.get('marketPrice', '?')
        median = r.get('medianPrice', '?')
        print(f"  {name[:45]:45s}  low=${lowest:>6}  market=${market:>6}  median=${median:>6}")

def cmd_deals(args):
    if not args:
        print("Usage: master deals <query>")
        return
    query = ' '.join(args)
    print(f"\n=== Finding deals: {query} ===")
    find_deals(query, max_price=50.0)

def cmd_track(args):
    if not args:
        print("Usage: master track <product_id>")
        return
    pid = int(args[0])
    print(f"\n=== Price history: {pid} ===")
    data = price_history(pid)
    print(json.dumps(data, indent=2)[:1500])

def cmd_product(args):
    if not args:
        print("Usage: master product <product_id>")
        return
    pid = int(args[0])
    print(f"\n=== Product details: {pid} ===")
    data = product_details(pid)
    print(f"Name: {data.get('productName', '?')}")
    print(f"Market: ${data.get('marketPrice', '?')}")
    print(f"Lowest: ${data.get('lowestPrice', '?')}")
    print(f"Median: ${data.get('medianPrice', '?')}")
    print(f"Set: {data.get('setName', '?')}")
    print(f"Rarity: {data.get('rarityName', '?')}")
    print(f"Listings: {data.get('totalListings', '?')}")
    print(f"SKUs: {len(data.get('skus', []))}")

def cmd_farm(args):
    if not args:
        print("Usage: farm status|monitor")
        return
    cmd = args[0]
    r = subprocess.run([
        sys.executable, 'farm_master.py', cmd
    ], capture_output=True, text=True)
    print(r.stdout)

def cmd_web(args):
    if not args:
        print("Usage: master web <url> or master web analyze <url>")
        return
    if args[0] == 'analyze' and len(args) > 1:
        url = args[1]
        from hack_mcp_server.web_analyzer import analyze_url
        data = analyze_url(url)
        print(f"\n=== Web Analysis: {url} ===")
        print(f"Title: {data.get('title')}")
        print(f"Forms: {len(data.get('forms', []))}")
        for f in data.get('forms', []):
            print(f"  {f.get('method')} inputs={f.get('inputs')}")
        print(f"CSRF: {len(data.get('csrf_tokens', []))}")
        print(f"Payment: {data.get('payment_gateways', [])}")
        print(f"Cookies: {len(data.get('cookies', []))}")
        print(f"API endpoints: {len(data.get('api_endpoints', []))}")
    else:
        print("Use: master web analyze <url>")

def cmd_price(args):
    if len(args) < 2:
        print("Usage: master price <url> <json_body>")
        return
    url = args[0]
    body = json.loads(args[1])
    from checkout_interceptor import analyze_checkout
    analyze_checkout(url, body)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print("Usage: master <command> [args]")
        print("Commands: search, deals, track, product, farm, web")
        sys.exit(1)

    cmd = args[0]
    rest = args[1:]

    if cmd == 'search': cmd_search(rest)
    elif cmd == 'deals': cmd_deals(rest)
    elif cmd == 'track': cmd_track(rest)
    elif cmd == 'product': cmd_product(rest)
    elif cmd == 'farm': cmd_farm(rest)
    elif cmd == 'web': cmd_web(rest)
    elif cmd == 'price': cmd_price(rest)
    else:
        print(f"Unknown: {cmd}")
        print("Commands: search, deals, track, product, farm, web, price")
