# Audit Intelligence

Audit Intelligence is GAIS's analytical layer that turns comparison discrepancies into **prioritized insights**, **pattern findings**, **entity risk rankings**, and **document recommendations** for GST field officers.

## Overview

```
ComparisonResult (records)
        │
        ▼
intelligence_service.analyze_session(session_id)
        │
        ├── pattern_detector.py       → cross-record patterns
        ├── timeline_builder.py       → month-level analysis
        ├── anomaly_detector.py       → supplier/customer rankings
        ├── case_prioritizer.py       → per-case priority + causes
        ├── executive_summary_generator.py → cards + heatmaps
        ├── document_recommender.py   → evidence checklist
        └── intelligence_store.py     → cache results
```

**Entry point:** `backend/intelligence/intelligence_service.py`  
**Models:** `backend/intelligence/models.py`

## Output Structure

`IntelligenceFullResponse`:

| Section | Content |
|---------|---------|
| `summary` | Cards, patterns, heatmaps, executive insights, top priority cases |
| `months` | Per-month match/mismatch percentages, top entities |
| `suppliers` | Ranked supplier GSTINs by discrepancy impact |
| `customers` | Ranked customer GSTINs |
| `cases` | `CaseIntelligence` list sorted by priority_score |
| `document_recommendations` | Discrepancy-type → required documents |

## Intelligence Summary Components

### Audit Intelligence Cards

`AuditIntelligenceCards`:

- `high_risk_cases` — cases with elevated priority
- `critical_suppliers` / `critical_customers` — entity count above threshold
- `largest_tax_difference` — max value gap
- `highest_risk_month` — month with worst mismatch rate
- `open_investigation_cases` — pending workflow count

Displayed in `AuditIntelligencePanel.jsx` on dashboard and referenced in audit report preview.

### Pattern Findings

`pattern_detector.py` identifies:

| Pattern type | Example |
|--------------|---------|
| `repeated_missing_invoices` | Same customer with 2+ EWB invoices missing from GSTR-1 |
| `repeated_gstin_mismatch` | Recurring GSTIN pair mismatches |
| `value_cluster` | Multiple value mismatches in same month |
| `duplicate_cluster` | Duplicate invoice keys concentrated by entity |

Each `PatternFinding` includes severity, affected count, and entity list.

### Risk Heatmaps

`RiskHeatmaps` provides `HeatmapCell` arrays for:

- Months
- Suppliers
- Customers
- Discrepancy categories

Cells contain count, risk_score, risk_percent for visual density maps in UI and reports.

### Executive Insights

`ExecutiveInsights`:

- `top_observations` — narrative bullet points
- `top_risks` — highest-impact risk statements
- `largest_tax_impact` — aggregate difference amount
- `largest_supplier_risk` / `largest_customer_risk` — entity identifiers
- `months_requiring_verification` — month labels for field visits

### Case Intelligence

Per discrepancy case (`CaseIntelligence`):

| Field | Purpose |
|-------|---------|
| `priority` | Critical / High / Medium / Low |
| `priority_score` | Numeric rank (higher = more urgent) |
| `priority_reason` | Human-readable justification |
| `patterns` | Pattern types affecting this case |
| `recommended_documents` | Invoices, EWB printouts, ledger extracts |
| `possible_causes` | Tax law / process hypotheses |
| `suggested_verifications` | Step-by-step officer actions |
| `gst_provisions` | Relevant GST rule references |
| `related_case_ids` | Linked cases (same invoice, entity, type) |

Case prioritization: `case_prioritizer.py` combines risk score, pattern membership, value impact, and recurrence.

## Caching

`analyze_session(session_id, force=False)`:

1. Returns cached `IntelligenceFullResponse` from `intelligence_store` if present
2. Otherwise computes, saves, returns
3. Pass `force=True` to invalidate (not exposed via API in v0.1)

Cache invalidates naturally when backend process restarts (in-memory store).

## Integration Points

### Investigation

`investigation_service._apply_intelligence()` merges intelligence fields into `InvestigationCase` during sync. Officers see priority, patterns, and document lists in the workbench.

### Dashboard

`AuditIntelligencePanel.jsx` calls `/api/intelligence/summary` or full intelligence endpoint.

### Audit Report

`audit_report_service.build_report_preview()` embeds intelligence cards, patterns, and high-risk months. Preview page: `AuditReportPreview.jsx`.

## API Endpoints

All require `session_id` query parameter.

| Endpoint | Returns |
|----------|---------|
| `GET /api/intelligence` | Full `IntelligenceFullResponse` |
| `GET /api/intelligence/summary` | `IntelligenceSummary` only |
| `GET /api/intelligence/months` | `{ months: MonthAnalysis[] }` |
| `GET /api/intelligence/suppliers` | `{ suppliers: EntityRanking[] }` |
| `GET /api/intelligence/customers` | `{ customers: EntityRanking[] }` |
| `GET /api/intelligence/cases?limit=50` | Paginated priority cases |

Frontend client: `frontend/src/api/intelligence.js`

## Submodules

| Module | Function |
|--------|----------|
| `anomaly_detector.py` | `rank_suppliers`, `rank_customers` |
| `timeline_builder.py` | `build_month_analysis` |
| `risk_classifier.py` | Score → priority level mapping |
| `recommendation_engine.py` | Cross-cutting recommendation logic |
| `document_recommender.py` | `build_document_catalog` — static + dynamic doc lists |
| `executive_summary_generator.py` | `build_intelligence_summary` |

## Testing

```bash
cd backend
pytest tests/test_intelligence_service.py -v
```

E2E: `e2e/intelligence.spec.js`  
Evidence: `docs/evidence/2026-07-09/22-audit-intelligence-dashboard.png`, `23-audit-intelligence-patterns.png`

## Limitations (v0.1)

- Analysis scope is **GSTR-1 vs EWB Outward** comparison only
- No ML models — all rules are deterministic heuristics
- GST provision strings are template-based, not jurisdiction-configurable
- Supplier/customer names depend on data available in comparison records

## Related

- [INVESTIGATION_ENGINE.md](./INVESTIGATION_ENGINE.md)
- [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md)
- [API_REFERENCE.md](./API_REFERENCE.md)
