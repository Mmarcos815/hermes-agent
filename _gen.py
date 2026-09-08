
import textwrap

content = """#!/usr/bin/env python3
\"\"\"Red Team Infrastructure as Code.
Generates Terraform configs and Ansible playbooks for C2 infrastructure.
Supports Sliver and Havoc frameworks, DNS/redirector management, and
inventory tracking. All operations are local file generation only.
\"\"\"

from __future__ import annotations
import json, os, shutil, textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class C2Instance:
    name: str; provider: str; region: str; c2_type: str
    size: str = "t3.medium"; domain: str = ""; redirector: bool = False
    tags: dict[str, str] = field(default_factory=dict)

@dataclass
class Redirector:
    name: str; domain: str; backend: str
    provider: str = "aws"; region: str = "us-east-1"; variant: str = "nginx"

@dataclass
class DNSRecord:
    name: str; record_type: str; value: str; ttl: int = 300

@dataclass
class InventoryEntry:
    asset_id: str; asset_type: str; name: str; provider: str; region: str
    status: str = "provisioning"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    notes: str = ""
"""

with open("C:/Users/mobil/orca/projects/my 1st/red_team_infrastructure.py", "w") as f:
    f.write(content)

print("Base written")
