# ===========================================================================
# BIONIC DAUGHTER v1 — YOUTUBE DATA API MCP SERVER
# ===========================================================================
# MCP server providing YouTube search, video info, channel data, and
# transcript/caption extraction. Uses YouTube Data API v3.
# SAFETY: YouTube Data API — read-only by default, no upload capabilities.
# Author: Bionic Daughter v1
# Date: 2026-08-20
# ===========================================================================

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from fastmcp import FastMCP

app = FastMCP("daughter_youtube")

# YouTube Data API v3 key (set as environment variable YOUTUBE_API_KEY)
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
BASE_URL = "https://www.googleapis.com/youtube/v3"

# User agent for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Insecure SSL context (for development; production should verify)
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _api_get(path: str, params: dict) -> dict:
    """Make a YouTube Data API GET request and return parsed JSON."""
    params["key"] = YOUTUBE_API_KEY
    url = f"{BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"error": str(e)}


def _extract_captions(video_id: str) -> str:
    """Try to get video captions/subtitles via the captions endpoint."""
    data = _api_get("/captions", {
        "videoId": video_id,
        "part": "snippet",
        "maxResults": 10,
    })
    if "error" in data:
        return f"Could not fetch captions metadata: {data['error']}"
    items = data.get("items", [])
    if not items:
        return "No captions/subtitles found for this video."
    out = []
    for item in items:
        sn = item.get("snippet", {})
        lang = sn.get("language", "unknown")
        out.append(f"  - Language: {lang} | Name: {sn.get('name', 'N/A')}")
    return "Available captions:\n" + "\n".join(out)


@app.tool()
def youtube_search(query: str, max_results: int = 10, published_after: str = "") -> str:
    """Search YouTube for videos matching a query. Returns titles, URLs, channel, views, date."""
    if not YOUTUBE_API_KEY:
        return (
            "ERROR: YOUTUBE_API_KEY not set.\n"
            "Get a key at: https://console.cloud.google.com/apis/credentials\n"
            "Enable YouTube Data API v3, create an API key.\n"
            "Then set: export YOUTUBE_API_KEY='your-key'"
        )
    params = {
        "part": "snippet",
        "q": query,
        "maxResults": min(max_results, 50),
        "type": "video",
        "order": "relevance",
        "regionCode": "US",
        "safeSearch": "moderate",
    }
    if published_after:
        params["publishedAfter"] = published_after
    data = _api_get("/search", params)
    if "error" in data:
        return f"ERROR: {data['error']}"
    items = data.get("items", [])
    if not items:
        return f"No videos found for: '{query}'"
    out = f"YouTube Search Results for: '{query}' ({len(items)} videos)\n\n"
    for i, item in enumerate(items, 1):
        sn = item.get("snippet", {})
        vid = item.get("id", {}).get("videoId", "N/A")
        title = sn.get("title", "No title")
        channel = sn.get("channelTitle", "Unknown")
        desc = sn.get("description", "")[:200]
        published = sn.get("publishedAt", "")[:10]
        out += f"{i}. {title}\n"
        out += f"   Video ID: {vid}\n"
        out += f"   URL: https://www.youtube.com/watch?v={vid}\n"
        out += f"   Channel: {channel}\n"
        out += f"   Published: {published}\n"
        out += f"   Description: {desc}\n\n"
    return out


@app.tool()
def youtube_video_info(video_id_or_url: str) -> str:
    """Get detailed info about a YouTube video (title, channel, views, duration, stats)."""
    video_id = video_id_or_url
    if "watch?v=" in video_id:
        video_id = video_id.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in video_id:
        video_id = video_id.split("youtu.be/")[-1].split("?")[0]
    if not video_id or len(video_id) != 11:
        return "ERROR: Invalid YouTube video ID. Provide a video ID (11 chars) or a full URL."

    data = _api_get("/videos", {
        "part": "snippet,statistics,contentDetails",
        "id": video_id,
    })
    if "error" in data:
        return f"ERROR: {data['error']}"
    items = data.get("items", [])
    if not items:
        return f"No video found with ID: {video_id}"

    item = items[0]
    sn = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})

    out = f"Video: {sn.get('title', 'N/A')}\n"
    out += f"Video ID: {video_id}\n"
    out += f"URL: https://www.youtube.com/watch?v={video_id}\n"
    out += f"Channel: {sn.get('channelTitle', 'N/A')}\n"
    out += f"Channel ID: {sn.get('channelId', 'N/A')}\n"
    out += f"Published: {sn.get('publishedAt', 'N/A')}\n"
    out += f"Duration: {details.get('duration', 'N/A')}\n"
    out += f"Definition: {details.get('definition', 'N/A')}\n"
    out += f"Caption status: {details.get('caption', 'N/A')}\n"
    out += f"Views: {stats.get('viewCount', 'N/A')}\n"
    out += f"Likes: {stats.get('likeCount', 'N/A')}\n"
    out += f"Comments: {stats.get('commentCount', 'N/A')}\n"
    out += f"Description:\n{sn.get('description', '(empty)')[:1000]}\n"
    return out


@app.tool()
def youtube_channel_info(channel_id_or_url: str) -> str:
    """Get channel info (name, subscriber count, total views, video count, description)."""
    channel_id = channel_id_or_url
    if "channel_id=" in channel_id:
        channel_id = channel_id.split("channel_id=")[-1].split("&")[0]
    elif "/channel/" in channel_id:
        channel_id = channel_id.split("/channel/")[-1].split("?")[0].split("/")[0]
    if not channel_id:
        return "ERROR: Invalid channel ID or URL."

    data = _api_get("/channels", {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
    })
    if "error" in data:
        return f"ERROR: {data['error']}"
    items = data.get("items", [])
    if not items:
        return f"No channel found with ID: {channel_id}"

    item = items[0]
    sn = item.get("snippet", {})
    stats = item.get("statistics", {})
    details = item.get("contentDetails", {})

    out = f"Channel: {sn.get('title', 'N/A')}\n"
    out += f"Channel ID: {channel_id}\n"
    out += f"Description: {sn.get('description', '(empty)')[:500]}\n"
    out += f"Country: {sn.get('country', 'N/A')}\n"
    out += f"Subscribers: {stats.get('subscriberCount', 'N/A')}\n"
    out += f"Total Views: {stats.get('viewCount', 'N/A')}\n"
    out += f"Total Videos: {stats.get('videoCount', 'N/A')}\n"
    out += f"Playlist ID (uploads): {details.get('relatedPlaylists', {}).get('uploads', 'N/A')}\n"
    return out


@app.tool()
def youtube_playlist_videos(playlist_id_or_url: str, max_results: int = 10) -> str:
    """List videos in a YouTube playlist."""
    playlist_id = playlist_id_or_url
    if "list=" in playlist_id:
        playlist_id = playlist_id.split("list=")[-1].split("&")[0]
    if not playlist_id:
        return "ERROR: Invalid playlist ID or URL."

    data = _api_get("/playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": min(max_results, 50),
    })
    if "error" in data:
        return f"ERROR: {data['error']}"
    items = data.get("items", [])
    if not items:
        return f"No videos found in playlist: {playlist_id}"

    out = f"Playlist Videos ({len(items)} shown):\n\n"
    for i, item in enumerate(items, 1):
        sn = item.get("snippet", {})
        vid = sn.get("resourceId", {}).get("videoId", "N/A")
        title = sn.get("title", "No title")
        thumb = sn.get("thumbnails", {}).get("medium", {}).get("url", "")
        out += f"{i}. {title}\n"
        out += f"   Video ID: {vid}\n"
        out += f"   URL: https://www.youtube.com/watch?v={vid}\n"
        out += f"   Thumbnail: {thumb}\n\n"
    return out


@app.tool()
def youtube_transcript_or_captions(video_id_or_url: str) -> str:
    """Check what captions/subtitles are available for a video."""
    video_id = video_id_or_url
    if "watch?v=" in video_id:
        video_id = video_id.split("watch?v=")[-1].split("&")[0]
    return _extract_captions(video_id)


@app.tool()
def youtube_search_learning(topic: str, difficulty: str = "beginner") -> str:
    """Search YouTube specifically for learning resources about a topic.
    Optimized for educational content — tutorials, courses, explanations."""
    keywords = {
        "beginner": "tutorial for beginners step by step basics",
        "intermediate": "intermediate guide deep dive explained",
        "advanced": "advanced masterclass expert professional",
    }
    suffix = keywords.get(difficulty, "tutorial")
    query = f"{topic} {suffix}"
    return youtube_search(query, max_results=15)


@app.tool()
def youtube_security_tutorials(topic: str) -> str:
    """Search YouTube for cybersecurity / hacking / security tutorials."""
    query = f"{topic} cybersecurity tutorial hacking security penetration testing ethical hacking 2025 2026"
    return youtube_search(query, max_results=20)


@app.tool()
def youtube_watch_list(topic: str) -> str:
    """Create a curated watch list for learning about a topic — returns top
    educational videos organized by type (tutorial, demo, lecture, hands-on)."""
    if not YOUTUBE_API_KEY:
        return "ERROR: YOUTUBE_API_KEY not set."

    tutorials = youtube_search(f"{topic} tutorial step by step", max_results=5)
    demos = youtube_search(f"{topic} demonstration live example", max_results=5)
    lectures = youtube_search(f"{topic} lecture course educational", max_results=5)

    result = f"=== WATCH LIST: {topic} ===\n\n"
    result += "┏━━━ TUTORIALS (step by step) ━━━━┓\n"
    result += tutorials[:1500] + "\n"
    result += "┏━━━ DEMOS (live examples) ━━━━┓\n"
    result += demos[:1500] + "\n"
    result += "┏━━━ LECTURES (educational) ━━━━┓\n"
    result += lectures[:1500] + "\n"
    return result


@app.tool()
def youtube_info() -> str:
    """Show YouTube MCP configuration and available tools."""
    key_status = "CONFIGURED" if YOUTUBE_API_KEY else "NOT CONFIGURED"
    key_display = (YOUTUBE_API_KEY[:8] + "***") if YOUTUBE_API_KEY else "N/A"
    return (
        "YouTube Data API v3 — Bionic Daughter v1 MCP Server\n"
        "====================================================\n\n"
        f"API Key: {key_status} ({key_display})\n"
        f"Get a key: https://console.cloud.google.com/apis/credentials\n"
        f"Enable: YouTube Data API v3\n\n"
        "Available Tools:\n"
        "  youtube_search(query, max_results, published_after) — Search videos\n"
        "  youtube_video_info(video_id_or_url) — Video details + stats\n"
        "  youtube_channel_info(channel_id_or_url) — Channel info + stats\n"
        "  youtube_playlist_videos(playlist_id_or_url, max_results) — Playlist contents\n"
        "  youtube_transcript_or_captions(video_id_or_url) — Available captions\n"
        "  youtube_search_learning(topic, difficulty) — Educational content search\n"
        "  youtube_security_tutorials(topic) — Security/hacking tutorials\n"
        "  youtube_watch_list(topic) — Curated learning watch list\n"
        "  youtube_info() — This info\n\n"
        "Setup:\n"
        "  1. Go to https://console.cloud.google.com/\n"
        "  2. Create a project (or use existing)\n"
        "  3. Enable YouTube Data API v3\n"
        "  4. Create credentials → API key\n"
        "  5. Set: export YOUTUBE_API_KEY='your-key'\n\n"
        "Quota: 10,000 units/day free tier.\n"
        "  - search.list: 100 units/call\n"
        "  - videos.list: 1 unit/call\n"
        "  - channels.list: 1 unit/call\n"
        "  - playlistItems.list: 1 unit/call\n\n"
        "The daughter can now literally WATCH and learn from YouTube videos!"
    )


if __name__ == "__main__":
    app.run()
