# Backend Architecture

The GAIS backend is a FastAPI application (`backend/main.py`) organized into services, domain packages, and Pydantic models.

## Request Lifecycle

```
HTTP Request
    → FastAPI route (main.py)
    → Service layer (services/*.py)
    → Domain logic (comparison/, intelligence/, merger.py)
    → Store (in-memory *_store.py)
    → Pydantic response / StreamingResponse
```

CORS middleware allows all origins in development. Custom response headers expose workbook metadata (`X-Workbook-Metadata`, `X-Suggested-Filename`).

## Package Layout

```
backend/
├── main.py                      # 37 HTTP endpoints
├── merger.py                    # GSTR-1 / GSTR-2A Excel merge
├── requirements.txt
├── Dockerfile
├── models/                      # Pydantic domain models
│   ├── audit_session.py         # AuditSession, DashboardResponse
│   ├── dealer_metadata.py       # DealerMetadata, workbook metadata
│   ├── investigation.py         # InvestigationCase, filters
│   ├── eway_classification.py   # Classify/validate responses
│   └── eway_merge.py            # EWB merge result models
├── services/                    # Application services
│   ├── audit_session_store.py   # Session CRUD (in-memory)
│   ├── dashboard_service.py     # Dashboard aggregation
│   ├── comparison_service.py    # Comparison orchestration
│   ├── comparison_store.py      # Comparison results + workbook cache
│   ├── investigation_service.py # Case sync, filters, updates
│   ├── investigation_store.py   # Case persistence
│   ├── audit_report_service.py  # Full audit report generation
│   ├── report_export.py         # Legacy dealer-only reports
│   ├── dealer_metadata_service.py
│   ├── dealer_validation.py
│   ├── eway_merge_service.py
│   ├── eway_classification_service.py
│   ├── eway_file_loader.py
│   ├── dealer_gstin_resolver.py
│   └── fy_months.py             # Financial year month parsing
├── comparison/                  # Comparison engine (domain)
│   ├── engine.py
│   ├── registry.py
│   ├── bootstrap.py             # Registers built-in comparators
│   ├── normalizer.py
│   ├── data_loader.py
│   ├── models.py                # ComparisonConfig, requests
│   ├── result_models.py         # ComparisonResult, ComparisonRecord
│   ├── comparison_types.py      # Enums: result types, risk levels
│   └── comparators/             # Matchers + reference comparator
└── intelligence/                # Audit intelligence (domain)
    ├── intelligence_service.py  # Orchestrator
    ├── intelligence_store.py    # Cache
    ├── pattern_detector.py
    ├── case_prioritizer.py
    ├── anomaly_detector.py
    ├── timeline_builder.py
    ├── executive_summary_generator.py
    ├── recommendation_engine.py
    ├── document_recommender.py
    ├── risk_classifier.py
    └── models.py
```

## Services

### Session & Dashboard

| Service | Key functions |
|---------|---------------|
| `audit_session_store` | `get_session`, `upsert_session` |
| `dashboard_service` | `build_dashboard`, `compute_readiness`, `build_month_coverage_map`, `ensure_session_datasets` |

`DashboardResponse` aggregates dataset statistics, upload health, duplicate detection, comparison status, discrepancies, and case tracking summary.

### Merge & EWB

| Service | Responsibility |
|---------|----------------|
| `merger.py` | Multi-file GSTR-1/GSTR-2A merge, missing month detection |
| `eway_merge_service` | Direction-aware EWB merge workflow |
| `eway_classification_service` | Classify EWB as outward/inward/unknown |
| `dealer_metadata_service` | Extract GSTIN, FY from uploaded workbooks |

### Comparison

`comparison_service.py`:

- Loads workbooks from request body or `comparison_store` cache
- Runs `ComparisonEngine.run(comparison_id, ...)`
- Applies `apply_result_to_session()` to update discrepancies
- Exposes paginated details, risk, observations

Side-effect import: `from comparison import bootstrap` registers comparators at startup.

### Investigation

`investigation_service.py`:

- `sync_cases_from_comparison()` — materializes cases from comparison records
- `_apply_intelligence()` — merges intelligence enrichment into cases
- Filtering, pagination, bulk update, export for reports

### Reports

| Service | Output |
|---------|--------|
| `audit_report_service` | Full session report: Excel, PDF, DOCX with cases + intelligence |
| `report_export` | Simpler dealer-metadata-only Excel/PDF |

## Models

All API contracts use Pydantic v2 `BaseModel`. Key aggregates:

- **`AuditSession`** — workflow state (datasets, history, discrepancies)
- **`DashboardResponse`** — computed view for frontend dashboard
- **`ComparisonResult`** — full comparison output with records, summary, observations
- **`InvestigationCase`** — workbench case with status, remarks, intelligence fields
- **`IntelligenceFullResponse`** — patterns, heatmaps, entity rankings, prioritized cases

## API Patterns

### Multipart file upload

```python
@app.post("/api/merge/gstr1")
async def api_merge_gstr1(files: List[UploadFile] = File(...), ignore_missing: bool = Query(False)):
    file_data = await _read_upload_files(files)
    ...
```

### JSON body with base64 workbooks

```python
class ComparisonRunRequest(BaseModel):
    session_id: str
    gstr1_workbook_base64: str = ""
    ewb_outward_workbook_base64: str = ""
```

### Structured domain errors

```python
except DealerValidationError as exc:
    return JSONResponse(status_code=400, content=exc.to_dict())
```

### Streaming binary responses

Reports and merged workbooks return `StreamingResponse` with `Content-Disposition` attachment headers.

## Comparison Engine Integration

See [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md). Registration in `comparison/bootstrap.py`:

```python
comparison_registry.register("gstr1_ewb_outward", GSTR1_EWB_CONFIG, compare_gstr1_vs_eway_outward)
```

## Intelligence Integration

`intelligence/intelligence_service.analyze_session(session_id)`:

1. Loads comparison result from store
2. Runs pattern detection, month analysis, supplier/customer ranking
3. Prioritizes each discrepancy case
4. Builds executive summary and heatmaps
5. Caches in `intelligence_store`

Called by `/api/intelligence/*` endpoints and indirectly during investigation sync.

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest                    # all tests
pytest tests/test_comparison_engine.py -v
```

Config: `backend/pytest.ini` — `testpaths = tests`, `pythonpath = .`

Test modules mirror services: `test_dashboard_service.py`, `test_investigation_service.py`, `test_intelligence_service.py`, etc.

## Running Locally

```bash
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Docker: `backend/Dockerfile` — Python 3.11-slim, exposes port 8000.

## Related

- [API_REFERENCE.md](./API_REFERENCE.md)
- [COMPARISON_ENGINE.md](./COMPARISON_ENGINE.md)
- [INVESTIGATION_ENGINE.md](./INVESTIGATION_ENGINE.md)
- [AUDIT_INTELLIGENCE.md](./AUDIT_INTELLIGENCE.md)
