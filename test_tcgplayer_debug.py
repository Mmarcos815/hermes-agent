import sys, requests
sys.path.insert(0, r'C:\Users\mobil\orca\projects\my 1st\farm_3phones\tcgplayer_bot')

BASE_URL = "https://mpapi.tcgplayer.com"
SEARCH_URL = "https://mp-search-api.tcgplayer.com"
GATEWAY_URL = "https://mpgateway.tcgplayer.com"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.tcgplayer.com",
    "Referer": "https://www.tcgplayer.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

session = requests.Session()
session.headers.update(DEFAULT_HEADERS)
mpfev = "5555"

print('=== TCGplayer API Debug ===')

# Test 1: Search endpoint
print('\n[1] Search: POST /v1/search/request')
payload = {
    "query": "Charizard VMAX",
    "filters": {"term": {"productLineName": ["pokemon"], "sellerStatus": "Live"}, "range": {"quantity": {"gte": 1}}},
    "sort": {"field": "relevance", "order": "desc"},
    "from": 0, "size": 3,
    "aggregations": ["product-name", "rarity", "set-name", "product-type"],
}
r = session.post(f"{SEARCH_URL}/v1/search/request?mpfev={mpfev}", json=payload, timeout=15)
print(f'  Status: {r.status_code}')
print(f'  Body (first 500 chars): {r.text[:500]}')

# Test 2: Product details endpoint
print('\n[2] Details: GET /v2/product/408577/details')
r2 = session.get(f"{SEARCH_URL}/v2/product/408577/details?mpfev={mpfev}", timeout=15)
print(f'  Status: {r2.status_code}')
print(f'  Body (first 500 chars): {r2.text[:500]}')

# Test 3: Product listings endpoint
print('\n[3] Listings: POST /v1/product/408577/listings')
lpayload = {
    "filters": {"term": {"sellerStatus": "Live", "channelId": 0, "language": ["English"], "condition": ["Near Mint"]}, "range": {"quantity": {"gte": 1}}, "exclude": {"channelExclusion": 0}},
    "from": 0, "size": 10,
    "sort": {"field": "price+shipping", "order": "asc"},
    "context": {"shippingCountry": "US", "cart": {"packages": {}}},
}
r3 = session.post(f"{SEARCH_URL}/v1/product/408577/listings?mpfev={mpfev}", json=lpayload, timeout=15)
print(f'  Status: {r3.status_code}')
print(f'  Body (first 500 chars): {r3.text[:500]}')

# Test 4: Pricepoints endpoint
print('\n[4] Pricepoints: GET /v1/pricepoints/buylist/marketprice/products/408577')
r4 = session.get(f"{GATEWAY_URL}/v1/pricepoints/buylist/marketprice/products/408577?mpfev={mpfev}", timeout=15)
print(f'  Status: {r4.status_code}')
print(f'  Body (first 500 chars): {r4.text[:500]}')

# Test 5: Direct search on TCGplayer (new API version?)
print('\n[5] Search v2: POST /v2/search/request')
payload2 = {"query": "Charizard VMAX", "from": 0, "size": 3}
r5 = session.post(f"{SEARCH_URL}/v2/search/request?mpfev={mpfev}", json=payload2, timeout=15)
print(f'  Status: {r5.status_code}')
print(f'  Body (first 500 chars): {r5.text[:500]}')

print('\n=== Debug Complete ===')
