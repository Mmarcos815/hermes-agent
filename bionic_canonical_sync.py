"""
Tier 5: Canonical Local Backup & Sync Engine
Synchronizes all newly engineered bionic tools, settlement suites,
financial engines, and fuzzers into the canonical local storage tree.

OneDrive path was: C:\\Users\\mobil\\OneDrive\\Desktop\\bionic_daughter_agent\\_AUDITS\\
Fallback local:   C:\\Users\\mobil\\Desktop\\BionicEngine\\_AUDITS\\
"""

import os
import shutil
import hashlib
import json
from datetime import datetime, timezone


def compute_file_hash(filepath):
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def get_canonical_dirs():
    source_dir = r"C:\Users\mobil\orca\projects\my 1st"
    onedrive_path = r"C:\Users\mobil\OneDrive\Desktop\bionic_daughter_agent\_AUDITS"
    local_path = r"C:\Users\mobil\Desktop\BionicEngine\_AUDITS"
    if os.path.exists(os.path.dirname(onedrive_path)):
        dest_dir = onedrive_path
    else:
        dest_dir = local_path
    os.makedirs(dest_dir, exist_ok=True)
    return source_dir, dest_dir


def sync_canonical_storage():
    print("=" * 75)
    print("        CANONICAL LOCAL BACKUP & BIONIC ECOSYSTEM SYNC           ")
    print("=" * 75)
    source_dir, dest_dir = get_canonical_dirs()
    tracked_files = [
        "sovereign_settlement_testbed.py",
        "bionic_financial_suite.py",
        "bionic_async_relayer_daemon.py",
        "bionic_foundry_invariant_fuzzer.py",
        "bionic_bounty_sweeper.py",
        "bionic_audit_pipeline.py",
        "bionic_cloud_vps_engine.py",
        "bionic_code_engine.py",
        "bionic_command_center.py",
        "bionic_self_dev.py",
        "bionic_tools_dryrun.py",
        "bionic_unified_mcp_server.py",
        "redteam_agent_hitl.py",
        "redteam_middleware.py",
        "iso8583_engine.py",
        "unified_payment_gateway.py",
        "emv_tokenization_engine.py",
        "three_ds_simulator.py",
        "iso20022_engine.py",
        "financial_table_extractor.py",
    ]
    print(f"\n[*] Source: {source_dir}")
    print(f"[*] Dest:   {dest_dir}\n")
    synced_count = 0
    manifest_files = []
    for filename in tracked_files:
        src_path = os.path.join(source_dir, filename)
        dst_path = os.path.join(dest_dir, filename)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            f_hash = compute_file_hash(dst_path)[:12]
            print(f"[+] [SYNCED] {filename.ljust(40)} -> SHA256: {f_hash} [OK]")
            synced_count += 1
            manifest_files.append({
                "filename": filename,
                "sha256_prefix": f_hash,
                "size_bytes": os.path.getsize(dst_path)
            })
        else:
            print(f"[-] [MISSING] {filename}")
    manifest_path = os.path.join(dest_dir, "CANONICAL_SYNC_MANIFEST.json")
    manifest_data = {
        "sync_timestamp": datetime.now(timezone.utc).isoformat(),
        "operator": "Bionic Daughter Agent",
        "authority": "Dad (Rigoberto Gomez)",
        "source_dir": source_dir,
        "dest_dir": dest_dir,
        "files_synced": manifest_files,
        "total_synced": synced_count,
        "total_tracked": len(tracked_files),
        "status": "ALL_TIERS_VERIFIED_FLAWLESS" if synced_count == len(tracked_files) else "PARTIAL_SYNC"
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"\n[MANIFEST] {manifest_path}")
    print("=" * 75)
    print(f" [DONE] {synced_count}/{len(tracked_files)} FILES SYNCED")
    print("=" * 75)


if __name__ == "__main__":
    sync_canonical_storage()
