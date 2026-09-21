#!/usr/bin/env python3
"""
deal_aggregator.py — Pokemon Card Deal & Promo Aggregator.

Scans multiple platforms for:
- Active coupon codes
- Free pack promotions
- Price mistakes (below market)
- Daily deals
- Giveaways

Platforms: TCGplayer, CardOutpost, Outpost, Boxed, eBay, Amazon
"""
import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

WORKSPACE = Path(__file__).resolve().parent
DEALS_FILE = WORKSPACE / "active_deals.json"
LOG_FILE = WORKSPACE / "deal_log.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ─── PLATFORM SCANNERS ─────────────────────────────────────────────────

def scan_tcgplayer_deals():
    """Scan TCGplayer for deals and promotions."""
    deals = []
    try:
        # Search for products with bestdiscount
        payload = {
            'query': 'Pokemon',
            'filters': {'productLineName': ['pokemon']},
            'from': 0, 'size': 20,
            'sort': {'field': 'bestdiscount', 'order': 'desc'}
        }
        r = requests.post('https://mp-search-api.tcgplayer.com/v1/search/request',
                         headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200 and r.text:
            data = r.json()
            results = data.get('results', [{}])[0].get('results', [])
            
            for item in results:
                name = item.get('productName', '')
                low = item.get('lowestPrice', 0)
                market = item.get('marketPrice', 0)
                pid = item.get('productId', '')
                discount = item.get('bestDiscount', 0)
                
                deals.append({
                    'platform': 'TCGplayer',
                    'name': name,
                    'price': low,
                    'market': market,
                    'discount': discount,
                    'url': f'https://www.tcgplayer.com/product/{pid}' if pid else '',
                    'type': 'best_discount',
                    'timestamp': datetime.now().isoformat()
                })
    except Exception as e:
        print(f"[TCGplayer] Error: {e}")
    return deals

def scan_cardoutpost_deals():
    """Scan CardOutpost for free packs and deals."""
    deals = []
    try:
        r = requests.get('https://www.cardoutpost.com', headers=HEADERS, timeout=15)
        html = r.text
        
        # Look for free pack promotions
        if 'free' in html.lower() or 'promo' in html.lower():
            # Extract promo text
            promo_matches = re.findall(r'(?:free|promo|deal|save)\s+[^\.<]{10,50}', html, re.I)
            for match in promo_matches[:5]:
                deals.append({
                    'platform': 'CardOutpost',
                    'name': match.strip(),
                    'type': 'promotion',
                    'url': 'https://www.cardoutpost.com',
                    'timestamp': datetime.now().isoformat()
                })
    except Exception as e:
        print(f"[CardOutpost] Error: {e}")
    return deals

def scan_outpost_deals():
    """Scan Outpost for free daily pulls."""
    deals = []
    try:
        r = requests.get('https://www.outpost.com', headers=HEADERS, timeout=15)
        html = r.text
        
        # Look for free pull promotions
        free_matches = re.findall(r'free\s+(?:pull|pack|box|card)', html, re.I)
        for match in free_matches[:5]:
            deals.append({
                'platform': 'Outpost',
                'name': match.strip(),
                'type': 'free_pull',
                'url': 'https://www.outpost.com',
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"[Outpost] Error: {e}")
    return deals

def scan_ebay_deals():
    """Scan eBay for Pokemon card deals."""
    deals = []
    try:
        # Search for Pokemon TCG auctions ending soon
        url = 'https://www.ebay.com/sch/i.html?_nkw=pokemon+tcg+booster+pack&_sop=10'
        r = requests.get(url, headers=HEADERS, timeout=15)
        html = r.text
        
        # Extract prices
        prices = re.findall(r'\$([0-9]+\.?[0-9]*)', html)
        titles = re.findall(r'class="s-item__title[^"]*">([^<]+)</span>', html)
        
        for i, (title, price) in enumerate(zip(titles[:10], prices[:10])):
            try:
                p = float(price)
                if p < 5:  # Under $5 = potential deal
                    deals.append({
                        'platform': 'eBay',
                        'name': title.strip(),
                        'price': p,
                        'type': 'auction_deal',
                        'url': 'https://www.ebay.com/sch/i.html?_nkw=pokemon+tcg+booster+pack',
                        'timestamp': datetime.now().isoformat()
                    })
            except:
                pass
    except Exception as e:
        print(f"[eBay] Error: {e}")
    return deals

def scan_amazon_deals():
    """Scan Amazon for Pokemon card deals."""
    deals = []
    try:
        url = 'https://www.amazon.com/s?k=pokemon+tcg+booster+pack&rh=p_36%3A-5000'
        r = requests.get(url, headers=HEADERS, timeout=15)
        html = r.text
        
        # Extract prices
        prices = re.findall(r'\$([0-9]+\.?[0-9]*)', html)
        titles = re.findall(r'class="a-size-medium a-color-base a-text-normal">([^<]+)</span>', html)
        
        for i, (title, price) in enumerate(zip(titles[:10], prices[:10])):
            try:
                p = float(price)
                if p < 5:
                    deals.append({
                        'platform': 'Amazon',
                        'name': title.strip(),
                        'price': p,
                        'type': 'deal',
                        'url': 'https://www.amazon.com/s?k=pokemon+tcg+booster+pack',
                        'timestamp': datetime.now().isoformat()
                    })
            except:
                pass
    except Exception as e:
        print(f"[Amazon] Error: {e}")
    return deals

def scan_reddit_giveaways():
    """Scan Reddit for Pokemon card giveaways."""
    deals = []
    try:
        # Search r/pkmntcg for giveaways
        url = 'https://www.reddit.com/r/pkmntcg/search.json?q=giveaway+OR+free+OR+promo&sort=new&t=day'
        r = requests.get(url, headers={**HEADERS, 'User-Agent': 'HermesDealBot/1.0'}, timeout=15)
        data = r.json()
        
        for post in data.get('data', {}).get('children', [])[:10]:
            title = post['data'].get('title', '')
            url = post['data'].get('url', '')
            if any(k in title.lower() for k in ['free', 'giveaway', 'promo', 'code']):
                deals.append({
                    'platform': 'Reddit',
                    'name': title,
                    'type': 'giveaway',
                    'url': url,
                    'timestamp': datetime.now().isoformat()
                })
    except Exception as e:
        print(f"[Reddit] Error: {e}")
    return deals

# ─── AGGREGATOR ────────────────────────────────────────────────────────

class DealAggregator:
    """Main deal aggregator."""
    
    def __init__(self):
        self.scanners = [
            scan_tcgplayer_deals,
            scan_cardoutpost_deals,
            scan_outpost_deals,
            scan_ebay_deals,
            scan_amazon_deals,
            scan_reddit_giveaways,
        ]
        self.all_deals = []
    
    def scan_all(self):
        """Run all scanners in parallel."""
        print(f"\n{'='*60}")
        print(f"DEAL AGGERATOR — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(lambda f: f(), self.scanners))
        
        self.all_deals = []
        for result in results:
            self.all_deals.extend(result)
        
        # Sort by discount (highest first)
        self.all_deals.sort(key=lambda x: x.get('discount', 0), reverse=True)
        
        return self.all_deals
    
    def save_deals(self):
        """Save deals to file."""
        with open(DEALS_FILE, 'w') as f:
            json.dump(self.all_deals, f, indent=2)
        print(f"\nSaved {len(self.all_deals)} deals to {DEALS_FILE}")
    
    def print_deals(self):
        """Print all deals."""
        if not self.all_deals:
            print("\nNo deals found this scan.")
            return
        
        print(f"\n{'='*60}")
        print(f"FOUND {len(self.all_deals)} DEALS")
        print(f"{'='*60}")
        
        for i, deal in enumerate(self.all_deals, 1):
            platform = deal.get('platform', 'Unknown')
            name = deal.get('name', '')[:50]
            dtype = deal.get('type', '')
            price = deal.get('price', '')
            discount = deal.get('discount', '')
            
            print(f"\n[{i}] {platform} | {dtype}")
            print(f"    {name}")
            if price:
                print(f"    Price: ${price}", end='')
            if discount:
                print(f" | Discount: {discount}%", end='')
            print()
            print(f"    {deal.get('url', '')}")
    
    def monitor(self, interval=3600):
        """Continuous monitoring mode."""
        print(f"Starting deal monitor (every {interval}s)...")
        print("Press Ctrl+C to stop.")
        
        while True:
            try:
                self.scan_all()
                self.print_deals()
                self.save_deals()
                print(f"\nNext scan in {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\nMonitor stopped.")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Pokemon Card Deal Aggregator")
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring')
    parser.add_argument('--interval', type=int, default=3600, help='Scan interval in seconds')
    args = parser.parse_args()
    
    agg = DealAggregator()
    
    if args.monitor:
        agg.monitor(args.interval)
    else:
        agg.scan_all()
        agg.print_deals()
        agg.save_deals()
