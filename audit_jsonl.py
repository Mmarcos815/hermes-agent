#!/usr/bin/env python3
"""Audit hacker_training JSONL files: count empty vs filled, domains, quality."""
import json
import os
import sys

DIR = r"C:\Users\mobil\orca\projects\my 1st\hacker_training"

files = sorted(f for f in os.listdir(DIR) if f.endswith('.jsonl'))

total_empty = 0
total_filled = 0
domain_counts = {}
subcat_counts = {}
filled_examples = {}
file_stats = []

for fname in files:
    fpath = os.path.join(DIR, fname)
    empty = 0
    filled = 0
    comps = []
    with open(fpath, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            c = d.get('completion', '')
            is_empty = not isinstance(c, str) or len(c.strip()) == 0
            if is_empty:
                empty += 1
            else:
                filled += 1
                comps.append(c.strip())
                domain = d.get('metadata', {}).get('domain', 'UNKNOWN')
                subcat = d.get('metadata', {}).get('subcategory', 'UNKNOWN')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
                subcat_counts[subcat] = subcat_counts.get(subcat, 0) + 1

    total_empty += empty
    total_filled += filled
    file_stats.append({
        'file': fname,
        'empty': empty,
        'filled': filled,
        'total': empty + filled,
        'sample': comps[0] if comps else None
    })
    if comps:
        filled_examples[fname] = comps[:3]  # first 3 examples

print("=== FILE-BY-FILE ===")
for s in file_stats:
    pct = (s['empty'] / s['total'] * 100) if s['total'] > 0 else 0
    print(f"{s['file']}: {s['empty']} empty / {s['filled']} filled ({pct:.1f}% empty), total={s['total']}")
    if s['sample']:
        print(f"  SAMPLE FILLED: {s['sample'][:150]}...")

print("\n=== DOMAIN SUMMARY ===")
for dom, cnt in sorted(domain_counts.items(), key=lambda x: -x[1]):
    print(f"  {dom}: {cnt}")

print("\n=== SUBCATEGORY SUMMARY ===")
for sub, cnt in sorted(subcat_counts.items(), key=lambda x: -x[1]):
    print(f"  {sub}: {cnt}")

print(f"\n=== GRAND TOTAL: {total_empty} empty / {total_filled} filled = {total_empty + total_filled} prompts ===")
print(f"Empty rate: {total_empty/(total_empty+total_filled)*100:.1f}%")

print("\n=== Filled Examples (first 3 per file) ===")
for fname, examples in filled_examples.items():
    print(f"\n--- {fname} ---")
    for i, ex in enumerate(examples, 1):
        print(f"  [{i}] {ex[:250]}")
