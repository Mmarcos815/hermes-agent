# LocalStack Cloud Attack Simulation Testing

LocalStack-based testing environment for simulating and detecting AWS cloud attack techniques.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | LocalStack container with S3, IAM, Lambda, EC2, CloudTrail |
| `setup.sh` | Initializes buckets, users, roles, Lambda, EC2, CloudTrail |
| `test_aws.py` | Pytest suite covering recon, escalation, exfiltration, persistence, detection |
| `README.md` | This file |

## Prerequisites

- Docker Desktop (running)
- Python 3.11+
- AWS CLI v2
- `boto3`, `pytest`

```bash
pip install boto3 pytest
```

## Quick Start

```bash
# 1. Start LocalStack
cd testing/localstack
docker compose up -d

# 2. Wait for health check, then initialize resources
chmod +x setup.sh
./setup.sh

# 3. Run tests
cd testing/localstack
pytest test_aws.py -v
```

## Test Categories

| Class | Technique | MITRE ATT&CK |
|-------|-----------|--------------|
| `TestReconnaissance` | S3/IAM/EC2 enumeration | T1526, T1580 |
| `TestPrivilegeEscalation` | Policy creation & attachment | T1098, T1548 |
| `TestDataExfiltration` | S3 data staging & misconfig | T1530, T1567 |
| `TestPersistence` | Lambda backdoor, access keys | T1098, T1133 |
| `TestDetection` | CloudTrail logging & lookup | T1562 |
| `TestLateralMovement` | Role assumption, metadata | T1550, T1552 |

## Environment Variables

| Variable | Value |
|----------|-------|
| `AWS_ACCESS_KEY_ID` | `test` |
| `AWS_SECRET_ACCESS_KEY` | `test` |
| `AWS_DEFAULT_REGION` | `us-east-1` |
| Endpoint | `http://localhost:4566` |

## Cleanup

```bash
docker compose down -v
```

## Notes

- LocalStack is for **testing only** — no real AWS resources are used.
- CloudTrail event propagation may be delayed; tests handle this gracefully.
- All resources are ephemeral and destroyed on container removal.
