# ADR-004: Investigation Workbench

**Status:** Accepted  
**Date:** 2026-07-09  
**Deciders:** GAIS core team

## Context

Comparison output produces hundreds of classified invoice records. Field officers need a **case management** layer to track verification status, assign priority, record remarks, and export subsets into formal audit reports — without re-processing Excel manually.

## Decision

Implement investigation as a **derived case layer** on top of comparison results:

```
ComparisonRecord (non-MATCHED)
    → InvestigationCase (stable case_id)
    → enriched by Audit Intelligence
    → officer updates persisted in investigation_store
```

Key design choices:

1. **Lazy sync** — `sync_cases_from_comparison()` runs on investigation API reads, not on every comparison write
2. **Stable case IDs** — SHA-256 hash of `session_id + invoice + result_type + index` (truncated to 12 hex)
3. **Preserve officer edits** — existing cases matched by `normalized_invoice + result_type` are not recreated
4. **Status workflow** — `Pending` → `Verified` / `Accepted` / `Rejected` / clarification states
5. **Intelligence merge** — `_apply_intelligence()` overlays priority, patterns, documents from intelligence layer
6. **Bulk operations** — `POST /api/investigation/bulk` for mass verification
7. **Report export** — `export_cases()` filters cases for `audit_report_service`

Case model: `backend/models/investigation.py`  
Service: `backend/services/investigation_service.py`

## Consequences

### Positive

- Officers work with cases, not raw comparison rows
- Investigation state survives comparison re-runs (matched by invoice key)
- Intelligence enrichment automatic on sync
- Dashboard case tracking panel reads same summary aggregates

### Negative

- Re-sync on every list request adds latency for large case sets
- Attachment model is metadata-only (no file upload in v0.1)
- Case ID includes record index — reordering comparison output could theoretically change IDs (mitigated by invoice+type key for preservation)

## Alternatives Considered

| Alternative | Why rejected |
|-------------|--------------|
| Edit comparison records directly | Mixes immutable analysis with workflow state |
| External case management tool | Integrated UX preferred for audit officers |
| Create all cases synchronously on comparison | Slows comparison API; lazy sync sufficient |

## References

- [INVESTIGATION_ENGINE.md](../INVESTIGATION_ENGINE.md)
- `backend/services/investigation_service.py`
- `frontend/src/pages/InvestigationPage.jsx`
- E2E: `e2e/investigation.spec.js`
