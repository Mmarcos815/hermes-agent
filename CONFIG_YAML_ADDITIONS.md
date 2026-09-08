# =============================================================================
# BIONIC DAUGHTER — CONFIG.YAML ADDITIONS (Round 5 manual merge)
# Date: 2026-09-02
# Apply these snippets to: C:\Users\mobil\AppData\Local\hermes\config.yaml
# Agent can't auto-merge (safety gate); drop in manually using any text editor.
# =============================================================================

# -----------------------------------------------------------------------------
# INSERT 1 — under `mcp_servers:` after the `hexstrike:` block (lines ~46-51)
# -----------------------------------------------------------------------------

  # === JETBRAINS IDE MCP PROXY (wired 2026-09-02) ===
  jetbrains_mcp:
    command: npx
    args:
      - -y
      - '@jetbrains/mcp-proxy'
    env:
      JETBRAINS_IDE_PORT: "63342"
    timeout: 60
    connect_timeout: 10

# -----------------------------------------------------------------------------
# INSERT 2 — at the end of the file (informational, no code change)
# -----------------------------------------------------------------------------

# HackerOne MCP — already wired (lines 137-142). Token now in
# C:\Users\mobil\AppData\Local\hermes\.env after Round 5 fix.
# Detector: python C:/Users/mobil/orca/projects/my 1st/h1_token_status.py
#
# 6 missing security headers finding on Ollama (Round 3):
# If you ever expose Ollama beyond localhost, add a reverse proxy with:
#   Strict-Transport-Security: max-age=31536000
#   Content-Security-Policy: default-src 'self'
#   X-Frame-Options: DENY
#   X-Content-Type-Options: nosniff
#   Referrer-Policy: no-referrer
#   Permissions-Policy: (restrict per your needs)
#
# Tesseract OCR install (Round 5):
# If you approved the silent install, verify:
#   ls C:\Tesseract-OCR\tesseract.exe
# Add C:\Tesseract-OCR to PATH (system env var), then:
#   python -c "import pytesseract; print(pytesseract.image_to_string('test.png'))"

# =============================================================================
# VERIFICATION — run these after merging
# =============================================================================

# 1. Confirm JetBrains proxy entry present:
#    grep -A8 "jetbrains_mcp:" C:/Users/mobil/AppData/Local/hermes/config.yaml
#
# 2. Confirm HackerOne token:
#    python C:/Users/mobil/orca/projects/my 1st/h1_token_status.py
#    Expected: "STATUS: OK — HackerOne MCP will work when Hermes boots"
#
# 3. Restart Hermes (or run a new session). The 3 newly-bootable MCPs
#    (hexstrike, hexstrike_live, bionic_unified) + jetbrains_mcp will
#    start. HackerOne will work because the token is now in scope.
#
# 4. Verify MCP server count:
#    grep "^  [a-z_]" C:/Users/mobil/AppData/Local/hermes/config.yaml | wc -l
#    Expected: 34 (33 existing + 1 jetbrains_mcp)
# =============================================================================