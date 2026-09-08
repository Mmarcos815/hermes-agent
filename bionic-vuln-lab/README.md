# Bionic Vuln Lab — Docker Deployment

Deliberately vulnerable Node.js/Express app for **authorized security training only**.

## Quick Start

```bash
# Build and run
docker compose up -d

# With nginx reverse proxy (optional)
docker compose --profile proxy up -d

# View logs
docker compose logs -f vuln-lab
```

The app is available at `http://localhost:5017`.

Health check: `curl http://localhost:5017/api/health`

## Endpoints

| Route | Vulnerability |
|-------|--------------|
| `/api/bola` | Broken Object Level Authorization |
| `/api/sqli` | SQL Injection |
| `/api/jwt` | JWT attacks |
| `/api/ssrf` | Server-Side Request Forgery |
| `/api/upload` | Unrestricted File Upload |
| `/api/nosql` | NoSQL Injection |
| `/api/xxe` | XML External Entity |
| `/api/race` | Race Conditions |
| `/api/admin` | Broken Access Control |
| `/api/ws` | WebSocket (XSS via broadcast) |

## Cloud Deployment (VPS)

Prerequisites: a running VPS with Docker installed.

```bash
./deploy.sh root@your-server-ip
```

Or manually:

```bash
docker build -t bionic-vuln-lab .
docker run -d --name bionic-vuln-lab --restart unless-stopped -p 5017:5017 bionic-vuln-lab
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Runtime environment |

## Architecture

```
┌─────────┐     ┌──────────┐     ┌─────────────┐
│  User   │────▶│  Nginx   │────▶│  Vuln Lab   │
│         │     │ (opt.)   │     │  :5017      │
└─────────┘     └──────────┘     └─────────────┘
```

No persistent state — the mock DB lives in memory and resets on container restart.

## ⚠️ Warning

This application is **intentionally vulnerable**. Never expose it to the public internet or deploy it alongside production services. Use only in isolated lab environments.
