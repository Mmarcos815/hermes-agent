#!/usr/bin/env bash
# Monthly PDF report generation
set -euo pipefail

REPORT_DIR="$HOME/orca/reports/monthly"
LOG_FILE="$HOME/orca/logs/monthly_report.log"
MONTH=$(date '+%Y-%m')
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

mkdir -p "$REPORT_DIR" "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Generating monthly report for $MONTH..." >> "$LOG_FILE"

# Aggregate scan results and generate markdown summary
{
  echo "# Monthly Security Report — $MONTH"
  echo ""
  echo "## Vulnerability Scans"
  for f in "$HOME"/orca/reports/vuln-scans/scan_*.txt; do
    [ -f "$f" ] && echo "### $(basename "$f")" && cat "$f" && echo ""
  done
} > "/tmp/report_$TIMESTAMP.md"

pandoc "/tmp/report_$TIMESTAMP.md" -o "$REPORT_DIR/report_$MONTH.pdf" >> "$LOG_FILE" 2>&1
rm -f "/tmp/report_$TIMESTAMP.md"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Report: $REPORT_DIR/report_$MONTH.pdf" >> "$LOG_FILE"
