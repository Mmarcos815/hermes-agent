#!/usr/bin/env python3
"""
tcgplayer_bot.py — Full TCGplayer automation bot.

Features:
- Login with credentials
- Search Pokemon cards
- Track prices and find deals
- Add to cart
- Checkout with stored payment
- Monitor drops and snipe deals

Usage:
    python tcgplayer_bot.py --login
    python tcgplayer_bot.py --search "Charizard VMAX"
    python tcgplayer_bot.py --track --max-price 50
    python tcgplayer_bot.py --snipe --product-id 123456 --max-price 100
    python tcgplayer_bot.py --checkout
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from tcgplayer_api import TCGplayerAPI

CONFIG_PATH = Path(__file__).parent / "config.json"
SESSION_PATH = Path(__file__).parent / "session.json"


def load_config() -> dict:
    """Load config from file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_session(api: TCGplayerAPI):
    """Save session cookies and token."""
    session = {
        "cookies": dict(api.session.cookies),
        "token": api.token,
        "user": api.user,
    }
    with open(SESSION_PATH, "w") as f:
        json.dump(session, f, indent=2)
    print(f"[SESSION] Saved to {SESSION_PATH}")


def load_session(api: TCGplayerAPI) -> bool:
    """Load session from file."""
    if not SESSION_PATH.exists():
        return False
    try:
        with open(SESSION_PATH) as f:
            session = json.load(f)
        api.session.cookies.update(session.get("cookies", {}))
        api.token = session.get("token")
        api.user = session.get("user")
        if api.token:
            api.session.headers["Authorization"] = f"Bearer {api.token}"
        return api.is_logged_in()
    except Exception:
        return False


def cmd_login(api: TCGplayerAPI, args):
    """Login and save session."""
    config = load_config()
    email = config.get("email") or input("Email: ")
    password = config.get("password") or input("Password: ")
    print(f"[LOGIN] Logging in as {email}...")
    if api.login(email, password):
        print(f"[LOGIN] Success! User: {api.user}")
        save_session(api)
    else:
        print("[LOGIN] FAILED")


def cmd_search(api: TCGplayerAPI, args):
    """Search for Pokemon cards."""
    query = " ".join(args.search) if isinstance(args.search, list) else args.search
    print(f"[SEARCH] Looking for: {query}")
    results = api.search_pokemon(query, page_size=args.limit)
    if not results:
        print("[SEARCH] No results or error")
        return
    items = results.get("results", [])
    print(f"[SEARCH] Found {len(items)} results:")
    for i, item in enumerate(items[:args.limit]):
        pid = item.get("productId")
        name = item.get("productName", "?")
        rarity = item.get("rarityName", "?")
        set_name = item.get("setName", "?")
        lowest = api.get_lowest_price(pid) if args.prices else None
        price_str = f" | Lowest: ${lowest:.2f}" if lowest else ""
        print(f"  {i+1}. {name} ({set_name}) [{rarity}] id={pid}{price_str}")


def cmd_track(api: TCGplayerAPI, args):
    """Track high-value cards under max price."""
    print(f"[TRACK] Scanning for deals under ${args.max_price}...")
    deals = api.track_high_value(max_price=args.max_price)
    if not deals:
        print("[TRACK] No deals found")
        return
    print(f"[TRACK] Found {len(deals)} deals:")
    for d in deals:
        print(f"  - {d['name']} ({d['set']}) [{d['rarity']}] @ ${d['lowest_price']:.2f}")
        print(f"    {d['url']}")


def cmd_add(api: TCGplayerAPI, args):
    """Add a product to cart."""
    pid = args.product_id
    print(f"[CART] Getting details for product {pid}...")
    details = api.get_product_details(pid)
    if not details:
        print("[CART] Failed to get product details")
        return
    skus = details.get("skus", [])
    if not skus:
        print("[CART] No SKUs available")
        return
    # Pick the first SKU (Near Mint, English)
    sku = skus[0]
    sku_id = sku.get("skuId")
    print(f"[CART] Adding SKU {sku_id} to cart...")
    if api.add_to_cart(sku_id, quantity=1):
        print("[CART] Added!")
    else:
        print("[CART] Failed")


def cmd_checkout(api: TCGplayerAPI, args):
    """Begin checkout."""
    print("[CHECKOUT] Starting...")
    cart = api.get_cart()
    if not cart or not cart.get("items"):
        print("[CHECKOUT] Cart is empty")
        return
    print(f"[CHECKOUT] Cart has {len(cart.get('items', []))} items")
    result = api.begin_checkout()
    print(f"[CHECKOUT] Result: {result}")


def cmd_snipe(api: TCGplayerAPI, args):
    """Snipe a product when price drops below threshold."""
    pid = args.product_id
    max_price = args.max_price
    interval = args.interval
    print(f"[SNIPE] Watching product {pid}, max ${max_price}, every {interval}s")
    while True:
        try:
            lowest = api.get_lowest_price(pid)
            if lowest and lowest <= max_price:
                print(f"[SNIPE] DEAL! ${lowest:.2f} <= ${max_price}")
                # Get SKU and add to cart
                details = api.get_product_details(pid)
                skus = details.get("skus", [])
                if skus:
                    sku_id = skus[0].get("skuId")
                    api.add_to_cart(sku_id)
                    print("[SNIPE] Added to cart!")
                    return
            else:
                print(f"[SNIPE] Current: ${lowest:.2f} > ${max_price}")
        except KeyboardInterrupt:
            print("\n[SNIPE] Stopped")
            return
        except Exception as e:
            print(f"[SNIPE] Error: {e}")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="TCGplayer Pokemon Card Bot")
    parser.add_argument("--login", action="store_true", help="Login and save session")
    parser.add_argument("--search", nargs="+", help="Search for cards")
    parser.add_argument("--track", action="store_true", help="Track high-value deals")
    parser.add_argument("--add", type=int, dest="product_id", help="Add product to cart")
    parser.add_argument("--checkout", action="store_true", help="Begin checkout")
    parser.add_argument("--snipe", action="store_true", help="Snipe a product")
    parser.add_argument("--max-price", type=float, default=50.0, help="Max price")
    parser.add_argument("--limit", type=int, default=10, help="Search limit")
    parser.add_argument("--prices", action="store_true", help="Show prices in search")
    parser.add_argument("--interval", type=int, default=30, help="Snipe interval (seconds)")
    args = parser.parse_args()

    api = TCGplayerAPI()

    # Try to load existing session
    if not load_session(api):
        if not args.login:
            print("[AUTH] No session. Run with --login first.")
            return

    if args.login:
        cmd_login(api, args)
    elif args.search:
        cmd_search(api, args)
    elif args.track:
        cmd_track(api, args)
    elif args.product_id and not args.snipe:
        cmd_add(api, args)
    elif args.checkout:
        cmd_checkout(api, args)
    elif args.snipe:
        cmd_snipe(api, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
