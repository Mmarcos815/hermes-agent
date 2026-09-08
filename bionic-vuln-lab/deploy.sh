#!/usr/bin/env bash
# deploy.sh — Deploy Bionic Vuln Lab to a cloud VPS (DigitalOcean / Linode / any Docker host)
set -euo pipefail

IMAGE="${IMAGE:-bionic-vuln-lab}"
TAG="${TAG:-latest}"
HOST="${1:?Usage: ./deploy.sh <user@host> [port]}"
SSH_PORT="${2:-22}"

echo "[*] Building image locally..."
docker build -t "${IMAGE}:${TAG}" .

echo "[*] Saving and transferring image..."
docker save "${IMAGE}:${TAG}" | ssh -p "${SSH_PORT}" "${HOST}" "docker load"

echo "[*] Deploying on remote host..."
ssh -p "${SSH_PORT}" "${HOST}" bash <<'REMOTE'
    IMAGE="${1:?}"
    TAG="${2:?}"
    docker stop bionic-vuln-lab 2>/dev/null || true
    docker rm bionic-vuln-lab 2>/dev/null || true
    docker run -d \
        --name bionic-vuln-lab \
        --restart unless-stopped \
        -p 5017:5017 \
        -e NODE_ENV=production \
        "${IMAGE}:${TAG}"
    docker ps --filter name=bionic-vuln-lab
REMOTE
