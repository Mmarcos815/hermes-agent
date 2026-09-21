import sys
sys.path.insert(0, r'C:\Users\mobil\orca\projects\my 1st\farm_3phones\tcgplayer_bot')
from tcgplayer_api import TCGplayerAPI

api = TCGplayerAPI()
print('=== TCGplayer Live Test ===')

# Test 1: Search
print('\n[1] Search: Charizard VMAX')
results = api.search_pokemon('Charizard VMAX', page_size=3)
if results:
    hits = results.get('hits', {})
    total = hits.get('total', 0)
    items = hits.get('hits', [])
    print(f'  Total results: {total}')
    for i, item in enumerate(items[:3]):
        src = item.get('_source', item)
        print(f'  [{i+1}] {src.get("productName", "?")} — ${src.get("lowestPrice", "?")} — ID:{src.get("productId", "?")}')
else:
    print('  Search returned empty (API may be rate-limited)')

# Test 2: Price history
print('\n[2] Price check: Charizard VMAX (ID 408577)')
price = api.get_lowest_price(408577)
print(f'  Lowest price: ${price}' if price else '  No price data')

# Test 3: Market price
print('\n[3] Market price: Charizard VMAX')
mp = api.get_market_price(408577)
print(f'  Market price: ${mp}' if mp else '  No market data')

print('\n=== Test Complete ===')
