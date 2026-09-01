# Investigation Engine

The investigation engine transforms comparison discrepancies into **actionable audit cases** that officers can filter, prioritize, update, and export into audit reports.

## Purpose

After GSTR-1 vs EWB comparison, raw `ComparisonRecord` rows are not sufficient for field audit work. The investigation layer adds:

- Stable **case IDs** and human-readable case numbers
- **Workflow status** (Pending → Verified → Accepted/Rejected)
- **Officer remarks** and attachment metadata
- **Intelligence enrichment** (priority, patterns, recommended documents)
- **Bulk operations** for high-volume audits

## Architecture

```
comparison_store (ComparisonResult)
        │
        ▼
investigation_service.sync_cases_from_comparison()
        │
        ├── generate_observations() → possible_reason, officer_action
        ├── _record_to_case()       → InvestigationCase
        ├── analyze_session()       → intelligence enrichment
        └── investigation_store     → persist cases
        │
        ▼
GET /api/investigation  → filtered, paginated list
PATCH /api/investigation/{case_id} → officer updates
```

**Key files:**

| File | Role |
|------|------|
| `backend/services/investigation_service.py` | Case sync, filters, updates, export |
| `backend/services/investigation_store.py` | In-memory case persistence |
| `backend/models/investigation.py` | Pydantic models |
| `frontend/src/pages/InvestigationPage.jsx` | Workbench UI |
| `frontend/src/api/investigation.js` | API client |

## Case Identity

Case IDs are deterministic hashes:

```python
raw = f"{session_id}:{normalized_invoice}:{result_type}:{index}"
case_id = sha256(raw).hexdigest()[:12]
case_number = f"CASE-{case_id[:8].upper()}"
```

This ensures the same discrepancy always maps to the same case across syncs while preserving officer updates.

## Case Model

`InvestigationCase` (`backend/models/investigation.py`):

| Field group | Fields |
|-------------|--------|
| Identity | `case_id`, `case_number`, `session_id` |
| Invoice | `invoice_number`, `normalized_invoice`, dates, values, `ewb_number` |
| Parties | `supplier_gstin`, `recipient_gstin` |
| Classification | `result_type`, `comparison_result`, `comparison_type` |
| Risk | `risk_score`, `priority`, `difference_amount` |
| Guidance | `possible_reason`, `suggested_verification` |
| Intelligence | `priority_score`, `patterns`, `recommended_documents`, `gst_provisions`, `related_case_ids` |
| Workflow | `status`, `assigned_officer`, `officer_remarks`, `attachments` |

### Case statuses

`Pending` | `Verified` | `Accepted` | `Rejected` | `Needs Clarification` | `Additional Documents Required`

Closed statuses: `Accepted`, `Rejected`, `Verified`.

### Priority mapping

From comparison risk score (`investigation_service._priority`):

| Score | Priority |
|-------|----------|
| ≥ 95 | Critical |
| ≥ 70 | High |
| ≥ 40 | Medium |
| < 40 | Low |

Intelligence may override priority via `_apply_intelligence()`.

## Category Filters

UI categories map to result types (`CATEGORY_MAP`):

| Filter key | Label |
|------------|-------|
| `MISSING_IN_GSTR1` | Missing in GSTR-1 |
| `MISSING_IN_EWAY` | Missing in EWB |
| `GSTIN_MISMATCH` | GSTIN Mismatch |
| `VALUE_MISMATCH` | Value Mismatch |
| `DATE_MISMATCH` | Date Mismatch |
| `DUPLICATE` | Duplicate |
| `HIGH_RISK` | High Risk (score ≥ 70) |

## Sync Behavior

`sync_cases_from_comparison(session_id)` runs on every investigation list/detail request:

1. Load existing cases from store (preserve officer edits)
2. Load comparison result; skip `MATCHED` records
3. For new discrepancies, create cases with observation hints
4. Run intelligence analysis; enrich all cases
5. Save merged case list

Existing cases matched by `normalized_invoice + result_type` are **not recreated** — remarks and status persist.

## API Endpoints

### List cases

`GET /api/investigation?session_id=...&category=...&offset=0&limit=50`

Query parameters:

| Param | Description |
|-------|-------------|
| `session_id` | Required |
| `category` | Result type or `HIGH_RISK` |
| `month` | Filter by source period substring |
| `gstin` | Supplier or recipient GSTIN |
| `risk_min` | Minimum risk score |
| `status` | Case status |
| `comparison_type` | e.g. `gstr1_ewb_outward` |
| `search` | Invoice number, case number, GSTIN |
| `high_risk_only` | Boolean shortcut for score ≥ 70 |

Response: `InvestigationListResponse` with `summary`, `cases`, `categories`.

### Case detail

`GET /api/investigation/{case_id}?session_id=...`

Returns single case with intelligence enrichment.

### Update case

`PATCH /api/investigation/{case_id}`

Body (`CaseUpdateRequest`):

```json
{
  "session_id": "session_abc123",
  "status": "Verified",
  "priority": "High",
  "assigned_officer": "AO-123",
  "officer_remarks": "Verified against books.",
  "attachments": {
    "notes": "Invoice copy on file",
    "reference_number": "INV-2023-001"
  }
}
```

### Bulk update

`POST /api/investigation/bulk`

```json
{
  "session_id": "session_abc123",
  "case_ids": ["abc123", "def456"],
  "status": "Verified",
  "officer_remarks": "Bulk verified after document review."
}
```

## Frontend Workbench

`InvestigationPage.jsx` layout:

```
┌──────────────────────────────────────────────────────────┐
│ InvestigationCategoryPanel  │  InvestigationDetailsPanel │
│ (filters + case list)       │  (selected case + actions) │
├──────────────────────────────────────────────────────────┤
│ ComparisonRecordsTable (related records)                    │
└──────────────────────────────────────────────────────────┘
```

Components:

- `InvestigationCategoryPanel.jsx` — category counts, case list
- `InvestigationDetailsPanel.jsx` — priority badge, remarks form, intelligence section
- `ComparisonRecordsTable.jsx` — tabular discrepancy data

Dashboard integration: `CaseTrackingPanel.jsx` shows open/closed/high-risk counts from dashboard API.

## Report Export Integration

`export_cases(session_id, case_ids?, high_risk_only?)` feeds:

- `POST /api/report/generate` — Excel, PDF, DOCX via `audit_report_service`

Officers can export all cases, selected IDs, or high-risk subset.

## Testing

```bash
cd backend
pytest tests/test_investigation_service.py -v
```

E2E: `e2e/investigation.spec.js` — workbench open, case remark, bulk verify, report export.

Evidence screenshots: `docs/evidence/2026-07-09/17-investigation-workbench.png` through `19-investigation-bulk.png`.

## Related

- [AUDIT_INTELLIGENCE.md](./AUDIT_INTELLIGENCE.md)
- [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md)
- [DECISIONS/ADR-004-Investigation.md](./DECISIONS/ADR-004-Investigation.md)
