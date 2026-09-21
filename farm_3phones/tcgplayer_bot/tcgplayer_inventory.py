#!/usr/bin/env python3
"""
tcgplayer_inventory.py — Inventory management for TCGplayer seller accounts.

Based on Postman collection endpoints:
  - GET  /v1/stores/{storeKey}/inventory/products
  - GET  /v1/stores/{storeKey}/inventory/skus/{skuId}
  - PUT  /v1/stores/{storeKey}/inventory/skus/{skuId}
  - POST /v1/stores/{storeKey}/inventory/skus/{skuId}/quantity
  - PUT  /v1/stores/{storeKey}/inventory/skus/{skuId}/price
  - POST /v1/stores/{storeKey}/inventory/skus/batch
  - GET  /v1/stores/{storeKey}/inventory/topsales
  - GET  /v1/stores/{storeKey}/inventory/groups
  - GET  /v1/stores/{storeKey}/inventory/categories
  - GET  /v1/stores/{storeKey}/inventory/skuprices
  - POST /v1/stores/{storeKey}/inventory/topsalessearch
  - POST /v1/stores/{storeKey}/inventory/productlists

Also supports:
  - GET  /v1/stores/{storeKey}/orders/manifest
  - GET  /v1/stores/{storeKey}/orders/{orderId}
  - GET  /v1/stores/{storeKey}/orders/{orderId}/items
  - GET  /v1/stores/{storeKey}/orders/{orderId}/tracking
  - POST /v1/stores/{storeKey}/orders/{orderId}/tracking
  - GET  /v1/stores/{storeKey}/orders
  - GET  /v1/stores/{storeKey}/customers
  - GET  /v1/stores/{storeKey}/customers/{customerToken}/orders
  - GET  /v1/stores/{storeKey}/customers/{customerToken}/addresses
  - GET  /v1/stores/{storeKey}/feedback
  - GET  /v1/stores/{storeKey}/address
  - GET  /v1/stores/{storeKey}/status/inactive

Usage:
    inv = TCGInventory()
    inv.login("user@email.com", "pass")
    inv.list_inventory()
    inv.update_price(sku_id=15179, price=12.99)
    inv.update_quantity(sku_id=15179, quantity=5)
    inv.batch_update_prices([{"skuId": 15179, "price": 9.99}])
    inv.get_orders()
"""
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

MPAPI = "https://mpapi.tcgplayer.com"
SEARCH_API = "https://mp-search-api.tcgplayer.com"
GATEWAY = "https://mpgateway.tcgplayer.com"
API_BASE = "https://api.tcgplayer.com"
MPFEV = "5555"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Connection": "keep-alive",
}


class TCGInventory:
    """TCGplayer inventory management for sellers."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.store_key: Optional[str] = None
        self.version = "v1.37.0"
        self.mpfev = MPFEV

    # ------------------------------------------------------------------
    # AUTH
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> bool:
        """Login to TCGplayer."""
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
            # Extract store key
            self.store_key = self.user.get("storeKey") if self.user else None
            return True
        return False

    def _store_url(self, path: str) -> str:
        """Build store API URL."""
        return f"{API_BASE}/{self.version}/stores/{self.store_key}{path}"

    # ------------------------------------------------------------------
    # INVENTORY MANAGEMENT
    # ------------------------------------------------------------------

    def list_inventory(self, offset: int = 0, limit: int = 100,
                       category_id: int = None) -> Dict:
        """List all inventory products (POSTMAN: List Product Summary/SKUs)."""
        url = self._store_url("/inventory/products")
        params = {"offset": offset, "limit": limit}
        if category_id:
            params["categoryId"] = category_id
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}

    def get_product_sku_quantity(self, product_id: int) -> Dict:
        """Get SKU quantities for a product (POSTMAN: Get Product Inventory Quantities)."""
        url = self._store_url(f"/inventory/products/{product_id}/quantity")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_sku(self, sku_id: int) -> Dict:
        """Get a specific SKU's details."""
        url = self._store_url(f"/inventory/skus/{sku_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_sku_quantity(self, sku_id: int) -> Dict:
        """Get SKU quantity (POSTMAN: Get SKU Quantity)."""
        url = self._store_url(f"/inventory/skus/{sku_id}/quantity")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_sku_price(self, sku_id: int) -> Dict:
        """Get SKU price (POSTMAN: Get SKU List Price)."""
        url = self._store_url(f"/inventory/skuprices/{sku_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def list_sku_prices(self, offset: int = 0, limit: int = 500) -> Dict:
        """List all SKU prices (POSTMAN: List SKU List Price)."""
        url = self._store_url("/inventory/skuprices")
        params = {"offset": offset, "limit": limit}
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}

    def update_sku(self, sku_id: int, quantity: int = None,
                   price: float = None, channel_id: int = None) -> Dict:
        """
        Update SKU inventory (POSTMAN: PUT Update SKU Inventory).
        Full update of quantity, price, and channel.
        """
        url = self._store_url(f"/inventory/skus/{sku_id}")
        body = {}
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = int(price * 100)  # cents
        if channel_id is not None:
            body["channelId"] = channel_id
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_price(self, sku_id: int, price: float,
                     channel_id: int = 1) -> Dict:
        """Update SKU price (POSTMAN: PUT/POST Update SKU Inventory Price)."""
        url = self._store_url(f"/inventory/skus/{sku_id}/price")
        body = [{"price": int(price * 100), "channelId": channel_id, "skuId": sku_id}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_quantity(self, sku_id: int, quantity: int,
                        channel_id: int = 1) -> Dict:
        """Increment SKU quantity (POSTMAN: POST Increment SKU Inventory Quantity)."""
        url = self._store_url(f"/inventory/skus/{sku_id}/quantity")
        body = {"quantity": quantity, "channelId": channel_id}
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def batch_update_prices(self, items: List[Dict]) -> Dict:
        """
        Batch update SKU prices (POSTMAN: POST Batch Update Store SKU Prices).
        items: [{"skuId": 15179, "price": 9.99, "channelId": 1}, ...]
        """
        url = self._store_url("/inventory/skus/batch")
        body = []
        for item in items:
            entry = {"skuId": item["skuId"]}
            if "price" in item:
                entry["price"] = int(item["price"] * 100)
            if "channelId" in item:
                entry["channelId"] = item["channelId"]
            if "quantity" in item:
                entry["quantity"] = item["quantity"]
            body.append(entry)
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def set_sku_price(self, sku_id: int, price: float,
                      channel_id: int = 1) -> Dict:
        """Set SKU list price (POSTMAN: POST Update SKU Inventory Price)."""
        url = self._store_url(f"/inventory/skus/{sku_id}/price")
        body = [{"skuId": sku_id, "price": int(price * 100), "channelId": channel_id}]
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # ORDERS & FULFILLMENT
    # ------------------------------------------------------------------

    def get_orders(self, offset: int = 0, limit: int = 50,
                   order_number: str = None) -> Dict:
        """List store orders (POSTMAN: Search Orders)."""
        url = self._store_url("/orders")
        params = {"offset": offset, "limit": limit}
        if order_number:
            params["orderNumber"] = order_number
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}

    def get_order_manifest(self) -> Dict:
        """Get order manifest (POSTMAN: Get Order Manifest)."""
        url = self._store_url("/orders/manifest")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_order_details(self, order_id: str) -> Dict:
        """Get order details (POSTMAN: Get Order Details)."""
        url = self._store_url(f"/orders/{order_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_order_items(self, order_id: str) -> Dict:
        """Get order items (POSTMAN: Get Order Items)."""
        url = self._store_url(f"/orders/{order_id}/items")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_order_tracking(self, order_id: str) -> Dict:
        """Get order tracking numbers (POSTMAN: Get Order Tracking Numbers)."""
        url = self._store_url(f"/orders/{order_id}/tracking")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def add_order_tracking(self, order_id: str, tracking_numbers: List[str]) -> Dict:
        """Add tracking numbers to order (POSTMAN: POST Add Order Tracking Number)."""
        url = self._store_url(f"/orders/{order_id}/tracking")
        resp = self.session.post(url, json=tracking_numbers)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def get_order_feedback(self, order_id: str) -> Dict:
        """Get order feedback (POSTMAN: Get Order Feedback)."""
        url = self._store_url(f"/orders/{order_id}/feedback")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    # ------------------------------------------------------------------
    # CUSTOMERS
    # ------------------------------------------------------------------

    def get_customers(self, name: str = None, offset: int = 0,
                      limit: int = 50) -> Dict:
        """Search store customers (POSTMAN: Search Store Customers)."""
        url = self._store_url("/customers")
        params = {"offset": offset, "limit": limit}
        if name:
            params["name"] = name
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else {}

    def get_customer_summary(self, customer_token: str) -> Dict:
        """Get customer summary (POSTMAN: Get Customer Summary)."""
        url = self._store_url(f"/customers/{customer_token}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_customer_addresses(self, customer_token: str) -> Dict:
        """Get customer addresses (POSTMAN: Get Customer Addresses)."""
        url = self._store_url(f"/customers/{customer_token}/addresses")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_customer_orders(self, customer_token: str) -> Dict:
        """Get customer orders (POSTMAN: Get Customer Orders)."""
        url = self._store_url(f"/customers/{customer_token}/orders")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    # ------------------------------------------------------------------
    # STORE INFO
    # ------------------------------------------------------------------

    def get_store_info(self) -> Dict:
        """Get store info (POSTMAN: Get Store Info)."""
        url = self._store_url("")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_store_address(self) -> Dict:
        """Get store address (POSTMAN: Get Store Address)."""
        url = self._store_url("/address")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_store_feedback(self) -> Dict:
        """Get store feedback (POSTMAN: Get Store Feedback)."""
        url = self._store_url("/feedback")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def set_store_status(self, status: str = "inactive") -> Dict:
        """Set store status (POSTMAN: Set Store Status)."""
        url = self._store_url(f"/status/{status}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_free_shipping_settings(self) -> Dict:
        """Get free shipping option (POSTMAN: Get Free Shipping Option)."""
        url = self._store_url("/freeshipping/settings")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    # ------------------------------------------------------------------
    # ANALYTICS
    # ------------------------------------------------------------------

    def get_top_sales(self, category_id: int = None) -> Dict:
        """Get top sold products (POSTMAN: List/Search Top Sold Products)."""
        if category_id:
            url = self._store_url("/inventory/topsalessearch")
            resp = self.session.post(url, json={"categoryId": category_id})
        else:
            url = self._store_url("/inventory/topsales")
            resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_inventory_groups(self) -> Dict:
        """Get inventory groups (POSTMAN: List All Groups)."""
        url = self._store_url("/inventory/groups")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_inventory_categories(self) -> Dict:
        """Get inventory categories (POSTMAN: List All Categories)."""
        url = self._store_url("/inventory/categories")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def search_inventory(self, query: str) -> Dict:
        """Search inventory (POSTMAN: List Catalog Objects)."""
        url = self._store_url(f"/inventory/search?q={query}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_related_products(self, product_id: int) -> Dict:
        """Get related products (POSTMAN: List Related Products)."""
        url = self._store_url(f"/inventory/products/{product_id}/relatedproducts")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_shipping_options(self, product_id: int) -> Dict:
        """Get shipping options (POSTMAN: List Shipping Options)."""
        url = self._store_url(f"/inventory/products/{product_id}/shippingoptions")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    # ------------------------------------------------------------------
    # BUYLIST
    # ------------------------------------------------------------------

    def get_buylist_prices(self, sku_id: int = None) -> Dict:
        """Get buylist prices (POSTMAN: List/Get SKU Buylist Price)."""
        if sku_id:
            url = self._store_url(f"/buylist/skuprices/{sku_id}")
        else:
            url = self._store_url("/buylist/skuprices")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def create_buylist(self, sku_id: int, price: float, quantity: int) -> Dict:
        """Create SKU buylist (POSTMAN: PUT Create SKU Buylist)."""
        url = self._store_url(f"/buylist/skus/{sku_id}")
        body = [{"skuId": sku_id, "price": price, "quantity": quantity}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def update_buylist_price(self, sku_id: int, price: float) -> Dict:
        """Update buylist price (POSTMAN: PUT Update SKU Buylist Price)."""
        url = self._store_url(f"/buylist/skus/{sku_id}/price")
        body = [{"skuId": sku_id, "price": price}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_buylist_quantity(self, sku_id: int, quantity: int) -> Dict:
        """Update buylist quantity (POSTMAN: PUT Update SKU Buylist Quantity)."""
        url = self._store_url(f"/buylist/skus/{sku_id}/quantity")
        body = [{"skuId": sku_id, "quantity": quantity}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # PRODUCT LISTS
    # ------------------------------------------------------------------

    def list_product_lists(self) -> Dict:
        """List all product lists (POSTMAN: List All ProductLists)."""
        url = f"{API_BASE}/{self.version}/inventory/productlists"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def get_product_list(self, list_id: str) -> Dict:
        """Get product list by ID (POSTMAN: Get ProductList By Id)."""
        url = f"{API_BASE}/{self.version}/inventory/productlists/{list_id}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else {}

    def create_product_list(self, items: List[Dict]) -> Dict:
        """
        Create a product list (POSTMAN: POST Create ProductList).
        items: [{"quantity": 2, "productConditionId": 21163}, ...]
        """
        url = f"{API_BASE}/{self.version}/inventory/productlists"
        resp = self.session.post(url, json=items)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    # ------------------------------------------------------------------
    # MASS ENTRY
    # ------------------------------------------------------------------

    def mass_entry(self, raw_text: str) -> Dict:
        """
        Mass entry request (POSTMAN: POST Mass Entry request).
        raw_text: newline-separated card entries.
        """
        url = "https://store.tcgplayer.com/massentry"
        resp = self.session.post(url, json={"text": raw_text})
        return resp.json() if resp.status_code == 200 else resp.json()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='TCGplayer Inventory Management')
    p.add_argument('cmd', choices=[
        'login', 'inventory', 'orders', 'customers', 'store',
        'update-price', 'update-qty', 'batch-prices', 'top-sales',
        'buylist', 'product-lists', 'search-inv', 'order-details'
    ])
    p.add_argument('--email', default='')
    p.add_argument('--password', default='')
    p.add_argument('--sku-id', type=int)
    p.add_argument('--product-id', type=int)
    p.add_argument('--price', type=float)
    p.add_argument('--quantity', type=int)
    p.add_argument('--order-id', default='')
    p.add_argument('--customer-token', default='')
    p.add_argument('--query', default='')
    p.add_argument('--limit', type=int, default=20)
    args = p.parse_args()

    inv = TCGInventory()

    if args.cmd == 'login':
        ok = inv.login(args.email, args.password)
        print(f"Login: {'OK' if ok else 'FAILED'}")
        if ok:
            print(f"Store Key: {inv.store_key}")
            print(json.dumps(inv.user, indent=2)[:2000])
    elif args.cmd == 'inventory':
        data = inv.list_inventory(limit=args.limit)
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'orders':
        data = inv.get_orders(limit=args.limit)
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'customers':
        data = inv.get_customers(name=args.query) if args.query else inv.get_customers()
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'store':
        data = inv.get_store_info()
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'update-price':
        if not args.sku_id or not args.price:
            print("Requires --sku-id and --price")
        else:
            data = inv.update_price(args.sku_id, args.price)
            print(json.dumps(data, indent=2)[:1000])
    elif args.cmd == 'update-qty':
        if not args.sku_id or not args.quantity:
            print("Requires --sku-id and --quantity")
        else:
            data = inv.update_quantity(args.sku_id, args.quantity)
            print(json.dumps(data, indent=2)[:1000])
    elif args.cmd == 'batch-prices':
        print("Use Python API: inv.batch_update_prices([{'skuId': 123, 'price': 9.99}])")
    elif args.cmd == 'top-sales':
        data = inv.get_top_sales()
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'buylist':
        if args.sku_id:
            data = inv.get_buylist_prices(args.sku_id)
        else:
            data = inv.get_buylist_prices()
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'product-lists':
        data = inv.list_product_lists()
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'search-inv':
        data = inv.search_inventory(args.query)
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'order-details':
        if not args.order_id:
            print("Requires --order-id")
        else:
            data = inv.get_order_details(args.order_id)
            print(json.dumps(data, indent=2)[:2000])
