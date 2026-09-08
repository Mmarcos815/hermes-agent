#!/usr/bin/env python3
"""
c2_deploy.py — C2 framework deployment artifacts (SIMULATION / EDUCATIONAL).

Generates Docker Compose + config files for Sliver and Mythic C2 labs.
Does NOT deploy anything to real infrastructure.

Usage:
    python c2_deploy.py -f sliver -o ./c2_lab/
    python c2_deploy.py -f mythic -o ./c2_lab/

Safety: All artifacts target Docker/localhost only. No external connections.
"""

import argparse, json, sys
from pathlib import Path
import yaml

SLIVER_COMPOSE = {
    "version": "3.8",
    "services": {
        "sliver-server": {
            "image": "ghcr.io/bishopfox/sliver:latest",
            "container_name": "sliver-c2-sim",
            "ports": ["31337:31337/tcp"],
            "volumes": ["./sliver_data:/root/.sliver"],
            "restart": "no",
        },
    },
}

MYTHIC_COMPOSE = {
    "version": "3.8",
    "services": {
        "mythic-server": {
            "image": "its-a-feature/mythic:latest",
            "container_name": "mythic-c2-sim",
            "ports": ["17443:17443/tcp"],
            "volumes": ["./mythic_data:/mythic"],
            "restart": "no",
        },
        "mythic-rabbitmq": {
            "image": "rabbitmq:3-management-alpine",
            "container_name": "mythic-mq-sim",
        },
        "mythic-postgres": {
            "image": "postgres:14-alpine",
            "container_name": "mythic-db-sim",
        },
    },
}


def gen_sliver(out):
    d = out / "sliver"
    d.mkdir(parents=True, exist_ok=True)
    (d / "docker-compose.yaml").write_text(yaml.dump(SLIVER_COMPOSE, default_flow_style=False))
    (d / "config.json").write_text(json.dumps({"name": "sliver_lab", "mtls_port": 31337}, indent=2))
    (d / "README.md").write_text("# Sliver Lab\n```bash\ndocker compose up -d\ndocker exec -it sliver-c2-sim sliver\n```\n")
    return d


def gen_mythic(out):
    d = out / "mythic"
    d.mkdir(parents=True, exist_ok=True)
    (d / "docker-compose.yaml").write_text(yaml.dump(MYTHIC_COMPOSE, default_flow_style=False))
    (d / "config.json").write_text(json.dumps({"name": "mythic_lab", "port": 17443}, indent=2))
    (d / "README.md").write_text("# Mythic Lab\n```bash\ndocker compose up -d\n# UI: https://localhost:17443\n```\n")
    return d


def main(argv=None):
    p = argparse.ArgumentParser(description="C2 lab artifact generator")
    p.add_argument("-f", "--framework", required=True, choices=["sliver", "mythic"])
    p.add_argument("-o", "--output", default="./c2_lab")
    a = p.parse_args(argv)

    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)

    if a.framework == "sliver":
        d = gen_sliver(out)
    else:
        d = gen_mythic(out)

    print(f"[+] {a.framework.upper()} artifacts: {d}")
    print(f"    Next: cd {a.framework}/ && docker compose up -d")
    return 0


if __name__ == "__main__":
    sys.exit(main())
