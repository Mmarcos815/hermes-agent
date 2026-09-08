#!/usr/bin/env python3
"""
Kubernetes Security Lab Tool
============================
A self-contained security lab that:
  1. Spins up a local Kubernetes cluster (kind or k3d)
  2. Runs kube-bench CIS benchmark
  3. Runs kube-hunter penetration test
  4. Generates a hardened RBAC manifest

Usage:
    python k8s_security_lab.py [--tool kind|k3d] [--skip-cluster] [--skip-bench] [--skip-hunter] [--output-dir ./output]

Requirements:
    - Docker installed and running
    - kubectl installed
    - kind OR k3d installed
    - kube-bench and kube-hunter installed (or use --skip flags)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path


CLUSTER_NAME = "security-lab"
KUBE_BENCH_VERSION = "0.7.3"
KUBE_HUNTER_VERSION = "0.6.8"


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def check_prerequisites(tool: str) -> bool:
    """Verify that required binaries are available."""
    print("[*] Checking prerequisites...")
    required = ["docker", "kubectl"]
    if tool == "kind":
        required.append("kind")
    elif tool == "k3d":
        required.append("k3d")
    missing = [b for b in required if not shutil.which(b)]
    if missing:
        print(f"[!] Missing binaries: {', '.join(missing)}")
        return False
    print("[+] All prerequisites satisfied.")
    return True


def create_cluster(tool: str) -> bool:
    """Create a local Kubernetes cluster using kind or k3d."""
    print(f"\n[*] Creating {tool} cluster '{CLUSTER_NAME}'...")
    if tool == "kind":
        config = textwrap.dedent("""\
            kind: Cluster
            apiVersion: kind.x-k8s.io/v1alpha4
            name: security-lab
            nodes:
              - role: control-plane
                kubeadmConfigPatches:
                  - |
                    kind: ClusterConfiguration
                    apiServer:
                      extraArgs:
                        audit-log-path: /var/log/kubernetes/audit.log
                        audit-policy-file: /etc/kubernetes/audit-policy.yaml
                extraMounts:
                  - hostPath: ./audit-policy.yaml
                    containerPath: /etc/kubernetes/audit-policy.yaml
            """)
        Path("audit-policy.yaml").write_text(textwrap.dedent("""\
            apiVersion: audit.k8s.io/v1
            kind: Policy
            rules:
              - level: Metadata
            """))
        run(["kind", "create", "cluster", "--name", CLUSTER_NAME, "--config", "-"],
            check=False)
        # kind doesn't support stdin config easily; use file approach
        config_path = Path("kind-config.yaml")
        config_path.write_text(config)
        result = run(["kind", "create", "cluster", "--name", CLUSTER_NAME,
                       "--config", str(config_path)], check=False)
    else:
        result = run(["k3d", "cluster", "create", CLUSTER_NAME,
                       "--agents", "1", "--no-lb"], check=False)
    if result.returncode != 0:
        print(f"[!] Cluster creation failed: {result.stderr}")
        return False
    print("[+] Cluster created successfully.")
    return True


def delete_cluster(tool: str) -> None:
    """Delete the local cluster."""
    print(f"\n[*] Deleting {tool} cluster '{CLUSTER_NAME}'...")
    if tool == "kind":
        run(["kind", "delete", "cluster", "--name", CLUSTER_NAME], check=False)
    else:
        run(["k3d", "cluster", "delete", CLUSTER_NAME], check=False)
    print("[+] Cluster deleted.")


def run_kube_bench(output_dir: Path) -> bool:
    """Run kube-bench CIS benchmark against the cluster."""
    print("\n[*] Running kube-bench CIS benchmark...")
    if not shutil.which("kube-bench"):
        print("[!] kube-bench not found. Install: "
              f"https://github.com/aquasecurity/kube-bench/releases/tag/v{KUBE_BENCH_VERSION}")
        return False
    output_file = output_dir / "kube-bench-results.json"
    result = run([
        "kube-bench", "run", "--json", "--outputfile", str(output_file)
    ], check=False)
    if result.returncode == 0:
        print(f"[+] kube-bench complete. Results: {output_file}")
        return True
    print(f"[!] kube-bench exited with code {result.returncode}")
    return False


def run_kube_hunter(output_dir: Path) -> bool:
    """Run kube-hunter penetration test."""
    print("\n[*] Running kube-hunter penetration test...")
    if not shutil.which("kube-hunter"):
        print("[!] kube-hunter not found. Install: pip install kube-hunter")
        return False
    output_file = output_dir / "kube-hunter-results.json"
    result = run([
        "kube-hunter", "--log", "file", "--log-file", str(output_file),
        "--report", "json", "--remote", "127.0.0.1"
    ], check=False)
    if result.returncode == 0:
        print(f"[+] kube-hunter complete. Results: {output_file}")
        return True
    print(f"[!] kube-hunter exited with code {result.returncode}")
    return False


def generate_hardened_rbac(output_dir: Path) -> None:
    """Generate a hardened RBAC manifest with least-privilege roles."""
    print("\n[*] Generating hardened RBAC manifest...")
    manifest = textwrap.dedent("""\
        # Hardened RBAC Manifest
        # Generated by k8s_security_lab.py
        # Applies least-privilege principles for cluster security.

        ---
        # 1. Read-only role for developers
        apiVersion: rbac.authorization.k8s.io/v1
        kind: ClusterRole
        metadata:
          name: developer-readonly
        rules:
          - apiGroups: [""]
            resources: ["pods", "services", "configmaps", "endpoints"]
            verbs: ["get", "list", "watch"]
          - apiGroups: ["apps"]
            resources: ["deployments", "replicasets", "statefulsets"]
            verbs: ["get", "list", "watch"]

        ---
        # 2. Binding: developers get read-only in 'dev' namespace
        apiVersion: rbac.authorization.k8s.io/v1
        kind: RoleBinding
        metadata:
          name: developer-readonly-binding
          namespace: dev
        subjects:
          - kind: Group
            name: developers
            apiGroup: rbac.authorization.k8s.io
        roleRef:
          kind: ClusterRole
          name: developer-readonly
          apiGroup: rbac.authorization.k8s.io

        ---
        # 3. Restricted pod security policy (baseline)
        apiVersion: policy/v1beta1
        kind: PodSecurityPolicy
        metadata:
          name: restricted-baseline
        spec:
          privileged: false
          allowPrivilegeEscalation: false
          requiredDropCapabilities:
            - ALL
          volumes:
            - 'configMap'
            - 'emptyDir'
            - 'projected'
            - 'secret'
            - 'downwardAPI'
            - 'persistentVolumeClaim'
          runAsUser:
            rule: 'MustRunAsNonRoot'
          seLinux:
            rule: 'RunAsAny'
          fsGroup:
            rule: 'RunAsAny'
          supplementalGroups:
            rule: 'RunAsAny'

        ---
        # 4. Network policy: default deny ingress
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        metadata:
          name: default-deny-ingress
          namespace: default
        spec:
          podSelector: {}
          policyTypes:
            - Ingress

        ---
        # 5. Service account with minimal token permissions
        apiVersion: v1
        kind: ServiceAccount
        metadata:
          name: minimal-sa
          namespace: default
        automountServiceAccountToken: false

        ---
        # 6. Audit policy for sensitive operations
        apiVersion: audit.k8s.io/v1
        kind: Policy
        metadata:
          name: sensitive-operations-audit
        rules:
          - level: RequestResponse
            resources:
              - group: ""
                resources: ["secrets", "configmaps"]
          - level: Request
            verbs: ["create", "update", "delete", "patch"]
    """)
    output_file = output_dir / "hardened-rbac.yaml"
    output_file.write_text(manifest)
    print(f"[+] Hardened RBAC manifest written to: {output_file}")


def generate_report(output_dir: Path, results: dict) -> None:
    """Generate a summary report of all lab activities."""
    print("\n[*] Generating summary report...")
    report = {
        "lab": "Kubernetes Security Lab",
        "timestamp": datetime.now().isoformat(),
        "cluster_name": CLUSTER_NAME,
        "results": results,
        "recommendations": [
            "Review kube-bench failures and remediate CIS benchmark gaps.",
            "Address kube-hunter findings by patching exposed services.",
            "Apply hardened-rbac.yaml to enforce least-privilege access.",
            "Enable audit logging and ship logs to a SIEM.",
            "Use Pod Security Standards (restricted) in all namespaces.",
            "Implement network policies for all workloads.",
        ],
    }
    report_file = output_dir / "security-lab-report.json"
    report_file.write_text(json.dumps(report, indent=2))
    print(f"[+] Report written to: {report_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Kubernetes Security Lab Tool")
    parser.add_argument("--tool", choices=["kind", "k3d"], default="kind",
                        help="Cluster tool to use (default: kind)")
    parser.add_argument("--skip-cluster", action="store_true",
                        help="Skip cluster creation (use existing)")
    parser.add_argument("--skip-bench", action="store_true",
                        help="Skip kube-bench CIS benchmark")
    parser.add_argument("--skip-hunter", action="store_true",
                        help="Skip kube-hunter pen-test")
    parser.add_argument("--output-dir", default="./output",
                        help="Output directory for results (default: ./output)")
    parser.add_argument("--keep-cluster", action="store_true",
                        help="Don't delete the cluster after the lab")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    # Step 0: Prerequisites
    if not check_prerequisites(args.tool):
        return 1

    # Step 1: Create cluster
    if not args.skip_cluster:
        results["cluster_created"] = create_cluster(args.tool)
        if not results["cluster_created"]:
            print("[!] Aborting: cluster creation failed.")
            return 1
    else:
        print("\n[*] Skipping cluster creation (--skip-cluster)")
        results["cluster_created"] = "skipped"

    # Step 2: Run kube-bench
    if not args.skip_bench:
        results["kube_bench"] = run_kube_bench(output_dir)
    else:
        print("\n[*] Skipping kube-bench (--skip-bench)")
        results["kube_bench"] = "skipped"

    # Step 3: Run kube-hunter
    if not args.skip_hunter:
        results["kube_hunter"] = run_kube_hunter(output_dir)
    else:
        print("\n[*] Skipping kube-hunter (--skip-hunter)")
        results["kube_hunter"] = "skipped"

    # Step 4: Generate hardened RBAC
    generate_hardened_rbac(output_dir)
    results["rbac_manifest"] = "generated"

    # Step 5: Summary report
    generate_report(output_dir, results)

    # Cleanup
    if not args.skip_cluster and not args.keep_cluster:
        delete_cluster(args.tool)

    print("\n[+] Kubernetes Security Lab complete!")
    print(f"    Results directory: {output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
