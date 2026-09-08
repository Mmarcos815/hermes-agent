#!/usr/bin/env python3
"""
Mobile App Analysis Workflow

Orchestrates a full static + dynamic analysis pipeline for Android APKs.
Combines APKTool, JADX, Frida, and custom checks into a unified report.

Usage:
    python analysis_workflow.py --apk ./test_apps/hardcoded_secrets.apk
    python analysis_workflow.py --apk ./app.apk --frida --package com.example.app
    python analysis_workflow.py --apk ./app.apk --output ./report/
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MobileAnalyzer:
    """Full mobile app analysis pipeline."""

    # Common vulnerability patterns for static analysis
    PATTERNS = {
        "hardcoded_secrets": {
            "patterns": [
                r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9]{16,}["\']',
                r'(?i)(secret|password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']',
                r'(?i)(aws[_-]?access[_-]?key|AKIA)[A-Z0-9]{16}',
                r'(?i)sk_(live|test)_[a-zA-Z0-9]{20,}',
                r'(?i)bearer\s+[a-zA-Z0-9\-._~+/]+=*',
                r'(?i)-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
            ],
            "severity": "HIGH",
            "description": "Hardcoded secrets found in source code",
        },
        "insecure_communication": {
            "patterns": [
                r'http://[^\s"\']+',
                r'usesCleartextTraffic\s*=\s*["\']true["\']',
                r'setJavaScriptEnabled\s*\(\s*true\s*\)',
                r'setAllowFileAccess\s*\(\s*true\s*\)',
                r'setAllowUniversalAccessFromFileURLs\s*\(\s*true\s*\)',
                r'trustAllCerts|TrustAll|trustAllHosts',
                r'ALLOW_ALL_HOSTNAME_VERIFIER',
                r'checkServerTrusted\s*\(\s*\)\s*\{\s*\}',
            ],
            "severity": "MEDIUM",
            "description": "Insecure network or WebView configuration",
        },
        "insecure_storage": {
            "patterns": [
                r'MODE_WORLD_READABLE',
                r'MODE_WORLD_WRITEABLE',
                r'getSharedPreferences\s*\([^,]+,\s*MODE_WORLD',
                r'Environment\.getExternalStorageDirectory',
                r'getExternalFilesDir',
                r'\.contains\s*\(\s*["\']password["\']\s*\)',
                r'\.contains\s*\(\s*["\']credit[_-]?card["\']\s*\)',
            ],
            "severity": "MEDIUM",
            "description": "Insecure data storage patterns",
        },
        "logging_leaks": {
            "patterns": [
                r'Log\.[vdiwe]\s*\([^)]*(?:password|token|secret|key|auth)',
                r'println\s*\([^)]*(?:password|token|secret|key)',
                r'System\.out\.print[^)]*(?:password|token|secret)',
            ],
            "severity": "LOW",
            "description": "Sensitive data written to logs",
        },
        "weak_crypto": {
            "patterns": [
                r'DES/',
                r'ECB',
                r'MD5',
                r'SHA1',
                r'Random\s*\(',
                r'new\s+Random\s*\(',
                r'SecureRandom.*null',
                r'IvParameterSpec\s*\(\s*new\s+byte',
            ],
            "severity": "MEDIUM",
            "description": "Weak cryptographic algorithms or usage",
        },
        "exported_components": {
            "patterns": [
                r'android:exported\s*=\s*["\']true["\']',
                r'android:debuggable\s*=\s*["\']true["\']',
                r'android:allowBackup\s*=\s*["\']true["\']',
            ],
            "severity": "INFO",
            "description": "Potentially dangerous manifest configuration",
        },
    }

    def __init__(self, apk_path: str, output_dir: Optional[str] = None):
        self.apk_path = Path(apk_path)
        if not self.apk_path.exists():
            raise FileNotFoundError(f"APK not found: {apk_path}")

        self.output_dir = Path(output_dir or "./analysis_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="analysis_"))
        self.findings: List[Dict] = []
        self.metadata: Dict = {}

    def analyze(self, run_frida: bool = False, package_name: Optional[str] = None) -> Dict:
        """Run the full analysis pipeline."""
        print(f"[*] Analyzing: {self.apk_path}")

        # Phase 1: Metadata extraction
        self._extract_metadata()

        # Phase 2: Decompile APK
        decompiled = self._decompile_apk()

        # Phase 3: Static analysis
        if decompiled:
            self._run_static_analysis(decompiled)

        # Phase 4: Manifest analysis
        self._analyze_manifest(decompiled)

        # Phase 5: Dynamic analysis (optional)
        if run_frida and package_name:
            self._run_dynamic_analysis(package_name)

        # Phase 6: Generate report
        report = self._generate_report()

        # Cleanup
        self._cleanup()

        return report

    def _extract_metadata(self):
        """Extract basic APK metadata."""
        stat = self.apk_path.stat()
        self.metadata = {
            "file_name": self.apk_path.name,
            "file_size": stat.st_size,
            "md5": self._file_hash("md5"),
            "sha256": self._file_hash("sha256"),
            "analysis_time": datetime.now().isoformat(),
        }
        print(f"[*] File: {self.metadata['file_name']} ({self.metadata['file_size']} bytes)")
        print(f"[*] SHA256: {self.metadata['sha256']}")

    def _file_hash(self, algorithm: str) -> str:
        """Calculate file hash."""
        h = hashlib.new(algorithm)
        with open(self.apk_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _decompile_apk(self) -> Optional[Path]:
        """Decompile APK using APKTool and JADX if available."""
        decompile_dir = self.temp_dir / "decompiled"
        decompile_dir.mkdir()

        # Try APKTool
        try:
            result = subprocess.run(
                ["apktool", "d", "-f", "-o", str(decompile_dir / "apktool"), str(self.apk_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[+] APKTool decompilation successful")
            else:
                print(f"[!] APKTool failed: {result.stderr[:200]}")
        except FileNotFoundError:
            print("[!] APKTool not found in PATH")
        except subprocess.TimeoutExpired:
            print("[!] APKTool timed out")

        # Try JADX
        try:
            result = subprocess.run(
                ["jadx", "-d", str(decompile_dir / "jadx"), str(self.apk_path)],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("[+] JADX decompilation successful")
            else:
                print(f"[!] JADX failed: {result.stderr[:200]}")
        except FileNotFoundError:
            print("[!] JADX not found in PATH")
        except subprocess.TimeoutExpired:
            print("[!] JADX timed out")

        return decompile_dir if decompile_dir.exists() else None

    def _run_static_analysis(self, decompiled_dir: Path):
        """Run pattern-based static analysis on decompiled sources."""
        print("[*] Running static analysis...")

        # Find all source files
        source_extensions = {".java", ".smali", ".xml", ".json", ".properties"}
        source_files = []
        for ext in source_extensions:
            source_files.extend(decompiled_dir.rglob(f"*{ext}"))

        for source_file in source_files:
            try:
                content = source_file.read_text(errors="ignore")
                relative_path = source_file.relative_to(decompiled_dir)

                for vuln_name, vuln_info in self.PATTERNS.items():
                    for pattern in vuln_info["patterns"]:
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            # Get context (surrounding lines)
                            start = max(0, match.start() - 100)
                            end = min(len(content), match.end() + 100)
                            context = content[start:end].replace("\n", " ").strip()

                            self.findings.append({
                                "type": vuln_name,
                                "severity": vuln_info["severity"],
                                "description": vuln_info["description"],
                                "file": str(relative_path),
                                "line": content[:match.start()].count("\n") + 1,
                                "match": match.group()[:100],
                                "context": context[:200],
                            })
            except Exception as e:
                continue

        print(f"[+] Found {len(self.findings)} potential issues")

    def _analyze_manifest(self, decompiled_dir: Optional[Path]):
        """Analyze AndroidManifest.xml for security issues."""
        if not decompiled_dir:
            return

        manifest_path = decompiled_dir / "apktool" / "AndroidManifest.xml"
        if not manifest_path.exists():
            return

        try:
            content = manifest_path.read_text(errors="ignore")

            # Extract package name
            pkg_match = re.search(r'package="([^"]+)"', content)
            if pkg_match:
                self.metadata["package_name"] = pkg_match.group(1)

            # Check for permissions
            permissions = re.findall(r'android:name="android\.permission\.([^"]+)"', content)
            dangerous_perms = [
                "READ_CONTACTS", "WRITE_CONTACTS", "READ_SMS", "SEND_SMS",
                "READ_PHONE_STATE", "CAMERA", "RECORD_AUDIO", "ACCESS_FINE_LOCATION",
                "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE", "CALL_PHONE",
            ]
            found_dangerous = [p for p in permissions if p in dangerous_perms]
            if found_dangerous:
                self.findings.append({
                    "type": "dangerous_permissions",
                    "severity": "INFO",
                    "description": f"Dangerous permissions: {', '.join(found_dangerous)}",
                    "file": "AndroidManifest.xml",
                    "line": 0,
                    "match": ", ".join(found_dangerous),
                    "context": "Manifest permissions",
                })

            # Check for exported activities
            exported = re.findall(r'<activity[^>]*android:exported="true"[^>]*>', content)
            if exported:
                self.findings.append({
                    "type": "exported_activities",
                    "severity": "MEDIUM",
                    "description": f"Found {len(exported)} exported activities",
                    "file": "AndroidManifest.xml",
                    "line": 0,
                    "match": f"{len(exported)} activities",
                    "context": "Exported components can be accessed by other apps",
                })

            # Check for debuggable flag
            if 'android:debuggable="true"' in content:
                self.findings.append({
                    "type": "debuggable_app",
                    "severity": "HIGH",
                    "description": "Application is debuggable",
                    "file": "AndroidManifest.xml",
                    "line": 0,
                    "match": "android:debuggable=true",
                    "context": "Debuggable apps allow code injection and analysis",
                })

        except Exception as e:
            print(f"[!] Manifest analysis error: {e}")

    def _run_dynamic_analysis(self, package_name: str):
        """Run Frida-based dynamic analysis."""
        print(f"[*] Running dynamic analysis on {package_name}...")

        try:
            import frida
        except ImportError:
            print("[!] Frida not installed. Run: pip install frida-tools")
            return

        try:
            device = frida.get_usb_device(timeout=5)
            pid = device.spawn([package_name])
            session = device.attach(pid)

            # Load all monitoring scripts
            from frida_scripts import SCRIPTS
            for script_name, script_code in SCRIPTS.items():
                if "bypass" in script_name:
                    continue  # Skip bypass scripts for pure monitoring
                try:
                    script = session.create_script(script_code)
                    script.load()
                    print(f"[+] Loaded Frida script: {script_name}")
                except Exception as e:
                    print(f"[!] Failed to load {script_name}: {e}")

            device.resume(pid)
            print("[*] Dynamic analysis active. Press Ctrl+C to stop.")

        except Exception as e:
            print(f"[!] Dynamic analysis failed: {e}")

    def _generate_report(self) -> Dict:
        """Generate the final analysis report."""
        # Count findings by severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for finding in self.findings:
            severity_counts[finding["severity"]] = severity_counts.get(finding["severity"], 0) + 1

        # Count by type
        type_counts: Dict[str, int] = {}
        for finding in self.findings:
            type_counts[finding["type"]] = type_counts.get(finding["type"], 0) + 1

        report = {
            "metadata": self.metadata,
            "summary": {
                "total_findings": len(self.findings),
                "severity_counts": severity_counts,
                "type_counts": type_counts,
            },
            "findings": self.findings,
        }

        # Save JSON report
        report_path = self.output_dir / f"report_{self.metadata.get('sha256', 'unknown')[:12]}.json"
        report_path.write_text(json.dumps(report, indent=2))
        print(f"[+] Report saved: {report_path}")

        # Print summary
        print("\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"File: {self.metadata.get('file_name', 'unknown')}")
        print(f"Package: {self.metadata.get('package_name', 'unknown')}")
        print(f"Total findings: {len(self.findings)}")
        print(f"  HIGH:   {severity_counts['HIGH']}")
        print(f"  MEDIUM: {severity_counts['MEDIUM']}")
        print(f"  LOW:    {severity_counts['LOW']}")
        print(f"  INFO:   {severity_counts['INFO']}")
        print("=" * 50)

        if self.findings:
            print("\nTop findings:")
            for finding in self.findings[:10]:
                print(f"  [{finding['severity']}] {finding['description']}")
                print(f"    File: {finding['file']}:{finding.get('line', '?')}")
                print(f"    Match: {finding['match'][:60]}")
                print()

        return report

    def _cleanup(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Mobile App Analysis Workflow")
    parser.add_argument("--apk", required=True, help="Path to APK file")
    parser.add_argument("--output", default="./analysis_output", help="Output directory")
    parser.add_argument("--frida", action="store_true", help="Run Frida dynamic analysis")
    parser.add_argument("--package", help="Package name for dynamic analysis")
    args = parser.parse_args()

    try:
        analyzer = MobileAnalyzer(args.apk, args.output)
        report = analyzer.analyze(run_frida=args.frida, package_name=args.package)

        # Exit with error code if high severity findings
        high_count = report["summary"]["severity_counts"].get("HIGH", 0)
        if high_count > 0:
            print(f"\n[!] {high_count} HIGH severity findings detected!")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"[!] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[!] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
