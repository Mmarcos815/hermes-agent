#!/bin/bash
# P1: Deploy vuln Lab to Production
# Supports: Local Docker, AWS EC2, DigitalOcean, Linode, Vultr

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  BIONIC VULN LAB — Production Deployment                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
DOMAIN=${1:-"vuln-lab.local"}
EMAIL=${2:-"admin@bionic.lab"}
PROVIDER=${3:-"local"}  # local, aws, digitalocean, linode, vultr

echo -e "${YELLOW}[1/5] Configuration${NC}"
echo "  Domain: $DOMAIN"
echo "  Email: $EMAIL"
echo "  Provider: $PROVIDER"
echo ""

# Pre-flight checks
echo -e "${YELLOW}[2/5] Pre-flight checks${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker not found${NC}"
    echo "Install: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}[ERROR] Docker Compose not found${NC}"
    exit 1
fi

echo "  ✅ Docker: $(docker --version)"
echo "  ✅ Compose: $(docker compose version 2>/dev/null || docker-compose --version)"
echo ""

# Build
echo -e "${YELLOW}[3/5] Building image${NC}"
docker compose build --no-cache
echo "  ✅ Build complete"
echo ""

# Deploy
echo -e "${YELLOW}[4/5] Deploying${NC}"

case $PROVIDER in
    local)
        docker compose up -d
        echo "  ✅ Local deployment complete"
        ;;
    aws)
        echo "  Deploying to AWS EC2..."
        echo "  ⚠️  Requires: aws-cli configured, EC2 instance running"
        echo "  Run: ssh ec2-user@$DOMAIN 'docker compose up -d'"
        ;;
    digitalocean)
        echo "  Deploying to DigitalOcean..."
        echo "  ⚠️  Requires: doctl configured, Droplet running"
        echo "  Run: ssh root@$DOMAIN 'docker compose up -d'"
        ;;
    *)
        echo "  ⚠️  Generic deployment — copy files and run:"
        echo "  scp -r . user@$DOMAIN:~/vuln-lab"
        echo "  ssh user@$DOMAIN 'cd ~/vuln-lab && docker compose up -d'"
        ;;
esac

echo ""

# Verify
echo -e "${YELLOW}[5/5] Verification${NC}"
sleep 3

if curl -s http://localhost:5017/api/health > /dev/null 2>&1; then
    echo "  ✅ Health check: PASS"
else
    echo -e "${RED}  ❌ Health check: FAIL${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  DEPLOYMENT COMPLETE                                        ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  App:      http://localhost:5017                            ║${NC}"
echo -e "${GREEN}║  Health:   http://localhost:5017/api/health                 ║${NC}"
echo -e "${GREEN}║  Endpoints: /api/bola, /api/sqli, /api/jwt, /api/ssrf     ║${NC}"
echo -e "${GREEN}║            /api/upload, /api/nosql, /api/xxe, /api/admin   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
