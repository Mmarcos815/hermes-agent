"""
Card Hunt Dashboard — Pokemon card deal tracker, farm monitor, price history.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from hermes_cli.web_deps import LateState, late

_log = logging.getLogger("card_hunt.dashboard")
router = APIRouter()

# Late-bound helpers
_require_token = late("_require_token")
load_config = late("load_config", "hermes_cli.config")


# ─── Dashboard HTML ──────────────────────────────────────────────────────

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Card Hunt Dashboard</title>
    <style>
        :root {
            --bg: #0d1117;
            --panel: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --accent: #58a6ff;
            --green: #3fb950;
            --yellow: #d29922;
            --red: #f85149;
            --purple: #a371f7;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border);
        }
        .header h1 { color: var(--accent); font-size: 24px; }
        .header .status { display: flex; gap: 10px; }
        .status-pill {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-online { background: var(--green); color: #000; }
        .status-offline { background: var(--red); color: #fff; }
        .status-warning { background: var(--yellow); color: #000; }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
        }
        .panel h2 {
            font-size: 14px;
            color: var(--accent);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Deal Feed */
        .deal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
        }
        .deal-item:hover { background: rgba(88, 166, 255, 0.1); }
        .deal-item:last-child { border-bottom: none; }
        .deal-name { font-size: 13px; }
        .deal-price {
            font-weight: 700;
            color: var(--green);
        }
        .deal-discount {
            font-size: 11px;
            color: var(--yellow);
        }

        /* Farm Status */
        .farm-device {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid var(--border);
        }
        .farm-device:last-child { border-bottom: none; }
        .device-name { font-weight: 600; }
        .device-info { font-size: 12px; color: #8b949e; }
        .battery { display: flex; align-items: center; gap: 5px; }
        .battery-bar {
            width: 40px;
            height: 12px;
            border: 1px solid var(--border);
            border-radius: 2px;
            overflow: hidden;
        }
        .battery-fill {
            height: 100%;
            background: var(--green);
        }

        /* Price Tracker */
        .price-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 10px;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }
        .price-row:last-child { border-bottom: none; }
        .price-low { color: var(--green); font-weight: 600; }
        .price-market { color: #8b949e; text-decoration: line-through; }

        /* Tabs */
        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
        }
        .tab {
            padding: 8px 16px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }
        .tab.active {
            background: var(--accent);
            color: #000;
            border-color: var(--accent);
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Search */
        .search-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .search-bar input {
            flex: 1;
            padding: 10px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text);
            font-size: 14px;
        }
        .search-bar button {
            padding: 10px 20px;
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
        }
        .search-bar button:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Card Hunt Dashboard</h1>
        <div class="status">
            <span class="status-pill status-online">● API Online</span>
            <span id="farm-status" class="status-pill status-offline">● Farm Offline</span>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="showTab('deals')">Deals</div>
        <div class="tab" onclick="showTab('tracker')">Price Tracker</div>
        <div class="tab" onclick="showTab('farm')">Farm Status</div>
    </div>

    <!-- Deals Tab -->
    <div id="deals" class="tab-content active">
        <div class="panel">
            <h2>Active Deals</h2>
            <div id="deals-list">
                <div class="deal-item">
                    <span class="deal-name">Loading deals...</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Tracker Tab -->
    <div id="tracker" class="tab-content">
        <div class="search-bar">
            <input type="text" id="search-input" placeholder="Search Pokemon cards..." value="Charizard">
            <button onclick="searchCards()">Search</button>
        </div>
        <div class="panel">
            <h2>Price Tracker</h2>
            <div id="price-list">
                <div class="price-row">
                    <span>Search for cards to track prices</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Farm Tab -->
    <div id="farm" class="tab-content">
        <div class="grid">
            <div class="panel">
                <h2>Farm Devices</h2>
                <div id="farm-devices">
                    <div class="farm-device">
                        <div>
                            <div class="device-name">Phone-01</div>
                            <div class="device-info">TCGP + Outpost</div>
                        </div>
                        <div class="battery">
                            <span>--%</span>
                            <div class="battery-bar"><div class="battery-fill" style="width:0%"></div></div>
                        </div>
                    </div>
                    <div class="farm-device">
                        <div>
                            <div class="device-name">Phone-02</div>
                            <div class="device-info">MintPull + Rip Rush</div>
                        </div>
                        <div class="battery">
                            <span>--%</span>
                            <div class="battery-bar"><div class="battery-fill" style="width:0%"></div></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="panel">
                <h2>Capture Status</h2>
                <div id="capture-status">
                    <div class="farm-device">
                        <span>MITM Proxy</span>
                        <span class="status-pill status-offline">● Stopped</span>
                    </div>
                    <div class="farm-device">
                        <span>Captured Flows</span>
                        <span>273</span>
                    </div>
                    <div class="farm-device">
                        <span>Reward Payloads</span>
                        <span>1.18 MB</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }

        async function searchCards() {
            const query = document.getElementById('search-input').value;
            const res = await fetch(`/api/cards/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            const list = document.getElementById('price-list');
            list.innerHTML = '';
            
            if (!data.results || data.results.length === 0) {
                list.innerHTML = '<div class="price-row"><span>No results found</span></div>';
                return;
            }

            data.results.forEach(item => {
                const row = document.createElement('div');
                row.className = 'price-row';
                row.innerHTML = `
                    <span>${item.name}</span>
                    <span>
                        <span class="price-low">$${item.low}</span>
                        <span class="price-market">$${item.market}</span>
                    </span>
                `;
                list.appendChild(row);
            });
        }

        async function loadDeals() {
            const res = await fetch('/api/cards/deals');
            const data = await res.json();
            
            const list = document.getElementById('deals-list');
            list.innerHTML = '';

            if (!data.deals || data.deals.length === 0) {
                list.innerHTML = '<div class="deal-item"><span class="deal-name">No active deals found</span></div>';
                return;
            }

            data.deals.forEach(deal => {
                const item = document.createElement('div');
                item.className = 'deal-item';
                item.innerHTML = `
                    <div>
                        <div class="deal-name">${deal.name}</div>
                        <div class="deal-discount">${deal.discount}% below market</div>
                    </div>
                    <div class="deal-price">$${deal.price}</div>
                `;
                list.appendChild(item);
            });
        }

        // Auto-refresh
        loadDeals();
        setInterval(loadDeals, 30000);
    </script>
</body>
</html>
"""


# ─── API Routes ──────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML."""
    return DASHBOARD_HTML


@router.get("/api/cards/search")
async def search_cards(q: str = "Charizard", limit: int = 20):
    """Search TCGplayer for cards."""
    import requests as req
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": q,
        "filters": {"productLineName": ["pokemon"]},
        "from": 0, "size": limit,
        "sort": {"field": "price+shipping", "order": "asc"}
    }
    
    try:
        r = req.post(
            "https://mp-search-api.tcgplayer.com/v1/search/request",
            headers=headers, json=payload, timeout=15
        )
        data = r.json()
        results = data.get("results", [{}])[0].get("results", [])
        
        cards = []
        for item in results[:limit]:
            cards.append({
                "name": item.get("productName", ""),
                "low": item.get("lowestPrice", 0),
                "market": item.get("marketPrice", 0),
                "id": item.get("productId", ""),
                "url": f"https://www.tcgplayer.com/product/{item.get('productId', '')}"
            })
        
        return {"results": cards}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/api/cards/deals")
async def get_deals():
    """Get active deals from aggregator."""
    deals_file = Path(__file__).resolve().parent.parent.parent / "farm_3phones" / "active_deals.json"
    
    if not deals_file.exists():
        return {"deals": []}
    
    try:
        with open(deals_file) as f:
            deals = json.load(f)
        return {"deals": deals}
    except Exception as e:
        return {"deals": [], "error": str(e)}
