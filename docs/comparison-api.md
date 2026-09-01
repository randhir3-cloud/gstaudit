# Comparison Engine API

Base URL: `http://127.0.0.1:8000`

## Run GSTR-1 vs EWB Outward Comparison

`POST /api/comparison/gstr1-eway`

Request body:

```json
{
  "session_id": "session_abc123",
  "gstr1_workbook_base64": "<base64 merged GSTR-1 xlsx>",
  "ewb_outward_workbook_base64": "<base64 merged EWB outward xlsx>"
}
```

Response:

```json
{
  "session_id": "session_abc123",
  "status": "completed",
  "summary": {
    "matched_count": 4,
    "missing_in_gstr1_count": 1,
    "missing_in_eway_count": 1,
    "gstin_mismatch_count": 1,
    "value_mismatch_count": 1,
    "date_mismatch_count": 1,
    "duplicate_count": 0,
    "overall_risk_score": 100,
    "risk_level": "CRITICAL",
    "total_difference_amount": 590.0
  },
  "observations_count": 5
}
```

## Cache Workbook (optional)

`POST /api/comparison/cache-workbook`

```json
{
  "session_id": "session_abc123",
  "dataset_key": "gstr1",
  "workbook_base64": "<base64>"
}
```

## Get Comparison Status

`GET /api/comparison/{session_id}`

Returns status, summary, and completion timestamp.

## Get Summary

`GET /api/comparison/{session_id}/summary`

## Get Filtered Details

`GET /api/comparison/{session_id}/details?result_type=MISSING_IN_GSTR1&offset=0&limit=100`

Result types: `MATCHED`, `MISSING_IN_GSTR1`, `MISSING_IN_EWAY`, `GSTIN_MISMATCH`, `VALUE_MISMATCH`, `DATE_MISMATCH`, `DUPLICATE`, `MULTIPLE_MATCHES`, `UNKNOWN`

## Get Risk

`GET /api/comparison/{session_id}/risk`

## Get Audit Observations

`GET /api/comparison/{session_id}/observations`

## Dashboard Integration

After comparison completes:

- `session.discrepancies` counts are updated
- `comparison_status` for `gstr1_ewb_outward` becomes `completed`
- Dashboard `GET /api/dashboard` includes updated discrepancies and `comparison_summary`

## Architecture

```
comparison/
  engine.py          — runs registered comparators
  registry.py        — modular comparator registration
  normalizer.py      — invoice/GSTIN/date/amount normalization
  comparators/
    gstr1_vs_eway_outward.py  — reference implementation
    invoice_matcher.py
    gstin_matcher.py
    value_matcher.py
    date_matcher.py
    duplicate_matcher.py
    summary_builder.py
    risk_engine.py
    observation_generator.py
```

Future comparators (GSTR-3B vs GSTR-1, etc.) register via `comparison_registry.register(...)` without engine changes.
