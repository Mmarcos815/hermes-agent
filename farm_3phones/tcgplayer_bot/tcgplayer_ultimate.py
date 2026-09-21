#!/usr/bin/env python3
"""
tcgplayer_ultimate.py — Full TCGplayer toolkit.
Search, price tracking, deal sniping, price history, market analysis.
"""
import requests, json, time
from pathlib import Path

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json', 'Accept': 'application/json',
    'Origin': 'https://www.tcgplayer.com', 'Referer': 'https://www.tcgplayer.com/',
}
DATA = Path('tcgplayer_data'); DATA.mkdir(exist_ok=True)

def search(query, line='pokemon', limit=20):
    """Search TCGplayer products."""
    url = 'https://mp-search-api.tcgplayer.com/v1/search/request'
    body = {'filters': {'term': {'productLineName': [line], 'name': [query]}}, 'from': 0, 'size': limit}
    r = requests.post(url, json=body, headers=HEADERS)
    results = r.json().get('results', [])
    return results[0].get('results', []) if results else []

def autocomplete(query):
    """Autocomplete search."""
    url = f'https://data.tcgplayer.com/autocomplete?q={query}'
    return requests.get(url, headers=HEADERS).json().get('products', [])

def product_details(pid):
    """Get full product details."""
    url = f'https://mp-search-api.tcgplayer.com/v2/product/{pid}/details?mpfev=5555'
    return requests.get(url, headers=HEADERS).json()

def listings(pid, limit=10):
    """Get seller listings."""
    url = f'https://mp-search-api.tcgplayer.com/v1/product/{pid}/listings'
    body = {'filters': {'term': {'sellerStatus': 'Live', 'channelId': 0, 'language': ['English']}}, 'from': 0, 'size': limit}
    return requests.post(url, json=body, headers=HEADERS).json()

def price_history(pid, range='quarter'):
    """Get price history."""
    url = f'https://infinite-api.tcgplayer.com/price/history/{pid}/detailed?range={range}'
    return requests.get(url, headers=HEADERS).json()

def market_price(pid):
    """Get market price."""
    url = 'https://mpgateway.tcgplayer.com/v1/pricepoints/marketprice/skus/search?mpfev=5555'
    return requests.post(url, json={'skuIds': [pid]}, headers=HEADERS).json()

def find_deals(query, max_price=10.0, min_discount=0.2):
    """Find deals: products below market price."""
    products = search(query)
    deals = []
    for p in products[:50]:
        name = p.get('productName', '?')
        pid = p.get('productId')
        lowest = p.get('lowestPrice') or p.get('marketPrice')
        if not lowest or float(lowest) > max_price:
            continue
        # Get full details for market price comparison
        details = product_details(pid)
        market = details.get('marketPrice')
        if market and float(market) > 0:
            discount = (float(market) - float(lowest)) / float(market)
            if discount >= min_discount:
                deals.append({'name': name, 'pid': pid, 'lowest': lowest, 'market': market, 'discount': discount})
                print(f'  DEAL: {name[:40]} — ${lowest} (market ${market}, {discount*100:.0f}% off)')
    return deals

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='TCGplayer Ultimate Toolkit')
    p.add_argument('cmd', choices=['search', 'deals', 'history', 'price', 'auto', 'details'])
    p.add_argument('--query', default='Charizard')
    p.add_argument('--pid', type=int)
    p.add_argument('--max-price', type=float, default=10.0)
    p.add_argument('--range', default='quarter')
    args = p.parse_args()

    if args.cmd == 'search':
        results = search(args.query)
        for r in results[:10]:
            print(f'  {r.get("productName", "?")}: ${r.get("lowestPrice", r.get("marketPrice", "?"))}')
    elif args.cmd == 'deals':
        find_deals(args.query, args.max_price)
    elif args.cmd == 'history':
        print(json.dumps(price_history(args.pid, args.range), indent=2)[:2000])
    elif args.cmd == 'price':
        print(json.dumps(market_price(args.pid), indent=2)[:1000])
    elif args.cmd == 'auto':
        print(json.dumps(autocomplete(args.query), indent=2)[:2000])
    elif args.cmd == 'details':
        print(json.dumps(product_details(args.pid), indent=2)[:2000])
