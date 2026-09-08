#!/usr/bin/env bash
# Weekly vulnerability scan against vuln lab
set -euo pipefail

SCAN_TARGET="10.0.0.100"
REPORT_DIR="$HOME/orca/reports/vuln-scans"
LOG_FILE="$HOME/orca/logs/weekly_scan.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

mkdir -p "$REPORT_DIR" "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting weekly vuln scan..." >> "$LOG_FILE"

nmap -sV --script vuln \
  -oN "$REPORT_DIR/scan_$TIMESTAMP.txt" \
  -oX "$REPORT_DIR/scan_$TIMESTAMP.xml" \
  "$SCAN_TARGET" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scan complete. Report: scan_$TIMESTAMP" >> "$LOG_FILE"
