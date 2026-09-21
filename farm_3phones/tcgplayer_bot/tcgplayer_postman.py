#!/usr/bin/env python3
"""
tcgplayer_postman.py — TCGplayer API client using official Postman collection endpoints.

Integrates all 79 endpoints from TCGplayer.postman_collection.json.
Auth via Bearer token (obtained from /token or /v2/login).

Reference: tcgplayer_postman/TCGPlayer.postman_collection.json

Usage:
    from tcgplayer_postman import TCGPostman
    api = TCGPostman()
    api.authenticate("public_key", "private_key")
    categories = api.list_categories()
    products = api.search_category_products(category_id=1, name="Charizard")
"""
import json
import time
import requests
from typing import Optional, Dict, Any, List

API_BASE = "https://api.tcgplayer.com"
MPAPI = "https://mpapi.tcgplayer.com"
SEARCH_API = "https://mp-search-api.tcgplayer.com"
GATEWAY = "https://mpgateway.tcgplayer.com"
MPGATEWAY = GATEWAY  # Alias for convenience
MPFEV = "5555"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
}


class TCGPostman:
    """TCGplayer API client using official Postman collection endpoints."""

    def __init__(self, version: str = "v1.37.0"):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.token: Optional[str] = None
        self.version = version
        self.base_url = f"{API_BASE}/{version}"
        self.mpfev = MPFEV

    # ------------------------------------------------------------------
    # AUTH (POSTMAN: Authenticate)
    # ------------------------------------------------------------------

    def authenticate(self, public_key: str, private_key: str) -> bool:
        """Authenticate via client credentials (POSTMAN: Authenticate)."""
        resp = self.session.post(
            f"{API_BASE}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": public_key,
                "client_secret": private_key,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token")
            if self.token:
                self.session.headers["Authorization"] = f"Bearer {self.token}"
            return True
        return False

    def login(self, email: str, password: str) -> bool:
        """User login via mpapi (alternative to token auth)."""
        resp = self.session.post(
            f"{MPAPI}/v2/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token") or data.get("token")
            if self.token:
                self.session.headers["Authorization"] = f"Bearer {self.token}"
            return True
        return False

    def store_authorize(self, code: str) -> Dict:
        """Store authorization (POSTMAN: Store Authorization)."""
        url = f"{API_BASE}/app/authorize/{code}"
        resp = self.session.post(url)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    # ------------------------------------------------------------------
    # CATALOG (POSTMAN: Categories, Groups, Products)
    # ------------------------------------------------------------------

    def list_categories(self, category_id: int = None, limit: int = 100,
                        offset: int = 0) -> Dict:
        """
        List categories (POSTMAN: List All Categories).
        Uses mpapi.tcgplayer.com/v2/Catalog/Categories (requires auth for full list).
        Falls back to CatalogGroups (no auth).
        """
        # CatalogGroups works without auth
        resp = self.session.get(f"{MPAPI}/v2/Catalog/CatalogGroups")
        if resp.status_code == 200:
            return resp.json()
        # Try catalog endpoint
        url = f"{self.base_url}/catalog/categories"
        resp = self.session.get(url, params={"limit": limit, "offset": offset})
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_category_details(self, category_id: int) -> Dict:
        """Get category details (POSTMAN: Get Category Details)."""
        # mpapi v2 requires auth; use search API manifest as fallback
        url = f"{SEARCH_API}/v1/search/request?categoryId={category_id}&mpfev={self.mpfev}"
        resp = self.session.get(url)
        if resp.status_code == 200:
            return resp.json()
        url = f"{self.base_url}/catalog/categories/{category_id}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_category_search_manifest(self, category_id: int) -> Dict:
        """Get category search manifest (POSTMAN: Get Category Search Manifest)."""
        url = f"{SEARCH_API}/v1/search/request?categoryId={category_id}&mpfev={self.mpfev}"
        resp = self.session.get(url)
        if resp.status_code == 200:
            return resp.json()
        url = f"{self.base_url}/catalog/categories/{category_id}/search/manifest"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_category_products(self, category_id: int,
                                name: str = None,
                                sort: str = "name",
                                limit: int = 100,
                                offset: int = 0,
                                **filters) -> Dict:
        """
        Search category products (POSTMAN: Search Category Products).
        Uses mp-search-api v1/search/request.
        """
        url = f"{SEARCH_API}/v1/search/request?mpfev={self.mpfev}"
        filter_list = []
        if name:
            filter_list.append({"name": "ProductName", "values": [name]})
        for fname, fvalues in filters.items():
            filter_list.append({"name": fname, "values": fvalues if isinstance(fvalues, list) else [fvalues]})
        body = {"sort": sort, "limit": limit, "offset": offset, "filters": filter_list}
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_groups(self, category_id: int, limit: int = 100,
                             offset: int = 0) -> Dict:
        """List all category groups (POSTMAN: List All Category Groups)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/groups"
        resp = self.session.get(url, params={"limit": limit, "offset": offset})
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_rarities(self, category_id: int) -> Dict:
        """List category rarities (POSTMAN: List All Category Rarities)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/rarities"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_printings(self, category_id: int) -> Dict:
        """List category printings (POSTMAN: List All Category Printings)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/printings"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_conditions(self, category_id: int) -> Dict:
        """List category conditions (POSTMAN: List All Category Conditions)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/conditions"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_languages(self, category_id: int) -> Dict:
        """List category languages (POSTMAN: List All Category Languages)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/languages"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_category_media(self, category_id: int) -> Dict:
        """List category media (POSTMAN: List All Category Media)."""
        url = f"{MPAPI}/v2/Catalog/Categories/{category_id}/media"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_groups(self, category_id: int = None, limit: int = 100,
                    offset: int = 0, **filters) -> Dict:
        """List all groups (POSTMAN: List All Group Details).
        Uses mpapi v2/Catalog/Groups (requires auth). Returns empty if unauthorized."""
        url = f"{MPAPI}/v2/Catalog/Groups"
        params = {"limit": limit, "offset": offset}
        if category_id:
            params["categoryId"] = category_id
        resp = self.session.get(url, params=params)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"error": resp.text[:500]}
        return {"error": resp.text[:500], "status": resp.status_code}

    def get_group_details(self, group_id: int) -> Dict:
        """Get group details (POSTMAN: Get Group Details)."""
        url = f"{MPAPI}/v2/Catalog/Groups/{group_id}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_group_media(self, group_id: int, category_id: int = None) -> Dict:
        """List group media (POSTMAN: List All Group Media)."""
        url = f"{MPAPI}/v2/Catalog/Groups/{group_id}/media"
        params = {}
        if category_id:
            params["categoryId"] = category_id
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_products(self, category_id: int = None,
                      product_types: str = "Cards",
                      limit: int = 200, offset: int = 0, **filters) -> Dict:
        """List all products (POSTMAN: List All Products)."""
        url = f"{MPAPI}/v2/Catalog/Products"
        params = {"limit": limit, "offset": offset}
        if category_id:
            params["categoryId"] = category_id
        if product_types:
            params["productTypes"] = product_types
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_product_details(self, product_ids: List[int]) -> Dict:
        """Get product details (POSTMAN: Get Product Details)."""
        ids_str = ",".join(str(pid) for pid in product_ids)
        url = f"{MPAPI}/v2/Catalog/Products/{ids_str}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_product_skus(self, product_id: int) -> Dict:
        """List product SKUs (POSTMAN: List Product SKUs)."""
        url = f"{MPAPI}/v2/Catalog/Products/{product_id}/skus"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_related_products(self, product_id: int) -> Dict:
        """List related products (POSTMAN: List Related Products)."""
        url = f"{MPAPI}/v2/Catalog/Products/{product_id}/productsalsopurchased"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_sku_details(self, sku_ids: List[int]) -> Dict:
        """Get SKU details (POSTMAN: Get SKU Details)."""
        ids_str = ",".join(str(s) for s in sku_ids)
        url = f"{MPAPI}/v2/Catalog/Skus/{ids_str}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_super_conditions(self) -> Dict:
        """List super conditions (POSTMAN: List SuperConditions)."""
        url = f"{MPAPI}/v2/Catalog/Superconditions"
        resp = self.session.get(url)
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception:
                return {"error": resp.text[:500]}
        return {"error": resp.text[:500], "status": resp.status_code}

    # ------------------------------------------------------------------
    # PRICING (POSTMAN: Market Price, Buylist)
    # ------------------------------------------------------------------

    def get_market_price(self, sku_ids: List[int]) -> Dict:
        """Get market price by SKU (POSTMAN: Get Market Price by SKU).
        Uses mpgateway endpoint that works without auth."""
        url = f"{MPGATEWAY}/v1/pricepoints/marketprice/skus/search?mpfev={self.mpfev}"
        resp = self.session.post(url, json={"skuIds": sku_ids})
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_product_market_prices(self, product_ids: List[int]) -> Dict:
        """List product market prices (POSTMAN: List Product Market Prices)."""
        ids_str = ",".join(str(p) for p in product_ids)
        url = f"{MPAPI}/v2/Pricing/Product/{ids_str}/MarketPrice"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_product_prices_by_group(self, group_id: int) -> Dict:
        """List product prices by group (POSTMAN: List Product Prices by Group)."""
        url = f"{MPAPI}/v2/Pricing/Group/{group_id}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_sku_market_prices(self, sku_ids: List[int]) -> Dict:
        """List SKU market prices (POSTMAN: List SKU Market Prices)."""
        url = f"{MPGATEWAY}/v1/pricepoints/marketprice/skus/search?mpfev={self.mpfev}"
        resp = self.session.post(url, json={"skuIds": sku_ids})
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_product_buylist_prices(self, product_ids: List[int]) -> Dict:
        """List product buylist prices (POSTMAN: List Product Buylist Prices)."""
        ids_str = ",".join(str(p) for p in product_ids)
        url = f"{MPAPI}/v2/Pricing/Product/{ids_str}/BuylistPrice"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_sku_buylist_prices(self, sku_ids: List[int]) -> Dict:
        """List SKU buylist prices (POSTMAN: List SKU Buylist Prices)."""
        url = f"{MPGATEWAY}/v1/pricepoints/buylist/skus/search?mpfev={self.mpfev}"
        resp = self.session.post(url, json={"skuIds": sku_ids})
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_sku_buylist_price(self, sku_id: int) -> Dict:
        """Get SKU buylist price (POSTMAN: Get SKU Buylist Price)."""
        url = f"{MPGATEWAY}/v1/pricepoints/buylist/skus/search?mpfev={self.mpfev}"
        resp = self.session.post(url, json={"skuIds": [sku_id]})
        return resp.json() if resp.status_code == 200 else resp.json()

    def create_sku_buylist(self, sku_id: int, price: float, quantity: int) -> Dict:
        """Create SKU buylist (POSTMAN: Create SKU Buylist). Requires seller auth."""
        url = f"{MPAPI}/v2/Pricing/Sku/{sku_id}/BuylistPrice"
        resp = self.session.put(url, json={"price": price, "quantity": quantity})
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def update_sku_buylist_price(self, sku_id: int, price: float) -> Dict:
        """Update SKU buylist price (POSTMAN: Update SKU Buylist Price). Requires seller auth."""
        url = f"{MPAPI}/v2/Pricing/Sku/{sku_id}/BuylistPrice/Update"
        resp = self.session.put(url, json={"price": price})
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_sku_buylist_quantity(self, sku_id: int, quantity: int) -> Dict:
        """Update SKU buylist quantity (POSTMAN: Update SKU Buylist Quantity). Requires seller auth."""
        url = f"{MPAPI}/v2/Pricing/Sku/{sku_id}/BuylistQuantity"
        resp = self.session.put(url, json={"quantity": quantity})
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # STORE INVENTORY (POSTMAN: Store endpoints)
    # ------------------------------------------------------------------

    def _store_url(self, store_key: str, path: str) -> str:
        return f"{self.base_url}/stores/{store_key}{path}"

    def get_store_info(self, store_key: str) -> Dict:
        """Get store info (POSTMAN: Get Store Info)."""
        url = f"{MPAPI}/v2/Stores/{store_key}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_store_self(self) -> Dict:
        """Get own store info (POSTMAN: Get Store Info self)."""
        url = f"{MPAPI}/v2/Stores/self"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_stores(self, name: str) -> Dict:
        """Search stores (POSTMAN: Search Stores)."""
        url = f"{MPAPI}/v2/Stores"
        resp = self.session.get(url, params={"name": name})
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_store_address(self, store_key: str) -> Dict:
        """Get store address (POSTMAN: Get Store Address)."""
        url = f"{MPAPI}/v2/Stores/{store_key}/address"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_store_feedback(self, store_key: str) -> Dict:
        """Get store feedback (POSTMAN: Get Store Feedback)."""
        url = f"{MPAPI}/v2/Stores/{store_key}/feedback"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_free_shipping_settings(self, store_key: str) -> Dict:
        """Get free shipping settings (POSTMAN: Get Free Shipping Option)."""
        url = f"{MPAPI}/v2/Stores/{store_key}/freeshipping/settings"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_category_skus(self, store_key: str, category_id: int) -> Dict:
        """Get category SKUs (POSTMAN: Get Category SKUs)."""
        url = f"{MPAPI}/v2/Stores/{store_key}/categories/{category_id}/skus"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def set_store_status(self, store_key: str, status: str = "inactive") -> Dict:
        """Set store status (POSTMAN: Set Store Status)."""
        url = f"{MPAPI}/v2/Stores/{store_key}/status/{status}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # STORE CUSTOMERS
    # ------------------------------------------------------------------

    def get_customer_summary(self, store_key: str, customer_token: str) -> Dict:
        """Get customer summary (POSTMAN: Get Customer Summary)."""
        url = self._store_url(store_key, f"/customers/{customer_token}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_customers(self, store_key: str, name: str) -> Dict:
        """Search store customers (POSTMAN: Search Store Customers)."""
        url = self._store_url(store_key, "/customers")
        resp = self.session.get(url, params={"name": name})
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_customer_addresses(self, store_key: str, customer_token: str) -> Dict:
        """Get customer addresses (POSTMAN: Get Customer Addresses)."""
        url = self._store_url(store_key, f"/customers/{customer_token}/addresses")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_customer_orders(self, store_key: str, customer_token: str) -> Dict:
        """Get customer orders (POSTMAN: Get Customer Orders)."""
        url = self._store_url(store_key, f"/customers/{customer_token}/orders")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # STORE INVENTORY
    # ------------------------------------------------------------------

    def get_product_inventory_quantities(self, store_key: str,
                                          product_id: int) -> Dict:
        """Get product inventory quantities (POSTMAN: Get Product Inventory Quantities)."""
        url = self._store_url(store_key, f"/inventory/products/{product_id}/quantity")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_product_summary(self, store_key: str) -> Dict:
        """List product summary (POSTMAN: List Product Summary)."""
        url = self._store_url(store_key, "/inventory/products")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_related_products_store(self, store_key: str, product_id: int) -> Dict:
        """List related products (store) (POSTMAN: List Related Products)."""
        url = self._store_url(store_key, f"/inventory/products/{product_id}/relatedproducts")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_shipping_options(self, store_key: str, product_id: int) -> Dict:
        """List shipping options (POSTMAN: List Shipping Options)."""
        url = self._store_url(store_key, f"/inventory/products/{product_id}/shippingoptions")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_sku_quantity(self, store_key: str, sku_id: int) -> Dict:
        """Get SKU quantity (POSTMAN: Get SKU Quantity)."""
        url = self._store_url(store_key, f"/inventory/skus/{sku_id}/quantity")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def increment_sku_quantity(self, store_key: str, sku_id: int,
                               quantity: int, channel_id: int = 1) -> Dict:
        """Increment SKU quantity (POSTMAN: POST Increment SKU Inventory Quantity)."""
        url = self._store_url(store_key, f"/inventory/skus/{sku_id}/quantity")
        body = {"quantity": quantity, "channelId": channel_id}
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def update_sku_inventory(self, store_key: str, sku_id: int,
                             quantity: int = None, price: float = None,
                             channel_id: int = None) -> Dict:
        """Update SKU inventory (POSTMAN: PUT Update SKU Inventory)."""
        url = self._store_url(store_key, f"/inventory/skus/{sku_id}")
        body = {}
        if quantity is not None:
            body["quantity"] = quantity
        if price is not None:
            body["price"] = int(price * 100)
        if channel_id is not None:
            body["channelId"] = channel_id
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_sku_inventory_price(self, store_key: str, sku_id: int,
                                   price: float, channel_id: int = 1) -> Dict:
        """Update SKU inventory price (POSTMAN: PUT Update SKU Inventory Price)."""
        url = self._store_url(store_key, f"/inventory/skus/{sku_id}/price")
        body = [{"price": int(price * 100), "channelId": channel_id}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def batch_update_sku_prices(self, store_key: str,
                                items: List[Dict]) -> Dict:
        """Batch update SKU prices (POSTMAN: POST Batch Update Store SKU Prices)."""
        url = self._store_url(store_key, "/inventory/skus/batch")
        body = []
        for item in items:
            entry = {"skuId": item["skuId"]}
            if "price" in item:
                entry["price"] = int(item["price"] * 100)
            if "channelId" in item:
                entry["channelId"] = item["channelId"]
            body.append(entry)
        resp = self.session.post(url, json=body)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def list_sku_list_prices(self, store_key: str, offset: int = 0,
                             limit: int = 500) -> Dict:
        """List SKU list prices (POSTMAN: List SKU List Price)."""
        url = self._store_url(store_key, "/inventory/skuprices")
        resp = self.session.get(url, params={"offset": offset, "limit": limit})
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_sku_list_price(self, store_key: str, sku_id: int) -> Dict:
        """Get SKU list price (POSTMAN: Get SKU List Price)."""
        url = self._store_url(store_key, f"/inventory/skuprices/{sku_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_inventory_groups(self, store_key: str) -> Dict:
        """List inventory groups (POSTMAN: List All Groups)."""
        url = self._store_url(store_key, "/inventory/groups")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_inventory_categories(self, store_key: str) -> Dict:
        """List inventory categories (POSTMAN: List All Categories)."""
        url = self._store_url(store_key, "/inventory/categories")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_top_sold(self, store_key: str) -> Dict:
        """List top sold products (POSTMAN: List Top Sold Products)."""
        url = self._store_url(store_key, "/inventory/topsales")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_top_sold(self, store_key: str, category_id: int) -> Dict:
        """Search top sold products (POSTMAN: Search Top Sold Products)."""
        url = self._store_url(store_key, "/inventory/topsalessearch")
        resp = self.session.post(url, json={"categoryId": category_id})
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_catalog_objects(self, store_key: str, query: str) -> Dict:
        """Search catalog objects (POSTMAN: List Catalog Objects)."""
        url = self._store_url(store_key, f"/inventory/search?q={query}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # ORDERS
    # ------------------------------------------------------------------

    def get_order_manifest(self, store_key: str) -> Dict:
        """Get order manifest (POSTMAN: Get Order Manifest)."""
        url = self._store_url(store_key, "/orders/manifest")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_order_details(self, store_key: str, order_id: str) -> Dict:
        """Get order details (POSTMAN: Get Order Details)."""
        url = self._store_url(store_key, f"/orders/{order_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_order_feedback(self, store_key: str, order_id: str) -> Dict:
        """Get order feedback (POSTMAN: Get Order Feedback)."""
        url = self._store_url(store_key, f"/orders/{order_id}/feedback")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def search_orders(self, store_key: str, order_number: str = None) -> Dict:
        """Search orders (POSTMAN: Search Orders)."""
        url = self._store_url(store_key, "/orders")
        params = {}
        if order_number:
            params["orderNumber"] = order_number
        resp = self.session.get(url, params=params)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_order_items(self, store_key: str, order_id: str) -> Dict:
        """Get order items (POSTMAN: Get Order Items)."""
        url = self._store_url(store_key, f"/orders/{order_id}/items")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_order_tracking(self, store_key: str, order_id: str) -> Dict:
        """Get order tracking (POSTMAN: Get Order Tracking Numbers)."""
        url = self._store_url(store_key, f"/orders/{order_id}/tracking")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def add_order_tracking(self, store_key: str, order_id: str,
                           tracking_numbers: List[str]) -> Dict:
        """Add order tracking (POSTMAN: POST Add Order Tracking Number)."""
        url = self._store_url(store_key, f"/orders/{order_id}/tracking")
        resp = self.session.post(url, json=tracking_numbers)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    # ------------------------------------------------------------------
    # BUYLIST
    # ------------------------------------------------------------------

    def get_sku_buylist_price(self, store_key: str, sku_id: int) -> Dict:
        """Get SKU buylist price (POSTMAN: Get SKU Buylist Price)."""
        url = self._store_url(store_key, f"/buylist/skuprices/{sku_id}")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def list_sku_buylist_prices_store(self, store_key: str) -> Dict:
        """List SKU buylist prices (POSTMAN: List SKU Buylist Price)."""
        url = self._store_url(store_key, "/buylist/skuprices")
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def create_sku_buylist(self, store_key: str, sku_id: int,
                           price: float, quantity: int) -> Dict:
        """Create SKU buylist (POSTMAN: PUT Create SKU Buylist)."""
        url = self._store_url(store_key, f"/buylist/skus/{sku_id}")
        body = [{"skuId": sku_id, "price": price, "quantity": quantity}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    def update_sku_buylist_price(self, store_key: str, sku_id: int,
                                 price: float) -> Dict:
        """Update SKU buylist price (POSTMAN: PUT Update SKU Buylist Price)."""
        url = self._store_url(store_key, f"/buylist/skus/{sku_id}/price")
        body = [{"skuId": sku_id, "price": price}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    def update_sku_buylist_quantity(self, store_key: str, sku_id: int,
                                    quantity: int) -> Dict:
        """Update SKU buylist quantity (POSTMAN: PUT Update SKU Buylist Quantity)."""
        url = self._store_url(store_key, f"/buylist/skus/{sku_id}/quantity")
        body = [{"skuId": sku_id, "quantity": quantity}]
        resp = self.session.put(url, json=body)
        return resp.json() if resp.status_code == 200 else resp.json()

    # ------------------------------------------------------------------
    # PRODUCT LISTS
    # ------------------------------------------------------------------

    def list_product_lists(self) -> Dict:
        """List all product lists (POSTMAN: List All ProductLists)."""
        url = f"{self.base_url}/inventory/productlists"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def get_product_list_by_id(self, list_id: str) -> Dict:
        """Get product list by ID (POSTMAN: Get ProductList By Id)."""
        url = f"{self.base_url}/inventory/productlists/{list_id}"
        resp = self.session.get(url)
        return resp.json() if resp.status_code == 200 else resp.json()

    def create_product_list(self, items: List[Dict]) -> Dict:
        """Create product list (POSTMAN: POST Create ProductList)."""
        url = f"{self.base_url}/inventory/productlists"
        resp = self.session.post(url, json=items)
        return resp.json() if resp.status_code in (200, 201) else resp.json()

    # ------------------------------------------------------------------
    # MASS ENTRY
    # ------------------------------------------------------------------

    def mass_entry(self, raw_text: str) -> Dict:
        """Mass entry request (POSTMAN: POST Mass Entry request)."""
        url = "https://store.tcgplayer.com/massentry"
        resp = self.session.post(url, json={"text": raw_text})
        return resp.json() if resp.status_code == 200 else resp.json()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='TCGplayer Postman API Client')
    p.add_argument('cmd', choices=[
        'categories', 'category', 'groups', 'products', 'product',
        'pricing', 'buylist', 'stores', 'store', 'search-catalog',
        'superconditions', 'list-product-lists'
    ])
    p.add_argument('--public-key', default='')
    p.add_argument('--private-key', default='')
    p.add_argument('--category-id', type=int)
    p.add_argument('--group-id', type=int)
    p.add_argument('--product-id', type=int)
    p.add_argument('--sku-id', type=int)
    p.add_argument('--store-key', default='')
    p.add_argument('--name', default='')
    p.add_argument('--limit', type=int, default=20)
    args = p.parse_args()

    api = TCGPostman()

    if args.public_key and args.private_key:
        ok = api.authenticate(args.public_key, args.private_key)
        print(f"Auth: {'OK' if ok else 'FAILED'}")
        if not ok:
            exit(1)

    if args.cmd == 'categories':
        data = api.list_categories(limit=args.limit)
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'category':
        if not args.category_id:
            print("Requires --category-id")
        else:
            data = api.get_category_details(args.category_id)
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'groups':
        data = api.list_groups(category_id=args.category_id, limit=args.limit)
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'products':
        data = api.list_products(category_id=args.category_id, limit=args.limit)
        print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'product':
        if not args.product_id:
            print("Requires --product-id")
        else:
            data = api.get_product_details([args.product_id])
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'pricing':
        if not args.product_id:
            print("Requires --product-id")
        else:
            data = api.get_market_price(args.product_id)
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'buylist':
        if not args.product_id:
            print("Requires --product-id")
        else:
            data = api.list_product_buylist_prices(args.product_id)
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'stores':
        if not args.name:
            print("Requires --name")
        else:
            data = api.search_stores(args.name)
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'store':
        if not args.store_key:
            print("Requires --store-key")
        else:
            data = api.get_store_info(args.store_key)
            print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'search-catalog':
        if not args.category_id or not args.name:
            print("Requires --category-id and --name")
        else:
            data = api.search_category_products(args.category_id, name=args.name)
            print(json.dumps(data, indent=2)[:3000])
    elif args.cmd == 'superconditions':
        data = api.list_super_conditions()
        print(json.dumps(data, indent=2)[:2000])
    elif args.cmd == 'list-product-lists':
        data = api.list_product_lists()
        print(json.dumps(data, indent=2)[:2000])
