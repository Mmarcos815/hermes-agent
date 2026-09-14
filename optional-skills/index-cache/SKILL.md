---
name: index-cache
description: "Index cache management and optimization for search and retrieval systems."
version: 1.0.0
author: Orchestra Research
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Indexing, Caching, Search, Retrieval, Performance, Database, Storage]

---

# Index Cache Skill

Guidance for building, maintaining, and optimizing index caches for search, retrieval, and data lookup systems.

## When to Use This Skill

This skill should be triggered when:
- Designing or implementing index-based caching layers
- Optimizing search index performance with caching
- Managing cache invalidation for indexed data
- Choosing between in-memory, disk-based, or distributed index caches
- Debugging cache-hit ratio or staleness issues

## Quick Reference

### Common Patterns

**Pattern 1: LRU cache for frequently accessed index entries**

```python
from functools import lru_cache

@lru_cache(maxsize=4096)
def get_index_entry(key: str) -> dict:
    """Retrieve index entry with LRU caching."""
    return index_lookup(key)
```

**Pattern 2: Time-based cache invalidation**

```python
import time
from cachetools import TTLCache

# Cache entries expire after 300 seconds
index_cache = TTLCache(maxsize=10000, ttl=300)

def get_cached_entry(key: str) -> dict:
    if key not in index_cache:
        index_cache[key] = index_lookup(key)
    return index_cache[key]
```

**Pattern 3: Two-level cache (memory + disk)**

```python
import diskcache as dc

# Hot cache in RAM, warm cache on disk
hot_cache = {}
warm_cache = dc.Cache('/tmp/index-cache')

def get_entry(key: str):
    if key in hot_cache:
        return hot_cache[key]
    if key in warm_cache:
        val = warm_cache[key]
        hot_cache[key] = val  # Promote to hot
        return val
    val = index_lookup(key)
    hot_cache[key] = val
    warm_cache[key] = val
    return val
```

### Cache invalidation strategies

| Strategy | When to use | Trade-off |
|----------|------------|-----------|
| TTL (time-to-live) | Data changes on known schedule | May serve stale data within window |
| Write-through | Data must never be stale | Higher write latency |
| Cache-aside (lazy) | Read-heavy workloads | First read after write is slow |
| Event-driven | Real-time invalidation needed | Requires pub/sub infrastructure |

## Reference Files

This skill includes reference documentation in `references/`:

- **cache-strategies.md** - Detailed comparison of caching strategies for index systems
- ** invalidation-patterns.md** - Patterns for keeping index caches consistent

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners

Start with TTL-based caches (simplest) before moving to event-driven invalidation.

### For Specific Features

- Cache sizing: See cache-strategies.md
- Invalidation: See invalidation-patterns.md

### For Code Examples

The quick reference above shows common patterns for memory, disk, and hybrid caches.

## Resources

### references/

Organized documentation extracted from official sources.

### scripts/

Add helper scripts for cache benchmarking and monitoring.

### assets/

Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from documentation
- Reference files preserve structure and examples from source docs
- Cache hit ratio is the primary metric to monitor

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information
