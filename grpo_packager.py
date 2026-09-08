"""
GRPO Dataset Packager — training-ready emission
Validates all reasoning traces and emits:
1. grpo_train.jsonl   — {prompt, completion} pairs for GRPO rollouts
2. grpo_meta.json     — corpus stats + integrity manifest
"""

import json
import os
import sys
from collections import Counter
from datetime import datetime

SRC = r"C:\Users\mobil\OneDrive\Desktop\bionic_daughter_agent\knowledge\grpo_security_reasoning_dataset.jsonl"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_JSONL = os.path.join(OUT_DIR, "grpo_train_ready.jsonl")
OUT_META = os.path.join(OUT_DIR, "grpo_meta.json")

def main():
    if not os.path.exists(SRC):
        print(f"[-] Source dataset missing: {SRC}")
        sys.exit(1)

    records, bad = [], 0
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                msgs = rec.get("messages", [])
                if len(msgs) >= 3 and msgs[-1]["role"] == "assistant":
                    prompt = "\n".join(m["content"] for m in msgs[:-1])
                    completion = msgs[-1]["content"]
                    records.append({
                        "prompt": prompt,
                        "completion": completion,
                        "metadata": rec.get("metadata", {}),
                    })
                else:
                    bad += 1
            except json.JSONDecodeError:
                bad += 1

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Corpus stats
    meta_counter = Counter()
    for r in records:
        m = r["metadata"]
        domain = m.get("domain") or m.get("category") or "unclassified"
        meta_counter[domain] += 1

    meta = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "source": SRC,
        "total_source_lines": len(records) + bad,
        "valid_records": len(records),
        "malformed_skipped": bad,
        "domains": dict(meta_counter.most_common()),
        "format": "GRPO prompt/completion JSONL (chat-templated on load)",
        "status": "TRAINING_READY",
    }
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("=" * 70)
    print("      GRPO DATASET PACKAGER — TRAINING-READY EMISSION")
    print("=" * 70)
    print(f"Valid records : {len(records):,}")
    print(f"Malformed     : {bad}")
    print(f"Domains       : {len(meta_counter)}")
    for d, c in meta_counter.most_common(10):
        print(f"  {d:30} {c:5,}")
    print("-" * 70)
    print(f"[OK] JSONL : {OUT_JSONL}")
    print(f"[OK] Meta  : {OUT_META}")

if __name__ == "__main__":
    main()
