#!/usr/bin/env python3
"""
Card Hunt Dashboard — Pokemon card deal tracker.
Uses TCGplayer API + deal aggregator.
"""
import json
import logging
from datetime import datetime
from pathlib import Path

import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("dashboard")

app = FastAPI(title="Card Hunt Dashboard")

TCGPLAYER_SEARCH = "https://mp-search-api.tcgplayer.com/v1/search/request"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

WORKSPACE = Path(__file__).resolve().parent


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Card Hunt Dashboard</title>
    <style>
        body { font-family: system-ui; background: #0f0f0f; color: #e0e0e0; margin: 0; }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 20px; border-bottom: 2px solid #e94560; }
        .header h1 { color: #e94560; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        .search-box input { flex: 1; padding: 12px; background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 8px; }
        .search-box button { padding: 12px 24px; background: #e94560; color: #fff; border: none; border-radius: 8px; cursor: pointer; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #1a1a1a; padding: 16px; border-radius: 8px; border: 1px solid #333; }
        .stat-card h3 { color: #888; font-size: 12px; margin-bottom: 8px; }
        .stat-card .value { color: #e94560; font-size: 24px; font-weight: bold; }
        .results { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; }
        .card { background: #1a1a1a; border-radius: 8px; border: 1px solid #333; overflow: hidden; transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); border-color: #e94560; }
        .card-body { padding: 16px; }
        .card h3 { color: #fff; font-size: 14px; margin-bottom: 8px; }
        .card .set { color: #888; font-size: 12px; margin-bottom: 12px; }
        .card .price-row { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .card .price-label { color: #888; font-size: 12px; }
        .card .price-value { font-weight: bold; }
        .card .low { color: #4ade80; }
        .card .market { color: #fbbf24; }
        .card .discount { color: #e94560; }
        .card a { display: block; margin-top: 12px; padding: 8px; background: #333; color: #4ade80; text-align: center; border-radius: 4px; text-decoration: none; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Card Hunt Dashboard</h1>
        <p>Pokemon TCG Deal Tracker</p>
    </div>
    <div class="container">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search Pokemon cards..." value="Charizard">
            <button onclick="search()">Search</button>
        </div>
        <div class="stats" id="stats"></div>
        <div id="results" class="results">
            <div style="color:#888;padding:40px;">Loading deals...</div>
        </div>
    </div>
    <script>
        async function search() {
            const query = document.getElementById('searchInput').value;
            const results = document.getElementById('results');
            const stats = document.getElementById('stats');
            results.innerHTML = '<div style="color:#888;padding:40px;">Searching...</div>';
            
            try {
                const resp = await fetch('/api/search?q=' + encodeURIComponent(query));
                const data = await resp.json();
                
                if (data.error) {
                    results.innerHTML = '<div style="color:#ef4444;padding:20px;">' + data.error + '</div>';
                    return;
                }
                
                const items = data.results || [];
                const total = data.total || items.length;
                
                const lowPrices = items.map(i => i.lowestPrice || 0).filter(p => p > 0);
                const avgLow = lowPrices.length ? (lowPrices.reduce((a,b) => a+b, 0) / lowPrices.length).toFixed(2) : 0;
                const deals = items.filter(i => i.marketPrice > 0 && i.lowestPrice > 0 && i.lowestPrice < i.marketPrice * 0.5).length;
                
                stats.innerHTML = `
                    <div class="stat-card"><h3>Total Results</h3><div class="value">${total.toLocaleString()}</div></div>
                    <div class="stat-card"><h3>Shown</h3><div class="value">${items.length}</div></div>
                    <div class="stat-card"><h3>Avg Low Price</h3><div class="value">$${avgLow}</div></div>
                    <div class="stat-card"><h3>Deals Found</h3><div class="value">${deals}</div></div>
                `;
                
                if (items.length === 0) {
                    results.innerHTML = '<div style="color:#888;padding:40px;">No results found. Try again.</div>';
                    return;
                }
                
                results.innerHTML = items.slice(0, 20).map(item => `
                    <div class="card">
                        <div class="card-body">
                            <h3>${item.productName || 'Unknown'}</h3>
                            <div class="set">${item.setName || ''}</div>
                            <div class="price-row">
                                <span class="price-label">Low:</span>
                                <span class="price-value low">$${item.lowestPrice?.toFixed(2) || '?'}</span>
                            </div>
                            <div class="price-row">
                                <span class="price-label">Market:</span>
                                <span class="price-value market">$${item.marketPrice?.toFixed(2) || '?'}</span>
                            </div>
                            <div class="price-row">
                                <span class="price-label">Discount:</span>
                                <span class="price-value discount">${item.discount || '?'}%</span>
                            </div>
                            <a href="${item.url || '#'}" target="_blank">View on TCGplayer</a>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                results.innerHTML = '<div style="color:#ef4444;padding:20px;">Error: ' + e.message + '</div>';
            }
        }
        
        search();
    </script>
</body>
</html>
    """


@app.get("/api/search")
async def search_api(q: str = "Charizard"):
    """Search TCGplayer for cards."""
    try:
        payload = {
            "query": q,
            "filters": {"productLineName": ["pokemon"]},
            "from": 0, "size": 20,
            "sort": {"field": "bestdiscount", "order": "desc"}
        }
        r = requests.post(TCGPLAYER_SEARCH, headers=HEADERS, json=payload, timeout=15)
        
        if r.status_code != 200 or not r.text:
            return JSONResponse({"error": f"TCGplayer returned {r.status_code}", "results": []})
        
        data = r.json()
        inner = data.get("results", [{}])
        items = inner[0].get("results", []) if inner else []
        
        results = []
        for item in items:
            low = item.get("lowestPrice", 0)
            market = item.get("marketPrice", 0)
            pid = item.get("productId", "")
            discount = 0
            if market > 0 and low > 0:
                discount = round((1 - low/market) * 100, 1)
            
            results.append({
                "productName": item.get("productName", ""),
                "setName": item.get("setName", ""),
                "lowestPrice": low,
                "marketPrice": market,
                "discount": discount,
                "url": f"https://www.tcgplayer.com/product/{pid}" if pid else "",
                "rarity": item.get("rarityName", ""),
            })
        
        return JSONResponse({"results": results, "total": inner[0].get("totalResults", 0) if inner else 0})
    except Exception as e:
        return JSONResponse({"error": str(e), "results": []})


@app.get("/api/deals")
async def deals_api():
    """Return cached deals from deal aggregator."""
    deals_file = WORKSPACE / "active_deals.json"
    if deals_file.exists():
        with open(deals_file) as f:
            return JSONResponse(json.load(f))
    return JSONResponse([])


@app.get("/api/farm/status")
async def farm_status():
    """Return farm status (phones, battery, proxy)."""
    return JSONResponse({
        "phones": {
            "phone-01": {"role": "TCGP + Outpost", "battery": "unknown", "proxy": "192.168.1.168:8080"},
            "phone-02": {"role": "MintPull", "battery": "unknown", "proxy": "192.168.1.168:8082"},
            "phone-03": {"role": "MintPull + Boxed", "battery": "unknown", "proxy": "192.168.1.168:8081"},
        },
        "mitm": "running" if True else "stopped",
        "last_capture": "2026-09-19T18:14:32",
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
