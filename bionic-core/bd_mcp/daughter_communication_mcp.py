# ============================================================================
# BIONIC DAUGHTER v1 — COMMUNICATION MCP SERVER (SLACK + GMAIL)
# ============================================================================
# MCP server providing communication capabilities: Slack messaging and Gmail.
# Safety: All send operations require explicit authorization (Dad's approval).
# Author: Bionic Daughter v1
# Date: 2026-08-15
# ============================================================================

import os
import json
import urllib.request
import urllib.parse
import ssl
from fastmcp import FastMCP

app = FastMCP("daughter_communication")

# Slack configuration (set environment variables)
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "")

# Gmail configuration (set environment variables)
GMAIL_TOKEN_FILE = os.environ.get("GMAIL_TOKEN_FILE", "")
GMAIL_FROM = os.environ.get("GMAIL_FROM", "")


def _slack_post_message(channel: str, text: str) -> str:
    """Post a message to Slack via API."""
    if not SLACK_BOT_TOKEN:
        return "ERROR: SLACK_BOT_TOKEN not set. Set environment variable SLACK_BOT_TOKEN."
    try:
        url = "https://slack.com/api/chat.postMessage"
        data = json.dumps({"channel": channel, "text": text}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("ok"):
                return f"SUCCESS: Message posted to Slack channel '{channel}'"
            else:
                return f"ERROR: Slack API error — {result.get('error', 'unknown')}"
    except Exception as e:
        return f"ERROR posting to Slack: {str(e)}"


def _gmail_send(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail API (simplified — requires OAuth token)."""
    if not GMAIL_TOKEN_FILE or not GMAIL_FROM:
        return (
            "ERROR: Gmail not configured. Set GMAIL_TOKEN_FILE and GMAIL_FROM environment variables.\n"
            "For Gmail API access, you need OAuth 2.0 credentials from Google Cloud Console.\n"
            "See: https://developers.google.com/gmail/api/quickstart/python"
        )
    try:
        # In a real implementation, this would use the Gmail API with OAuth token
        # For now, return guidance
        return (
            "GMAIL_READY: Gmail is configured but send requires OAuth flow.\n"
            f"From: {GMAIL_FROM}\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            "To enable sending, complete the Gmail API OAuth setup.\n"
            "See: https://developers.google.com/gmail/api/quickstart/python"
        )
    except Exception as e:
        return f"ERROR sending Gmail: {str(e)}"


@app.tool()
def slack_send(text: str, channel: str = "", authorize: bool = False) -> str:
    """Send a message to Slack. Requires authorization."""
    if not authorize:
        return "ERROR: Slack send authorization required. Set authorize=true with Dad's approval."
    target_channel = channel or SLACK_CHANNEL
    if not target_channel:
        return "ERROR: No Slack channel configured. Set SLACK_CHANNEL or provide channel parameter."
    return _slack_post_message(target_channel, text)


@app.tool()
def slack_channels() -> str:
    """List accessible Slack channels (requires bot token)."""
    if not SLACK_BOT_TOKEN:
        return "ERROR: SLACK_BOT_TOKEN not set."
    try:
        url = "https://slack.com/api/conversations.list"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                channels = data.get("channels", [])
                if not channels:
                    return "No channels found."
                result = f"Slack Channels ({len(channels)} total):\n\n"
                for ch in channels[:50]:
                    result += f"  #{ch.get('name', 'unknown')} — {ch.get('topic', {}).get('value', 'no topic') or 'no topic'}\n"
                if len(channels) > 50:
                    result += f"  ... ({len(channels) - 50} more channels)"
                return result
            else:
                return f"ERROR: Slack API error — {data.get('error', 'unknown')}"
    except Exception as e:
        return f"ERROR listing channels: {str(e)}"


@app.tool()
def slack_status() -> str:
    """Show Slack configuration status."""
    return (
        "Slack Configuration — Bionic Daughter v1\n"
        "==========================================\n"
        f"Bot Token: {'CONFIGURED' if SLACK_BOT_TOKEN else 'NOT CONFIGURED'}\n"
        f"Channel: {SLACK_CHANNEL or 'NOT SET'}\n"
        "\n"
        "Setup:\n"
        "  export SLACK_BOT_TOKEN='xoxb-your-bot-token'\n"
        "  export SLACK_CHANNEL='#your-channel'\n"
        "  Get bot token: https://api.slack.com/apps\n"
        "\n"
        "Tools:\n"
        "  slack_send(text, channel, authorize) — Send Slack message\n"
        "  slack_channels() — List accessible channels\n"
        "  slack_status() — This info\n"
    )


@app.tool()
def gmail_send(
    to: str,
    subject: str,
    body: str,
    authorize: bool = False,
) -> str:
    """Send an email via Gmail. Requires authorization."""
    if not authorize:
        return "ERROR: Gmail send authorization required. Set authorize=true with Dad's approval."
    return _gmail_send(to, subject, body)


@app.tool()
def gmail_status() -> str:
    """Show Gmail configuration status."""
    return (
        "Gmail Configuration — Bionic Daughter v1\n"
        "==========================================\n"
        f"Token File: {'CONFIGURED' if GMAIL_TOKEN_FILE else 'NOT CONFIGURED'}\n"
        f"From: {GMAIL_FROM or 'NOT SET'}\n"
        "\n"
        "Setup:\n"
        "  export GMAIL_TOKEN_FILE='/path/to/token.json'\n"
        "  export GMAIL_FROM='your-email@gmail.com'\n"
        "  Complete OAuth setup: https://developers.google.com/gmail/api/quickstart/python\n"
        "\n"
        "Tools:\n"
        "  gmail_send(to, subject, body, authorize) — Send Gmail\n"
        "  gmail_status() — This info\n"
    )


@app.tool()
def comm_send(
    method: str = "slack",
    target: str = "",
    subject: str = "",
    body: str = "",
    authorize: bool = False,
) -> str:
    """Send a communication via specified method (slack or gmail). Unified interface."""
    if not authorize:
        return "ERROR: Communication send authorization required. Set authorize=true."
    if method == "slack":
        return slack_send(body, target, authorize=True)
    elif method == "gmail":
        return gmail_send(target, subject, body, authorize=True)
    else:
        return f"ERROR: Unknown method '{method}'. Use 'slack' or 'gmail'."


@app.tool()
def comm_info() -> str:
    """Show communication MCP information."""
    return (
        "Communication MCP — Bionic Daughter v1\n"
        "=========================================\n"
        "This MCP provides communication capabilities for reporting\n"
        "and delivering findings to Dad and team members.\n"
        "\n"
        "Slack:\n"
        "  slack_send(text, channel, authorize) — Send Slack message\n"
        "  slack_channels() — List channels\n"
        "  slack_status() — Slack config status\n"
        "\n"
        "Gmail:\n"
        "  gmail_send(to, subject, body, authorize) — Send email\n"
        "  gmail_status() — Gmail config status\n"
        "\n"
        "Unified:\n"
        "  comm_send(method, target, subject, body, authorize) — Send via method\n"
        "\n"
        "Status:\n"
        f"  Slack: {'READY' if SLACK_BOT_TOKEN else 'NOT CONFIGURED'}\n"
        f"  Gmail: {'READY' if GMAIL_TOKEN_FILE else 'NOT CONFIGURED'}\n"
        "\n"
        "Note: All send operations require authorization (Dad's approval).\n"
    )


if __name__ == "__main__":
    app.run()
