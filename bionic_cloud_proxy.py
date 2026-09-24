#!/usr/bin/env python3
"""
BIONIC PROXY CLOUD BUILDER v1.0
Deploys FREE proxy servers on cloud free tiers.
AWS Free Tier: 750 hrs EC2/mo for 12 months
Google Cloud Free: f1-micro always free
Oracle Cloud Always Free: 4 ARM cores, unlimited bandwidth
Azure Free: 750 hrs B1S
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL PURPOSES ONLY
"""
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# ── PROXY SERVER SETUP SCRIPT ────────────────────────────────────────────
PROXY_SETUP_SCRIPT = """#!/bin/bash
# Squid Proxy Server Setup
apt-get update -y
apt-get install -y squid apache2-utils

# Configure Squid
cat > /etc/squid/squid.conf << 'EOF'
http_port 3128
auth_param basic program /usr/lib/squid/basic_ncsa_auth /etc/squid/passwd
auth_param basic realm proxy
acl authenticated proxy_auth REQUIRED
http_access allow authenticated
http_access deny all
request_header_access Via deny all
request_header_access X-Forwarded-For deny all
request_header_access Referer deny all
forwarded_for off
visible_hostname localhost
EOF

# Create proxy user
PROXY_USER="bionic"
PROXY_PASS="$(openssl rand -base64 12)"
htpasswd -bc /etc/squid/passwd "$PROXY_USER" "$PROXY_PASS"

# Start Squid
systemctl restart squid
systemctl enable squid

# Print credentials
echo "PROXY_USER=$PROXY_USER"
echo "PROXY_PASS=$PROXY_PASS"
echo "PROXY_URL=http://$PROXY_USER:$PROXY_PASS@$(curl -s ifconfig.me):3128"
"""

# ── CLOUD FREE TIERS ────────────────────────────────────────────────────
CLOUD_TIERS = {
    "aws": {
        "name": "AWS Free Tier",
        "free_for": "12 months",
        "specs": "t2.micro (1 vCPU, 1GB RAM)",
        "hours": "750 hours/month",
        "region": "us-east-1",
        "docs": "https://aws.amazon.com/free/",
    },
    "gcloud": {
        "name": "Google Cloud Free",
        "free_for": "Always Free",
        "specs": "f1-micro (0.2 vCPU, 0.6GB RAM)",
        "hours": "Always free (US regions)",
        "region": "us-central1-a",
        "docs": "https://cloud.google.com/free/",
    },
    "oracle": {
        "name": "Oracle Cloud Always Free",
        "free_for": "Always Free",
        "specs": "4x ARM A1 cores, 24GB RAM",
        "hours": "Unlimited",
        "docs": "https://www.oracle.com/cloud/free/",
    },
    "azure": {
        "name": "Azure Free Tier",
        "free_for": "12 months",
        "specs": "B1S (1 vCPU, 1GB RAM)",
        "hours": "750 hours/month",
        "docs": "https://azure.microsoft.com/en-us/free/",
    },
}

# ── PROXY DEPLOYER ────────────────────────────────────────────────────────
class ProxyDeployer:
    """Deploy proxy servers on cloud free tiers."""
    
    def __init__(self):
        self.config_path = Path.home() / ".bionic_proxy" / "cloud_config.json"
        self.proxies = []
    
    def show_cloud_tiers(self):
        """Show available cloud free tiers."""
        print("=" * 60)
        print("CLOUD FREE TIERS — Deploy Proxy Servers")
        print("=" * 60)
        
        for name, tier in CLOUD_TIERS.items():
            print(f"\n[{name}]")
            print(f"  Free for: {tier['free_for']}")
            print(f"  Specs: {tier['specs']}")
            print(f"  Hours: {tier['hours']}")
            print(f"  Docs: {tier['docs']}")
    
    def get_ssh_key(self):
        """Generate SSH key for cloud access."""
        ssh_path = Path.home() / ".ssh" / "bionic_proxy"
        
        if ssh_path.exists():
            return ssh_path
        
        ssh_path.parent.mkdir(parents=True, exist_ok=True)
        
        subprocess.run([
            "ssh-keygen",
            "-t", "rsa",
            "-b", "2048",
            "-f", str(ssh_path),
            "-N", "",
        ], capture_output=True)
        
        return ssh_path
    
    def setup_aws_proxy(self):
        """Setup proxy on AWS Free Tier."""
        print("\n[AWS Free Tier Setup]")
        print("1. Sign up at https://aws.amazon.com/free/")
        print("2. Launch EC2 instance: t2.micro, Ubuntu 22.04")
        print("3. Connect via SSH:")
        print("   ssh -i ~/.ssh/bionic_proxy ubuntu@<public-ip>")
        print("4. Run setup script:")
        print(PROXY_SETUP_SCRIPT)
        
        # Generate setup file
        with open("setup_proxy.sh", "w") as f:
            f.write(PROXY_SETUP_SCRIPT)
        
        print("\nSetup script saved to setup_proxy.sh")
    
    def setup_oracle_proxy(self):
        """Setup proxy on Oracle Cloud Always Free."""
        print("\n[Oracle Cloud Always Free Setup]")
        print("1. Sign up at https://www.oracle.com/cloud/free/")
        print("2. Launch ARM instance: Always Free eligible")
        print("3. Connect via SSH:")
        print("   ssh -i ~/.ssh/bionic_proxy ubuntu@<public-ip>")
        print("4. Run setup script:")
        print(PROXY_SETUP_SCRIPT)
    
    def setup_gcloud_proxy(self):
        """Setup proxy on Google Cloud Free."""
        print("\n[Google Cloud Free Setup]")
        print("1. Sign up at https://cloud.google.com/free/")
        print("2. Launch f1-micro instance (US regions)")
        print("3. Connect via SSH:")
        print("   ssh -i ~/.ssh/bionic_proxy <username>@<public-ip>")
        print("4. Run setup script:")
        print(PROXY_SETUP_SCRIPT)
    
    def setup_all(self):
        """Show all cloud setup guides."""
        print("=" * 60)
        print("BIONIC CLOUD PROXY BUILDER")
        print("=" * 60)
        
        self.show_cloud_tiers()
        
        print("\n" + "=" * 60)
        print("SETUP GUIDES")
        print("=" * 60)
        
        self.setup_aws_proxy()
        self.setup_oracle_proxy()
        self.setup_gcloud_proxy()
        
        print("\n" + "=" * 60)
        print("INSTRUCTIONS")
        print("=" * 60)
        print("1. Sign up for cloud free tiers above")
        print("2. Run the setup script on each instance")
        print("3. Save proxy URLs to cloud_proxies.txt")
        print("4. Run: python bionic_cloud_proxy.py load")
        print("5. Run: python bionic_cloud_proxy.py start")

# ── PROXY MANAGER ────────────────────────────────────────────────────────
class CloudProxyManager:
    """Manages proxy servers deployed on cloud free tiers."""
    
    def __init__(self):
        self.config_path = Path.home() / ".bionic_proxy" / "cloud_proxies.json"
        self.proxies = []
    
    def add_proxy(self, url: str, location: str = "", provider: str = ""):
        """Add a proxy to the list."""
        self.proxies.append({
            "url": url,
            "location": location,
            "provider": provider,
            "added": datetime.now().isoformat(),
        })
        self.save()
    
    def load_from_file(self, filepath: str = "cloud_proxies.txt"):
        """Load proxies from a text file (one per line)."""
        if Path(filepath).exists():
            with open(filepath) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.add_proxy(line)
            print(f"Loaded {len(self.proxies)} proxies")
    
    def save(self):
        """Save proxies to config."""
        with open(self.config_path, "w") as f:
            json.dump(self.proxies, f, indent=2)
    
    def get(self):
        """Get a random proxy."""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def validate(self, proxy_url: str) -> bool:
        """Test if proxy is working."""
        try:
            resp = requests.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=10,
            )
            return resp.status_code == 200
        except:
            return False
    
    def validate_all(self):
        """Test all proxies."""
        working = []
        dead = []
        
        for proxy in self.proxies:
            if self.validate(proxy["url"]):
                working.append(proxy)
                print(f"  ✅ {proxy['provider']}: {proxy['url'][:50]}...")
            else:
                dead.append(proxy)
                print(f"  ❌ {proxy['provider']}: {proxy['url'][:50]}...")
        
        print(f"\n{len(working)} working, {len(dead)} dead")
        return working, dead

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bionic_cloud_proxy.py deploy|add|list|validate|get")
        print("  deploy - Show cloud deployment guides")
        print("  add - Add a proxy manually")
        print("  list - List all proxies")
        print("  validate - Test all proxies")
        print("  get - Get a random proxy")
        sys.exit(1)
    
    cmd = sys.argv[1]
    manager = CloudProxyManager()
    
    if cmd == "deploy":
        deployer = ProxyDeployer()
        deployer.setup_all()
    
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: python bionic_cloud_proxy.py add PROXY_URL")
            sys.exit(1)
        proxy = sys.argv[2]
        manager.add_proxy(proxy)
        print(f"Added: {proxy}")
    
    elif cmd == "list":
        if manager.config_path.exists():
            with open(manager.config_path) as f:
                proxies = json.load(f)
            print(f"{len(proxies)} proxies:")
            for p in proxies:
                print(f"  {p.get('provider', '?')}: {p['url'][:60]}...")
        else:
            print("No proxies saved.")
    
    elif cmd == "validate":
        if manager.config_path.exists():
            with open(manager.config_path) as f:
                manager.proxies = json.load(f)
            manager.validate_all()
        else:
            print("No proxies saved.")
    
    elif cmd == "get":
        if manager.config_path.exists():
            with open(manager.config_path) as f:
                manager.proxies = json.load(f)
            proxy = manager.get()
            if proxy:
                print(proxy["url"])
            else:
                print("No proxies available.")
        else:
            print("No proxies saved.")
