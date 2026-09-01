# API Reference

Complete HTTP API for GAIS backend (`backend/main.py`).

**Base URL (development):** `http://127.0.0.1:8000`  
**OpenAPI interactive docs:** `http://127.0.0.1:8000/docs`  
**Production (Docker Compose):** frontend proxies `/api/` → backend — use `http://localhost:8081/api/...`

**Total endpoints:** 37 route handlers (v0.1)

---

## Health

### 1. Health Check

`GET /health`

Response:

```json
{ "status": "healthy", "service": "Excel Merger API" }
```

---

## Dealer

### 2. Extract Dealer Metadata

`POST /api/dealer/extract`

| Param | In | Required | Description |
|-------|-----|----------|-------------|
| `files` | multipart | yes | GSTR workbook files |
| `return_type` | query | yes | `gstr1` or `gstr2a` |

Returns `WorkbookMetadataResponse` with `workbook_id`, `dealer`, `source_files`.

Errors: `400` — `DealerValidationError` JSON body.

---

## Legacy Reports (Dealer-Only)

### 3. Export Excel Report

`POST /api/reports/excel`

Form fields: `dealer_json`, `current_dataset`, `report_title`

Returns: Excel stream (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`).

### 4. Export PDF Report

`POST /api/reports/pdf`

Same form fields. Returns PDF stream.

---

## E-Way Bill

### 5. Classify EWB Files

`POST /api/eway/classify`

| Param | In | Description |
|-------|-----|-------------|
| `ewb_files` | multipart | EWB Excel files |
| `dealer_gstin` | query | Optional user GSTIN |
| `expected_direction` | query | `outward` or `inward` |
| `gstr1_files` | multipart | Optional cross-check |
| `gstr2a_files` | multipart | Optional cross-check |

Response: `EwayClassifyResponse` — per-file direction, status, confidence.

### 6. Validate EWB Batch

`POST /api/eway/validate`

Same params; `expected_direction` required. Returns `EwayValidateResponse`.

### 7. Merge EWB Outward

`POST /api/merge/eway/outward`

| Param | In | Description |
|-------|-----|-------------|
| `files` | multipart | EWB files |
| `ignore_missing` | query | Skip missing month warning |
| `dealer_gstin` | query | Optional GSTIN override |

Returns JSON merge result with `workbook_base64`, `row_count`, `sheet_list`, `dealer`, `suggested_filename`.

Errors: `400` — `EwayValidationError`.

### 8. Merge EWB Inward

`POST /api/merge/eway/inward`

Same as outward with inward classification.

### 9. Merge EWB (Legacy)

`POST /api/merge/eway`

Legacy undirected merge. Returns Excel stream attachment.

---

## GSTR Merge

### 10. Merge GSTR-1

`POST /api/merge/gstr1`

| Param | In | Description |
|-------|-----|-------------|
| `files` | multipart | Monthly GSTR-1 files |
| `ignore_missing` | query | Proceed despite month gaps |

Returns: merged Excel stream. Headers: `X-Suggested-Filename`, `X-Workbook-Metadata`.

Warning response (`400`): `{ "status": "warning", "error_type": "missing_months", "missing": [...] }`

### 11. Merge GSTR-2A

`POST /api/merge/gstr2a`

Same behavior as GSTR-1 for GSTR-2A files.

---

## Session & Dashboard

### 12. Sync Session

`POST /api/session/sync`

Body: full `AuditSession` JSON.

Returns: `DashboardResponse` (persisted + aggregated).

### 13. Get Dashboard

`GET /api/dashboard?session_id=`

Returns complete `DashboardResponse` or empty defaults if no session.

### 14. Month Coverage

`GET /api/dashboard/month-coverage?session_id=`

Returns per-dataset month upload map.

### 15. Statistics

`GET /api/dashboard/statistics?session_id=`

```json
{
  "per_module": { "gstr1": {...}, ... },
  "summary": { "files_uploaded": 0, ... }
}
```

### 16. Upload History

`GET /api/dashboard/upload-history?session_id=`

```json
{ "history": [ { "timestamp", "dataset", "filename", "rows", ... } ] }
```

### 17. Discrepancies

`GET /api/dashboard/discrepancies?session_id=`

Returns `DiscrepancySummary` object.

### 18. Readiness

`GET /api/dashboard/readiness?session_id=`

```json
{
  "readiness": { "gstr1": 100, "ewb_outward": 80, "overall": 90 },
  "audit_readiness_percent": 90.0,
  "can_start_audit": true,
  "audit_status": "draft"
}
```

---

## Comparison

### 19. Run GSTR-1 vs EWB Comparison

`POST /api/comparison/gstr1-eway`

Body:

```json
{
  "session_id": "session_abc123",
  "gstr1_workbook_base64": "",
  "ewb_outward_workbook_base64": ""
}
```

See [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md) for response shape.

### 20. Cache Workbook

`POST /api/comparison/cache-workbook`

Body: `{ "session_id", "dataset_key", "workbook_base64" }`

### 21. Get Comparison

`GET /api/comparison/{session_id}`

### 22. Get Comparison Summary

`GET /api/comparison/{session_id}/summary`

### 23. Get Comparison Details

`GET /api/comparison/{session_id}/details`

Query: `result_type`, `offset` (default 0), `limit` (default 100, max 1000)

### 24. Get Comparison Risk

`GET /api/comparison/{session_id}/risk`

### 25. Get Observations

`GET /api/comparison/{session_id}/observations`

---

## Investigation

### 26. List Investigation Cases

`GET /api/investigation?session_id=...`

Query filters: `category`, `month`, `gstin`, `risk_min`, `status`, `comparison_type`, `search`, `high_risk_only`, `offset`, `limit`.

### 27. Get Case Detail

`GET /api/investigation/{case_id}?session_id=...`

### 28. Update Case

`PATCH /api/investigation/{case_id}`

Body: `CaseUpdateRequest` (includes `session_id`).

### 29. Bulk Update Cases

`POST /api/investigation/bulk`

Body: `BulkCaseUpdateRequest` — `case_ids`, optional `status`, `officer_remarks`.

---

## Intelligence

### 30. Full Intelligence Analysis

`GET /api/intelligence?session_id=...`

### 31. Intelligence Summary

`GET /api/intelligence/summary?session_id=...`

### 32. Intelligence by Month

`GET /api/intelligence/months?session_id=...`

### 33. Supplier Rankings

`GET /api/intelligence/suppliers?session_id=...`

### 34. Customer Rankings

`GET /api/intelligence/customers?session_id=...`

### 35. Priority Cases

`GET /api/intelligence/cases?session_id=...&limit=50`

---

## Audit Report

### 36. Report Preview

`GET /api/report/preview?session_id=...`

Returns structured preview: dealer info, executive summary, intelligence cards, case counts.

### 37. Generate Report

`POST /api/report/generate?session_id=...&format=excel|pdf|docx&high_risk_only=false&case_ids=`

Returns binary stream with `Content-Disposition` attachment.

---

## Common Response Headers

| Header | When |
|--------|------|
| `Content-Disposition` | File downloads |
| `X-Suggested-Filename` | Merge responses |
| `X-Workbook-Metadata` | GSTR merge — JSON `WorkbookMetadataResponse` |

## Error Conventions

| Code | Meaning |
|------|---------|
| `400` | Validation error, missing months, domain errors |
| `404` | Session, comparison, or case not found |
| `500` | Unexpected server error |

Domain errors return JSON bodies with `error_type` and `message` fields where applicable.

## CORS

Development: `allow_origins=["*"]`. Restrict in production (see [SECURITY.md](./SECURITY.md)).

## Related

- [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md)
- [INVESTIGATION_ENGINE.md](./INVESTIGATION_ENGINE.md)
- [AUDIT_INTELLIGENCE.md](./AUDIT_INTELLIGENCE.md)
