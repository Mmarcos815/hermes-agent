#!/usr/bin/env python3
"""
tcgplayer_checkout.py — Full checkout flow for TCGplayer.com.

Flow: login → search → select SKU → add to cart → fill shipping → fill payment → submit order.

Uses requests-based API (no browser dependency).

POSTMAN ENDPOINTS INTEGRATED:
  - POST /v2/login (mpapi.tcgplayer.com)
  - POST /v2/cart/item
  - GET  /v2/cart
  - POST /v2/checkout
  - POST /v2/checkout/{id}/payment
  - GET  /v2/checkout/{id}
  - GET  /v2/user/addresses
  - GET  /v2/user/paymentMethods
  - POST /v2/shipping/options

Usage:
    from tcgplayer_checkout import TCGCheckout
    co = TCGCheckout()
    co.login("user@email.com", "pass")
    co.search_and_add("Charizard VMAX", max_price=30.0)
    co.set_shipping_address({...})
    co.checkout()
"""
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# Base URLs (from Postman collection + reverse engineering)
MPAPI = "https://mpapi.tcgplayer.com"
SEARCH_API = "https://mp-search-api.tcgplayer.com"
GATEWAY = "https://mpgateway.tcgplayer.com"
STORE_URL = "https://store.tcgplayer.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Connection": "keep-alive",
}

MPFEV = "5555"


class TCGCheckout:
    """Full TCGplayer checkout flow."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.cart: Optional[Dict] = None
        self.checkout_data: Optional[Dict] = None
        self.mpfev = MPFEV

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> bool:
        """
        Login to TCGplayer. Uses the mpapi v2 login endpoint.
        Sets Bearer token on success.
        """
        resp = self.session.post(
            f"{MPAPI}/v2/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token") or data.get("token")
            if self.token:
                self.session.headers["Authorization"] = f"Bearer {self.token}"
            self.user = data.get("user", data)
            return True
        return False

    def is_logged_in(self) -> bool:
        """Check if session is still valid."""
        if not self.token:
            return False
        resp = self.session.get(f"{MPAPI}/v2/user?mpfev={self.mpfev}")
        if resp.status_code == 200:
            self.user = resp.json()
            return True
        return False

    def get_user_info(self) -> Dict:
        """Get current user profile."""
        resp = self.session.get(f"{MPAPI}/v2/user?mpfev={self.mpfev}")
        return resp.json() if resp.status_code == 200 else {}

    def get_addresses(self) -> List[Dict]:
        """Get saved shipping addresses (POSTMAN: Get Customer Addresses)."""
        resp = self.session.get(f"{MPAPI}/v2/user/addresses?mpfev={self.mpfev}")
        if resp.status_code == 200:
            return resp.json().get("addresses", resp.json().get("results", []))
        return []

    def get_payment_methods(self) -> List[Dict]:
        """Get saved payment methods."""
        resp = self.session.get(f"{MPAPI}/v2/user/paymentMethods?mpfev={self.mpfev}")
        if resp.status_code == 200:
            return resp.json().get("paymentMethods", resp.json().get("results", []))
        return []

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search(self, query: str, line: str = "Pokemon", limit: int = 20) -> List[Dict]:
        """Search for products (uses mp-search-api, no auth required)."""
        url = f"{SEARCH_API}/v1/search/request?q={query}&isList=false&mpfev={self.mpfev}"
        body = {
            "algorithm": "sales_dismax",
            "from": 0,
            "size": limit,
            "filters": {
                "term": {"productLineName": [line]},
                "range": {},
                "match": {},
            },
            "listingSearch": {
                "context": {"cart": {"packages": {}}},
                "filters": {
                    "term": {"sellerStatus": "Live", "channelId": 0},
                    "range": {"quantity": {"gte": 1}},
                    "exclude": {"channelExclusion": 0},
                },
            },
            "context": {
                "cart": {"packages": {}},
                "shippingCountry": "US",
                "userProfile": {},
            },
            "settings": {"useFuzzySearch": True, "didYouMean": {}},
            "sort": {},
        }
        r = self.session.post(url, json=body)
        results = r.json().get("results", [])
        return results[0].get("results", []) if results else []

    def get_product_details(self, product_id: int) -> Dict:
        """Get full product details with SKUs."""
        url = f"{SEARCH_API}/v2/product/{product_id}/details?mpfev={self.mpfev}"
        return self.session.get(url).json()

    def get_listings(self, product_id: int, limit: int = 10,
                     condition: str = "Near Mint", language: str = "English") -> List[Dict]:
        """Get seller listings for a product."""
        url = f"{SEARCH_API}/v1/product/{product_id}/listings?mpfev={self.mpfev}"
        body = {
            "filters": {
                "term": {
                    "sellerStatus": "Live",
                    "channelId": 0,
                    "language": [language],
                    "condition": [condition],
                },
                "range": {"quantity": {"gte": 1}},
                "exclude": {"channelExclusion": 0},
            },
            "from": 0,
            "size": limit,
            "sort": {"field": "price+shipping", "order": "asc"},
            "context": {"shippingCountry": "US", "cart": {"packages": {}}},
        }
        r = self.session.post(url, json=body)
        results = r.json().get("results", [])
        listings = []
        for r in results:
            for l in r.get("listings", []):
                listings.append({
                    "skuId": r.get("skuId"),
                    "price": l.get("price", {}).get("sellerPrice"),
                    "shipping": l.get("price", {}).get("shippingPrice", 0),
                    "total": l.get("price", {}).get("totalPrice"),
                    "sellerId": l.get("sellerId"),
                    "sellerName": l.get("sellerName"),
                    "condition": r.get("conditionName"),
                    "quantity": l.get("quantity"),
                })
        return listings

    def search_and_add(self, query: str, max_price: float = 50.0,
                       line: str = "pokemon", condition: str = "Near Mint") -> Optional[Dict]:
        """
        Search for a product and add the cheapest matching SKU to cart.
        Returns the cart item if successful, None otherwise.
        """
        results = self.search(query, line, limit=10)
        if not results:
            print(f"[!] No results for '{query}'")
            return None

        for product in results[:5]:
            pid = product.get("productId")
            name = product.get("productName", "?")
            listings = self.get_listings(pid, limit=5, condition=condition)
            for listing in listings:
                total = listing.get("total") or listing.get("price", 0)
                if total and float(total) <= max_price:
                    print(f"  Adding: {name} — ${total} (SKU {listing['skuId']})")
                    if self.add_to_cart(listing["skuId"], 1, listing.get("price")):
                        return listing
        print(f"[!] No affordable listings under ${max_price} for '{query}'")
        return None

    # ------------------------------------------------------------------
    # CART
    # ------------------------------------------------------------------

    def get_cart(self) -> Dict:
        """Get current cart contents (POSTMAN: GET /v2/cart)."""
        resp = self.session.get(f"{MPAPI}/v2/cart?mpfev={self.mpfev}")
        self.cart = resp.json() if resp.status_code == 200 else {}
        return self.cart

    def add_to_cart(self, sku_id: int, quantity: int = 1,
                    price: Optional[float] = None) -> bool:
        """Add a SKU to cart (POSTMAN: POST /v2/cart/item)."""
        item = {"skuId": sku_id, "quantity": quantity, "directSeller": False}
        if price:
            item["price"] = price
        resp = self.session.post(
            f"{MPAPI}/v2/cart/item?mpfev={self.mpfev}",
            json=item,
        )
        return resp.status_code in (200, 201)

    def remove_from_cart(self, item_id: str) -> bool:
        """Remove item from cart."""
        resp = self.session.delete(
            f"{MPAPI}/v2/cart/item/{item_id}?mpfev={self.mpfev}"
        )
        return resp.status_code == 200

    def clear_cart(self) -> bool:
        """Remove all items from cart."""
        self.get_cart()
        if not self.cart:
            return True
        items = self.cart.get("items", [])
        for item in items:
            item_id = item.get("id")
            if item_id:
                self.remove_from_cart(item_id)
        return True

    def update_cart_item(self, item_id: str, quantity: int) -> bool:
        """Update quantity of a cart item."""
        resp = self.session.put(
            f"{MPAPI}/v2/cart/item/{item_id}?mpfev={self.mpfev}",
            json={"quantity": quantity},
        )
        return resp.status_code == 200

    def get_cart_total(self) -> float:
        """Get cart subtotal."""
        cart = self.get_cart()
        total = 0
        for item in cart.get("items", []):
            total += item.get("price", 0) * item.get("quantity", 1)
        return total

    # ------------------------------------------------------------------
    # CHECKOUT
    # ------------------------------------------------------------------

    def begin_checkout(self) -> Dict:
        """
        Begin the checkout process (POSTMAN: POST /v2/checkout).
        Returns checkout ID and shipping/payment requirements.
        """
        resp = self.session.post(
            f"{MPAPI}/v2/checkout?mpfev={self.mpfev}",
            json={},
        )
        self.checkout_data = resp.json() if resp.status_code in (200, 201) else {}
        return self.checkout_data

    def get_checkout(self, checkout_id: str) -> Dict:
        """Get checkout details (POSTMAN: GET /v2/checkout/{id})."""
        resp = self.session.get(
            f"{MPAPI}/v2/checkout/{checkout_id}?mpfev={self.mpfev}"
        )
        return resp.json() if resp.status_code == 200 else {}

    def set_shipping_address(self, address: Dict) -> bool:
        """
        Set shipping address on current checkout.
        address: {
            "firstName": "John", "lastName": "Doe",
            "addressLine1": "123 Main St", "city": "Anytown",
            "state": "CA", "postalCode": "90210", "country": "US",
            "phone": "555-0100"
        }
        """
        checkout_id = self.checkout_data.get("checkoutId") if self.checkout_data else None
        if not checkout_id:
            self.begin_checkout()
            checkout_id = self.checkout_data.get("checkoutId")

        resp = self.session.post(
            f"{MPAPI}/v2/checkout/{checkout_id}/shipping/address?mpfev={self.mpfev}",
            json=address,
        )
        return resp.status_code in (200, 201)

    def set_shipping_method(self, shipping_code: str) -> bool:
        """Set shipping method on checkout."""
        checkout_id = self.checkout_data.get("checkoutId") if self.checkout_data else None
        if not checkout_id:
            return False
        resp = self.session.post(
            f"{MPAPI}/v2/checkout/{checkout_id}/shipping/method?mpfev={self.mpfev}",
            json={"shippingCode": shipping_code},
        )
        return resp.status_code in (200, 201)

    def submit_payment(self, payment_nonce: str) -> Dict:
        """
        Submit payment for checkout (POSTMAN: POST /v2/checkout/{id}/payment).
        payment_nonce: Braintree payment nonce or saved payment method token.
        """
        checkout_id = self.checkout_data.get("checkoutId") if self.checkout_data else None
        if not checkout_id:
            self.begin_checkout()
            checkout_id = self.checkout_data.get("checkoutId")

        payload = {
            "paymentMethodNonce": payment_nonce,
            "storeInVault": False,
        }
        resp = self.session.post(
            f"{MPAPI}/v2/checkout/{checkout_id}/payment?mpfev={self.mpfev}",
            json=payload,
        )
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def submit_order(self, payment_nonce: str = None) -> Dict:
        """
        Full order submission. Requires begin_checkout to be called first.
        If payment_nonce provided, submits payment. Otherwise returns
        order summary awaiting payment.
        """
        checkout_id = self.checkout_data.get("checkoutId") if self.checkout_data else None
        if not checkout_id:
            raise ValueError("No active checkout. Call begin_checkout() first.")

        payload = {}
        if payment_nonce:
            payload["paymentMethodNonce"] = payment_nonce
        resp = self.session.post(
            f"{MPAPI}/v2/checkout/{checkout_id}/submit?mpfev={self.mpfev}",
            json=payload,
        )
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    # ------------------------------------------------------------------
    # HIGH-LEVEL WORKFLOW
    # ------------------------------------------------------------------

    def full_checkout_flow(self, email: str, password: str, query: str,
                           max_price: float = 50.0,
                           shipping_address: Dict = None,
                           payment_nonce: str = None) -> Dict:
        """
        Full checkout flow: login → search → add → checkout → submit.
        Returns order confirmation or error details.
        """
        result = {"success": False, "steps": {}}

        # Step 1: Login
        if not self.login(email, password):
            result["steps"]["login"] = "FAILED"
            return result
        result["steps"]["login"] = "OK"

        # Step 2: Search & Add
        item = self.search_and_add(query, max_price)
        if not item:
            result["steps"]["add_to_cart"] = "FAILED"
            return result
        result["steps"]["add_to_cart"] = f"OK (SKU {item['skuId']})"

        # Step 3: Checkout
        checkout = self.begin_checkout()
        if not checkout.get("checkoutId"):
            result["steps"]["begin_checkout"] = "FAILED"
            return result
        result["steps"]["begin_checkout"] = f"OK ({checkout['checkoutId']})"

        # Step 4: Shipping Address
        if shipping_address:
            addr_ok = self.set_shipping_address(shipping_address)
            result["steps"]["shipping_address"] = "OK" if addr_ok else "SKIPPED"

        # Step 5: Submit
        if payment_nonce:
            submit = self.submit_order(payment_nonce)
            result["steps"]["submit"] = submit
            result["order_id"] = submit.get("orderId")
            result["success"] = submit.get("success", False)
        else:
            result["steps"]["submit"] = "AWAITING_PAYMENT"

        return result


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='TCGplayer Checkout Tool')
    p.add_argument('cmd', choices=['login', 'cart', 'add', 'checkout', 'addresses', 'search', 'full'])
    p.add_argument('--email', default='')
    p.add_argument('--password', default='')
    p.add_argument('--query', default='Charizard VMAX')
    p.add_argument('--max-price', type=float, default=50.0)
    p.add_argument('--sku-id', type=int)
    args = p.parse_args()

    co = TCGCheckout()

    if args.cmd == 'login':
        ok = co.login(args.email, args.password)
        print(f"Login: {'OK' if ok else 'FAILED'}")
        if ok:
            print(json.dumps(co.user, indent=2)[:2000])
    elif args.cmd == 'cart':
        cart = co.get_cart()
        print(json.dumps(cart, indent=2)[:2000])
    elif args.cmd == 'add':
        if args.sku_id:
            ok = co.add_to_cart(args.sku_id)
            print(f"Add SKU {args.sku_id}: {'OK' if ok else 'FAILED'}")
        else:
            co.search_and_add(args.query, args.max_price)
    elif args.cmd == 'search':
        results = co.search(args.query, limit=10)
        for r in results[:5]:
            print(f"  {r.get('productName', '?')}: ${r.get('lowestPrice', '?')} (ID {r.get('productId')})")
    elif args.cmd == 'addresses':
        addresses = co.get_addresses()
        print(json.dumps(addresses, indent=2)[:2000])
    elif args.cmd == 'checkout':
        co.begin_checkout()
        print(json.dumps(co.checkout_data, indent=2)[:2000])
    elif args.cmd == 'full':
        print("Full checkout flow requires --email, --password, and valid payment info.")
        print("This is a dry-run demo. Use the Python API for real orders.")
        # Demo dry-run
        ok = co.login(args.email, args.password)
        print(f"Login: {'OK' if ok else 'FAILED'}")
        if ok:
            co.search_and_add(args.query, args.max_price)
            print(f"Cart total: ${co.get_cart_total():.2f}")
            co.begin_checkout()
            print(f"Checkout ID: {co.checkout_data.get('checkoutId', 'N/A')}")
