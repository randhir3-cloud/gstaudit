# ADR-009: Caching Strategy

## Status

Proposed

## Context

Comparison and intelligence recomputation on large workbooks (100k+ rows) is expensive. Dashboard refreshes re-fetch aggregated stats.

## Layers

1. **In-process LRU** — comparison results keyed by `(session_id, comparator_id, workbook_hash)` (current partial behavior)
2. **Redis** (optional) — shared cache across API instances
3. **HTTP ETag** — dashboard summary endpoints
4. **Frontend SWR** — hooks cache with stale-while-revalidate

## Decision (recommended)

Phase 1: strengthen in-process cache with TTL and workbook content hash.
Phase 2: Redis when horizontal scaling is required.

## Consequences

- Cache invalidation on new upload/merge for affected datasets
- Document cache keys in API_REFERENCE

## References

- [PERFORMANCE.md](../PERFORMANCE.md)
