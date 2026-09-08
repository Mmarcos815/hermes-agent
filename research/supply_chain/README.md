# Supply Chain Research

## Methodology

1. **Dependency Risk Analysis** — Parse manifests, cross-reference OSV for vulns, flag recent/low-download packages.
2. **Typosquat Detection** — Generate name mutations (deletions, transpositions, keyboard-adjacent swaps), probe registries.
3. **CI/CD Audit** — Scan workflows for `pull_request_target`, unpinned actions, missing permissions, script injection.
4. **CVE Monitoring** — Poll OSV for supply-chain-related CVEs filtered by watched packages.

## Usage

```
python package_analyzer.py /path/to/project
python typosquat_monitor.py --packages requests lodash --ecosystem pypi
python ci_cd_auditor.py /path/to/repo/.github/workflows
python cve_monitor.py --packages requests flask --severity HIGH
```

## References
- [OSV](https://osv.dev/) | [NVD](https://nvd.nist.gov/) | [MITRE ATT&CK: T1195](https://attack.mitre.org/techniques/T1195/)
