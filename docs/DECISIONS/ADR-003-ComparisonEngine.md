# ADR-003: Comparison Engine Design

**Status:** Accepted  
**Date:** 2026-07-09  
**Deciders:** GAIS core team

## Context

GST audit requires reconciling invoices across returns (GSTR-1) and logistics records (E-Way Bills). Rules vary by discrepancy type (missing, GSTIN mismatch, value/date mismatch, duplicates). Future pairs (GSTR-2A vs EWB Inward, GSTR-3B vs GSTR-1) must be addable without rewriting core logic.

## Decision

Build a **registry-based comparison engine**:

```python
# comparison/registry.py
comparison_registry.register(comparison_id, ComparisonConfig, comparator_fn)

# comparison/engine.py
class ComparisonEngine:
    def run(self, comparison_id, left_bytes, right_bytes, session_id) -> ComparisonResult:
        fn = comparison_registry.get(comparison_id)
        return fn(config, left_bytes, right_bytes, session_id)
```

Supporting design:

1. **Shared matchers** in `comparison/comparators/` — invoice, GSTIN, date, value, duplicate
2. **Normalizer** — single source for invoice number and amount normalization
3. **Result types** — enum `ComparisonResultType` for stable API filters
4. **Risk engine** — weighted scores per result type; overall level from peak score
5. **Observation generator** — officer-facing narrative from classified records
6. **Reference comparator** — `gstr1_vs_eway_outward.py` demonstrates full pipeline

Bootstrap registration in `comparison/bootstrap.py`; imported as side effect in `comparison_service.py`.

## Matching Strategy (GSTR-1 vs EWB Outward)

Primary key: **normalized invoice number**

Classification order for matched keys:

1. Duplicate check (either side)
2. Multiple GSTR-1 matches → `MULTIPLE_MATCHES`
3. GSTIN comparison
4. Date comparison (with tolerance)
5. Value comparison (with ₹1 rounding tolerance)
6. Else `MATCHED`

Unmatched EWB → `MISSING_IN_GSTR1`. Unmatched GSTR-1 → `MISSING_IN_EWAY`.

## Consequences

### Positive

- Adding GSTR-2A vs EWB Inward = one comparator file + bootstrap line
- Matchers unit-tested independently (`test_comparison_matchers.py`)
- Consistent `ComparisonResult` shape for investigation and intelligence downstream
- Paginated details API avoids huge JSON payloads

### Negative

- Invoice-number-only matching misses legitimate suffix/prefix variations (normalizer mitigates partially)
- Single-threaded in-process execution — large datasets block request
- Workbook bytes must be available server-side (cache or upload)

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| SQL-based reconciliation | Excel source of truth; pandas pipeline simpler |
| One monolithic compare function | Not extensible for new pairs |
| Fuzzy ML matching | Deterministic rules required for audit defensibility |

## References

- [COMPARISON_ENGINE.md](../COMPARISON_ENGINE.md)
- `backend/comparison/comparators/gstr1_vs_eway_outward.py`
- `backend/comparison/comparators/risk_engine.py`
