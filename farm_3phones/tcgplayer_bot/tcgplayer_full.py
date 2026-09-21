#!/usr/bin/env python3
"""
tcgplayer_full.py — Full TCGplayer API client extracted from official Postman collection.

ALL endpoints from TCGplayer API v1.9.0.
Authentication: OAuth2 client_credentials (publicId/privateId).

Usage:
    from tcgplayer_full import TCGplayerFull
    client = TCGplayerFull(publicId="...", privateId="...")
    products = client.search_pokemon("Charizard VMAX")
    details = client.product_details(684332)
    listings = client.product_listings(684332, condition=["Near Mint"])
"""
import requests
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

BASE_URLS = {
    "api": "https://api.tcgplayer.com",
    "mpapi": "https://mpapi.tcgplayer.com",
    "mp-search-api": "https://mp-search-api.tcgplayer.com",
    "infinite-api": "https://infinite-api.tcgplayer.com",
    "mpgateway": "https://mpgateway.tcgplayer.com",
    "data": "https://data.tcgplayer.com",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
}

POST_HEADERS = {**DEFAULT_HEADERS, "Content-Type": "application/json"}


class TCGplayerFull:
    """Full TCGplayer API client — ALL endpoints from official Postman collection."""

    def __init__(self, publicId: str = "", privateId: str = "", accessToken: str = ""):
        self.publicId = publicId
        self.privateId = privateId
        self.accessToken = accessToken
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if accessToken:
            self.session.headers["Authorization"] = f"Bearer {accessToken}"

    # ─── AUTHENTICATION ─────────────────────────────────────────────────

    def authenticate(self) -> dict:
        """POST /token — Get OAuth2 access token."""
        url = f"{BASE_URLS['api']}/token"
        data = f"grant_type=client_credentials&client_id={self.publicId}&client_secret={self.privateId}"
        resp = self.session.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code == 200:
            self.accessToken = resp.json().get("access_token", "")
            self.session.headers["Authorization"] = f"Bearer {self.accessToken}"
            return {"status": "ok", "token": self.accessToken[:20] + "..."}
        return {"status": "error", "code": resp.status_code, "body": resp.text[:500]}

    # ─── CATALOG ─────────────────────────────────────────────────────────

    def list_categories(self, limit: int = 100) -> dict:
        """GET /catalog/categories — List all categories."""
        url = f"{BASE_URLS['api']}/v1.9.0/catalog/categories?limit={limit}"
        return self.session.get(url).json()

    def get_category_details(self, categoryId: int) -> dict:
        """GET /catalog/categories/{id} — Get category details."""
        url = f"{BASE_URLS['api']}/v1.9.0/catalog/categories/{categoryId}"
        return self.session.get(url).json()

    def get_category_manifest(self, categoryId: int) -> dict:
        """GET /catalog/categories/{id}/search/manifest — Get search manifest."""
        url = f"{BASE_URLS['api']}/v1.9.0/catalog/categories/{categoryId}/search/manifest"
        return self.session.get(url).json()

    def list_products(self, categoryId: int, limit: int = 100, offset: int = 0, sort: str = "name", filters: list = None) -> dict:
        """POST /catalog/products — Search products in a category."""
        url = f"{BASE_URLS['api']}/v1.9.0/catalog/products"
        body = {"sort": sort, "limit": limit, "offset": offset, "filters": filters or []}
        return self.session.post(url, json=body).json()

    def search_pokemon(self, query: str, limit: int = 10) -> dict:
        """Search Pokemon products by name."""
        return self.list_products(categoryId=3, limit=limit, filters=[{"name": "name", "values": [query]}])

    def get_product_details(self, productId: int) -> dict:
        """GET /catalog/products/{id} — Get product details."""
        url = f"{BASE_URLS['api']}/v1.9.0/catalog/products/{productId}"
        return self.session.get(url).json()

    def get_product_categories(self) -> dict:
        """GET /catalog/categories — Get Pokemon category ID."""
        cats = self.list_categories()
        for cat in cats.get("results", []):
            if "pokemon" in cat.get("name", "").lower():
                return cat
        return {}

    # ─── PRICING (mpgateway) ─────────────────────────────────────────────

    def get_market_price(self, productId: int) -> dict:
        """GET /pricepoints/marketprice/products/{id} — Get market price."""
        url = f"{BASE_URLS['mpgateway']}/v1/pricepoints/marketprice/skus/search?mpfev=5555"
        return self.session.post(url, json={"skuIds": [productId]}, headers=POST_HEADERS).json()

    def get_price_history(self, productId: int, range: str = "quarter") -> dict:
        """GET /price/history/{id}/detailed — Get price history."""
        url = f"{BASE_URLS['infinite-api']}/price/history/{productId}/detailed?range={range}"
        return self.session.get(url).json()

    def get_buylist_price(self, productId: int) -> dict:
        """GET /pricepoints/buylist/marketprice/products/{id} — Get buylist price."""
        url = f"{BASE_URLS['mpgateway']}/v1/pricepoints/buylist/marketprice/products/{productId}?mpfev=5555"
        return self.session.get(url).json()

    # ─── SEARCH (mp-search-api) ──────────────────────────────────────────

    def search_products(self, query: str, categoryId: int = 3, limit: int = 20) -> dict:
        """POST /search/request — Full search with filters."""
        url = f"{BASE_URLS['mp-search-api']}/v1/search/request"
        body = {
            "filters": {
                "term": {
                    "productLineName": ["pokemon"],
                    "name": [query],
                    "sellerStatus": "Live",
                    "channelId": 0,
                },
                "range": {"quantity": {"gte": 1}},
            },
            "from": 0,
            "size": limit,
            "sort": {"field": "price+shipping", "order": "asc"},
        }
        return self.session.post(url, json=body, headers=POST_HEADERS).json()

    def product_details_v2(self, productId: int) -> dict:
        """GET /v2/product/{id}/details — Full product details."""
        url = f"{BASE_URLS['mp-search-api']}/v2/product/{productId}/details?mpfev=5555"
        return self.session.get(url).json()

    def product_listings(self, productId: int, conditions: list = None, limit: int = 10) -> dict:
        """POST /v1/product/{id}/listings — Get seller listings."""
        url = f"{BASE_URLS['mp-search-api']}/v1/product/{productId}/listings"
        body = {
            "filters": {
                "term": {"sellerStatus": "Live", "channelId": 0, "language": ["English"]},
                "range": {"quantity": {"gte": 1}},
            },
            "from": 0,
            "size": limit,
        }
        if conditions:
            body["filters"]["term"]["condition"] = conditions
        return self.session.post(url, json=body, headers=POST_HEADERS).json()

    def product_sales(self, productId: int, conditions: list = None, limit: int = 25) -> dict:
        """POST /v2/product/{id}/latestsales — Get recent sales."""
        url = f"{BASE_URLS['mpapi']}/v2/product/{productId}/latestsales?mpfev=5555"
        body = {
            "conditions": conditions or [],
            "languages": [1],
            "variants": [1],
            "listingType": "All",
            "limit": limit,
        }
        return self.session.post(url, json=body, headers=POST_HEADERS).json()

    # ─── INVENTORY (authenticated) ───────────────────────────────────────

    def get_inventory(self) -> dict:
        """GET /v2/inventory — Get user inventory."""
        url = f"{BASE_URLS['api']}/v2/inventory"
        return self.session.get(url).json()

    def add_inventory(self, productId: int, quantity: int, price: float, condition: str = "Near Mint") -> dict:
        """POST /v2/inventory — Add item to inventory."""
        url = f"{BASE_URLS['api']}/v2/inventory"
        body = {"productId": productId, "quantity": quantity, "price": price, "condition": condition}
        return self.session.post(url, json=body).json()

    # ─── ORDERS (authenticated) ─────────────────────────────────────────

    def get_orders(self, status: str = "All", limit: int = 10) -> dict:
        """GET /v2/orders — Get orders."""
        url = f"{BASE_URLS['api']}/v2/orders?status={status}&limit={limit}"
        return self.session.get(url).json()

    # ─── UTILITIES ───────────────────────────────────────────────────────

    def save_to_file(self, data: dict, filename: str):
        """Save response to JSON file."""
        path = Path("tcgplayer_data") / filename
        path.parent.mkdir(exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return str(path)


# ─── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TCGplayer Full API Client")
    parser.add_argument("--public-id", default="", help="API public ID")
    parser.add_argument("--private-id", default="", help="API private ID")
    parser.add_argument("--token", default="", help="Existing access token")
    parser.add_argument("command", choices=["auth", "search", "details", "listings", "sales", "price", "history", "categories"])
    parser.add_argument("--query", default="Charizard", help="Search query")
    parser.add_argument("--product-id", type=int, default=684332, help="Product ID")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    client = TCGplayerFull(args.public_id, args.private_id, args.token)

    if args.command == "auth":
        print(json.dumps(client.authenticate(), indent=2))
    elif args.command == "search":
        print(json.dumps(client.search_pokemon(args.query, args.limit), indent=2)[:2000])
    elif args.command == "details":
        print(json.dumps(client.product_details_v2(args.product_id), indent=2)[:2000])
    elif args.command == "listings":
        print(json.dumps(client.product_listings(args.product_id, limit=args.limit), indent=2)[:2000])
    elif args.command == "sales":
        print(json.dumps(client.product_sales(args.product_id, limit=args.limit), indent=2)[:2000])
    elif args.command == "price":
        print(json.dumps(client.get_market_price(args.product_id), indent=2)[:2000])
    elif args.command == "history":
        print(json.dumps(client.get_price_history(args.product_id), indent=2)[:2000])
    elif args.command == "categories":
        print(json.dumps(client.list_categories(), indent=2)[:2000])
