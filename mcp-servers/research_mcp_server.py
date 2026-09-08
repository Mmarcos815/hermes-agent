#!/usr/bin/env python3
"""
Research MCP Server — Academic research & threat intelligence via MCP.
Connects to real public APIs (arXiv, NVD, AlienVault OTX, HackerNews, GitHub Advisories).
No API keys required.

Tools: paper_search, vulnerability_search, threat_intel, news_analysis, trend_analysis
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "research-mcp"
USER_AGENT = "ResearchMCP/1.0 (security-research)"
TIMEOUT = 30

ARXIV_API = "http://export.arxiv.org/api/query"
NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OTX_API = "https://otx.alienvault.com/api/v1"
HN_API = "https://hacker-news.firebaseio.com/v0"
GH_ADVISORY = "https://api.github.com/advisories"


def _http_get(url: str, params: dict | None = None, accept: str = "application/json") -> dict[str, Any]:
    """GET URL with params, return parsed JSON."""
    if params:
        qs = urllib.parse.urlencode(params, safe=":+")
        url = f"{url}?{qs}" if "?" not in url else f"{url}&{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if "json" in resp.headers.get("Content-Type", "") or accept == "application/json":
                return json.loads(raw) if raw.strip() else {}
            return {"_raw": raw[:8000]}
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:1000]
        except Exception:
            pass
        return {"_error": f"HTTP {e.code}", "_url": url, "_detail": body}
    except urllib.error.URLError as e:
        return {"_error": str(e.reason), "_url": url}
    except Exception as e:
        return {"_error": str(e), "_url": url}


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


mcp = FastMCP(SERVER_NAME)


@mcp.tool()
def paper_search(query: str, max_results: int = 10, category: str = "cs.CR") -> dict[str, Any]:
    """Search academic papers via arXiv API.

    Args:
        query: Search terms (e.g., "zero-day detection", "LLM security")
        max_results: Number of papers to return (1-50)
        category: arXiv category — default cs.CR (cryptography & security).
                  Other: cs.AI, cs.LG, cs.CV, stat.ML, physics.soc-ph

    Returns papers with title, authors, abstract, PDF link, and date.
    """
    max_results = max(1, min(50, max_results))
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND ({search_query})"

    result = _http_get(ARXIV_API, {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }, accept="application/atom+xml")

    if "_error" in result:
        return {"tool": "paper_search", "error": result, "timestamp": _ts()}

    raw = result.get("_raw", "")
    papers = []
    for entry in re.findall(r"<entry>(.*?)</entry>", raw, re.DOTALL):
        def _tag(tag: str) -> str:
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", entry, re.DOTALL)
            return m.group(1).strip() if m else ""

        title = _tag("title").replace("\n", " ").strip()
        summary = _tag("summary").replace("\n", " ").strip()
        published = _tag("published")[:10]
        authors = re.findall(r"<name>(.*?)</name>", entry)
        id_match = re.search(r"arxiv\.org/abs/([\d.]+)", entry)
        arxiv_id = id_match.group(1) if id_match else ""

        papers.append({
            "title": title,
            "authors": authors[:10],
            "abstract": summary[:500],
            "published": published,
            "arxiv_id": arxiv_id,
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else "",
            "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "",
        })

    return {
        "tool": "paper_search",
        "query": query,
        "category": category,
        "total_returned": len(papers),
        "timestamp": _ts(),
        "papers": papers,
    }


@mcp.tool()
def vulnerability_search(query: str, max_results: int = 10, severity: str = "CRITICAL", days_back: int = 30) -> dict[str, Any]:
    """Search NVD (National Vulnerability Database) for CVEs.

    Args:
        query: CVE search term (e.g., "Apache", "Log4j", "Windows RDP")
        max_results: Number of CVEs to return (1-50)
        severity: Filter by severity — CRITICAL, HIGH, MEDIUM, LOW, or ALL
        days_back: How many days back to search (max 120)

    Returns CVE entries with CVSS scores, descriptions, references, and dates.
    """
    max_results = max(1, min(50, max_results))
    params: dict[str, Any] = {"keywordSearch": query, "resultsPerPage": max_results}
    if severity.upper() != "ALL":
        params["cvssV3Severity"] = severity.upper()

    result = _http_get(NVD_API, params)
    if "_error" in result:
        return {"tool": "vulnerability_search", "error": result, "timestamp": _ts()}

    vulnerabilities = []
    for item in result.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id", "")
        descs = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descs if d.get("lang") == "en"),
            descs[0]["value"] if descs else "",
        )[:500]

        metrics = cve.get("metrics", {})
        cvss_data = {}
        if "cvssMetricV31" in metrics:
            cvss_data = metrics["cvssMetricV31"][0].get("cvssData", {})
        elif "cvssMetricV30" in metrics:
            cvss_data = metrics["cvssMetricV30"][0].get("cvssData", {})

        references = [ref.get("url", "") for ref in cve.get("references", [])[:5]]
        published = cve.get("published", "")[:10]
        weaknesses = [
            desc.get("value", "")
            for w in cve.get("weaknesses", [])
            for desc in w.get("description", [])
            if desc.get("lang") == "en"
        ][:3]

        vulnerabilities.append({
            "cve_id": cve_id,
            "description": description,
            "severity": cvss_data.get("baseSeverity", "UNKNOWN"),
            "cvss_score": cvss_data.get("baseScore"),
            "attack_vector": cvss_data.get("attackVector", ""),
            "published": published,
            "references": references,
            "cwe_ids": weaknesses,
        })

    return {
        "tool": "vulnerability_search",
        "query": query,
        "severity_filter": severity,
        "days_back": days_back,
        "total_returned": len(vulnerabilities),
        "total_available": result.get("totalResults", 0),
        "timestamp": _ts(),
        "vulnerabilities": vulnerabilities,
    }


@mcp.tool()
def threat_intel(indicator: str, indicator_type: str = "general") -> dict[str, Any]:
    """Query AlienVault OTX for threat intelligence on an indicator.

    Args:
        indicator: The IOC — domain, IP, URL, hash, or CVE
        indicator_type: Type — general, domain, ipv4, ipv6, url, hostname, file_hash, cve

    Returns threat context, pulses, detections, and related malware.
    """
    indicator = indicator.strip()
    type_map = {
        "general": "/indicators/general/{ind}",
        "domain": "/indicators/domain/{ind}",
        "ipv4": "/indicators/IPv4/{ind}",
        "ipv6": "/indicators/IPv6/{ind}",
        "url": "/indicators/url/{ind}",
        "hostname": "/indicators/hostname/{ind}",
        "file_hash": "/indicators/file/{ind}",
        "cve": "/indicators/cve/{ind}",
    }
    path = type_map.get(indicator_type, type_map["general"]).format(
        ind=urllib.parse.quote(indicator, safe="")
    )
    result = _http_get(f"{OTX_API}{path}")

    if "_error" in result:
        return {"tool": "threat_intel", "error": result, "timestamp": _ts()}

    pulses = result.get("pulse_info", {}).get("pulses", [])
    pulse_summary = [{
        "name": p.get("name", ""),
        "author": p.get("author", {}).get("username", ""),
        "tags": p.get("tags", []),
        "created": p.get("created", "")[:10],
        "references": p.get("references", [])[:3],
    } for p in pulses[:10]]

    return {
        "tool": "threat_intel",
        "indicator": indicator,
        "indicator_type": indicator_type,
        "sections_available": result.get("sections", []),
        "reputation": result.get("reputation", {}),
        "country": result.get("geo", {}).get("country_name", ""),
        "asn": result.get("geo", {}).get("asn", ""),
        "malware_samples": len(result.get("malware", {}).get("data", [])) if isinstance(result.get("malware"), dict) else 0,
        "related_pulses": len(pulses),
        "pulses": pulse_summary,
        "whois": result.get("whois", ""),
        "timestamp": _ts(),
    }


@mcp.tool()
def news_analysis(query: str = "security", max_stories: int = 10, min_score: int = 20) -> dict[str, Any]:
    """Analyze security-related stories from HackerNews.

    Args:
        query: Search topic (e.g., "security", "vulnerability", "ransomware")
        max_stories: Number of stories to return (1-50)
        min_score: Minimum score filter

    Returns top HN stories with scores, comments, and discussion links.
    """
    max_stories = max(1, min(50, max_stories))
    top_ids_raw = _http_get(f"{HN_API}/topstories.json")

    if not isinstance(top_ids_raw, list):
        return {"tool": "news_analysis", "error": top_ids_raw, "timestamp": _ts()}

    stories = []
    query_lower = query.lower()

    for story_id in top_ids_raw[:100]:
        if len(stories) >= max_stories:
            break
        item = _http_get(f"{HN_API}/item/{story_id}.json")
        if "_error" in item:
            continue

        title = item.get("title", "")
        score = item.get("score", 0)
        if score < min_score or query_lower not in title.lower():
            continue

        stories.append({
            "title": title,
            "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score": score,
            "comments": item.get("descendants", 0),
            "author": item.get("by", ""),
            "time": datetime.fromtimestamp(item["time"], tz=timezone.utc).isoformat() if item.get("time") else "",
            "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
        })

    stories.sort(key=lambda s: s["score"], reverse=True)
    total_comments = sum(s["comments"] for s in stories)
    avg_score = sum(s["score"] for s in stories) / len(stories) if stories else 0

    return {
        "tool": "news_analysis",
        "query": query,
        "stories_found": len(stories),
        "total_comments": total_comments,
        "average_score": round(avg_score, 1),
        "timestamp": _ts(),
        "stories": stories[:max_stories],
    }


@mcp.tool()
def trend_analysis(ecosystem: str = "pip", severity: str = "critical", max_results: int = 10) -> dict[str, Any]:
    """Analyze trending security vulnerabilities from GitHub Advisory DB.

    Args:
        ecosystem: Package ecosystem — pip, npm, maven, rubygems, nuget, go, cargo, composer
        severity: Filter severity — critical, high, moderate, low, or all
        max_results: Number of advisories to return (1-50)

    Returns trending advisories with GHSA IDs, CVSS scores, affected versions, and fix recommendations.
    """
    max_results = max(1, min(50, max_results))
    ecosystem_map = {
        "pip": "pip", "pypi": "pip", "npm": "npm", "maven": "maven",
        "gradle": "maven", "rubygems": "rubygems", "gem": "rubygems",
        "nuget": "nuget", ".net": "nuget", "go": "go", "golang": "go",
        "cargo": "cargo", "rust": "cargo", "composer": "composer", "php": "composer",
    }
    gh_eco = ecosystem_map.get(ecosystem.lower().strip(), ecosystem.lower().strip())

    params: dict[str, Any] = {
        "ecosystem": gh_eco, "per_page": max_results,
        "sort": "updated", "direction": "desc",
    }
    if severity.lower() != "all":
        params["severity"] = severity.lower()

    url = f"{GH_ADVISORY}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/vnd.github+json",
    })

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            advisories = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        return {"tool": "trend_analysis", "error": f"HTTP {e.code}", "timestamp": _ts()}
    except Exception as e:
        return {"tool": "trend_analysis", "error": str(e), "timestamp": _ts()}

    if not isinstance(advisories, list):
        return {"tool": "trend_analysis", "error": "Unexpected response", "timestamp": _ts()}

    trends = []
    for adv in advisories[:max_results]:
        vulns = adv.get("vulnerabilities", [])
        affected, fixed_versions = [], []
        for v in vulns[:3]:
            pkg = v.get("package", {})
            affected.append({
                "package": pkg.get("name", ""),
                "ecosystem": pkg.get("ecosystem", ""),
                "range": v.get("vulnerable_version_range", ""),
            })
            if v.get("patched_versions"):
                fixed_versions.append(v["patched_versions"])

        cvss = adv.get("cvss") or {}
        trends.append({
            "ghsa_id": adv.get("ghsa_id", ""),
            "cve_id": adv.get("cve_id", ""),
            "summary": adv.get("summary", ""),
            "description": (adv.get("description", "") or "")[:500],
            "severity": adv.get("severity", "unknown"),
            "cvss_score": cvss.get("score") if isinstance(cvss, dict) else None,
            "cvss_vector": cvss.get("vector_string", "") if isinstance(cvss, dict) else "",
            "published": adv.get("published_at", "")[:10],
            "updated": adv.get("updated_at", "")[:10],
            "affected_packages": affected,
            "fixed_in": fixed_versions[:3],
            "references": [r if isinstance(r, str) else r.get("url", "") for r in adv.get("references", [])[:3]],
            "url": f"https://github.com/advisories/{adv.get('ghsa_id', '')}",
        })

    severity_counts = {}
    for t in trends:
        severity_counts[t["severity"]] = severity_counts.get(t["severity"], 0) + 1

    return {
        "tool": "trend_analysis",
        "ecosystem": gh_eco,
        "severity_filter": severity,
        "total_returned": len(trends),
        "severity_breakdown": severity_counts,
        "timestamp": _ts(),
        "trends": trends,
    }


if __name__ == "__main__":
    mcp.run()
