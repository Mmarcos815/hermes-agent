# Automation — Cron Jobs for my 1st

Scheduled tasks for the project.

## Jobs

| File | Schedule | Purpose |
|------|----------|---------|
| `daily_sync.sh` | Daily 2:00 AM | Rsync project to OneDrive backup |
| `weekly_scan.sh` | Sunday 3:00 AM | Nmap vuln scan against lab target |
| `monthly_report.sh` | 1st, 4:00 AM | Aggregate scans into PDF report |

## Prerequisites

- `rsync` — file sync
- `nmap` — vulnerability scanning
- `pandoc` — PDF report generation

## Setup

```bash
# Make scripts executable
chmod +x ~/orca/projects/my\ 1st/automation/*.sh

# Install crontab
crontab ~/orca/projects/my\ 1st/automation/crontab.conf

# Verify
crontab -l
```

## Logs

All jobs log to `~/orca/logs/`:
- `daily_sync.log`
- `weekly_scan.log`
- `monthly_report.log`

## Reports

- Vuln scans: `~/orca/reports/vuln-scans/`
- Monthly PDFs: `~/orca/reports/monthly/`
