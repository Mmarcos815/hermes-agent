#!/usr/bin/env python3
"""Supply Chain Attack Framework — Educational / Lab Only.

Detects and simulates supply chain attack vectors for red-team labs.
Usage examples:
    python supply_chain.py --mode dependency-confusion --package lodash
    python supply_chain.py --mode typosquat --package requests --registry pypi
    python supply_chain.py --mode cicd --manifest .github/workflows/ci.yml
    python supply_chain.py --mode container --image alpine:latest
    python supply_chain.py --mode integrity --package tensorflow --local-path tf.tar.gz
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Finding:
    severity: str
    title: str
    description: str
    recommendation: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanReport:
    mode: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)


# ── 1. Dependency Confusion Scanner ──────────────────────────────────────
class DependencyConfusionScanner:
    """Detects packages vulnerable to dependency confusion.

    Attackers register internal package names on public registries with higher
    versions; package managers may resolve to the malicious version.
    """

    def __init__(self, registry_url: str, package_name: str) -> None:
        self.registry_url = registry_url.rstrip("/")
        self.package_name = package_name

    def scan(self) -> ScanReport:
        rpt = ScanReport("dependency-confusion")
        internal = bool(re.search(r"^@|internal|corp-|private-", self.package_name, re.I))
        is_public = self._check_public()
        if is_public and internal:
            rpt.add(Finding("high", f"Name '{self.package_name}' on public registry",
                "An attacker could publish a higher versioned malicious package.",
                "Use scoped packages, configure registry routing, or reserve the name."))
        elif not is_public and not internal:
            rpt.add(Finding("info", f"Package '{self.package_name}' not found on public registry",
                "Name appears internal; lower confusion risk."))
        return rpt

    def _check_public(self) -> bool:
        print(f"[*] Querying {self.registry_url}/{self.package_name} ...")
        return False


# ── 2. Typosquatting Detector ────────────────────────────────────────────
_KEY_NEIGHBORS = {"a":"qsxw","b":"vghn","c":"xdfv","d":"serfcx","e":"wrds",
    "f":"drtgvc","g":"ftyhbv","h":"gyujnb","i":"ujko","j":"huiknm","k":"jiolm",
    "l":"kop","m":"njk","n":"bhjm","o":"iklp","p":"ol","q":"wa","r":"etdf",
    "s":"wedxza","t":"ryfg","u":"yijh","v":"cfgb","w":"qase","x":"zsdc",
    "y":"tugh","z":"asx"}

class TyposquatDetector:
    """Detects typosquat candidates for a package name."""

    def __init__(self, package_name: str, registry: str = "pypi") -> None:
        self.package_name = package_name
        self.registry = registry

    def _variants(self, max_n: int = 20) -> list[str]:
        s = self.package_name
        out: set[str] = set()
        ops = [
            lambda s: [s[:i]+s[i+1:] for i in range(len(s))],
            lambda s: [s[:i]+s[i]+s[i:] for i in range(len(s))],
            lambda s: [s[:i]+s[i+1]+s[i]+s[i+2:] for i in range(len(s)-1)],
            lambda s: [s[:i]+n+s[i+1:] for i,c in enumerate(s) for n in _KEY_NEIGHBORS.get(c,"")],
        ]
        for op in ops:
            for v in op(s):
                if v != s and len(v) >= 2:
                    out.add(v)
                if len(out) >= max_n:
                    return sorted(out)[:max_n]
        return sorted(out)

    def scan(self) -> ScanReport:
        rpt = ScanReport("typosquat-detection")
        candidates = self._variants()
        found = self._check_exist(candidates)
        for v in found:
            rpt.add(Finding("medium", f"Potential typosquat: '{v}'",
                f"'{v}' exists on {self.registry} and resembles '{self.package_name}'.",
                "Use lockfiles and exact-version pinning."))
        if not found:
            rpt.add(Finding("info", f"No typosquats found for '{self.package_name}'",
                f"Checked {len(candidates)} candidates."))
        return rpt

    def _check_exist(self, variants: list[str]) -> list[str]:
        print(f"[*] Checking {len(variants)} candidates on {self.registry} ...")
        return []


# ── 3. CI/CD Pipeline Attack Patterns ────────────────────────────────────
CICD_RULES = [
    ("CICD-001","Untrusted action ref",r"uses:\s*\S+@(?!\S*refs/heads/)","high",
     "Action pinned to a mutable tag instead of full SHA.",
     "Pin all third-party actions to full-length commit SHAs."),
    ("CICD-002","Script injection",r"\$\{\{\s*github\.event\.","critical",
     "Untrusted event data interpolated into shell steps.",
     "Pass event data via environment variables."),
    ("CICD-003","pull_request_target",r"pull_request_target","high",
     "pull_request_target runs with secrets and write perms.",
     "Avoid pull_request_target; use pull_request + workflow_run."),
    ("CICD-004","Self-hosted runner",r"runs-on:\s*self-hosted","medium",
     "Self-hosted runners may persist state between untrusted jobs.",
     "Never use self-hosted runners for public fork PRs."),
]

class CICDScanner:
    def __init__(self, manifest_path: str) -> None:
        self.manifest_path = manifest_path

    def scan(self) -> ScanReport:
        rpt = ScanReport("cicd-pipeline")
        content = self._read()
        if content is None:
            rpt.add(Finding("info","Manifest not found",self.manifest_path))
            return rpt
        for rid,name,pat,sev,desc,rec in CICD_RULES:
            for m in re.finditer(pat, content, re.MULTILINE):
                rpt.add(Finding(sev,f"[{rid}] {name}",desc,rec,
                    {"match":m.group(0),"pos":m.start()}))
        if not report_findings(rpt):
            rpt.add(Finding("info","No common patterns detected","Manual review still recommended."))
        return rpt

    def _read(self) -> str | None:
        if not os.path.isfile(self.manifest_path):
            return None
        with open(self.manifest_path,"r",encoding="utf-8") as f:
            return f.read()


# ── 4. Container Image Scanner ───────────────────────────────────────────
CONTAINER_CHECKS = [
    ("CONT-001","Latest tag","medium","'latest' is mutable and unpinable."),
    ("CONT-002","Root user","medium","Defaults to root; increases blast radius."),
    ("CONT-003","No HEALTHCHECK","low","Orchestrator cannot detect runtime failure."),
    ("CONT-004","Secrets in layers","high","Build-time secrets may be baked in."),
]

class ContainerImageScanner:
    def __init__(self, image_ref: str) -> None:
        self.image_ref = image_ref

    def scan(self) -> ScanReport:
        rpt = ScanReport("container-image")
        if self.image_ref.endswith(":latest"):
            rpt.add(Finding("medium","Uses 'latest' tag",
                "Latest tags are mutable and cannot be integrity-pinned.",
                "Pin to a digest (image@sha256:...)."))
        rpt.add(Finding("info","Surface analysis available",
            f"Checks: {', '.join(c[1] for c in CONTAINER_CHECKS)}",
            evidence={"image": self.image_ref}))
        return rpt


# ── 5. Package Integrity Verifier ────────────────────────────────────────
class IntegrityVerifier:
    def __init__(self, package_name: str, version: str) -> None:
        self.package_name = package_name
        self.version = version

    def _hash(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path,"rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify(self, local_path: str, expected: str | None) -> ScanReport:
        rpt = ScanReport("integrity-verification")
        if not os.path.isfile(local_path):
            rpt.add(Finding("high","Artifact not found",local_path))
            return rpt
        actual = self._hash(local_path)
        if expected:
            if actual == expected:
                rpt.add(Finding("info","Hash matches — integrity verified",
                    f"{self.package_name}@{self.version}", evidence={"sha256":actual}))
            else:
                rpt.add(Finding("critical","Hash mismatch — possible tampering",
                    f"Expected {expected[:16]}... but got {actual[:16]}...",
                    "Do not install. Re-download from trusted source.",
                    {"expected":expected,"actual":actual}))
        else:
            rpt.add(Finding("info","Computed SHA-256",evidence={"sha256":actual}))
        return rpt


# ── Helpers ──────────────────────────────────────────────────────────────
def report_findings(rpt: ScanReport) -> bool:
    return bool(rpt.findings)


def print_report(rpt: ScanReport) -> None:
    print(f"\n{'='*60}\nSupply Chain Scan — mode: {rpt.mode}\n{'='*60}")
    for f in rpt.findings:
        print(f"\n  [{f.severity.upper()}] {f.title}\n    {f.description}")
        if f.recommendation:
            print(f"    → {f.recommendation}")
        if f.evidence:
            print(f"    evidence: {f.evidence}")
    counts = {}
    for f in rpt.findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    print(f"\n  Summary: {counts}\n{'='*60}\n")


# ── CLI ──────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Supply Chain Attack Framework (lab)")
    p.add_argument("--mode", required=True,
        choices=["dependency-confusion","typosquat","cicd","container","integrity"])
    p.add_argument("--registry-url", default="https://registry.npmjs.org")
    p.add_argument("--registry", default="pypi")
    p.add_argument("--package", default="")
    p.add_argument("--version", default="")
    p.add_argument("--manifest", default=".github/workflows/ci.yml")
    p.add_argument("--image", default="")
    p.add_argument("--local-path", default="")
    p.add_argument("--expected-hash", default="")
    a = p.parse_args(argv)

    if a.mode == "dependency-confusion":
        scanner = DependencyConfusionScanner(a.registry_url, a.package)
        report = scanner.scan()
    elif a.mode == "typosquat":
        scanner = TyposquatDetector(a.package, a.registry)
        report = scanner.scan()
    elif a.mode == "cicd":
        scanner = CICDScanner(a.manifest)
        report = scanner.scan()
    elif a.mode == "container":
        scanner = ContainerImageScanner(a.image or f"{a.package}:latest")
        report = scanner.scan()
    elif a.mode == "integrity":
        verifier = IntegrityVerifier(a.package, a.version)
        report = verifier.verify(a.local_path, a.expected_hash or None)
    else:
        return 1

    print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
