# Skill 8: Kubernetes Security — PROGRESS.md

**Status:** ✅ DONE
**Started:** 2026-09-04

## What was built
- `k8s_security_lab.py` (341 lines) — Full K8s security lab tool

## Capabilities
1. **Cluster Setup:** `kind` or `k3d` cluster creation with audit logging
2. **CIS Benchmark:** `kube-bench run --json` — scans against CIS K8s benchmark
3. **Pen-Testing:** `kube-hunter --report json` — automated pen-test
4. **RBAC Generation:** `hardened-rbac.yaml` — least-privilege ClusterRole + PodSecurityPolicy + NetworkPolicy + audit policy
5. **Summary Report:** JSON report with remediation recommendations

## Usage
```bash
python k8s_security_lab.py --tool kind                    # Full pipeline with kind
python k8s_security_lab.py --tool k3d                     # Full pipeline with k3d
python k8s_security_lab.py --skip-cluster                 # Use existing cluster
python k8s_security_lab.py --skip-bench                   # Skip kube-bench
python k8s_security_lab.py --skip-hunter                  # Skip kube-hunter
python k8s_security_lab.py --keep-cluster                 # Don't delete cluster
python k8s_security_lab.py --output-dir ./output          # Custom output dir
```

## Prerequisites
- `docker` — Container runtime
- `kubectl` — K8s CLI
- `kind` or `k3d` — Local cluster tool
- `kube-bench` — CIS benchmark
- `kube-hunter` — Pen-test tool

## Output
- `output/kube-bench-results.json` — CIS benchmark results
- `output/kube-hunter-results.json` — Pen-test findings
- `output/hardened-rbac.yaml` — Hardened RBAC manifest
- `output/security-lab-report.json` — Summary report
