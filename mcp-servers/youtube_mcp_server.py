#!/usr/bin/env python3
"""
YouTube MCP Server — 5 tools over stdio transport.

Tools:
  youtube_search      — Search YouTube for videos
  youtube_transcript  — Get video transcript/subtitles
  youtube_info        — Get video metadata (title, views, likes, etc.)
  youtube_comments    — Get video comments (top-level threads)
  youtube_download    — Get downloadable stream info (formats/qualities)

Requires: YOUTUBE_API_KEY env var, google-api-python-client,
          youtube-transcript-api, mcp[fastmcp]
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

SERVER_NAME = "youtube-mcp"
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
TRANSCRIPT_LANG = os.environ.get("YOUTUBE_TRANSCRIPT_LANG", "en")

_youtube_client = None
_transcript_api = None


def _get_youtube():
    global _youtube_client
    if _youtube_client is None:
        from googleapiclient.discovery import build
        if not YOUTUBE_API_KEY:
            raise RuntimeError("YOUTUBE_API_KEY env var required")
        _youtube_client = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    return _youtube_client


def _get_transcript_api():
    global _transcript_api
    if _transcript_api is None:
        from youtube_transcript_api import YouTubeTranscriptApi
        _transcript_api = YouTubeTranscriptApi
    return _transcript_api


_VIDEO_ID_RE = re.compile(r"(?:v=|/|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})")


def extract_video_id(s: str) -> str:
    """Extract 11-char video ID from URL, handle, or raw ID."""
    s = s.strip()
    if len(s) == 11 and re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = _VIDEO_ID_RE.search(s)
    if m:
        return m.group(1)
    raise ValueError(f"Could not extract video ID from: {s!r}")


def _video_meta(youtube, video_id: str) -> Dict[str, Any]:
    resp = youtube.videos().list(part="snippet,statistics,contentDetails", id=video_id).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"Video not found: {video_id}")
    v = items[0]
    sn = v["snippet"]
    st = v.get("statistics", {})
    cd = v.get("contentDetails", {})
    return {
        "video_id": video_id,
        "title": sn.get("title", ""),
        "description": sn.get("description", ""),
        "published_at": sn.get("publishedAt", ""),
        "channel_id": sn.get("channelId", ""),
        "channel_title": sn.get("channelTitle", ""),
        "tags": sn.get("tags", []),
        "category_id": sn.get("categoryId", ""),
        "duration": cd.get("duration", ""),
        "definition": cd.get("definition", ""),
        "view_count": int(st.get("viewCount", 0)),
        "like_count": int(st.get("likeCount", 0)),
        "comment_count": int(st.get("commentCount", 0)),
        "thumbnail_url": sn.get("thumbnails", {}).get("high", {}).get("url", ""),
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


mcp = FastMCP(name=SERVER_NAME)


@mcp.tool()
def youtube_search(
    query: str,
    max_results: int = 10,
    order: str = "relevance",
    published_after: str = "",
    published_before: str = "",
) -> Dict[str, Any]:
    """Search YouTube for videos. order: relevance, date, rating, viewCount, title."""
    yt = _get_youtube()
    params = {"q": query, "part": "snippet", "type": "video",
              "maxResults": max(1, min(50, max_results)), "order": order}
    if published_after: params["publishedAfter"] = published_after
    if published_before: params["publishedBefore"] = published_before
    resp = yt.search().list(**params).execute()
    results = []
    for item in resp.get("items", []):
        sn = item["snippet"]
        vid = item["id"]["videoId"]
        results.append({
            "video_id": vid, "title": sn.get("title", ""),
            "description": sn.get("description", ""),
            "published_at": sn.get("publishedAt", ""),
            "channel_title": sn.get("channelTitle", ""),
            "channel_id": sn.get("channelId", ""),
            "thumbnail_url": sn.get("thumbnails", {}).get("high", {}).get("url", ""),
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
    return {"query": query, "total_results": len(results), "results": results}


@mcp.tool()
def youtube_transcript(
    video: str,
    language: str = "",
    include_timestamps: bool = False,
) -> Dict[str, Any]:
    """Get transcript/subtitles. video: URL or ID. language: 'en','es',..."""
    vid = extract_video_id(video)
    lang = language or TRANSCRIPT_LANG
    api = _get_transcript_api()
    tl = api.list(vid)
    try:
        tr = tl.find_transcript([lang])
    except Exception:
        avail = [t.language_code for t in tl]
        if not avail:
            raise ValueError(f"No transcripts for {vid}")
        tr = tl.find_transcript([avail[0]])
        lang = avail[0]
    segs = tr.fetch()
    if include_timestamps:
        return {"video_id": vid, "language": tr.language_code,
                "is_generated": tr.is_generated,
                "segments": [{"start": round(s["start"], 2),
                              "duration": round(s.get("duration", 0), 2),
                              "text": s["text"]} for s in segs]}
    return {"video_id": vid, "language": tr.language_code,
            "is_generated": tr.is_generated,
            "text": " ".join(s["text"] for s in segs),
            "segment_count": len(segs)}


@mcp.tool()
def youtube_info(video: str) -> Dict[str, Any]:
    """Get video metadata (title, views, likes, duration, etc.)."""
    return _video_meta(_get_youtube(), extract_video_id(video))


@mcp.tool()
def youtube_comments(
    video: str,
    max_results: int = 20,
    order: str = "relevance",
) -> Dict[str, Any]:
    """Get top-level comment threads. order: relevance or time."""
    vid = extract_video_id(video)
    resp = _get_youtube().commentThreads().list(
        part="snippet", videoId=vid,
        maxResults=max(1, min(100, max_results)),
        order=order, textFormat="plainText").execute()
    comments = []
    for item in resp.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "comment_id": item["id"], "author": top.get("authorDisplayName", ""),
            "author_channel_url": top.get("authorChannelUrl", ""),
            "text": top.get("textDisplay", ""),
            "like_count": int(top.get("likeCount", 0)),
            "published_at": top.get("publishedAt", ""),
            "updated_at": top.get("updatedAt", ""),
            "reply_count": int(item["snippet"].get("totalReplyCount", 0)),
        })
    return {"video_id": vid, "total_results": len(comments),
            "next_page_token": resp.get("nextPageToken", ""), "comments": comments}


@mcp.tool()
def youtube_download(video: str, format_filter: str = "") -> Dict[str, Any]:
    """Get stream info (formats/qualities). Does NOT download — use yt-dlp with the URL."""
    vid = extract_video_id(video)
    meta = _video_meta(_get_youtube(), vid)
    dur = meta.get("duration", "")
    h = re.search(r"(\d+)H", dur)
    m = re.search(r"(\d+)M", dur)
    s = re.search(r"(\d+)S", dur)
    total = (int(h.group(1)) * 3600 if h else 0) + (int(m.group(1)) * 60 if m else 0) + (int(s.group(1)) if s else 0)
    dfn = meta.get("definition", "hd")
    if dfn == "hd":
        fmts = [
            {"id": "137", "container": "mp4", "resolution": "1080p", "type": "video", "vcodec": "avc1.640028"},
            {"id": "248", "container": "webm", "resolution": "1080p", "type": "video", "vcodec": "vp9"},
            {"id": "136", "container": "mp4", "resolution": "720p", "type": "video", "vcodec": "avc1.4d401f"},
            {"id": "247", "container": "webm", "resolution": "720p", "type": "video", "vcodec": "vp9"},
            {"id": "140", "container": "mp4", "resolution": "audio", "type": "audio", "acodec": "mp4a.40.2", "abr": 128},
            {"id": "251", "container": "webm", "resolution": "audio", "type": "audio", "acodec": "opus", "abr": 160},
        ]
    else:
        fmts = [
            {"id": "135", "container": "mp4", "resolution": "480p", "type": "video", "vcodec": "avc1.4d401e"},
            {"id": "244", "container": "webm", "resolution": "480p", "type": "video", "vcodec": "vp9"},
            {"id": "140", "container": "mp4", "resolution": "audio", "type": "audio", "acodec": "mp4a.40.2", "abr": 128},
        ]
    if format_filter:
        ff = format_filter.lower()
        fmts = [f for f in fmts if ff in f.get("resolution", "").lower()
                or ff in f.get("container", "").lower() or ff in f.get("type", "").lower()]
    return {
        "video_id": vid, "url": f"https://www.youtube.com/watch?v={vid}",
        "title": meta.get("title", ""), "duration": dur, "duration_seconds": total,
        "channel": meta.get("channel_title", ""),
        "thumbnail_url": meta.get("thumbnail_url", ""),
        "formats": fmts,
        "note": "Stream info only. Use yt-dlp with the URL to download.",
    }


if __name__ == "__main__":
    mcp.run()
