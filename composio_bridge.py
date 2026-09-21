#!/usr/bin/env python3
"""
Composio Bridge Module
Wraps Composio search, scrape, and code tools as MCP tools.
Replaces web_search, web_extract, and execute_code when credits available.
"""
import json
from composio import Composio

c = Composio(api_key='ak_DpeVbvplJ8zYj-VVcNYR')

def composio_search(query: str, provider: str = "duckduckgo") -> str:
    """
    Search the web via Composio. Providers: duckduckgo, google, bing, tavily, exa.
    """
    provider_map = {
        "duckduckgo": "COMPOSIO_SEARCH_DUCK_DUCK_GO",
        "google": "COMPOSIO_SEARCH_GOOGLE",
        "bing": "COMPOSIO_SEARCH_BING",
        "tavily": "TAVILY_SEARCH",
        "exa": "EXA_ANSWER",
    }
    slug = provider_map.get(provider, "COMPOSIO_SEARCH_DUCK_DUCK_GO")
    try:
        result = c.tools.execute(
            slug=slug,
            arguments={"query": query, "max_results": 5}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def composio_scrape(url: str, provider: str = "fetch") -> str:
    """
    Scrape a URL via Composio. Providers: fetch, firecrawl.
    """
    try:
        if provider == "firecrawl":
            result = c.tools.execute(
                slug="FIRECRAWL_BATCH_SCRAPE",
                arguments={"urls": [url]}
            )
        else:
            result = c.tools.execute(
                slug="COMPOSIO_SEARCH_FETCH_URL_CONTENT",
                arguments={"url": url}
            )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

def composio_execute(code: str, language: str = "python") -> str:
    """
    Execute code via Composio code interpreter.
    """
    try:
        result = c.tools.execute(
            slug="CODEINTERPRETER_EXECUTE_CODE",
            arguments={"code": code, "language": language}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
