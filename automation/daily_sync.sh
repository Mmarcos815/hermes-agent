#!/usr/bin/env bash
# Daily canonical sync to OneDrive
set -euo pipefail

SOURCE_DIR="$HOME/orca/projects/my 1st"
ONEDRIVE_DIR="$HOME/OneDrive/orca-backups/my-1st"
LOG_FILE="$HOME/orca/logs/daily_sync.log"

mkdir -p "$(dirname "$LOG_FILE")" "$ONEDRUDE_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting daily sync..." >> "$LOG_FILE"

rsync -av --delete \
  --exclude='.git/' \
  --exclude='node_modules/' \
  --exclude='__pycache__/' \
  "$SOURCE_DIR/" "$ONEDRIVE_DIR/" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync complete." >> "$LOG_FILE"
