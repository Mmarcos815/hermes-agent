#!/usr/bin/env python3
"""Evidence collection and chain-of-custody tracker.

Usage:
    evidence_tracker.py add  <file> --finding FIND-001 --type screenshot
    evidence_tracker.py list [--finding FIND-001]
    evidence_tracker.py verify <file>
    evidence_tracker.py export [--format json|csv]

All evidence metadata is stored in evidence/chain_of_custody.json.
Each entry is SHA-256 hashed so tampering is detectable.
"""

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

EVIDENCE_DIR = Path("evidence")
CUSTODY_FILE = EVIDENCE_DIR / "chain_of_custody.json"
VALID_TYPES = {"screenshot", "pcap", "log", "note", "scan", "other"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_chain() -> list[dict]:
    if CUSTODY_FILE.exists():
        return json.loads(CUSTODY_FILE.read_text())
    return []


def save_chain(chain: list[dict]) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    CUSTODY_FILE.write_text(json.dumps(chain, indent=2))


def add_evidence(file_path: str, finding_id: str, ev_type: str) -> dict:
    if ev_type not in VALID_TYPES:
        print(f"error: type must be one of {sorted(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)

    src = Path(file_path)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    # Copy into evidence dir, preserving original
    dest_dir = EVIDENCE_DIR / "store"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    dest.write_bytes(src.read_bytes())

    file_hash = sha256_file(dest)
    entry = {
        "id": f"{finding_id}-{len(load_chain()) + 1:03d}",
        "finding_id": finding_id,
        "type": ev_type,
        "original_name": src.name,
        "stored_path": str(dest),
        "sha256": file_hash,
        "size_bytes": dest.stat().st_size,
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "collected_by": os.getenv("USER") or os.getenv("USERNAME") or "unknown",
    }

    chain = load_chain()
    chain.append(entry)
    save_chain(chain)
    print(f"added: {entry['id']}  sha256={file_hash}")
    return entry


def list_evidence(finding_id: str | None = None) -> list[dict]:
    chain = load_chain()
    if finding_id:
        chain = [e for e in chain if e["finding_id"] == finding_id]
    for e in chain:
        print(f"{e['id']:20s}  {e['type']:10s}  {e['sha256'][:16]}…  {e['collected_at']}")
    return chain


def verify_evidence(file_path: str) -> bool:
    path = Path(file_path)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    current_hash = sha256_file(path)
    chain = load_chain()
    matches = [e for e in chain if e.get("stored_path") == str(path)]
    if not matches:
        print(f"warning: {path} not in chain of custody")
        return False

    expected = matches[-1]["sha256"]
    ok = current_hash == expected
    status = "OK" if ok else "TAMPERED"
    print(f"{status}: {current_hash} (expected {expected})")
    return ok


def export_chain(fmt: str) -> None:
    chain = load_chain()
    if fmt == "json":
        print(json.dumps(chain, indent=2))
    elif fmt == "csv":
        w = csv.DictWriter(
            sys.stdout,
            fieldnames=["id", "finding_id", "type", "sha256",
                        "collected_at", "collected_by"],
        )
        w.writeheader()
        w.writerows(chain)
    else:
        print(f"error: unknown format {fmt}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description="Evidence chain-of-custody tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("add", help="Register a piece of evidence")
    sp.add_argument("file")
    sp.add_argument("--finding", required=True)
    sp.add_argument("--type", required=True)

    sp = sub.add_parser("list", help="List evidence")
    sp.add_argument("--finding")

    sp = sub_parser_verify = sub.add_parser("verify", help="Verify file integrity")
    sp.add_argument("file")

    sp = sub.add_parser("export", help="Export chain of custody")
    sp.add_argument("--format", choices=["json", "csv"], default="json")

    args = p.parse_args()
    if args.cmd == "add":
        add_evidence(args.file, args.finding, args.type)
    elif args.cmd == "list":
        list_evidence(args.finding)
    elif args.cmd == "verify":
        verify_evidence(args.file)
    elif args.cmd == "export":
        export_chain(args.format)


if __name__ == "__main__":
    main()
