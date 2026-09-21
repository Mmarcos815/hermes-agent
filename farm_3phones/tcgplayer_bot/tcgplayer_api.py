#!/usr/bin/env python3
"""
tcgplayer_api.py — TCGplayer API client for Pokemon card automation.

Full flow: login → search → product details → add to cart → checkout.

API endpoints (reverse-engineered from live traffic):
  - POST https://mpapi.tcgplayer.com/v2/login
  - GET  https://mpapi.tcgplayer.com/v2/user
  - POST https://mp-search-api.tcgplayer.com/v1/search/request
  - GET  https://mp-search-api.tcgplayer.com/v2/product/{productId}/details
  - POST https://mp-search-api.tcgplayer.com/v1/product/{productId}/listings
  - POST https://mpapi.tcgplayer.com/v2/cart/item
  - GET  https://mpapi.tcgplayer.com/v2/cart
  - POST https://mpapi.tcgplayer.com/v2/checkout
  - POST https://payments.braintree-api.com/graphql

Usage:
    api = TCGplayerAPI()
    api.login("user@email.com", "password")
    results = api.search_pokemon("Charizard VMAX")
    api.add_to_cart(sku_id, price)
    api.checkout()
"""

import json
import time
import requests
from typing import Optional, Dict, Any, List


BASE_URL = "https://mpapi.tcgplayer.com"
SEARCH_URL = "https://mp-search-api.tcgplayer.com"
GATEWAY_URL = "https://mpgateway.tcgplayer.com"
BRAINTREE_URL = "https://payments.braintree-api.com/graphql"
STORE_URL = "https://store.tcgplayer.com"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}


class TCGplayerAPI:
    """TCGplayer API client."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.user = None
        self.cart = None
        self.token = None
        self.mpfev = "5555"

    # ------------------------------------------------------------------
    # AUTH
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> bool:
        """Login and get session token."""
        resp = self.session.post(
            f"{BASE_URL}/v2/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("token")
            if self.token:
                self.session.headers["Authorization"] = f"Bearer {self.token}"
            self.user = data.get("user", data)
            return True
        return False

    def is_logged_in(self) -> bool:
        """Check if session is valid."""
        resp = self.session.get(f"{BASE_URL}/v2/user?mpfev={self.mpfev}")
        if resp.status_code == 200:
            self.user = resp.json()
            return True
        return False

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------

    def search_pokemon(self, query: str, page: int = 1, page_size: int = 24) -> Dict:
        """Search for Pokemon cards."""
        payload = {
            "query": query,
            "filters": {
                "term": {
                    "productLineName": ["pokemon"],
                    "sellerStatus": "Live",
                },
                "range": {"quantity": {"gte": 1}},
            },
            "sort": {"field": "relevance", "order": "desc"},
            "from": (page - 1) * page_size,
            "size": page_size,
            "aggregations": ["product-name", "rarity", "set-name", "product-type"],
        }
        resp = self.session.post(
            f"{SEARCH_URL}/v1/search/request?mpfev={self.mpfev}",
            json=payload,
        )
        return resp.json() if resp.status_code == 200 else {}

    def get_product_details(self, product_id: int) -> Dict:
        """Get full product details including SKUs."""
        resp = self.session.get(
            f"{SEARCH_URL}/v2/product/{product_id}/details?mpfev={self.mpfev}"
        )
        return resp.json() if resp.status_code == 200 else {}

    def get_product_listings(
        self,
        product_id: int,
        condition: str = "Near Mint",
        language: str = "English",
        sort: str = "price+shipping",
        order: str = "asc",
        page: int = 1,
        page_size: int = 10,
    ) -> Dict:
        """Get all seller listings for a product."""
        filters = {
            "term": {
                "sellerStatus": "Live",
                "channelId": 0,
                "language": [language],
            },
            "range": {"quantity": {"gte": 1}},
            "exclude": {"channelExclusion": 0},
        }
        if condition:
            filters["term"]["condition"] = [condition]

        payload = {
            "filters": filters,
            "from": (page - 1) * page_size,
            "size": page_size,
            "sort": {"field": sort, "order": order},
            "context": {
                "shippingCountry": "US",
                "cart": {"packages": {}},
            },
        }
        resp = self.session.post(
            f"{SEARCH_URL}/v1/product/{product_id}/listings?mpfev={self.mpfev}",
            json=payload,
        )
        return resp.json() if resp.status_code == 200 else {}

    def get_lowest_price(self, product_id: int, condition: str = "Near Mint") -> Optional[float]:
        """Get the lowest available price for a product."""
        listings = self.get_product_listings(product_id, condition=condition, page_size=10)
        results = listings.get("results", [])
        if not results:
            return None
        prices = []
        for r in results:
            for l in r.get("listings", []):
                p = l.get("price", {}).get("sellerPrice")
                if p is not None:
                    prices.append(p)
        return min(prices) if prices else None

    # ------------------------------------------------------------------
    # CART
    # ------------------------------------------------------------------

    def get_cart(self) -> Dict:
        """Get current cart contents."""
        resp = self.session.get(f"{BASE_URL}/v2/cart?mpfev={self.mpfev}")
        self.cart = resp.json() if resp.status_code == 200 else {}
        return self.cart

    def add_to_cart(self, sku_id: int, quantity: int = 1, price: Optional[float] = None) -> bool:
        """Add a SKU to cart."""
        item = {
            "skuId": sku_id,
            "quantity": quantity,
            "directSeller": False,
        }
        if price:
            item["price"] = price

        resp = self.session.post(
            f"{BASE_URL}/v2/cart/item?mpfev={self.mpfev}",
            json=item,
        )
        return resp.status_code in (200, 201)

    def remove_from_cart(self, item_id: str) -> bool:
        """Remove item from cart."""
        resp = self.session.delete(
            f"{BASE_URL}/v2/cart/item/{item_id}?mpfev={self.mpfev}"
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

    # ------------------------------------------------------------------
    # CHECKOUT
    # ------------------------------------------------------------------

    def begin_checkout(self) -> Dict:
        """Begin the checkout process."""
        resp = self.session.post(
            f"{BASE_URL}/v2/checkout?mpfev={self.mpfev}",
            json={},
        )
        return resp.json() if resp.status_code in (200, 201) else {}

    def get_checkout(self, checkout_id: str) -> Dict:
        """Get checkout details."""
        resp = self.session.get(
            f"{BASE_URL}/v2/checkout/{checkout_id}?mpfev={self.mpfev}"
        )
        return resp.json() if resp.status_code == 200 else {}

    def submit_checkout(self, checkout_id: str, payment_nonce: str) -> Dict:
        """Submit payment for checkout."""
        payload = {
            "paymentMethodNonce": payment_nonce,
            "storeInVault": False,
        }
        resp = self.session.post(
            f"{BASE_URL}/v2/checkout/{checkout_id}/payment?mpfev={self.mpfev}",
            json=payload,
        )
        return resp.json() if resp.status_code in (200, 201) else {}

    # ------------------------------------------------------------------
    # PRICE HISTORY & ANALYTICS
    # ------------------------------------------------------------------

    def get_price_history(self, product_id: int, range_: str = "quarter") -> Dict:
        """Get price history for a product."""
        resp = self.session.get(
            f"https://infinite-api.tcgplayer.com/price/history/{product_id}/detailed?range={range_}"
        )
        return resp.json() if resp.status_code == 200 else {}

    def get_market_price(self, product_id: int) -> Optional[float]:
        """Get the current market price."""
        resp = self.session.get(
            f"{GATEWAY_URL}/v1/pricepoints/buylist/marketprice/products/{product_id}?mpfev={self.mpfev}"
        )
        if resp.status_code == 200:
            data = resp.json()
            # Extract market price from response
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("marketPrice")
            elif isinstance(data, dict):
                return data.get("marketPrice")
        return None

    # ------------------------------------------------------------------
    # HIGH-VALUE TRACKING
    # ------------------------------------------------------------------

    def track_high_value(self, max_price: float = 50.0) -> List[Dict]:
        """Find high-value Pokemon cards under max_price."""
        targets = [
            "Charizard VMAX", "Charizard VSTAR", "Pikachu VMAX",
            "Mewtwo VMAX", "Umbreon VMAX", "Rayquaza VMAX",
            "Gold Star Charizard", "Gold Star Pikachu",
        ]
        results = []
        for name in targets:
            try:
                search = self.search_pokemon(name, page_size=5)
                for r in search.get("results", []):
                    pid = r.get("productId")
                    price = self.get_lowest_price(pid)
                    if price and price <= max_price:
                        results.append({
                            "name": r.get("productName", name),
                            "product_id": pid,
                            "lowest_price": price,
                            "rarity": r.get("rarityName"),
                            "set": r.get("setName"),
                            "url": f"https://www.tcgplayer.com/product/{pid}",
                        })
            except Exception:
                continue
        return sorted(results, key=lambda x: x.get("lowest_price", 999))

    def __repr__(self):
        return f"<TCGplayerAPI user={self.user.get('email') if self.user else None}>"
