# Comparison Engine

The GAIS comparison engine reconciles invoice-level records between two merged workbooks and produces classified discrepancies, risk scores, and audit observations.

> **Base URL (dev):** `http://127.0.0.1:8000`

## Overview

```
Workbooks (bytes)
    → data_loader.py          # Parse Excel to normalized records
    → invoice_matcher.py      # Build index by normalized invoice number
    → Per-record classification # gstin, date, value matchers
    → duplicate_matcher.py    # Duplicate detection
    → summary_builder.py      # Aggregate counts
    → risk_engine.py          # Score each record + overall level
    → observation_generator.py # Officer-facing audit observations
    → ComparisonResult        # Stored + applied to AuditSession
```

## Architecture

```
backend/comparison/
├── engine.py              # ComparisonEngine.run(comparison_id, left, right, session_id)
├── registry.py            # comparison_registry.register(id, config, fn)
├── bootstrap.py           # Registers gstr1_ewb_outward at import time
├── normalizer.py          # Invoice/GSTIN/date/amount normalization
├── data_loader.py         # load_gstr1_records, load_eway_outward_records
├── models.py              # ComparisonConfig, ComparisonRunRequest
├── result_models.py       # ComparisonResult, ComparisonRecord, ComparisonDetailPage
├── comparison_types.py    # ComparisonResultType, RiskLevel enums
└── comparators/
    ├── gstr1_vs_eway_outward.py   # Reference implementation (registered)
    ├── gstr2a_vs_eway_inward.py   # Stub — not yet registered
    ├── invoice_matcher.py
    ├── gstin_matcher.py
    ├── value_matcher.py
    ├── date_matcher.py
    ├── duplicate_matcher.py
    ├── summary_builder.py
    ├── risk_engine.py
    └── observation_generator.py
```

Orchestration: `backend/services/comparison_service.py`  
Persistence: `backend/services/comparison_store.py`

## Registered Comparisons

| ID | Left | Right | Function |
|----|------|-------|----------|
| `gstr1_ewb_outward` | GSTR-1 workbook | EWB Outward workbook | `compare_gstr1_vs_eway_outward` |

Registration (`comparison/bootstrap.py`):

```python
comparison_registry.register("gstr1_ewb_outward", GSTR1_EWB_CONFIG, compare_gstr1_vs_eway_outward)
```

Adding a new comparison requires **no changes** to `ComparisonEngine` — only register in bootstrap.

## Comparison Algorithm (GSTR-1 vs EWB Outward)

1. Load records from both workbooks via `data_loader`.
2. Detect duplicate invoice keys in each dataset.
3. Build invoice index: `normalized_invoice → [records]`.
4. **Iterate EWB records:**
   - Duplicate key → `DUPLICATE`
   - Multiple GSTR-1 matches → `MULTIPLE_MATCHES`
   - No GSTR-1 match → `MISSING_IN_GSTR1`
   - Else match and classify: GSTIN → Date → Value → `MATCHED` or mismatch type
5. **Remaining GSTR-1 records** not matched → `MISSING_IN_EWAY` or `DUPLICATE`.
6. Score each record; build summary and observations.

## Result Types

From `comparison/comparison_types.py`:

| Type | Meaning |
|------|---------|
| `MATCHED` | Invoice aligned on number, GSTIN, date, value |
| `MISSING_IN_GSTR1` | In EWB but not in GSTR-1 |
| `MISSING_IN_EWAY` | In GSTR-1 but not in EWB |
| `GSTIN_MISMATCH` | Invoice matched, GSTIN differs |
| `VALUE_MISMATCH` | GSTIN/date OK, amount differs |
| `DATE_MISMATCH` | GSTIN OK, date differs |
| `DUPLICATE` | Duplicate normalized invoice key |
| `MULTIPLE_MATCHES` | Ambiguous GSTR-1 matches |
| `UNKNOWN` | Unclassified |

## Risk Scoring

`risk_engine.py` assigns per-record scores (0–100) and overall `RiskLevel`:

| Result type | Weight |
|-------------|--------|
| MISSING_IN_GSTR1 | 100 |
| MISSING_IN_EWAY | 95 |
| GSTIN_MISMATCH | 80 |
| VALUE_MISMATCH | 70 (reduced to 10 if diff ≤ ₹1) |
| DATE_MISMATCH | 40 |
| MULTIPLE_MATCHES | 60 |
| DUPLICATE | 30 |

Overall level = f(max individual scores): CRITICAL ≥95, HIGH ≥80, MEDIUM ≥40, else LOW.

## API Endpoints

### Run GSTR-1 vs EWB Outward Comparison

`POST /api/comparison/gstr1-eway`

Request:

```json
{
  "session_id": "session_abc123",
  "gstr1_workbook_base64": "<optional — uses cache if omitted>",
  "ewb_outward_workbook_base64": "<optional>"
}
```

When base64 fields are empty, `comparison_service` loads workbooks from `comparison_store` cache populated during merge.

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

### Cache Workbook (optional)

`POST /api/comparison/cache-workbook`

```json
{
  "session_id": "session_abc123",
  "dataset_key": "gstr1",
  "workbook_base64": "<base64>"
}
```

Dataset keys: `gstr1`, `gstr2a`, `ewb_outward`, `ewb_inward`.

### Get Comparison Status

`GET /api/comparison/{session_id}`

Returns full comparison object: status, summary, timestamps, observation count.

### Get Summary

`GET /api/comparison/{session_id}/summary`

### Get Filtered Details (paginated)

`GET /api/comparison/{session_id}/details?result_type=MISSING_IN_GSTR1&offset=0&limit=100`

Returns `ComparisonDetailPage` with `records`, `total`, `offset`, `limit`.

### Get Risk

`GET /api/comparison/{session_id}/risk`

Returns risk breakdown: overall score, level, category weights.

### Get Audit Observations

`GET /api/comparison/{session_id}/observations`

```json
{
  "observations": [
    {
      "invoice_number": "...",
      "result_type": "MISSING_IN_GSTR1",
      "risk_score": 100,
      "observation_text": "...",
      "possible_reasons": ["..."],
      "officer_action": "Verify..."
    }
  ]
}
```

## Dashboard Integration

After comparison completes, `comparison_service.apply_result_to_session()`:

1. Updates `session.discrepancies` counts
2. Sets `comparison_status` for `gstr1_ewb_outward` → `completed`
3. Sets `audit_status` → `in_progress`

`GET /api/dashboard` includes updated discrepancies and comparison summary via `dashboard_service.build_dashboard()`.

Frontend: `ComparisonStatusCards.jsx` shows pair status; `ComparisonScreen.jsx` runs comparison and displays detail links.

## Normalization Rules

`comparison/normalizer.py` (high level):

- **Invoice numbers:** uppercase, strip spaces/special chars, leading-zero normalization
- **GSTIN:** 15-char uppercase validation
- **Dates:** parse multiple Excel date formats; compare with configurable tolerance via `ComparisonConfig.normalizer`
- **Amounts:** compare taxable/invoice values with tolerance (default ₹1 for rounding)

## Testing

```bash
cd backend
pytest tests/test_comparison_engine.py
pytest tests/test_comparison_matchers.py
pytest tests/test_comparison_normalizer.py
pytest tests/test_comparison_risk_observations.py
pytest tests/test_comparison_service.py
```

Fixtures: `backend/tests/comparison_fixtures.py`

E2E: `e2e/comparison.spec.js`

## Extending the Engine

1. Implement comparator function matching signature in `registry.py`.
2. Add `ComparisonConfig` with dataset keys and labels.
3. Register in `bootstrap.py`.
4. Add service method + route in `comparison_service.py` / `main.py`.
5. Add frontend pair in `COMPARISON_PAIRS` (`audit_session.py`) and UI.

Example future comparator: GSTR-3B vs GSTR-1 (not yet implemented).

## Related

- [API_REFERENCE.md](./API_REFERENCE.md)
- [INVESTIGATION_ENGINE.md](./INVESTIGATION_ENGINE.md)
- [DECISIONS/ADR-003-ComparisonEngine.md](./DECISIONS/ADR-003-ComparisonEngine.md)
- Legacy short doc: [comparison-api.md](./comparison-api.md)
